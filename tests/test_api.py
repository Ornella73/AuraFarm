"""FastAPI Route Handlers Unit & Integration Tests (100% synchronous & socketless)."""
import json
import pytest
from src.core.config import settings
from src.core.database import init_db
from src.data_ingestion.weather_service import WeatherService
from src.api.main import (
    list_villages,
    list_precalculated_sheets,
    get_village_sheet,
    ussd_webhook,
    handle_missed_call,
    ivr_incoming_call,
    ivr_dtmf_input,
    record_rain_observation,
    RainObservationPayload,
    get_village_observations,
    get_radio_bulletin,
    run_backtest,
    dashboard_view,
    ussd_simulator_view,
    trigger_daily_pipeline
)

@pytest.fixture(autouse=True)
def setup_api_test(tmp_path, monkeypatch):
    test_db = tmp_path / "test_api.db"
    monkeypatch.setattr(settings, "DB_PATH", test_db)
    WeatherService._api_available = False
    init_db()
    trigger_daily_pipeline(scenario="optimal_onset")

def test_list_villages():
    villages = list_villages()
    assert len(villages) >= 10
    names = [v["village_name"] for v in villages]
    assert "Davié" in names
    assert "Kantindi" in names
    assert "Komah" in names

def test_list_and_get_precalculated_sheets():
    sheets = list_precalculated_sheets()
    assert len(sheets) > 0
    
    # Specific sheet
    sheet = get_village_sheet("TG_MAR_ZIO_01", "mais")
    assert sheet["village_name"] == "Davié"
    assert sheet["crop_type"] == "mais"
    assert sheet["alert_status"] in ["SEMER", "ATTENDRE"]

def test_ussd_webhook_flow():
    sess_id = "api_sess_001"
    phone = "+22890123456"

    # 1. Dial code *384*228#
    r1 = ussd_webhook(sessionId=sess_id, phoneNumber=phone, text="")
    assert r1.body.decode("utf-8").startswith("CON ")
    assert "1. Eʋegbe" in r1.body.decode("utf-8")

    # 2. Select French (4)
    r2 = ussd_webhook(sessionId=sess_id, phoneNumber=phone, text="4")
    assert r2.body.decode("utf-8").startswith("CON ")
    assert "1. Dois-je semer ?" in r2.body.decode("utf-8")

    # 3. Select Sowing query (1)
    r3 = ussd_webhook(sessionId=sess_id, phoneNumber=phone, text="4*1")
    body = r3.body.decode("utf-8")
    assert "SEMEZ" in body or "ATTENDEZ" in body
    # Validate GSM 03.38 character limit (<= 160 characters excluding prefix)
    clean_text = body.replace("CON ", "").replace("END ", "")
    assert len(clean_text) <= 160

def test_missed_call_bip_handler():
    resp = handle_missed_call(phoneNumber="+22890123456")
    data = json.loads(resp.body.decode("utf-8"))
    assert data["status"] == "CALLBACK_QUEUED"
    assert "audio_files" in data
    assert data["duration_sec"] >= 25

def test_ivr_voice_twiml_generation():
    resp = ivr_incoming_call(From="+22890123456", village="TG_MAR_ZIO_01", crop="mais", lang="francais")
    xml_str = resp.body.decode("utf-8")
    assert "<Response>" in xml_str
    assert "<Gather" in xml_str
    assert "numDigits=\"1\"" in xml_str
    assert "TZEE-W-SR" in xml_str

def test_ivr_dtmf_inputs():
    # 1. Replay audio
    r1 = ivr_dtmf_input(Digits="1", village="TG_MAR_ZIO_01", crop="mais", lang="francais")
    assert "<Gather" in r1.body.decode("utf-8")

    # 2. Connect to agent
    r2 = ivr_dtmf_input(Digits="2", village="TG_MAR_ZIO_01", crop="mais", lang="francais")
    assert "agent d'encadrement ICAT" in r2.body.decode("utf-8")

def test_observations_submission_and_retrieval():
    payload = RainObservationPayload(village_id="TG_MAR_ZIO_01", rainfall_mm=21.0, reporter_type="farmer")
    res = record_rain_observation(payload)
    assert res["status"] == "SUCCESS"

    obs = get_village_observations("TG_MAR_ZIO_01")
    assert len(obs) >= 1
    assert obs[0]["rainfall_mm"] == 21.0

def test_radio_bulletin_generation():
    bulletin = get_radio_bulletin("Maritime")
    assert bulletin["region"] == "Maritime"
    assert "BULLETIN RADIO COMMUNAUTAIRE" in bulletin["script_fr"]
    assert "AURAFARM RADIO" in bulletin["script_local"]

def test_radio_bulletin_all_regions():
    from src.dashboard.bulletin_generator import CommunityRadioBulletinGenerator
    gen = CommunityRadioBulletinGenerator()
    all_b = gen.generate_all_regions()
    assert len(all_b) == 5
    for reg in ["maritime", "plateaux", "centrale", "kara", "savanes"]:
        assert reg in all_b
        assert "script_fr" in all_b[reg]
        assert "script_local" in all_b[reg]


def test_backtest_benchmark_endpoint():
    bench = run_backtest()
    assert bench["total_tests"] >= 12
    assert bench["accuracy_pct"] >= 90.0
    assert bench["false_start_safety_rate_pct"] == 100.0

def test_pwa_html_views():
    dash = dashboard_view()
    assert "<!DOCTYPE html>" in dash
    assert "AuraFarm" in dash
    assert "Bulletin Radio" in dash

    sim = ussd_simulator_view()
    assert "<!DOCTYPE html>" in sim
    assert "AURAFARM 2G" in sim
    assert "*384*228#" in sim
