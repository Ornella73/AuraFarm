"""Stateful USSD Session Engine conforming to GSM 03.38 standard (<= 160 characters)."""
import re
from datetime import datetime, date, timezone, timedelta
from typing import Dict, Any, Optional
from src.core.models import Language, CropType, AlertStatus, FieldRainObservation, FarmerProfile
from src.core.security import hash_phone_number
from src.core.database import (
    get_precalculated_sheet,
    save_field_observation,
    get_farmer_profile,
    save_farmer_profile,
    record_event,
    record_planting_report
)
from src.data_ingestion.repositories import SpatialRepository
from src.channels.base import UssdResponse

class UssdSessionEngine:
    """Manages USSD state transitions with strict <= 160 character screens and zero external API latency."""

    def __init__(self, repo: Optional[SpatialRepository] = None):
        self.repo = repo or SpatialRepository()
        # In-memory session store (session_id -> state dict)
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def process_request(self, session_id: str, phone_number: str, text: str) -> UssdResponse:
        """Handle incoming USSD request.
        'text' is the raw string of inputs delimited by '*' (standard Africa/GSM gateway convention).
        E.g. '' (start), '1' (first step), '1*2' (second step).
        """
        phone_hash = hash_phone_number(phone_number)
        profile = get_farmer_profile(phone_hash)

        # Parse cumulative user inputs (e.g. '', '4', '4*1', '4*3*18.5')
        inputs = [p.strip() for p in text.split("*") if p.strip()] if text else []
        
        session = self._sessions.get(session_id)
        if not session:
            # First interaction of this USSD session
            started_with_lang_menu = not bool(profile and profile.language)
            session = {
                "phone_number": phone_number,
                "phone_hash": phone_hash,
                "village_id": profile.village_id if profile else "TG_MAR_ZIO_01",
                "language": profile.language if profile else None,
                "primary_crop": profile.primary_crop if profile else CropType.MAIS,
                "started_with_lang_menu": started_with_lang_menu
            }
            self._sessions[session_id] = session

        if session["started_with_lang_menu"]:
            if not inputs:
                return UssdResponse(
                    text="AuraFarm Togo:\n1. Eʋegbe\n2. Kabɩyɛ\n3. Mina\n4. Français",
                    is_terminal=False
                )
            # First element of cumulative inputs is the language selection
            lang_choice = inputs[0]
            lang_map = {"1": Language.EWE, "2": Language.KABIYE, "3": Language.MINA, "4": Language.FRANCAIS}
            session["language"] = lang_map.get(lang_choice, Language.FRANCAIS)
            menu_inputs = inputs[1:]
        else:
            menu_inputs = inputs

        return self._handle_main_menu(session, menu_inputs)

    def _handle_main_menu(self, session: Dict[str, Any], inputs: list[str]) -> UssdResponse:
        lang = session["language"] or Language.FRANCAIS
        village = self.repo.get_village(session["village_id"])
        village_name = village.village_name if village else "Togo"

        if not inputs:
            # Show Main Menu (strictly <= 160 chars)
            if lang == Language.EWE:
                msg = (
                    f"AuraFarm {village_name}:\n"
                    f"1. Mado ku fífíia ?\n"
                    f"2. Nuku nyuitɔ\n"
                    f"3. Gblɔ tsi ƒe sesẽ\n"
                    f"4. Nye kɔƒe\n"
                    f"5. Medo ku vɔ\n"
                    f"6. Yɔm le ka dzi\n"
                    f"7. ICAT dɔwɔla"
                )
            elif lang == Language.KABIYE:
                msg = (
                    f"AuraFarm {village_name}:\n"
                    f"1. Mɑɖʊ tɛtʊ ?\n"
                    f"2. Pɩlɩʊ kɩbaŋʊ\n"
                    f"3. Kɛlɩ tɛʊ nɩʊ\n"
                    f"4. Ma-tɛtʊ\n"
                    f"5. Mɑɖʊ tɛtʊ tɛ\n"
                    f"6. Ya-m nɛ yaa\n"
                    f"7. ICAT tʊmɩyɛtʊ"
                )
            elif lang == Language.MINA:
                msg = (
                    f"AuraFarm {village_name}:\n"
                    f"1. Mado ku fifiia ?\n"
                    f"2. Nuku nyuitɔ\n"
                    f"3. Gblɔ tsi xexi\n"
                    f"4. Nye kɔƒe\n"
                    f"5. Medo nuku vɔ\n"
                    f"6. Yɔm kple gbe\n"
                    f"7. ICAT gbɔtɔ"
                )
            else:
                msg = (
                    f"AuraFarm {village_name}:\n"
                    f"1. Dois-je semer ?\n"
                    f"2. Variété adaptée\n"
                    f"3. Signaler la pluie\n"
                    f"4. Mon profil\n"
                    f"5. J'ai semé\n"
                    f"6. Rappel vocal gratuit\n"
                    f"7. Parler à un agent"
                )
            return UssdResponse(text=msg[:160], is_terminal=False)

        cmd = inputs[0]

        # 1. Dois-je semer ? (Sowing Decision)
        if cmd == "1":
            return self._handle_sowing_query(session, inputs[1:])

        # 2. Variété adaptée (Variety Details)
        elif cmd == "2":
            return self._handle_variety_query(session, inputs[1:])

        # 3. Signaler pluie (Field Rain Gauge submission)
        elif cmd == "3":
            return self._handle_rain_report(session, inputs[1:])

        # 4. Mon profil (et modification village / culture)
        elif cmd == "4":
            return self._handle_profile_menu(session, inputs[1:])

        # 5. J'ai semé (Déclaration de date de semis)
        elif cmd == "5":
            return self._handle_planting_declaration(session, inputs[1:])

        # 6. Rappel vocal gratuit
        elif cmd == "6":
            return self._handle_voice_callback(session)

        # 7. Parler à un agent (ICAT)
        elif cmd == "7":
            return self._handle_agent_contact(session, inputs[1:])

        # 0. Retour au Menu Principal
        elif cmd == "0":
            return self._handle_main_menu(session, [])

        # 9. Quitter
        elif cmd == "9":
            farewell = "Merci d'utiliser AuraFarm. À bientôt !" if lang == Language.FRANCAIS else "Akpe na mi !"
            return UssdResponse(text=farewell, is_terminal=True)

        else:
            return UssdResponse(text="Choix invalide. Réessayez.", is_terminal=False)

    def _handle_sowing_query(self, session: Dict[str, Any], sub_inputs: list[str]) -> UssdResponse:
        village_id = session["village_id"]
        crop = session.get("primary_crop", CropType.MAIS)
        lang = session.get("language") or Language.FRANCAIS
        
        # Sub-second retrieval from precalculated SQLite table
        sheet = get_precalculated_sheet(village_id, crop)
        village = self.repo.get_village(village_id)
        v_name = village.village_name if village else "Village"

        # Check sub-input: "1" to request a free voice call back
        if sub_inputs and sub_inputs[0] == "1":
            record_event(
                event_type="callback_request",
                village_id=village_id,
                channel="USSD",
                payload={"crop": crop.value, "origin": "sowing_screen"},
                phone_hash=session["phone_hash"]
            )
            if lang == Language.EWE:
                resp_text = "Míexɔ wò biabia! Míaƒo nu na wò le aɖabaƒoƒo 1 me le vɔvɔ̃ me."
            elif lang == Language.KABIYE:
                resp_text = "Ðɩmʊ ña-tɔm! Ðɩkaɣ-ŋ yaʊ faa cɛcɛka 1 taa."
            elif lang == Language.MINA:
                resp_text = "Míexɔ wò biabia! Mía yɔ wò le miniti 1 me faa."
            else:
                resp_text = "Demande reçue ! Vous allez recevoir un appel vocal gratuit dans 1 min."
            return UssdResponse(
                text=resp_text[:160],
                is_terminal=True
            )
        if sub_inputs and sub_inputs[0] == "0":
            return self._handle_main_menu(session, [])

        if not sheet:
            if lang == Language.EWE:
                not_found = f"AuraFarm {v_name}: Nyawo le bubum. Bip ICAT dɔwɔla."
            elif lang == Language.KABIYE:
                not_found = f"AuraFarm {v_name}: Tɔm wɛ kalʊʊ taa. Pɔzɩ ICAT tɔmɩyɛtʊ."
            elif lang == Language.MINA:
                not_found = f"AuraFarm {v_name}: Nyawo le bubum. Bip ICAT tɔ."
            else:
                not_found = f"AuraFarm {v_name}: Données en calcul. Consultez votre agent ICAT."
            return UssdResponse(
                text=not_found[:160],
                is_terminal=True
            )

        # Record real-time consultation event
        record_event(
            event_type="consultation",
            village_id=village_id,
            channel="USSD",
            payload={
                "type": "sowing_advice",
                "crop": crop.value,
                "status": sheet.alert_status.value,
                "variety": sheet.recommended_variety_name,
                "language": lang.value
            },
            phone_hash=session["phone_hash"]
        )

        # Build concise GSM 03.38 response in the chosen language (<= 160 chars)
        if lang == Language.EWE:
            if sheet.alert_status == AlertStatus.SEMER:
                status_text = "MÍATE ŊU AƑÃ FIFI !"
            elif sheet.alert_status == AlertStatus.RISQUE:
                status_text = f"NUXƆXLƆ̃ ! Kuɖiɖi {sheet.dry_spell_risk_days}ŋkeke le vavãm."
            elif sheet.alert_status == AlertStatus.ATTENDRE_CONSULTER_AGENT:
                status_text = "LALA ! Bip ICAT dɔwɔla."
            else:
                status_text = "LALA GBƆ̃ ! Tsi medza sɔgbɔ o."

            msg = (
                f"AuraFarm {v_name} [{crop.value.upper()}]:\n"
                f"{status_text}\n"
                f"Nuku: {sheet.recommended_variety_name}\n"
                f"Tsi 3j: {sheet.rain_last_3days_mm:.0f}mm\n"
                f"1. Yɔm le ka | 0. Menu"
            )
        elif lang == Language.KABIYE:
            if sheet.alert_status == AlertStatus.SEMER:
                status_text = "MƖPƖZƖƔ MƖDƲ TƐTƲ NƆƆNƆƆ !"
            elif sheet.alert_status == AlertStatus.RISQUE:
                status_text = f"KALAŊGBAŊƲ ! Wɩsɩ {sheet.dry_spell_risk_days}k le lɩʊ."
            elif sheet.alert_status == AlertStatus.ATTENDRE_CONSULTER_AGENT:
                status_text = "ƖDAŊ ! Pɔzɩ ICAT tɔmɩyɛtʊ."
            else:
                status_text = "ƖTAADƲ TƐTƲ ! Tɛʊ tɩtala."

            msg = (
                f"AuraFarm {v_name} [{crop.value.upper()}]:\n"
                f"{status_text}\n"
                f"Pɩlɩʊ: {sheet.recommended_variety_name}\n"
                f"Tɛʊ 3j: {sheet.rain_last_3days_mm:.0f}mm\n"
                f"1. Ya-m nɛ yaa | 0. Menu"
            )
        elif lang == Language.MINA:
            if sheet.alert_status == AlertStatus.SEMER:
                status_text = "MIATƐŊ ADO NUKU FIFIA !"
            elif sheet.alert_status == AlertStatus.RISQUE:
                status_text = f"KPƆ NYUIE ! Kuɖiɖi {sheet.dry_spell_risk_days}ŋkeke le vavãm."
            elif sheet.alert_status == AlertStatus.ATTENDRE_CONSULTER_AGENT:
                status_text = "LALA ! Bip ICAT tɔ."
            else:
                status_text = "MIGADO NUKU O ! Tsi mesɔ o."

            msg = (
                f"AuraFarm {v_name} [{crop.value.upper()}]:\n"
                f"{status_text}\n"
                f"Nuku: {sheet.recommended_variety_name}\n"
                f"Tsi 3j: {sheet.rain_last_3days_mm:.0f}mm\n"
                f"1. Yɔm kple gbe | 0. Menu"
            )
        else: # Français
            if sheet.alert_status == AlertStatus.SEMER:
                status_text = "SEMEZ DES MAINTENANT !"
            elif sheet.alert_status == AlertStatus.RISQUE:
                status_text = f"ATTENTION RISQUE ! Secheresse {sheet.dry_spell_risk_days}j prevue."
            elif sheet.alert_status == AlertStatus.ATTENDRE_CONSULTER_AGENT:
                status_text = "ATTENDEZ ! Consultez agent ICAT."
            else:
                status_text = "ATTENDEZ ! Pluie insuffisante."

            msg = (
                f"AuraFarm {v_name} [{crop.value.upper()}]:\n"
                f"{status_text}\n"
                f"Var: {sheet.recommended_variety_name}\n"
                f"Pluie 3j: {sheet.rain_last_3days_mm:.0f}mm. Conf: {sheet.confidence.value}\n"
                f"1. Rappel vocal | 0. Menu"
            )
        return UssdResponse(text=msg[:160], is_terminal=False)

    def _handle_variety_query(self, session: Dict[str, Any], sub_inputs: list[str]) -> UssdResponse:
        if sub_inputs and sub_inputs[0] == "0":
            return self._handle_main_menu(session, [])

        village_id = session["village_id"]
        crop = session.get("primary_crop", CropType.MAIS)
        lang = session.get("language") or Language.FRANCAIS
        sheet = get_precalculated_sheet(village_id, crop)
        variety_id = sheet.recommended_variety_id if sheet else "TZEE_W_SR"
        variety = self.repo.get_variety(variety_id)

        record_event(
            event_type="consultation",
            village_id=village_id,
            channel="USSD",
            payload={
                "type": "variety_query",
                "crop": crop.value,
                "variety": variety.variety_name if variety else variety_id
            },
            phone_hash=session["phone_hash"]
        )

        if not variety:
            if lang == Language.EWE:
                return UssdResponse(text="Nuku nyuitɔ: Bip ICAT dɔwɔla.", is_terminal=True)
            elif lang == Language.KABIYE:
                return UssdResponse(text="Pɩlɩʊ kɩbaŋʊ: Pɔzɩ ICAT tʊmɩyɛtʊ.", is_terminal=True)
            elif lang == Language.MINA:
                return UssdResponse(text="Nuku nyuitɔ: Bip ICAT tɔ.", is_terminal=True)
            return UssdResponse(text="Variété locale recommandée. Renseignez-vous auprès de votre coopérative.", is_terminal=True)

        if lang == Language.EWE:
            msg = (
                f"Nuku: {variety.variety_name}\n"
                f"Kɔsiɖa: {variety.cycle_days_nominal}ŋkeke | Dzɔdzɔ: {variety.potential_yield_t_ha}t/ha\n"
                f"Kuɖiɖi dɔ: {variety.drought_tolerance}\n"
                f"0. Menu"
            )
        elif lang == Language.KABIYE:
            msg = (
                f"Pɩlɩʊ: {variety.variety_name}\n"
                f"Kɩyakɩŋ: {variety.cycle_days_nominal} | Pɩlɩʊ: {variety.potential_yield_t_ha}t/ha\n"
                f"Wɩsɩ: {variety.drought_tolerance}\n"
                f"0. Menu"
            )
        elif lang == Language.MINA:
            msg = (
                f"Nuku: {variety.variety_name}\n"
                f"Ŋkeke: {variety.cycle_days_nominal} | Dzɔtɔ: {variety.potential_yield_t_ha}t/ha\n"
                f"Kuɖiɖi: {variety.drought_tolerance}\n"
                f"0. Menu"
            )
        else:
            msg = (
                f"Var: {variety.variety_name}\n"
                f"Cycle: {variety.cycle_days_nominal}j | Rend: {variety.potential_yield_t_ha}t/ha\n"
                f"Tol. secheresse: {variety.drought_tolerance}\n"
                f"Dispo semences: Cooperative\n"
                f"0. Menu"
            )
        return UssdResponse(text=msg[:160], is_terminal=False)

    def _handle_rain_report(self, session: Dict[str, Any], sub_inputs: list[str]) -> UssdResponse:
        lang = session.get("language") or Language.FRANCAIS
        if not sub_inputs:
            if lang == Language.EWE:
                prompt_text = "Tsi ƒe xexi:\nŊlɔ tsi dza le mm me (kpɔɖeŋu: 18.5) :\n0. Menu"
            elif lang == Language.KABIYE:
                prompt_text = "Tɛʊ nɩʊ tɔm:\nMa tɛʊ mm taa (kɩɖaʊ: 18.5) :\n0. Menu"
            elif lang == Language.MINA:
                prompt_text = "Tsi xexi:\nŊlɔ tsi le mm me (kpɔɖeŋu: 18.5) :\n0. Menu"
            else:
                prompt_text = "Releve pluviometre:\nEntrez la quantite de pluie tombee en mm (ex: 18.5) :\n0. Menu"
            return UssdResponse(text=prompt_text[:160], is_terminal=False)

        if sub_inputs[0] == "0":
            return self._handle_main_menu(session, [])

        val_str = sub_inputs[0].replace(",", ".")
        try:
            rain_mm = float(val_str)
            if rain_mm < 0 or rain_mm > 350:
                return UssdResponse(text="Valeur hors limites (0-350 mm). Verifiez et recommencez.", is_terminal=True)

            obs = FieldRainObservation(
                village_id=session["village_id"],
                observation_date=date.today().isoformat(),
                rainfall_mm=rain_mm,
                reporter_type="farmer",
                reported_at=datetime.now(timezone.utc).isoformat()
            )
            save_field_observation(obs)

            record_event(
                event_type="rain_report",
                village_id=session["village_id"],
                channel="USSD",
                payload={
                    "rainfall_mm": rain_mm,
                    "reporter_type": "farmer"
                },
                phone_hash=session["phone_hash"]
            )

            village = self.repo.get_village(session["village_id"])
            v_name = village.village_name if village else "village"

            if lang == Language.EWE:
                msg = f"Akpe ! Tsi {rain_mm:.1f} mm xɔ le {v_name} me. Nyawo trɔ le mɔ̃ dzi."
            elif lang == Language.KABIYE:
                msg = f"Ɛsɔ ɛwazɩ ! Tɛʊ {rain_mm:.1f} mm mʊwa {v_name} taa."
            elif lang == Language.MINA:
                msg = f"Akpe kaka ! Tsi {rain_mm:.1f} mm xɔ le {v_name} me."
            else:
                msg = f"Merci ! Pluie de {rain_mm:.1f} mm enregistree pour {v_name}. Le modele en tient compte."

            return UssdResponse(text=msg[:160], is_terminal=True)
        except ValueError:
            return UssdResponse(text="Format invalide. Entrez un nombre en mm (ex: 22).", is_terminal=True)

    def _handle_profile_menu(self, session: Dict[str, Any], sub_inputs: list[str]) -> UssdResponse:
        village_id = session["village_id"]
        village = self.repo.get_village(village_id)
        v_name = village.village_name if village else "Davié"
        region = village.region if village else "Maritime"
        crop = session.get("primary_crop", CropType.MAIS)

        if not sub_inputs:
            msg = (
                f"Profil AuraFarm {v_name}:\n"
                f"Region: {region}\n"
                f"Culture: {crop.value.upper()}\n"
                f"1. Changer village\n"
                f"2. Changer culture\n"
                f"0. Menu"
            )
            return UssdResponse(text=msg[:160], is_terminal=False)

        choice = sub_inputs[0]
        if choice == "0":
            return self._handle_main_menu(session, [])
        elif choice == "1":
            return self._handle_village_change(session, sub_inputs[1:])
        elif choice == "2":
            return self._handle_crop_change(session, sub_inputs[1:])
        else:
            return UssdResponse(text="Choix invalide.\n0. Menu", is_terminal=False)

    def _handle_planting_declaration(self, session: Dict[str, Any], sub_inputs: list[str]) -> UssdResponse:
        village_id = session["village_id"]
        crop = session.get("primary_crop", CropType.MAIS)
        lang = session.get("language") or Language.FRANCAIS
        sheet = get_precalculated_sheet(village_id, crop)
        var_name = sheet.recommended_variety_name if sheet else "Variété locale"
        village = self.repo.get_village(village_id)
        v_name = village.village_name if village else "Village"

        if not sub_inputs:
            if lang == Language.EWE:
                msg = (
                    f"Nuku dodo ({v_name}):\n"
                    f"Gbe ka gbe nèdo ku ?\n"
                    f"1. Egbe\n"
                    f"2. Ŋkeke 2 va yi\n"
                    f"3. Ŋkeke 5 va yi\n"
                    f"0. Menu"
                )
            elif lang == Language.KABIYE:
                msg = (
                    f"Mɩsɩ ɖʊʊ ({v_name}):\n"
                    f"Kɩyakʊ ŋgʊ ŋɖʊ mɩsɩ ?\n"
                    f"1. Sɔnɔ\n"
                    f"2. Kɩyakɩŋ 2 wayɩ\n"
                    f"3. Kɩyakɩŋ 5 wayɩ\n"
                    f"0. Menu"
                )
            elif lang == Language.MINA:
                msg = (
                    f"Nuku dodo ({v_name}):\n"
                    f"Ŋkeke tɛ nèdo ku ?\n"
                    f"1. Egbe\n"
                    f"2. Ŋkeke 2 va yi\n"
                    f"3. Ŋkeke 5 va yi\n"
                    f"0. Menu"
                )
            else:
                msg = (
                    f"Declaration de semis ({v_name}):\n"
                    f"Quand avez-vous seme ?\n"
                    f"1. Aujourd'hui\n"
                    f"2. Il y a 1-3 jours\n"
                    f"3. Il y a 4-7 jours\n"
                    f"0. Menu"
                )
            return UssdResponse(text=msg[:160], is_terminal=False)

        choice = sub_inputs[0]
        if choice == "0":
            return self._handle_main_menu(session, [])

        offset_map = {"1": 0, "2": -2, "3": -5}
        if choice in offset_map:
            offset = offset_map[choice]
            planted_date = (date.today() + timedelta(days=offset)).isoformat()
            record_planting_report(
                phone_hash=session["phone_hash"],
                village_id=village_id,
                crop_type=crop.value,
                variety_name=var_name,
                planted_date=planted_date
            )
            if lang == Language.EWE:
                msg = f"Akpe ! Nuku dodo xɔ le {v_name} [{crop.value.upper()}] me. Ŋkeke 21 gbɔna kpɔ̃m."
            elif lang == Language.KABIYE:
                msg = f"Ɛsɔ ɛwazɩ ! Ðɩmʊ ña-tɔm {v_name} [{crop.value.upper()}] taa."
            elif lang == Language.MINA:
                msg = f"Akpe kaka ! Míexɔ wò nuku dodo le {v_name} me."
            else:
                msg = (
                    f"Semis enregistre pour {v_name} [{crop.value.upper()}] !\n"
                    f"Suivi hydrique active pour proteger vos 21 premiers jours."
                )
            return UssdResponse(text=msg[:160], is_terminal=True)
        else:
            return UssdResponse(text="Choix invalide. Reessayez.", is_terminal=True)

    def _handle_voice_callback(self, session: Dict[str, Any]) -> UssdResponse:
        village_id = session["village_id"]
        crop = session.get("primary_crop", CropType.MAIS)
        lang = session.get("language") or Language.FRANCAIS
        record_event(
            event_type="callback_request",
            village_id=village_id,
            channel="USSD",
            payload={"crop": crop.value, "language": lang.value},
            phone_hash=session["phone_hash"]
        )
        if lang == Language.EWE:
            msg = "Míexɔ wò biabia ! Míaƒo nu na wò le Eʋegbe me le vɔvɔ̃ me le aɖabaƒoƒo 1 me."
        elif lang == Language.KABIYE:
            msg = "Ðɩmʊ ña-tɔm ! Ðɩkaɣ-ŋ yaʊ Kabɩyɛ taa faa cɛcɛka 1 taa."
        elif lang == Language.MINA:
            msg = "Míexɔ wò biabia ! Mía yɔ wò le Mina me faa le miniti 1 me."
        else:
            msg = "Demande recue ! Vous allez recevoir un appel vocal gratuit dans 1 minute."
        return UssdResponse(text=msg[:160], is_terminal=True)

    def _handle_agent_contact(self, session: Dict[str, Any], sub_inputs: list[str]) -> UssdResponse:
        village = self.repo.get_village(session["village_id"])
        region = village.region if village else "Maritime"

        agents = {
            "Maritime": ("Agent Kossi Mensah", "+228 90 12 34 56"),
            "Plateaux": ("Agente Akossiwa Adanlete", "+228 91 23 45 67"),
            "Centrale": ("Agent Essossinam Tchao", "+228 92 34 56 78"),
            "Kara": ("Agente Pyalo Bakali", "+228 93 45 67 89"),
            "Savanes": ("Agent Yendoube Combey", "+228 94 56 78 90")
        }
        agent_name, agent_tel = agents.get(region, ("Conseiller ICAT Togo", "+228 90 00 00 00"))

        if sub_inputs and sub_inputs[0] == "0":
            return self._handle_main_menu(session, [])

        msg = (
            f"Conseiller ICAT ({region}):\n"
            f"{agent_name}\n"
            f"Tel: {agent_tel}\n"
            f"Dispo: 7h-17h (Lun-Ven)\n"
            f"0. Menu"
        )
        return UssdResponse(text=msg[:160], is_terminal=False)

    def _handle_crop_change(self, session: Dict[str, Any], sub_inputs: list[str]) -> UssdResponse:
        crops = [
            (CropType.MAIS, "Maïs"),
            (CropType.SORGHO, "Sorgho"),
            (CropType.NIEBE, "Niébé")
        ]
        if not sub_inputs:
            lines = "\n".join(f"{i+1}. {name}" for i, (_, name) in enumerate(crops))
            msg = f"Choisir culture (Loi 2019-014):\n{lines}\n0. Menu"
            return UssdResponse(text=msg[:160], is_terminal=False)

        choice = sub_inputs[0]
        if choice == "0":
            return self._handle_main_menu(session, [])
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(crops):
                selected_crop, crop_label = crops[idx]
                session["primary_crop"] = selected_crop
                profile = get_farmer_profile(session["phone_hash"])
                if profile:
                    profile.primary_crop = selected_crop
                    save_farmer_profile(profile)
                else:
                    profile = FarmerProfile(
                        phone_hash=session["phone_hash"],
                        village_id=session["village_id"],
                        language=session.get("language") or Language.FRANCAIS,
                        primary_crop=selected_crop,
                        opt_in_voice=True,
                        opt_in_sms=True,
                        registered_at=datetime.now(timezone.utc).isoformat()
                    )
                    save_farmer_profile(profile)

                record_event(
                    event_type="crop_change",
                    village_id=session["village_id"],
                    channel="USSD",
                    payload={"crop": selected_crop.value},
                    phone_hash=session["phone_hash"]
                )
                return UssdResponse(
                    text=f"Culture configuree sur {crop_label} ! Alertes gratuites activees.",
                    is_terminal=True
                )
        except ValueError:
            pass
        return UssdResponse(text="Choix invalide. Reessayez.", is_terminal=True)

    def _handle_village_change(self, session: Dict[str, Any], sub_inputs: list[str]) -> UssdResponse:
        # Hierarchical selection: Step 1 = Region, Step 2 = Village
        regions = self.repo.get_regions()
        if not sub_inputs:
            reg_list = "\n".join(f"{i+1}. {r}" for i, r in enumerate(regions))
            return UssdResponse(text=f"Choisir votre region:\n{reg_list}\n0. Menu", is_terminal=False)

        if sub_inputs[0] == "0":
            return self._handle_main_menu(session, [])

        try:
            reg_idx = int(sub_inputs[0]) - 1
            if reg_idx < 0 or reg_idx >= len(regions):
                return UssdResponse(text="Region invalide.", is_terminal=True)
            chosen_region = regions[reg_idx]

            v_list = self.repo.get_villages_by_region(chosen_region)
            if len(sub_inputs) == 1:
                options = "\n".join(f"{i+1}. {v.village_name}" for i, v in enumerate(v_list[:5]))
                return UssdResponse(text=f"Choisir village ({chosen_region}):\n{options}\n0. Menu", is_terminal=False)

            if sub_inputs[1] == "0":
                return self._handle_main_menu(session, [])

            v_idx = int(sub_inputs[1]) - 1
            if v_idx < 0 or v_idx >= len(v_list):
                return UssdResponse(text="Village invalide.", is_terminal=True)

            selected_village = v_list[v_idx]
            session["village_id"] = selected_village.village_id

            # Save to permanent farmer profile
            profile = FarmerProfile(
                phone_hash=session["phone_hash"],
                village_id=selected_village.village_id,
                language=session["language"] or selected_village.langue_majoritaire,
                primary_crop=session.get("primary_crop", selected_village.culture_principale_1),
                opt_in_voice=True,
                opt_in_sms=True,
                registered_at=datetime.now(timezone.utc).isoformat()
            )
            save_farmer_profile(profile)

            record_event(
                event_type="village_change",
                village_id=selected_village.village_id,
                channel="USSD",
                payload={
                    "village_name": selected_village.village_name,
                    "region": chosen_region
                },
                phone_hash=session["phone_hash"]
            )

            return UssdResponse(
                text=f"Village configure sur {selected_village.village_name} ({selected_village.prefecture}) !",
                is_terminal=True
            )
        except ValueError:
            return UssdResponse(text="Erreur de saisie. Recommencez.", is_terminal=True)
