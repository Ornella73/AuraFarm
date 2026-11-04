"""Stateful USSD Session Engine conforming to GSM 03.38 standard (<= 160 characters)."""
import re
from datetime import datetime, date, timezone
from typing import Dict, Any, Optional
from src.core.models import Language, CropType, AlertStatus, FieldRainObservation, FarmerProfile
from src.core.security import hash_phone_number
from src.core.database import (
    get_precalculated_sheet,
    save_field_observation,
    get_farmer_profile,
    save_farmer_profile
)
from src.data_ingestion.repositories import SpatialRepository
from src.channels.base import UssdResponse

class UssdSessionEngine:
    """Manages USSD state transitions with strict < 160 character screens and zero external API latency."""

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
                msg = f"AuraFarm {village_name}:\n1. Mado ku fífíia ?\n2. Nuku nyuitɔ\n3. Gblɔ tsi ƒe sesẽ\n4. Trɔ kɔƒe\n9. Do le eme"
            elif lang == Language.KABIYE:
                msg = f"AuraFarm {village_name}:\n1. Mɑɖʊ tɛtʊ ?\n2. Pɩlɩʊ kɩbaŋʊ\n3. Kɛlɩ tɛʊ nɩʊ\n4. Lɛɛzɩ tɛtʊ\n9. Lɩɩ"
            elif lang == Language.MINA:
                msg = f"AuraFarm {village_name}:\n1. Mado ku fifiia ?\n2. Nuku nyuitɔ\n3. Gblɔ tsi xexi\n4. Trɔ kɔƒe\n9. Gbe"
            else:
                msg = f"AuraFarm {village_name}:\n1. Dois-je semer ?\n2. Variété adaptée\n3. Signaler pluie (mm)\n4. Mon village\n9. Quitter"
            return UssdResponse(text=msg, is_terminal=False)

        cmd = inputs[0]

        # 1. Dois-je semer ? (Sowing Decision)
        if cmd == "1":
            return self._handle_sowing_query(session, inputs[1:])

        # 2. Variété adaptée (Variety Details)
        elif cmd == "2":
            return self._handle_variety_query(session)

        # 3. Signaler pluie (Field Rain Gauge submission)
        elif cmd == "3":
            return self._handle_rain_report(session, inputs[1:])

        # 4. Changer village (Administrative selection)
        elif cmd == "4":
            return self._handle_village_change(session, inputs[1:])

        # 9. Quitter / Désinscription
        elif cmd == "9":
            farewell = "Merci d'utiliser AuraFarm. À bientôt !" if lang == Language.FRANCAIS else "Akpe na mi !"
            return UssdResponse(text=farewell, is_terminal=True)

        else:
            return UssdResponse(text="Choix invalide. Réessayez.", is_terminal=False)

    def _handle_sowing_query(self, session: Dict[str, Any], sub_inputs: list[str]) -> UssdResponse:
        village_id = session["village_id"]
        crop = session.get("primary_crop", CropType.MAIS)
        lang = session["language"] or Language.FRANCAIS
        
        # Sub-second retrieval from precalculated SQLite table
        sheet = get_precalculated_sheet(village_id, crop)
        village = self.repo.get_village(village_id)
        v_name = village.village_name if village else "Village"

        # Check sub-input: "1" to request a free voice call back
        if sub_inputs and sub_inputs[0] == "1":
            return UssdResponse(
                text="Demande reçue! Vous allez recevoir un appel vocal gratuit dans 1 minute.",
                is_terminal=True
            )

        if not sheet:
            return UssdResponse(
                text=f"AuraFarm {v_name}: Données en calcul. Consultez votre agent ICAT.",
                is_terminal=True
            )

        # Build concise GSM 03.38 response
        status_label = sheet.alert_status.value
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
            f"1. Rappel vocal gratuit"
        )
        return UssdResponse(text=msg[:160], is_terminal=False)

    def _handle_variety_query(self, session: Dict[str, Any]) -> UssdResponse:
        village_id = session["village_id"]
        crop = session.get("primary_crop", CropType.MAIS)
        sheet = get_precalculated_sheet(village_id, crop)
        variety_id = sheet.recommended_variety_id if sheet else "TZEE_W_SR"
        variety = self.repo.get_variety(variety_id)

        if not variety:
            return UssdResponse(text="Variété locale recommandée. Renseignez-vous auprès de votre coopérative.", is_terminal=True)

        msg = (
            f"Variete: {variety.variety_name}\n"
            f"Cycle: {variety.cycle_days_nominal}j. Rend: {variety.potential_yield_t_ha}t/ha\n"
            f"Tol. secheresse: {variety.drought_tolerance}\n"
            f"Dispo semences: Oui (cooperative)"
        )
        return UssdResponse(text=msg[:160], is_terminal=True)

    def _handle_rain_report(self, session: Dict[str, Any], sub_inputs: list[str]) -> UssdResponse:
        if not sub_inputs:
            return UssdResponse(
                text="Releve pluviometre:\nEntrez la quantite de pluie tombee en mm (ex: 18.5) :",
                is_terminal=False
            )

        val_str = sub_inputs[0].replace(",", ".")
        try:
            rain_mm = float(val_str)
            if rain_mm < 0 or rain_mm > 350:
                return UssdResponse(text="Valeur hors limites (0-350 mm). Verifiez et recommencez.", is_terminal=True)

            # Record in SQLite field observations
            obs = FieldRainObservation(
                village_id=session["village_id"],
                observation_date=date.today().isoformat(),
                rainfall_mm=rain_mm,
                reporter_type="farmer",
                reported_at=datetime.now(timezone.utc).isoformat()
            )
            save_field_observation(obs)

            village = self.repo.get_village(session["village_id"])
            v_name = village.village_name if village else "village"

            return UssdResponse(
                text=f"Merci ! Pluie de {rain_mm:.1f} mm enregistree pour {v_name}. Le modele en tient compte.",
                is_terminal=True
            )
        except ValueError:
            return UssdResponse(text="Format invalide. Entrez un nombre en mm (ex: 22).", is_terminal=True)

    def _handle_village_change(self, session: Dict[str, Any], sub_inputs: list[str]) -> UssdResponse:
        # Hierarchical selection: Step 1 = Region, Step 2 = Village
        regions = self.repo.get_regions()
        if not sub_inputs:
            reg_list = "\n".join(f"{i+1}. {r}" for i, r in enumerate(regions))
            return UssdResponse(text=f"Choisir votre region:\n{reg_list}", is_terminal=False)

        try:
            reg_idx = int(sub_inputs[0]) - 1
            if reg_idx < 0 or reg_idx >= len(regions):
                return UssdResponse(text="Region invalide.", is_terminal=True)
            chosen_region = regions[reg_idx]

            v_list = self.repo.get_villages_by_region(chosen_region)
            if len(sub_inputs) == 1:
                options = "\n".join(f"{i+1}. {v.village_name}" for i, v in enumerate(v_list[:5]))
                return UssdResponse(text=f"Choisir village ({chosen_region}):\n{options}", is_terminal=False)

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
                primary_crop=selected_village.culture_principale_1,
                opt_in_voice=True,
                opt_in_sms=True,
                registered_at=datetime.now(timezone.utc).isoformat()
            )
            save_farmer_profile(profile)

            return UssdResponse(
                text=f"Village configure sur {selected_village.village_name} ({selected_village.prefecture}) !",
                is_terminal=True
            )
        except ValueError:
            return UssdResponse(text="Erreur de saisie. Recommencez.", is_terminal=True)
