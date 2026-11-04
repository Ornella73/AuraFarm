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

