"""Backtesting engine validating false season start detection and sowing alerts."""
from datetime import date
from typing import Dict, List, Any
from src.core.models import Village, AlertStatus, RegimePluvio, CropType, Language
from src.data_ingestion.repositories import SpatialRepository
from src.data_ingestion.weather_service import WeatherService, WeatherData
from src.alerts.season_detector import SeasonDetector

class BacktestEngine:
    def __init__(self, repo: SpatialRepository):
        self.repo = repo
        self.weather_service = WeatherService()
        self.detector = SeasonDetector()

    def run_benchmark(self) -> Dict[str, Any]:
        """Run full backtest suite across multiple agro-climatic scenarios and villages."""
        villages = self.repo.list_villages()
        if not villages:
            return {"error": "No villages available in repository"}

        results = {
            "total_tests": 0,
            "optimal_onsets_detected": 0,
            "false_starts_averted": 0,
            "insufficient_rains_blocked": 0,
            "pre_season_rains_blocked": 0,
            "critical_errors": 0,  # e.g. emitting SEMER during a false start
            "scenarios": []
        }

        # Select 3 benchmark villages representing South, Center, and North Togo
        benchmark_villages = [
            v for v in villages if v.village_id in ["TG_MAR_ZIO_01", "TG_CEN_TCH_01", "TG_SAV_TON_01"]
        ]
        if not benchmark_villages:
            benchmark_villages = villages[:3]

        for v in benchmark_villages:
            soil = self.repo.get_soil_for_village(v.village_id)

            # 1. Test Optimal Onset in-season
            in_season_date = date(2025, 4, 15) if v.regime_pluviometrique == RegimePluvio.BIMODAL else date(2025, 6, 1)
            w_opt = self.weather_service.get_weather_for_village(v, simulated_scenario="optimal_onset", reference_date=in_season_date)
            res_opt = self.detector.evaluate_onset(v, soil, w_opt, current_date=in_season_date)
            results["total_tests"] += 1
            if res_opt.alert_status == AlertStatus.SEMER:
                results["optimal_onsets_detected"] += 1
            else:
                results["critical_errors"] += 1
            results["scenarios"].append({
                "village": v.village_name,
                "scenario": "optimal_onset",
                "alert": res_opt.alert_status.value,
                "confidence": res_opt.confidence.value,
                "success": res_opt.alert_status == AlertStatus.SEMER
            })

            # 2. Test False Start (Big initial rain followed by 9 dry days)
            w_false = self.weather_service.get_weather_for_village(v, simulated_scenario="false_start", reference_date=in_season_date)
            res_false = self.detector.evaluate_onset(v, soil, w_false, current_date=in_season_date)
            results["total_tests"] += 1
            if res_false.alert_status in (AlertStatus.RISQUE, AlertStatus.ATTENDRE):
                results["false_starts_averted"] += 1
            else:
                # Emitting SEMER during a false start is a catastrophic error for smallholders!
                results["critical_errors"] += 1
            results["scenarios"].append({
                "village": v.village_name,
                "scenario": "false_start",
                "alert": res_false.alert_status.value,
                "confidence": res_false.confidence.value,
                "success": res_false.alert_status == AlertStatus.RISQUE
            })

            # 3. Test Insufficient Rain (< 20mm)
            w_insuff = self.weather_service.get_weather_for_village(v, simulated_scenario="insufficient_rain", reference_date=in_season_date)
            res_insuff = self.detector.evaluate_onset(v, soil, w_insuff, current_date=in_season_date)
            results["total_tests"] += 1
            if res_insuff.alert_status == AlertStatus.ATTENDRE:
                results["insufficient_rains_blocked"] += 1
            results["scenarios"].append({
                "village": v.village_name,
                "scenario": "insufficient_rain",
                "alert": res_insuff.alert_status.value,
                "confidence": res_insuff.confidence.value,
                "success": res_insuff.alert_status == AlertStatus.ATTENDRE
            })

            # 4. Test Pre-season Rain before floor date (e.g. Feb 15 in South, March 15 in North)
            pre_season_date = date(2025, 2, 10)
            w_pre = self.weather_service.get_weather_for_village(v, simulated_scenario="optimal_onset", reference_date=pre_season_date)
            res_pre = self.detector.evaluate_onset(v, soil, w_pre, current_date=pre_season_date)
            results["total_tests"] += 1
            if res_pre.alert_status == AlertStatus.ATTENDRE:
                results["pre_season_rains_blocked"] += 1
            results["scenarios"].append({
                "village": v.village_name,
                "scenario": "pre_season_isolated_storm",
                "alert": res_pre.alert_status.value,
                "confidence": res_pre.confidence.value,
                "success": res_pre.alert_status == AlertStatus.ATTENDRE
            })

        # Calculate metrics
        results["accuracy_pct"] = round(
            ((results["total_tests"] - results["critical_errors"]) / max(1, results["total_tests"])) * 100.0, 1
        )
        results["false_start_safety_rate_pct"] = round(
            (results["false_starts_averted"] / max(1, len(benchmark_villages))) * 100.0, 1
        )

        return results
