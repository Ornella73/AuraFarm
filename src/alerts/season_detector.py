"""Season onset and false start detector for West African rainfed agriculture."""
from datetime import date
from typing import Dict, List, Optional
from dataclasses import dataclass
from src.core.models import Village, SoilProfile, AlertStatus, ConfidenceLevel, Language, RegimePluvio
from src.data_ingestion.weather_service import WeatherData

@dataclass
class SeasonAlertResult:
    alert_status: AlertStatus
    confidence: ConfidenceLevel
    rain_last_3days_mm: float
    rain_forecast_7days_mm: float
    dry_spell_forecast_days: int
    is_false_start_risk: bool
    reasons: List[str]
    advice_fr: str
    advice_local: Dict[Language, str]
    audio_keys: List[str]

class SeasonDetector:
    """Detects rainfall onset and protects farmers against false season starts."""

    # Earliest calendar date threshold by regime (month, day)
    FLOOR_DATES: Dict[RegimePluvio, tuple[int, int]] = {
        RegimePluvio.BIMODAL: (3, 10),              # South: March 10th
        RegimePluvio.TRANSITION_UNIMODAL: (4, 20), # Central: April 20th
        RegimePluvio.UNIMODAL: (5, 10)              # North: May 10th
    }

    # Agronomic trigger thresholds (Sivakumar / AGRHYMET calibrated for Togo)
    RAIN_3DAY_MIN_THRESHOLD_MM = 20.0
    MAX_PERMISSIBLE_DRY_SPELL_DAYS = 7

    def evaluate_onset(
        self,
        village: Village,
        soil: Optional[SoilProfile],
        weather: WeatherData,
        current_date: Optional[date] = None,
        recommended_variety_name: str = "sélectionnée"
    ) -> SeasonAlertResult:
        cur_date = current_date or date.today()
        reasons: List[str] = []

        floor_month, floor_day = self.FLOOR_DATES.get(village.regime_pluviometrique, (3, 15))
        before_floor_date = (cur_date.month < floor_month) or (cur_date.month == floor_month and cur_date.day < floor_day)

        rain_3d = weather.rain_last_3days_mm
        dry_spell = weather.dry_spell_forecast_max_days
        forecast_7d = weather.rain_forecast_7days_mm

        # Adjust dry spell tolerance based on soil retention
        max_dry = self.MAX_PERMISSIBLE_DRY_SPELL_DAYS
        if soil and soil.taw_mm_m < 80:
            # Low water retention soil (e.g. sandy littoral or gravelly): lower tolerance to dry spells
            max_dry = 5
            reasons.append(f"Sol à faible réserve utile ({soil.taw_mm_m:.0f} mm/m) : tolérance sécheresse réduite à {max_dry}j.")

        is_false_start = False

        # --- DECISION LOGIC ---

        # Case 1: Pre-season rainfall before regional floor date
        if before_floor_date:
            status = AlertStatus.ATTENDRE
            confidence = ConfidenceLevel.SUR
            reasons.append(
                f"Date actuelle ({cur_date.strftime('%d/%m')}) antérieure à la date plancher "
                f"de la zone ({floor_day:02d}/{floor_month:02d}). Pluies précoces non fiables."
            )

        # Case 2: Sufficient trigger rain, BUT long dry spell forecast -> FALSE START RISK!
        elif rain_3d >= self.RAIN_3DAY_MIN_THRESHOLD_MM and dry_spell > max_dry:
            status = AlertStatus.RISQUE
            is_false_start = True
            confidence = ConfidenceLevel.SUR if dry_spell >= 9 else ConfidenceLevel.ASSEZ_SUR
            reasons.append(
                f"FAUX DÉPART DÉTECTÉ : Pluie initiale observée ({rain_3d:.1f} mm ≥ 20 mm), "
                f"mais une séquence sèche de {dry_spell} jours consécutifs est prévue. "
                "Risque majeur de dessèchement des jeunes plantules."
            )

        # Case 3: Sufficient trigger rain AND safe post-sowing forecast -> OPTIMAL SOWING
        elif rain_3d >= self.RAIN_3DAY_MIN_THRESHOLD_MM and dry_spell <= max_dry and forecast_7d >= 15.0:
            status = AlertStatus.SEMER
            confidence = ConfidenceLevel.SUR if weather.ground_obs_corrected else ConfidenceLevel.ASSEZ_SUR
            reasons.append(
                f"CONDITIONS OPTIMALES : Pluie efficace sur 3 jours ({rain_3d:.1f} mm ≥ 20 mm). "
                f"Séquence sèche maximale prévue ({dry_spell}j ≤ {max_dry}j) et bon relais ({forecast_7d:.1f} mm prévus)."
            )

        # Case 4: Insufficient trigger rain -> WAIT
        else:
            status = AlertStatus.ATTENDRE
            confidence = ConfidenceLevel.SUR if rain_3d < 10.0 else ConfidenceLevel.ASSEZ_SUR
            reasons.append(
                f"Pluie observée sur 3 jours ({rain_3d:.1f} mm) inférieure au seuil de semis (20 mm). "
                "L'humidité du sol reste insuffisante pour assurer la levée."
            )

        # Build translated advice messages
        advice_fr, advice_local, audio_keys = self._build_messages(
            status=status,
            village=village,
            variety_name=recommended_variety_name,
            dry_spell=dry_spell
        )

        return SeasonAlertResult(
            alert_status=status,
            confidence=confidence,
            rain_last_3days_mm=rain_3d,
            rain_forecast_7days_mm=forecast_7d,
            dry_spell_forecast_days=dry_spell,
            is_false_start_risk=is_false_start,
            reasons=reasons,
            advice_fr=advice_fr,
            advice_local=advice_local,
            audio_keys=audio_keys
        )

    def _build_messages(
        self,
        status: AlertStatus,
        village: Village,
        variety_name: str,
        dry_spell: int
    ) -> tuple[str, Dict[Language, str], List[str]]:
        """Generate structured messages and audio sequence keys."""
        if status == AlertStatus.SEMER:
            fr = f"AuraFarm {village.village_name} : SEMEZ dès maintenant. La variété recommandée est {variety_name}."
            local = {
                Language.EWE: f"AuraFarm {village.village_name} : Tsi dza nyuie. Miateŋu adó bli fífíia. Nuku nyuitɔe nye {variety_name}.",
                Language.KABIYE: f"AuraFarm {village.village_name} : Tɛʊ nɩwa camɩyɛ. Ɩpɩzɩɣ ɩdʊ tɛtʊ fɛɛŋ. Pɩlɩʊ kɩbaŋʊ: {variety_name}.",
                Language.MINA: f"AuraFarm {village.village_name} : Tsi dza nyuie. Miateŋu adó ku fifiia. Nuku nyuitɔ: {variety_name}.",
                Language.FRANCAIS: fr
            }
            audio = ["audio_intro", "audio_semer", f"audio_var_{variety_name.lower().replace('-', '_')}", "audio_rejouer_agent"]

        elif status == AlertStatus.RISQUE:
            fr = f"AuraFarm {village.village_name} : ATTENTION RISQUE de faux départ. Séquence sèche de {dry_spell} jours prévue. Ne semez pas !"
            local = {
                Language.EWE: f"AuraFarm {village.village_name} : Nyanyui kple nuxɔxlɔ̃ : Kuɖiɖi gbɔna ŋkeke {dry_spell}. Migado ku fifiia o !",
                Language.KABIYE: f"AuraFarm {village.village_name} : Kalaŋgbaŋʊ : Wɩsɩ kaɣ lɩʊ kɩyakɩŋ {dry_spell}. Ɩtaadʊ tɛtʊ, pɩkaɣ wɛɛkʊʊ !",
                Language.MINA: f"AuraFarm {village.village_name} : Kpɔ nyuie : Kuɖiɖi gbɔna ŋkeke {dry_spell}. Migadó ku o !",
                Language.FRANCAIS: fr
            }
            audio = ["audio_intro", "audio_risque_faux_depart", "audio_ne_pas_semer", "audio_rejouer_agent"]

        elif status == AlertStatus.ATTENDRE_CONSULTER_AGENT:
            fr = f"AuraFarm {village.village_name} : Données météo en cours d’actualisation. Ne semez pas, consultez votre agent ICAT/ITRA."
            local = {
                Language.EWE: f"AuraFarm {village.village_name} : Mielala vie boŋ. Miegadodɔ nuku o, miabia gbedela ICAT gbɔ.",
                Language.KABIYE: f"AuraFarm {village.village_name} : Ɩɖaŋ pazɩ. Ɩtaadʊ tɛtʊ, ɩpɔzɩ ICAT tʊmɩyɛ tʊ cɔlɔ.",
                Language.MINA: f"AuraFarm {village.village_name} : Midzudzɔ kpoo. Migadó ku o, ne miabia afɔdola ICAT tɔgbɔ.",
                Language.FRANCAIS: fr
            }
            audio = ["audio_intro", "audio_securite_stale", "audio_consulter_agent"]

        else: # ATTENDRE
            fr = f"AuraFarm {village.village_name} : Pluie encore insuffisante. ATTENDEZ avant d'engager vos semis."
            local = {
                Language.EWE: f"AuraFarm {village.village_name} : Tsi la mede o. Miegandó ku kaba o, milala vie.",
                Language.KABIYE: f"AuraFarm {village.village_name} : Tɛʊ tatasɩ nɩʊ camɩyɛ. Ɩtaadʊ tɛtʊ lɔŋ, ɩɖaŋ pazɩ.",
                Language.MINA: f"AuraFarm {village.village_name} : Tsi mede o. Midzudzɔ, migadó ku dodo o.",
                Language.FRANCAIS: fr
            }
            audio = ["audio_intro", "audio_attendre_pluie", "audio_rejouer_agent"]

        return fr, local, audio
