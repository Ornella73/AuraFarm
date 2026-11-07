"""Soil water balance engine and unified agronomic decision support.

Features:
- Hargreaves-Samani reference evapotranspiration (ET0) based on latitude and daily Tmin/Tmax
- Soil root-zone water reservoir accounting for total available water (TAW = taw_mm_m * depth_cm / 100)
- 21-day post-sowing seedling survival simulation detecting dessication below permanent wilting point
- Ideal sowing window calculation by variety cycle length and regional cessation dates
"""
import math
from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple, Any
from src.core.models import (
    Village,
    SoilProfile,
    Variety,
    CropType,
    RegimePluvio,
    ConfidenceLevel,
    ZoneProfile,
    SowingWindowResult,
    WaterBalanceStatus
)
from src.core.database import get_zone_profile, get_village_zone_mapping


def calculate_hargreaves_samani_et0(
    tmin_c: float,
    tmax_c: float,
    latitude_deg: float,
    day_of_year: int
) -> float:
    """Calculate daily reference evapotranspiration ET0 (mm/day) via Hargreaves-Samani (FAO-56 standard).
    
    Args:
        tmin_c: Minimum daily air temperature (°C)
        tmax_c: Maximum daily air temperature (°C)
        latitude_deg: Geographical latitude in decimal degrees (Togo: 6.0° to 11.2°N)
        day_of_year: Julian day of year (1-365)
    """
    phi = math.radians(latitude_deg)
    j = max(1, min(365, day_of_year))

    # Solar declination delta (radians)
    delta = 0.409 * math.sin(2.0 * math.pi * j / 365.0 - 1.39)

    # Inverse relative distance Earth-Sun dr
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * j / 365.0)

    # Sunset hour angle omega_s (radians)
    cos_omega_s = -math.tan(phi) * math.tan(delta)
    cos_omega_s = max(-1.0, min(1.0, cos_omega_s))
    omega_s = math.acos(cos_omega_s)

    # Extraterrestrial solar radiation Ra in MJ / (m^2 * day)
    g_sc = 0.0820  # Solar constant MJ / m^2 / min
    ra_mj = (24.0 * 60.0 / math.pi) * g_sc * dr * (
        omega_s * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(omega_s)
    )
    # Convert Ra from MJ/(m^2*day) to equivalent depth of water evaporation (mm/day)
    ra_mm = 0.408 * max(0.1, ra_mj)

    t_mean = (tmax_c + tmin_c) / 2.0
    tdiff = max(0.1, tmax_c - tmin_c)

    # FAO Hargreaves formula: ET0 = 0.0023 * (Tmean + 17.8) * sqrt(Tmax - Tmin) * Ra
    et0 = 0.0023 * (t_mean + 17.8) * math.sqrt(tdiff) * ra_mm
    return round(max(0.5, min(10.0, et0)), 2)


