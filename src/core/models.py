"""Core Pydantic domain models and enumerations for AuraFarm."""
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

class AlertStatus(str, Enum):
    SEMER = "SEMER"
    ATTENDRE = "ATTENDRE"
    RISQUE = "RISQUE"
    ATTENDRE_CONSULTER_AGENT = "ATTENDRE_CONSULTER_AGENT"

class ConfidenceLevel(str, Enum):
    SUR = "SUR"
    ASSEZ_SUR = "ASSEZ_SUR"
    INCERTAIN = "INCERTAIN"

class Language(str, Enum):
    EWE = "ewe"
    KABIYE = "kabiye"
    MINA = "mina"
    FRANCAIS = "francais"

class CropType(str, Enum):
    MAIS = "mais"
    SORGHO = "sorgho"
    NIEBE = "niebe"

class RegimePluvio(str, Enum):
    BIMODAL = "bimodal"
    TRANSITION_UNIMODAL = "transition_unimodal"
    UNIMODAL = "unimodal"

class Village(BaseModel):
    village_id: str
    village_name: str
    canton: str
    prefecture: str
    region: str
    latitude: float
    longitude: float
    regime_pluviometrique: RegimePluvio
    altitude_m: float
    sol_dominant: str
    culture_principale_1: CropType
    culture_principale_2: CropType
    langue_majoritaire: Language

class SoilProfile(BaseModel):
    description: str
    texture: str
    depth_cm: float
    clay_pct: float
    sand_pct: float
    organic_carbon_g_kg: float
    theta_fc_m3_m3: float
    theta_pwp_m3_m3: float
    theta_sat_m3_m3: float
    ksat_mm_day: float
    taw_mm_m: float

class Variety(BaseModel):
    variety_id: str
    crop_type: CropType
    variety_name: str
    cycle_days_min: int
    cycle_days_max: int
    cycle_days_nominal: int
    water_req_mm: float
    drought_tolerance: str
    photoperiod_sensitive: bool
    grain_color: str
    potential_yield_t_ha: float
    source_organism: str
    zones_recommandees: str
    disponibilite_locale_defaut: bool = True

class PrecalculatedSheet(BaseModel):
    village_id: str
    village_name: str
    crop_type: CropType
    calculation_date: str
    recommended_variety_id: str
    recommended_variety_name: str
    alert_status: AlertStatus
    confidence: ConfidenceLevel
    rain_last_3days_mm: float
    rain_forecast_7days_mm: float
    dry_spell_risk_days: int
    is_data_stale: bool
    advice_fr: str
    advice_local: str
    audio_key_sequence: List[str] = Field(default_factory=list)
    last_weather_update: str

class FarmerProfile(BaseModel):
    phone_hash: str
    village_id: str
    language: Language = Language.FRANCAIS
    primary_crop: CropType = CropType.MAIS
    opt_in_voice: bool = True
    opt_in_sms: bool = True
    registered_at: str

class FieldRainObservation(BaseModel):
    village_id: str
    observation_date: str
    rainfall_mm: float
    reporter_type: str = "farmer"  # "farmer" | "agent"
    reported_at: str

class MonthlyClimateNorm(BaseModel):
    month: int
    rain_mean_mm: float
    rain_days: float
    tmin_mean_c: float
    tmax_mean_c: float
    p_wet_given_dry: float
    p_wet_given_wet: float
    gamma_shape: float
    gamma_scale: float

class VillageSoilSummary(BaseModel):
    village_id: str
    village_name: str
    texture: str
    taw_mm_m: float
    depth_cm: float
    drainage: str

class ZoneProfile(BaseModel):
    zone_id: str
    zone_name: str
    regime: RegimePluvio
    annual_rainfall_mean_mm: float
    annual_rainfall_std_mm: float
    season_1_earliest_sowing_date: str
    season_2_earliest_sowing_date: Optional[str] = None
    season_2_status: Optional[str] = None  # ex: "a_valider" pour bimodal
    false_start_probability_baseline: float
    soil_default_taw_mm_m: float
    soil_default_depth_cm: float
    soil_default_drainage: str
    monthly_climate: List[MonthlyClimateNorm]
    sentinel_villages: List[VillageSoilSummary] = Field(default_factory=list)

class DailySimulatedRecord(BaseModel):
    date: str
    month: int
    day_of_year: int
    rainfall_mm: float
    is_rain_day: bool
    tmin_c: float
    tmax_c: float
    potential_et0_mm: float
    soil_water_depletion_mm: Optional[float] = None

class SowingWindowResult(BaseModel):
    village_id: str
    village_name: str
    crop_type: CropType
    variety_id: str
    variety_name: str
    cycle_days: int
    window_start: str
    window_end: str
    best_sowing_date: str
    season_rain_cessation_date: str
    false_start_probability_pct: float
    confidence: ConfidenceLevel
    water_satisfaction_index_pct: float
    reasons: List[str] = Field(default_factory=list)

class WaterBalanceStatus(BaseModel):
    village_id: str
    taw_mm: float
    current_water_mm: float
    soil_moisture_pct: float
    is_at_wilting_point: bool
    daily_et0_mm: float
    sufficient_for_sowing: bool
    post_sowing_21d_false_start_risk: bool
    details: str



