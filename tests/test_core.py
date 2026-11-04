"""Unit tests for AuraFarm core: security, config, and database."""
import pytest
from src.core.config import settings
from src.core.security import normalize_phone_number, hash_phone_number, mask_phone_number
from src.core.models import (
    PrecalculatedSheet,
    FarmerProfile,
    FieldRainObservation,
    AlertStatus,
    ConfidenceLevel,
    Language,
    CropType
)
from src.core.database import (
    init_db,
    save_precalculated_sheet,
    get_precalculated_sheet,
    save_farmer_profile,
    get_farmer_profile,
    save_field_observation,
    get_recent_field_observations
)

def test_phone_normalization_and_masking():
    # Togolese formats: 8 digits local, +228, 00228
    assert normalize_phone_number("90 12 34 56") == "+22890123456"
    assert normalize_phone_number("+228 90 12 34 56") == "+22890123456"
    assert normalize_phone_number("00228 70 99 88 77") == "+22870998877"
    
    # Masking for privacy
    masked = mask_phone_number("+22890123456")
    assert "9012" not in masked
    assert masked.startswith("+22890")
    assert masked.endswith("56")

def test_phone_hashing_pseudonymization():
    h1 = hash_phone_number("+22890123456")
    h2 = hash_phone_number("90123456")
    h3 = hash_phone_number("+22870112233")
    
    assert h1 == h2
    assert h1 != h3
    assert h1.startswith("msisdn_")
    # Raw phone must not appear anywhere in hash
    assert "90123456" not in h1

def test_database_crud(tmp_path, monkeypatch):
    test_db = tmp_path / "test_aurafarm.db"
    monkeypatch.setattr(settings, "DB_PATH", test_db)
    
    init_db()
    
    # Precalculated sheet
    sheet = PrecalculatedSheet(
        village_id="TG_MAR_ZIO_01",
        village_name="Davié",
        crop_type=CropType.MAIS,
        calculation_date="2026-03-25",
        recommended_variety_id="TZEE_W_SR",
        recommended_variety_name="TZEE-W-SR",
        alert_status=AlertStatus.SEMER,
        confidence=ConfidenceLevel.SUR,
        rain_last_3days_mm=26.5,
        rain_forecast_7days_mm=42.0,
        dry_spell_risk_days=2,
        is_data_stale=False,
        advice_fr="Conditions optimales pour semer la variété extra-précoce TZEE-W-SR.",
        advice_local="Míateŋu adó bli fífíia.",
        audio_key_sequence=["salut_ewe", "semer_mais", "variete_tzeews"],
        last_weather_update="2026-03-25T06:00:00Z"
    )
    save_precalculated_sheet(sheet)
    
    retrieved = get_precalculated_sheet("TG_MAR_ZIO_01", CropType.MAIS)
    assert retrieved is not None
    assert retrieved.village_name == "Davié"
    assert retrieved.alert_status == AlertStatus.SEMER
    assert retrieved.confidence == ConfidenceLevel.SUR
    assert retrieved.recommended_variety_id == "TZEE_W_SR"
    
    # Farmer profile
    profile = FarmerProfile(
        phone_hash="msisdn_test123",
        village_id="TG_MAR_ZIO_01",
        language=Language.EWE,
        primary_crop=CropType.MAIS,
        opt_in_voice=True,
        opt_in_sms=True,
        registered_at="2026-03-20T10:00:00Z"
    )
    save_farmer_profile(profile)
    retrieved_prof = get_farmer_profile("msisdn_test123")
    assert retrieved_prof is not None
    assert retrieved_prof.village_id == "TG_MAR_ZIO_01"
    assert retrieved_prof.language == Language.EWE
    
    # Field observations
    obs = FieldRainObservation(
        village_id="TG_MAR_ZIO_01",
        observation_date="2026-03-24",
        rainfall_mm=18.5,
        reporter_type="farmer",
        reported_at="2026-03-24T18:30:00Z"
    )
    save_field_observation(obs)
    obs_list = get_recent_field_observations("TG_MAR_ZIO_01", limit=5)
    assert len(obs_list) == 1
    assert obs_list[0].rainfall_mm == 18.5