class SoilWaterReservoir:
    """Single-layer soil water balance reservoir for crop root zone."""

    def __init__(
        self,
        taw_mm_m: float,
        depth_cm: float,
        initial_fill_fraction: float = 0.50
    ):
        """
        Args:
            taw_mm_m: Total Available Water capacity per meter depth (mm/m)
            depth_cm: Effective root zone soil depth (cm)
            initial_fill_fraction: Initial water content relative to TAW (0.0=wilting point, 1.0=field capacity)
        """
        self.taw_mm_m = taw_mm_m
        self.depth_cm = depth_cm
        self.taw_mm = round(taw_mm_m * (depth_cm / 100.0), 1)
        self.current_water_mm = round(self.taw_mm * max(0.0, min(1.0, initial_fill_fraction)), 1)

    @property
    def soil_moisture_pct(self) -> float:
        """Percentage of plant-available water capacity currently available."""
        if self.taw_mm <= 0:
            return 0.0
        return round((self.current_water_mm / self.taw_mm) * 100.0, 1)

    @property
    def depletion_mm(self) -> float:
        """Root zone depletion below field capacity (mm)."""
        return round(max(0.0, self.taw_mm - self.current_water_mm), 1)

    @property
    def is_at_wilting_point(self) -> bool:
        """True if root zone available water is below 5% of TAW (wilting point)."""
        return self.current_water_mm <= (0.05 * self.taw_mm)

    def step(
        self,
        rainfall_mm: float,
        et0_mm: float,
        crop_stage_kc: float = 0.40,
        depletion_factor_p: float = 0.50
    ) -> Dict[str, float]:
        """Advance water balance by 1 day.
        
        Args:
            rainfall_mm: Daily precipitation (mm)
            et0_mm: Daily reference evapotranspiration (mm)
            crop_stage_kc: Crop coefficient (default 0.40 for emergence/initial stage)
            depletion_factor_p: Fraction of TAW that can be depleted without moisture stress
        """
        # Readily available water RAW = p * TAW
        raw_mm = depletion_factor_p * self.taw_mm

        # Water stress coefficient Ks
        if self.current_water_mm >= (self.taw_mm - raw_mm):
            ks = 1.0
        elif self.current_water_mm <= 0.0:
            ks = 0.0
        else:
            ks = self.current_water_mm / max(0.1, (self.taw_mm - raw_mm))
            ks = max(0.0, min(1.0, ks))

        # Actual crop evapotranspiration
        etc_act = ks * crop_stage_kc * et0_mm

        # Infiltration (precipitation stored up to field capacity; excess is runoff/deep drainage)
        available_capacity = self.taw_mm - self.current_water_mm
        infiltrated = min(rainfall_mm, available_capacity + etc_act)
        runoff = max(0.0, rainfall_mm - infiltrated)

        # Update storage
        new_storage = self.current_water_mm + infiltrated - etc_act
        self.current_water_mm = round(max(0.0, min(self.taw_mm, new_storage)), 1)

        return {
            "rainfall_mm": rainfall_mm,
            "infiltrated_mm": round(infiltrated, 1),
            "runoff_mm": round(runoff, 1),
            "etc_act_mm": round(etc_act, 2),
            "ks": round(ks, 2),
            "current_water_mm": self.current_water_mm,
            "soil_moisture_pct": self.soil_moisture_pct
        }


def simulate_post_sowing_21days(
    reservoir: SoilWaterReservoir,
    daily_rain: List[float],
    daily_tmax: List[float],
    daily_tmin: List[float],
    latitude_deg: float,
    start_doy: int
) -> Dict[str, Any]:
    """Simulate 21 days following hypothetical sowing to assess seedling dessication risk.
    
    A false start occurs if:
    1. Soil water drops to permanent wilting point (<= 5% of TAW) for >= 3 consecutive days, OR
    2. Minimum soil moisture drops below 10% under high evaporative demand (ET0 > 5 mm/day).
    """
    history = []
    consecutive_wilting_days = 0
    max_consecutive_wilting = 0
    min_moisture = 100.0

    # Clone reservoir state for simulation
    sim_res = SoilWaterReservoir(
        taw_mm_m=reservoir.taw_mm_m,
        depth_cm=reservoir.depth_cm,
        initial_fill_fraction=reservoir.current_water_mm / max(0.1, reservoir.taw_mm)
    )

    n_days = min(21, len(daily_rain))
    for i in range(n_days):
        doy = (start_doy + i - 1) % 365 + 1
        tmin = daily_tmin[i] if i < len(daily_tmin) else 22.0
        tmax = daily_tmax[i] if i < len(daily_tmax) else 33.0
        rain = daily_rain[i] if i < len(daily_rain) else 0.0

        et0 = calculate_hargreaves_samani_et0(tmin, tmax, latitude_deg, doy)
        step_out = sim_res.step(rain, et0, crop_stage_kc=0.40)
        history.append(step_out)

        m = step_out["soil_moisture_pct"]
        if m < min_moisture:
            min_moisture = m

        if sim_res.is_at_wilting_point:
            consecutive_wilting_days += 1
            if consecutive_wilting_days > max_consecutive_wilting:
                max_consecutive_wilting = consecutive_wilting_days
        else:
            consecutive_wilting_days = 0

    is_false_start_risk = (max_consecutive_wilting >= 3) or (min_moisture < 12.0)
    reasons = []
    if max_consecutive_wilting >= 3:
        reasons.append(f"Épuisement sous point de flétrissement pendant {max_consecutive_wilting} jours consécutifs.")
    if min_moisture < 12.0:
        reasons.append(f"Humidité minimale critique atteinte ({min_moisture:.1f}% de la réserve utile).")

    return {
        "is_false_start_risk": is_false_start_risk,
        "max_consecutive_wilting_days": max_consecutive_wilting,
        "min_soil_moisture_pct": round(min_moisture, 1),
        "final_soil_moisture_pct": sim_res.soil_moisture_pct,
        "reasons": reasons,
        "history": history
    }


