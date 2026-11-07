"""Agro-climatic What-If Simulation and Sensitivity Analysis Engine for AuraFarm.

Provides:
1. Fast (< 500 ms) perturbation simulations:
   - Rainfall variation (-40% to +40%)
   - Temperature shift (-2°C to +4°C)
   - Soil Total Available Water (TAW) modifier (0.5x to 1.5x)
   - Sowing delay (0 to 30 days)
   - Artificial dry spell injection (post-sowing seedling test)
2. Sensitivity Tornado analysis measuring impacts on:
   - Sowing onset date shift (days)
   - False start probability delta (%)
   - Crop water stress days count
3. Chart-ready time-series payloads for the 6 interactive dataviz components.
"""
import math
from datetime import date, timedelta
from typing import Dict, Any, List, Optional, Tuple
from src.core.models import CropType, RegimePluvio
from src.data_ingestion.repositories import SpatialRepository
from src.core.database import get_zone_profile, get_village_zone_mapping, list_zone_profiles
from src.data_ingestion.stochastic_weather import StochasticWeatherGenerator
from src.agro_climate.water_balance import (
    calculate_hargreaves_samani_et0,
    SoilWaterReservoir,
    calculate_sowing_window
)


def _detect_onset_day(
    rainfall_series: List[float],
    min_3day_rain: float = 20.0,
    max_subsequent_dry_spell: int = 7,
    search_start_day: int = 60,  # March 1st onwards
    search_end_day: int = 220    # August 10th
) -> Tuple[Optional[int], bool]:
    """Detect onset of rainy season using standard FAO/AGRHYMET criterion.
    Returns (onset_doy, has_false_start).
    """
    n = len(rainfall_series)
    for i in range(search_start_day - 1, min(search_end_day, n - 22)):
        # 3-day rainfall sum
        three_day_sum = rainfall_series[i] + rainfall_series[i + 1] + rainfall_series[i + 2]
        if three_day_sum >= min_3day_rain:
            # Check subsequent 21 days for lethal dry spell
            subsequent = rainfall_series[i + 3 : i + 24]
            max_dry = 0
            current_dry = 0
            for r in subsequent:
                if r < 1.0:
                    current_dry += 1
                    if current_dry > max_dry:
                        max_dry = current_dry
                else:
                    current_dry = 0
            
            if max_dry > max_subsequent_dry_spell:
                # This is a false start
                return i + 1, True
            else:
                # Valid onset
                return i + 1, False

    return None, False


