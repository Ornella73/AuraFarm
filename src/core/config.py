"""Configuration module for AuraFarm."""
import os
from pathlib import Path
from dataclasses import dataclass

BASE_DIR = Path(__file__).resolve().parent.parent.parent

@dataclass
class Settings:
    AURAFARM_ENV: str = os.getenv("AURAFARM_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / os.getenv("DATA_DIR", "data")
    DB_PATH: Path = BASE_DIR / "data" / "aurafarm.db"
    
    # Freshness & Safety Guard
    DATA_FRESHNESS_MAX_HOURS: int = int(os.getenv("DATA_FRESHNESS_MAX_HOURS", "48"))
    STALE_DATA_DEFAULT_ALERT: str = os.getenv("STALE_DATA_DEFAULT_ALERT", "ATTENDRE_CONSULTER_AGENT")
    
    # Privacy / Togo Law 2019-014
    PHONE_HASH_SALT: str = os.getenv("PHONE_HASH_SALT", "aurafarm_togo_hackathon_2026_salt")
    
    # Weather APIs
    OPEN_METEO_API_URL: str = os.getenv("OPEN_METEO_API_URL", "https://api.open-meteo.com/v1/forecast")
    NASA_POWER_API_URL: str = os.getenv("NASA_POWER_API_URL", "https://power.larc.nasa.gov/api/temporal/daily/point")
    
    # Telecom Channels
    DEFAULT_TELECOM_OPERATOR: str = os.getenv("DEFAULT_TELECOM_OPERATOR", "yas_togo")
    USSD_SERVICE_CODE: str = os.getenv("USSD_SERVICE_CODE", "*384*228#")
    
    # Voice IVR
    VOICE_PROVIDER: str = os.getenv("VOICE_PROVIDER", "mock")
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_CALLER_ID: str = os.getenv("TWILIO_CALLER_ID", "+22890000000")

settings = Settings()