def calculate_sowing_window(
    village: Village,
    variety: Variety,
    zone_profile: Optional[ZoneProfile] = None,
    current_soil: Optional[SoilProfile] = None,
    reference_date: Optional[date] = None
) -> SowingWindowResult:
    """Compute the ideal variety-specific sowing window bounded by rainy season cessation."""
    ref_date = reference_date or date.today()
    year = ref_date.year

    # 1. Floor date (window start baseline)
    zone_id = village.region.upper()
    if not zone_profile:
        zone_profile = get_zone_profile(zone_id)

    if zone_profile:
        earliest_month, earliest_day = map(int, zone_profile.season_1_earliest_sowing_date.split("-"))
    else:
        earliest_month, earliest_day = (5, 15) if village.regime_pluviometrique == RegimePluvio.UNIMODAL else (3, 15)

    window_start_dt = date(year, earliest_month, earliest_day)

    # 2. Regional rainy season cessation date (end of reliable rains)
    # Savanes: mid-October | Kara: late October | Centrale: end October | Plateaux/Maritime: mid-July (S1) or late Nov (S2)
    if village.regime_pluviometrique == RegimePluvio.UNIMODAL:
        cessation_dt = date(year, 10, 15) if "SAV" in village.village_id else date(year, 10, 25)
    elif village.regime_pluviometrique == RegimePluvio.TRANSITION_UNIMODAL:
        cessation_dt = date(year, 10, 31)
    else:
        # Bimodal: If current date is after July 15, calculate for season 2 (Petite saison)
        if ref_date >= date(year, 7, 15):
            window_start_dt = date(year, 9, 1)
            cessation_dt = date(year, 11, 20)
        else:
            cessation_dt = date(year, 7, 15)

    # 3. Latest safe sowing date: crop cycle MUST complete before soil dries out after rain cessation
    # Add buffer of 10 days of residual root moisture
    cycle_days = variety.cycle_days_nominal
    latest_safe_dt = cessation_dt + timedelta(days=10) - timedelta(days=cycle_days)
    if latest_safe_dt < window_start_dt:
        latest_safe_dt = window_start_dt + timedelta(days=15)

    # 4. Best sowing date: 5 to 10 days after window start (when rains are reliably established)
    best_dt = window_start_dt + timedelta(days=7)
    if best_dt > latest_safe_dt:
        best_dt = latest_safe_dt

    # 5. Baseline false start risk and confidence
    base_risk = (zone_profile.false_start_probability_baseline * 100.0) if zone_profile else 25.0

    # Soil modifier: low TAW soil increases risk
    taw = current_soil.taw_mm_m if current_soil else 100.0
    if taw < 80.0:
        base_risk += 12.0
    elif taw > 130.0:
        base_risk = max(5.0, base_risk - 8.0)

    confidence = ConfidenceLevel.SUR if base_risk < 20.0 else (
        ConfidenceLevel.ASSEZ_SUR if base_risk < 35.0 else ConfidenceLevel.INCERTAIN
    )

    # Estimated water satisfaction index for this variety cycle
    wsi = round(min(100.0, max(60.0, 100.0 - (base_risk * 0.4))), 1)

    reasons = [
        f"Cycle de la variété {variety.variety_name} : {cycle_days} jours.",
        f"Fin estimée des pluies utiles : {cessation_dt.strftime('%d/%m/%Y')}.",
        f"Dernier délai de semis recommandé : {latest_safe_dt.strftime('%d/%m/%Y')} pour garantir la maturité."
    ]

    return SowingWindowResult(
        village_id=village.village_id,
        village_name=village.village_name,
        crop_type=variety.crop_type,
        variety_id=variety.variety_id,
        variety_name=variety.variety_name,
        cycle_days=cycle_days,
        window_start=window_start_dt.strftime("%Y-%m-%d"),
        window_end=latest_safe_dt.strftime("%Y-%m-%d"),
        best_sowing_date=best_dt.strftime("%Y-%m-%d"),
        season_rain_cessation_date=cessation_dt.strftime("%Y-%m-%d"),
        false_start_probability_pct=round(base_risk, 1),
        confidence=confidence,
        water_satisfaction_index_pct=wsi,
        reasons=reasons
    )

