"""Test suite for Step E6: Restructured USSD Engine (*384*228#) with 7 streamlined options."""
import pytest
from src.core.models import Language, CropType, AlertStatus, ConfidenceLevel, PrecalculatedSheet
from src.core.database import init_db, save_precalculated_sheet, get_planting_reports, get_live_events
from src.data_ingestion.repositories import SpatialRepository
from src.channels.ussd_engine import UssdSessionEngine

@pytest.fixture(autouse=True)
def setup_ussd_environment(tmp_path, monkeypatch):
    from src.core.config import settings
    monkeypatch.setattr(settings, "DB_PATH", tmp_path / "test_ussd_v2.db")
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
        rain_last_3days_mm=28.0,
        rain_forecast_7days_mm=45.0,
        dry_spell_risk_days=2,
        is_data_stale=False,
        advice_fr="SEMEZ dès maintenant.",
        advice_local="Tsi dza nyuie.",
        audio_key_sequence=["audio_intro"],
        last_weather_update="2026-03-25T06:00:00Z"
    )
    save_precalculated_sheet(sheet)
    return sheet

def test_ussd_main_menu_character_length_all_languages():
    """Verify that main menu in all 4 national languages is strictly <= 160 GSM 03.38 chars."""
    repo = SpatialRepository()
    engine = UssdSessionEngine(repo=repo)
    phone = "+22890112233"

    for lang_code, lang_num in [("EWE", "1"), ("KABIYE", "2"), ("MINA", "3"), ("FRANCAIS", "4")]:
        sess_id = f"sess_lang_{lang_code}"
        # Dial -> Language menu
        r1 = engine.process_request(sess_id, phone, "")
        assert r1.validate_gsm_length()
        assert len(r1.text) <= 160

        # Select language -> Main menu
        r2 = engine.process_request(sess_id, phone, lang_num)
        assert r2.validate_gsm_length(), f"Menu for {lang_code} exceeds 160 chars: {len(r2.text)}"
        assert len(r2.text) <= 160
        assert not r2.is_terminal

def test_option_1_dois_je_semer():
    """Verify Option 1 delivers immediate decision with callback & menu options <= 160 chars."""
    repo = SpatialRepository()
    engine = UssdSessionEngine(repo=repo)
    phone = "+22890554433"
    sess_id = "sess_opt1"

    # Français -> Option 1
    resp = engine.process_request(sess_id, phone, "4*1")
    assert resp.validate_gsm_length()
    assert "SEMEZ DES MAINTENANT !" in resp.text
    assert "TZEE-W-SR" in resp.text
    assert "0. Menu" in resp.text
    assert not resp.is_terminal

    # Sub-input 0 -> Return to main menu
    resp_menu = engine.process_request(sess_id, phone, "4*1*0")
    assert "1. Dois-je semer ?" in resp_menu.text
    assert not resp_menu.is_terminal

def test_option_1_in_local_languages():
    """Verify that selecting Éwé, Kabiyè, or Mina outputs the final decision in that language."""
    repo = SpatialRepository()
    engine = UssdSessionEngine(repo=repo)
    phone = "+22890554433"

    # 1. Éwé (1) -> Option 1
    resp_ewe = engine.process_request("sess_opt1_ewe", phone, "1*1")
    assert resp_ewe.validate_gsm_length()
    assert "MÍATE ŊU AƑÃ" in resp_ewe.text
    assert "Nuku:" in resp_ewe.text

    # 2. Kabiyè (2) -> Option 1
    resp_kab = engine.process_request("sess_opt1_kab", phone, "2*1")
    assert resp_kab.validate_gsm_length()
    assert "MƖPƖZƖƔ MƖDƲ" in resp_kab.text
    assert "Pɩlɩʊ:" in resp_kab.text

    # 3. Mina (3) -> Option 1
    resp_mina = engine.process_request("sess_opt1_mina", phone, "3*1")
    assert resp_mina.validate_gsm_length()
    assert "MIATƐŊ ADO" in resp_mina.text


def test_option_2_variete_adaptee():
    """Verify Option 2 details recommended seed variety within 160 chars."""
    repo = SpatialRepository()
    engine = UssdSessionEngine(repo=repo)
    phone = "+22890554433"
    sess_id = "sess_opt2"

    resp = engine.process_request(sess_id, phone, "4*2")
    assert resp.validate_gsm_length()
    assert "TZEE-W-SR" in resp.text
    assert "Cycle:" in resp.text
    assert "0. Menu" in resp.text

def test_option_4_mon_profil_and_crop_change():
    """Verify Option 4 displays profile and allows changing primary crop."""
    repo = SpatialRepository()
    engine = UssdSessionEngine(repo=repo)
    phone = "+22890554433"
    sess_id = "sess_opt4"

    # View profile
    resp_prof = engine.process_request(sess_id, phone, "4*4")
    assert resp_prof.validate_gsm_length()
    assert "Profil AuraFarm" in resp_prof.text
    assert "1. Changer village" in resp_prof.text
    assert "2. Changer culture" in resp_prof.text

    # Select 2 (Changer culture) -> Culture choices
    resp_crop_menu = engine.process_request(sess_id, phone, "4*4*2")
    assert resp_crop_menu.validate_gsm_length()
    assert "1. Maïs" in resp_crop_menu.text
    assert "2. Sorgho" in resp_crop_menu.text

    # Choose Sorgho (2)
    resp_done = engine.process_request(sess_id, phone, "4*4*2*2")
    assert resp_done.is_terminal
    assert "Sorgho" in resp_done.text

def test_option_5_j_ai_seme_declaration():
    """Verify Option 5 records planting date declaration and generates audit event."""
    repo = SpatialRepository()
    engine = UssdSessionEngine(repo=repo)
    phone = "+22890554433"
    sess_id = "sess_opt5"

    # Prompt declaration date
    resp_prompt = engine.process_request(sess_id, phone, "4*5")
    assert resp_prompt.validate_gsm_length()
    assert "Quand avez-vous seme ?" in resp_prompt.text
    assert "1. Aujourd'hui" in resp_prompt.text

    # Select 1 (Aujourd'hui)
    resp_confirm = engine.process_request(sess_id, phone, "4*5*1")
    assert resp_confirm.validate_gsm_length()
    assert resp_confirm.is_terminal
    assert "Semis enregistre" in resp_confirm.text

    # Verify in DB
    reports = get_planting_reports(village_id="TG_MAR_ZIO_01")
    assert len(reports) >= 1

def test_option_6_and_7_callback_and_agent():
    """Verify Option 6 registers free callback and Option 7 shows ICAT contacts."""
    repo = SpatialRepository()
    engine = UssdSessionEngine(repo=repo)
    phone = "+22890554433"

    # Option 6: Callback
    sess_6 = "sess_opt6"
    resp6 = engine.process_request(sess_6, phone, "4*6")
    assert resp6.validate_gsm_length()
    assert resp6.is_terminal
    assert "Demande recue" in resp6.text

    # Check callback event
    evts = get_live_events(limit=5)
    assert any(e["event_type"] == "callback_request" for e in evts)

    # Option 7: ICAT Agent
    sess_7 = "sess_opt7"
    resp7 = engine.process_request(sess_7, phone, "4*7")
    assert resp7.validate_gsm_length()
    assert "Conseiller ICAT" in resp7.text
    assert "+228" in resp7.text