def run_perturbation_simulation(
    village_id: str = "TG_MAR_ZIO_01",
    crop_type: str = "mais",
    rain_factor: float = 1.0,
    temp_delta_c: float = 0.0,
    taw_factor: float = 1.0,
    delay_days: int = 0,
    dry_spell_injection: Optional[int] = None,
    dry_spell_start_day: int = 7,
    seed: int = 42
) -> Dict[str, Any]:
    """Execute rapid deterministic what-if scenario and compute all resulting dynamics."""
    repo = SpatialRepository()
    village = repo.get_village(village_id)
    if not village:
        village = repo.get_village("TG_MAR_ZIO_01")
        village_id = "TG_MAR_ZIO_01"

    mapping = get_village_zone_mapping(village_id)
    zone = mapping["zone"] if mapping else get_zone_profile("MARITIME")
    soil_summary = mapping["village_soil"] if mapping else None

    # Base soil properties
    base_taw_m = soil_summary.taw_mm_m if soil_summary else 120.0
    base_depth_cm = soil_summary.depth_cm if soil_summary else 100.0
    effective_taw_m = max(40.0, min(220.0, base_taw_m * taw_factor))

    # Generate synthetic weather
    generator = StochasticWeatherGenerator(zone_profile=zone, seed=seed)
    season_baseline = generator.generate_season(year=2026)

    # Build perturbed weather series
    baseline_records = season_baseline.daily_records
    days_count = len(baseline_records)

    base_rain: List[float] = [r.rainfall_mm for r in baseline_records]
    pert_rain: List[float] = [round(max(0.0, r.rainfall_mm * rain_factor), 1) for r in baseline_records]

    base_tmin: List[float] = [r.tmin_c for r in baseline_records]
    pert_tmin: List[float] = [round(r.tmin_c + temp_delta_c, 1) for r in baseline_records]

    base_tmax: List[float] = [r.tmax_c for r in baseline_records]
    pert_tmax: List[float] = [round(r.tmax_c + temp_delta_c, 1) for r in baseline_records]

    # Detect baseline onset
    base_onset_doy, base_false_start = _detect_onset_day(base_rain)

    # Detect perturbed onset (before dry spell injection to see if trigger shifts)
    pert_onset_doy, _ = _detect_onset_day(pert_rain)

    # Apply dry spell injection if requested
    if dry_spell_injection and dry_spell_injection > 0 and pert_onset_doy:
        inject_start = min(days_count - 1, pert_onset_doy + dry_spell_start_day)
        inject_end = min(days_count, inject_start + dry_spell_injection)
        for d in range(inject_start, inject_end):
            pert_rain[d] = 0.0

    # Re-evaluate false start on perturbed rain
    if pert_onset_doy:
        # Check 21 days after onset
        sub = pert_rain[pert_onset_doy + 2 : min(days_count, pert_onset_doy + 23)]
        max_d = 0
        cur_d = 0
        for r in sub:
            if r < 1.0:
                cur_d += 1
                if cur_d > max_d:
                    max_d = cur_d
            else:
                cur_d = 0
        pert_false_start = max_d > 7
    else:
        pert_false_start = False

    # Simulate daily water balance for perturbed condition
    reservoir = SoilWaterReservoir(
        taw_mm_m=effective_taw_m,
        depth_cm=base_depth_cm,
        initial_fill_fraction=0.30
    )

    dates: List[str] = []
    days: List[int] = []
    et0_series: List[float] = []
    soil_storage_series: List[float] = []
    soil_moisture_pct_series: List[float] = []
    stress_days_count = 0
    cum_rain = 0.0
    cum_rain_series: List[float] = []

    for idx, rec in enumerate(baseline_records):
        doy = rec.day_of_year
        p_rain = pert_rain[idx]
        p_tmin = pert_tmin[idx]
        p_tmax = pert_tmax[idx]

        cum_rain = round(cum_rain + p_rain, 1)
        cum_rain_series.append(cum_rain)

        et0 = calculate_hargreaves_samani_et0(
            tmin_c=p_tmin,
            tmax_c=p_tmax,
            latitude_deg=village.latitude,
            day_of_year=doy
        )
        et0_series.append(et0)

        # Kc varies with crop stage (higher if after onset + delay)
        is_growing = pert_onset_doy and (doy >= pert_onset_doy + delay_days)
        kc = 0.85 if is_growing else 0.40

        step_res = reservoir.step(rainfall_mm=p_rain, et0_mm=et0, crop_stage_kc=kc)
        soil_storage_series.append(step_res["current_water_mm"])
        soil_moisture_pct_series.append(step_res["soil_moisture_pct"])

        if is_growing and step_res["soil_moisture_pct"] < 35.0:
            stress_days_count += 1

        days.append(doy)
        dates.append(rec.date)

    # Compute Sowing Window for crop
    c_type = CropType(crop_type.lower()) if crop_type.lower() in [c.value for c in CropType] else CropType.MAIS
    variety_id = "TZEE_W_SR" if c_type == CropType.MAIS else ("SORGHO_LOCAL" if c_type == CropType.SORGHO else "TN5_78")
    variety = repo.get_variety(variety_id)
    if not variety:
        var_list = repo.list_varieties()
        variety = var_list[0] if var_list else None

    window_res = None
    if variety:
        window_res = calculate_sowing_window(
            village=village,
            variety=variety,
            zone_profile=zone
        )

    # Baseline false start risk %
    base_risk_pct = round(zone.false_start_probability_baseline * 100.0, 1)
    pert_risk_pct = round(
        max(5.0, min(95.0, base_risk_pct * (1.6 if rain_factor < 0.85 else (0.6 if rain_factor > 1.15 else 1.0)) + (20.0 if pert_false_start else 0.0))),
        1
    )

    base_onset_date = dates[base_onset_doy - 1] if base_onset_doy else "Non détecté"
    pert_onset_date = dates[pert_onset_doy - 1] if pert_onset_doy else "Non détecté"
    onset_shift = (pert_onset_doy - base_onset_doy) if (pert_onset_doy and base_onset_doy) else 0

    return {
        "village_id": village_id,
        "village_name": village.village_name,
        "region": village.region,
        "crop": c_type.value,
        "parameters": {
            "rain_factor": rain_factor,
            "temp_delta_c": temp_delta_c,
            "taw_factor": taw_factor,
            "delay_days": delay_days,
            "dry_spell_injection": dry_spell_injection,
            "seed": seed
        },
        "baseline": {
            "onset_day_of_year": base_onset_doy,
            "onset_date": base_onset_date,
            "has_false_start": base_false_start,
            "false_start_risk_pct": base_risk_pct,
            "total_rainfall_mm": round(sum(base_rain), 1),
            "mean_tmax_c": round(sum(base_tmax) / len(base_tmax), 1)
        },
        "perturbed": {
            "onset_day_of_year": pert_onset_doy,
            "onset_date": pert_onset_date,
            "has_false_start": pert_false_start,
            "false_start_risk_pct": pert_risk_pct,
            "total_rainfall_mm": round(sum(pert_rain), 1),
            "mean_tmax_c": round(sum(pert_tmax) / len(pert_tmax), 1),
            "water_stress_days": stress_days_count,
            "recommended_variety": variety.variety_name if variety else "TZEE-W-SR",
            "sowing_window_start": window_res.window_start if window_res else "2026-03-25",
            "sowing_window_end": window_res.window_end if window_res else "2026-04-15"
        },
        "delta": {
            "onset_shift_days": onset_shift,
            "rainfall_delta_mm": round(sum(pert_rain) - sum(base_rain), 1),
            "false_start_risk_delta_pct": round(pert_risk_pct - base_risk_pct, 1),
            "temp_delta_c": temp_delta_c,
            "stress_days": stress_days_count
        },
        "series": {
            "days": days,
            "dates": dates,
            "rain_baseline_mm": base_rain,
            "rain_perturbed_mm": pert_rain,
            "rain_cumulative_mm": cum_rain_series,
            "tmin_c": pert_tmin,
            "tmax_c": pert_tmax,
            "et0_mm": et0_series,
            "soil_water_storage_mm": soil_storage_series,
            "soil_moisture_pct": soil_moisture_pct_series,
            "raw_threshold_pct": 50.0,
            "wilting_threshold_pct": 5.0
        }
    }


