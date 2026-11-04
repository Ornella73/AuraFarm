"""Daily Precompute Engine generating decision sheets for all Togolese villages and crops."""
from datetime import datetime, date, timezone
from typing import List, Optional
from src.core.models import (
    Village,
    PrecalculatedSheet,
    CropType,
    AlertStatus,
    ConfidenceLevel
)
from src.core.database import save_precalculated_sheet, record_freshness
from src.data_ingestion.repositories import SpatialRepository
from src.data_ingestion.weather_service import WeatherService, WeatherData
from src.data_ingestion.freshness_watchdog import FreshnessWatchdog
from src.crop_models.resilience_scorer import CropResilienceScorer
from src.alerts.season_detector import SeasonDetector

class PrecomputeEngine:
    """Pre-calculates village decision sheets once daily.
    Enables sub-second lookup on low-bandwidth 2G USSD and Voice channels.
    """
    def __init__(
        self,
        repo: Optional[SpatialRepository] = None,
        weather_service: Optional[WeatherService] = None,
        watchdog: Optional[FreshnessWatchdog] = None
    ):
        self.repo = repo or SpatialRepository()
        self.weather_service = weather_service or WeatherService()
        self.watchdog = watchdog or FreshnessWatchdog()
        self.scorer = CropResilienceScorer()
        self.detector = SeasonDetector()

    def run_daily_pipeline(
        self,
        reference_date: Optional[date] = None,
        simulated_weather_scenario: Optional[str] = None
    ) -> List[PrecalculatedSheet]:
        """Execute pre-calculation for all registered villages and candidate crops."""
        ref_date = reference_date or date.today()
        calc_timestamp = datetime.now(timezone.utc).isoformat()
        generated_sheets: List[PrecalculatedSheet] = []

        villages = self.repo.list_villages()
        crops_to_process = [CropType.MAIS, CropType.SORGHO, CropType.NIEBE]

        for v in villages:
            soil = self.repo.get_soil_for_village(v.village_id)
            
            # Fetch weather
            weather = self.weather_service.get_weather_for_village(
                village=v,
                simulated_scenario=simulated_weather_scenario,
                reference_date=ref_date
            )

            # Record freshness for the source
            record_freshness(
                source_name=weather.source,
                timestamp_iso=weather.timestamp.isoformat(),
                status="OK",
                details=f"Village {v.village_id} updated."
            )

            for crop in crops_to_process:
                # 1. Filter candidate varieties
                candidates = self.repo.get_varieties_for_village_and_crop(v, crop)
                if not candidates:
                    # Fallback to general crop varieties if regional catalog is restricted
                    candidates = self.repo.list_varieties_for_crop(crop)

                # 2. Select best variety via resilience scoring
                best_var, var_conf, var_explanation = self.scorer.select_best_variety(
                    village=v,
                    soil=soil,
                    candidates=candidates,
                    season_month=ref_date.month
                )

                variety_id = best_var.variety_id if best_var else "VARIETE_LOCALE"
                variety_name = best_var.variety_name if best_var else "Variété locale"

                # 3. Detect season onset & false starts
                onset_res = self.detector.evaluate_onset(
                    village=v,
                    soil=soil,
                    weather=weather,
                    current_date=ref_date,
                    recommended_variety_name=variety_name
                )

                # 4. Strict Freshness Guard relative to the operational run date
                final_alert, is_stale, freshness_reason = self.watchdog.evaluate_safety(
                    proposed_alert=onset_res.alert_status,
                    last_weather_update=weather.timestamp,
                    has_recent_field_rain=weather.ground_obs_corrected,
                    reference_time=datetime(ref_date.year, ref_date.month, ref_date.day, 6, 0, tzinfo=timezone.utc)
                )

                # Merge confidence
                if is_stale:
                    confidence = ConfidenceLevel.INCERTAIN
                    advice_fr = (
                        f"AuraFarm {v.village_name} : Attention, données météo non actualisées. "
                        "Ne prenez pas de risque, consultez votre agent d'encadrement ICAT/ITRA."
                    )
                    local_text = onset_res.advice_local.get(
                        v.langue_majoritaire,
                        onset_res.advice_local[v.langue_majoritaire]
                    )
                else:
                    confidence = onset_res.confidence
                    advice_fr = onset_res.advice_fr
                    local_text = onset_res.advice_local.get(v.langue_majoritaire, advice_fr)

                # Build precalculated sheet
                sheet = PrecalculatedSheet(
                    village_id=v.village_id,
                    village_name=v.village_name,
                    crop_type=crop,
                    calculation_date=ref_date.isoformat(),
                    recommended_variety_id=variety_id,
                    recommended_variety_name=variety_name,
                    alert_status=final_alert,
                    confidence=confidence,
                    rain_last_3days_mm=weather.rain_last_3days_mm,
                    rain_forecast_7days_mm=weather.rain_forecast_7days_mm,
                    dry_spell_risk_days=weather.dry_spell_forecast_max_days,
                    is_data_stale=is_stale,
                    advice_fr=advice_fr,
                    advice_local=local_text,
                    audio_key_sequence=onset_res.audio_keys,
                    last_weather_update=weather.timestamp.isoformat()
                )

                # Save in local SQLite DB (< 1s retrieval for IVR/USSD)
                save_precalculated_sheet(sheet)
                generated_sheets.append(sheet)

        return generated_sheets
