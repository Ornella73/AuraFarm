"""Unit tests for low-bandwidth 2G channels (USSD, Voice IVR, Missed Call, SMS)."""
import pytest
from src.core.models import Language, CropType, AlertStatus, ConfidenceLevel, PrecalculatedSheet
from src.core.database import init_db, save_precalculated_sheet
from src.data_ingestion.repositories import SpatialRepository
from src.channels.ussd_engine import UssdSessionEngine
from src.channels.voice_ivr import VoiceIvrEngine
from src.channels.missed_call import MissedCallHandler
from src.channels.sms_handler import SmsHandler
from src.channels.providers import MockChannelProvider

@pytest.fixture
def repo():
    return SpatialRepository()

@pytest.fixture
def setup_test_sheet(tmp_path, monkeypatch):
    from src.core.config import settings
    monkeypatch.setattr(settings, "DB_PATH", tmp_path / "test_channels.db")
    init_db()

    sheet = PrecalculatedSheet(
        village_id="TG_MAR_ZIO_01",
        village_name="Davié",
        crop_type=CropType.MAIS,
        calculation_date="2026-03-25",
        recommended_variety_id="TZEE_W_SR",
        recommended_variety_name="TZEE-W-SR",
        alert_status=AlertStatus.SEMER,
        confidence=ConfidenceLevel.SUR,
        rain_last_3days_mm=26.0,
        rain_forecast_7days_mm=40.0,
        dry_spell_risk_days=2,
        is_data_stale=False,
        advice_fr="SEMEZ dès maintenant.",
        advice_local="Tsi dza nyuie.",
        audio_key_sequence=["audio_intro"],
        last_weather_update="2026-03-25T06:00:00Z"
    )
    save_precalculated_sheet(sheet)
    return sheet

def test_ussd_session_flow_and_gsm_length(setup_test_sheet, repo):
    engine = UssdSessionEngine(repo=repo)
    phone = "+22890123456"
    sess_id = "sess_001"

    # Step 1: Initial dial -> Language selection menu
    r1 = engine.process_request(session_id=sess_id, phone_number=phone, text="")
    assert r1.is_terminal is False
    assert r1.validate_gsm_length() is True
    assert "1. Eʋegbe" in r1.text
    assert "4. Français" in r1.text

    # Step 2: Choose Français (4) -> Main Menu
    r2 = engine.process_request(session_id=sess_id, phone_number=phone, text="4")
    assert r2.is_terminal is False
    assert r2.validate_gsm_length() is True
    assert "1. Dois-je semer ?" in r2.text
    assert "2. Variété adaptée" in r2.text

    # Step 3: Choose "1" (Dois-je semer ?) -> Sowing decision screen
    r3 = engine.process_request(session_id=sess_id, phone_number=phone, text="4*1")
    assert r3.validate_gsm_length() is True
    assert "SEMEZ DES MAINTENANT !" in r3.text
    assert "TZEE-W-SR" in r3.text
    assert "Pluie 3j: 26mm" in r3.text

def test_ussd_rain_report_submission(setup_test_sheet, repo):
    engine = UssdSessionEngine(repo=repo)
    phone = "+22890998877"
    sess_id = "sess_rain"

    # Select Français (4), then option 3 (Signaler pluie)
    r1 = engine.process_request(session_id=sess_id, phone_number=phone, text="4*3")
    assert "Releve pluviometre" in r1.text

    # Enter 18.5 mm
    r2 = engine.process_request(session_id=sess_id, phone_number=phone, text="4*3*18.5")
    assert r2.is_terminal is True
    assert "Pluie de 18.5 mm enregistree" in r2.text

def test_voice_ivr_generation(setup_test_sheet):
    ivr = VoiceIvrEngine()
    playlist = ivr.generate_ivr_playlist(setup_test_sheet, Language.EWE)
    assert len(playlist.audio_files) == 4
    assert "ewe/intro.mp3" in playlist.audio_files[0]
    assert 25 <= playlist.estimated_duration_sec <= 45
    assert "Tsi dza nyuie" in playlist.text_transcript

    # TwiML generation with DTMF Gather
    twiml = ivr.generate_twiml(setup_test_sheet, Language.FRANCAIS, host_url="https://api.aurafarm.tg")
    assert "<Response>" in twiml
    assert "<Gather" in twiml
    assert "numDigits=\"1\"" in twiml

def test_missed_call_handler(setup_test_sheet):
    handler = MissedCallHandler()
    res = handler.process_incoming_bip("+22890123456")
    assert res["status"] == "CALLBACK_QUEUED"
    assert res["alert_status"] == "SEMER"
    assert "••••56" in res["phone_masked"]
    assert res["duration_sec"] >= 25

def test_sms_handler_segment_boundaries(setup_test_sheet):
    sms = SmsHandler()
    alert = sms.format_alert_sms(setup_test_sheet, Language.FRANCAIS)
    assert alert["single_sms_compliant"] is True
    assert alert["encoding"] == "GSM-7"
    assert alert["segments"] == 1
    assert "SEMEZ le mais" in alert["text"]