def compute_sensitivity_tornado(
    village_id: str = "TG_MAR_ZIO_01",
    crop_type: str = "mais",
    seed: int = 42
) -> Dict[str, Any]:
    """Compute sensitivity tornado data evaluating elasticities of climatic and soil factors."""
    base = run_perturbation_simulation(village_id=village_id, crop_type=crop_type, seed=seed)
    base_onset = base["baseline"]["onset_day_of_year"] or 90
    base_risk = base["baseline"]["false_start_risk_pct"]

    perturbations = [
        ("Pluie -30%", {"rain_factor": 0.70}),
        ("Pluie +30%", {"rain_factor": 1.30}),
        ("Pluie -20%", {"rain_factor": 0.80}),
        ("Pluie +20%", {"rain_factor": 1.20}),
        ("Température +2°C", {"temp_delta_c": 2.0}),
        ("Température +4°C", {"temp_delta_c": 4.0}),
        ("Température -2°C", {"temp_delta_c": -2.0}),
        ("Rétention Sol -30%", {"taw_factor": 0.70}),
        ("Rétention Sol +30%", {"taw_factor": 1.30}),
        ("Sécheresse Post-Semis 10j", {"dry_spell_injection": 10})
    ]

    tornado_items = []
    for label, kwargs in perturbations:
        sim = run_perturbation_simulation(
            village_id=village_id,
            crop_type=crop_type,
            seed=seed,
            **kwargs
        )
        onset_shift = sim["delta"]["onset_shift_days"]
        risk_delta = sim["delta"]["false_start_risk_delta_pct"]
        stress = sim["delta"]["stress_days"]

        # Composite impact score for tornado sorting
        impact_score = abs(onset_shift) * 1.5 + abs(risk_delta) + (stress * 0.5)

        tornado_items.append({
            "factor": label,
            "onset_shift_days": onset_shift,
            "false_start_risk_delta_pct": risk_delta,
            "stress_days": stress,
            "impact_score": round(impact_score, 1)
        })

    # Sort descending by impact magnitude
    tornado_items.sort(key=lambda x: x["impact_score"], reverse=True)

    return {
        "village_id": village_id,
        "crop": crop_type,
        "baseline_onset_doy": base_onset,
        "baseline_false_start_risk_pct": base_risk,
        "tornado": tornado_items
    }


