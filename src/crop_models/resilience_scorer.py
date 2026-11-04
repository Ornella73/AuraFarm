"""Crop Resilience Scorer based on Soil-Water Balance & FAO/AquaCrop crop yield response."""
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from src.core.models import Village, SoilProfile, Variety, CropType, RegimePluvio, ConfidenceLevel

@dataclass
class VarietyEvaluation:
    variety: Variety
    expected_yield_t_ha: float
    yield_potential_pct: float
    failure_rate_pct: float
    drought_risk_score: float  # 0 (low risk) to 100 (high risk)
    resilience_score: float     # 0 to 100 (higher is better)
    suitability_explanation: str

class CropResilienceScorer:
    """Evaluates crop varieties against soil water storage and seasonal rain patterns."""

    # FAO Ky coefficients (yield response factor to water deficit)
    KY_FACTORS: Dict[CropType, float] = {
        CropType.MAIS: 1.25,    # High sensitivity to water stress, especially flowering
        CropType.SORGHO: 0.90,  # Moderate sensitivity, highly drought-hardy
        CropType.NIEBE: 0.85    # Low sensitivity, highly rustic legume
    }

    def evaluate_varieties(
        self,
        village: Village,
        soil: Optional[SoilProfile],
        candidates: List[Variety],
        season_month: int = 3
    ) -> List[VarietyEvaluation]:
        """Rank candidate varieties based on soil water retention and climate regime."""
        if not candidates:
            return []

        # Soil Available Water Capacity (mm)
        if soil:
            soil_storage_capacity_mm = soil.taw_mm_m * (soil.depth_cm / 100.0)
        else:
            soil_storage_capacity_mm = 100.0  # Safe default if soil data absent

        # Estimate seasonal rainfall budget based on historical climatology (1991-2025)
        seasonal_rain_mm, season_length_days = self._estimate_season_budget(village.regime_pluviometrique, season_month)

        evaluations: List[VarietyEvaluation] = []
        for var in candidates:
            eval_res = self._evaluate_single_variety(
                var=var,
                soil_storage_mm=soil_storage_capacity_mm,
                seasonal_rain_mm=seasonal_rain_mm,
                season_length_days=season_length_days
            )
            evaluations.append(eval_res)

        # Sort by resilience score descending
        evaluations.sort(key=lambda x: x.resilience_score, reverse=True)
        return evaluations

    def _estimate_season_budget(self, regime: RegimePluvio, month: int) -> Tuple[float, int]:
        """Estimate typical seasonal rainfall and length for the zone."""
        if regime == RegimePluvio.BIMODAL:
            # Main season (March-July) vs Short season (Sept-Nov)
            if 8 <= month <= 11:
                # Petite saison au Sud (courte: ~70 jours, ~250-350 mm)
                return 320.0, 75
            else:
                # Grande saison au Sud (~110 jours, ~500-750 mm)
                return 620.0, 115
        elif regime == RegimePluvio.TRANSITION_UNIMODAL:
            # Centrale (~130 jours, ~700-900 mm)
            return 800.0, 135
        else:
            # Savanes / Kara (Soudano-Sahélien: ~105-120 jours, ~550-750 mm)
            return 650.0, 110

    def _evaluate_single_variety(
        self,
        var: Variety,
        soil_storage_mm: float,
        seasonal_rain_mm: float,
        season_length_days: int
    ) -> VarietyEvaluation:
        ky = self.KY_FACTORS.get(var.crop_type, 1.0)
        
        # 1. Cycle length vs season length penalty
        cycle_nominal = var.cycle_days_nominal
        cycle_margin = season_length_days - cycle_nominal
        
        if cycle_margin < -10:
            # Cycle strictly exceeds season length: severe truncation risk
            cycle_penalty = 40.0
            failure_risk_cycle = 45.0
        elif cycle_margin < 0:
            cycle_penalty = 20.0
            failure_risk_cycle = 25.0
        else:
            cycle_penalty = 0.0
            failure_risk_cycle = 5.0

        # 2. Water supply vs Water demand
        # Effective water available = Seasonal rain + 50% of soil storage buffer
        effective_water = seasonal_rain_mm + (0.5 * soil_storage_mm)
        water_ratio = min(1.2, effective_water / max(1.0, var.water_req_mm))
        
        # Relative ET deficit (1 - ETa / ETc)
        water_deficit = max(0.0, 1.0 - min(1.0, water_ratio))
        
        # FAO-56 Yield reduction: (1 - Ky * deficit)
        yield_ratio = max(0.2, 1.0 - (ky * water_deficit))
        
        # Drought tolerance bonus
        drought_bonus = {
            "tres_forte": 10.0,
            "forte": 6.0,
            "moyenne": 2.0,
            "faible": 0.0
        }.get(var.drought_tolerance, 4.0)

        # Failure rate (% of seasons failing to achieve 40% yield)
        estimated_failure_rate = min(95.0, max(2.0, (water_deficit * 65.0) + failure_risk_cycle - (drought_bonus * 0.8)))

        # Expected yield (t/ha)
        expected_yield = round(var.potential_yield_t_ha * yield_ratio * (1.0 - (cycle_penalty / 100.0)), 2)
        yield_pct = round(yield_ratio * 100.0, 1)

        # Composite Resilience Score (0 to 100)
        resilience = (
            (yield_pct * 0.45) +
            ((100.0 - estimated_failure_rate) * 0.40) +
            (drought_bonus * 1.5) -
            cycle_penalty
        )
        resilience_score = round(max(5.0, min(99.0, resilience)), 1)
        drought_risk = round(max(5.0, min(95.0, (water_deficit * 100.0) - drought_bonus)), 1)

        # Contextual explanation
        if cycle_margin < -5:
            explanation = (
                f"Variété {var.variety_name} : cycle long ({cycle_nominal}j) risquant d'être écourté "
                f"par la fin de saison ({season_length_days}j). Résilience limitée."
            )
        elif drought_risk > 35:
            explanation = (
                f"Variété {var.variety_name} : besoin hydrique ({var.water_req_mm:.0f}mm) élevé face "
                f"à la réserve du sol ({soil_storage_mm:.0f}mm). Risque en cas de sécheresse."
            )
        else:
            explanation = (
                f"Variété {var.variety_name} : excellent ajustement au sol ({soil_storage_mm:.0f}mm) "
                f"et cycle ({cycle_nominal}j) adapté. Tolérance sécheresse {var.drought_tolerance}."
            )

        return VarietyEvaluation(
            variety=var,
            expected_yield_t_ha=expected_yield,
            yield_potential_pct=yield_pct,
            failure_rate_pct=round(estimated_failure_rate, 1),
            drought_risk_score=drought_risk,
            resilience_score=resilience_score,
            suitability_explanation=explanation
        )

    def select_best_variety(
        self,
        village: Village,
        soil: Optional[SoilProfile],
        candidates: List[Variety],
        season_month: int = 3
    ) -> Tuple[Optional[Variety], ConfidenceLevel, str]:
        """Return the best variety along with confidence and reasoning."""
        evals = self.evaluate_varieties(village, soil, candidates, season_month)
        if not evals:
            return None, ConfidenceLevel.INCERTAIN, "Aucune variété disponible localement pour cette zone."

        top = evals[0]
        # Assign confidence level
        if top.resilience_score >= 75.0 and top.failure_rate_pct <= 15.0:
            confidence = ConfidenceLevel.SUR
        elif top.resilience_score >= 60.0 and top.failure_rate_pct <= 30.0:
            confidence = ConfidenceLevel.ASSEZ_SUR
        else:
            confidence = ConfidenceLevel.INCERTAIN

        return top.variety, confidence, top.suitability_explanation