def get_dashboard_charts_data(
    village_id: str = "TG_MAR_ZIO_01",
    crop_type: str = "mais"
) -> Dict[str, Any]:
    """Provide comprehensive dataset structured specifically for the 6 interactive dashboard charts."""
    sim = run_perturbation_simulation(village_id=village_id, crop_type=crop_type, seed=42)
    tornado = compute_sensitivity_tornado(village_id=village_id, crop_type=crop_type, seed=42)

    repo = SpatialRepository()
    village = repo.get_village(village_id) or repo.get_village("TG_MAR_ZIO_01")
    zone_profiles = list_zone_profiles()

    # Chart 1: Rain & Cumulative Rain
    chart_rain = {
        "labels": sim["series"]["dates"],
        "daily_rain_mm": sim["series"]["rain_perturbed_mm"],
        "cumulative_rain_mm": sim["series"]["rain_cumulative_mm"],
        "onset_day_index": sim["perturbed"]["onset_day_of_year"] - 1 if sim["perturbed"]["onset_day_of_year"] else None,
        "has_false_start": sim["perturbed"]["has_false_start"]
    }

    # Chart 2: Temperature Profile
    chart_temp = {
        "labels": sim["series"]["dates"],
        "tmin_c": sim["series"]["tmin_c"],
        "tmax_c": sim["series"]["tmax_c"],
        "thermal_stress_threshold_c": 35.0
    }

    # Chart 3: Soil Water Reservoir
    chart_soil = {
        "labels": sim["series"]["dates"],
        "soil_moisture_pct": sim["series"]["soil_moisture_pct"],
        "storage_mm": sim["series"]["soil_water_storage_mm"],
        "field_capacity_pct": 100.0,
        "raw_threshold_pct": 50.0,
        "wilting_point_pct": 5.0
    }

    # Chart 4: Sowing Windows by Variety
    varieties = repo.list_varieties()
    v_windows = []
    for v in varieties[:6]:
        v_win = calculate_sowing_window(
            village=village,
            variety=v,
            zone_profile=get_zone_profile(village.region)
        )
        v_windows.append({
            "variety_name": v.variety_name,
            "crop": v.crop_type.value,
            "cycle_days": v.cycle_days_nominal,
            "start_date": v_win.window_start,
            "end_date": v_win.window_end,
            "window_days": (date.fromisoformat(v_win.window_end) - date.fromisoformat(v_win.window_start)).days
        })

    # Chart 5: Inter-zone comparison
    z_comparison = []
    for z in zone_profiles:
        z_comparison.append({
            "zone_id": z.zone_id,
            "zone_name": z.zone_name,
            "regime": z.regime.value,
            "annual_rainfall_mean_mm": z.annual_rainfall_mean_mm,
            "false_start_probability_baseline": round(z.false_start_probability_baseline * 100.0, 1),
            "season_1_earliest_sowing_date": z.season_1_earliest_sowing_date
        })

    return {
        "village_id": village_id,
        "village_name": village.village_name,
        "crop": crop_type,
        "chart_rain": chart_rain,
        "chart_temp": chart_temp,
        "chart_soil": chart_soil,
        "chart_windows": v_windows,
        "chart_zones": z_comparison,
        "chart_tornado": tornado["tornado"]
    }
