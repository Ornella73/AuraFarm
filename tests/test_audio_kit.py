"""Unit and integration tests for Step E1: Audio phrase bank, upload, and status tracking."""
import io
import pytest
from src.core.config import settings
from src.core.database import init_db
from src.channels.audio_registry import AudioRegistry
from src.api.main import (
    get_audio_phrases,
    export_audio_csv,
    upload_audio_clip,
    update_clip_status,
    ClipStatusUpdatePayload,
    audio_recorder_view
)
import shutil
from starlette.datastructures import UploadFile as StarletteUploadFile

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_audio.db"
    test_data = tmp_path / "data"
    test_data.mkdir(parents=True, exist_ok=True)
    real_csv = settings.BASE_DIR / "data" / "audio_phrase_bank.csv"
    if real_csv.exists():
        shutil.copy(real_csv, test_data / "audio_phrase_bank.csv")
    monkeypatch.setattr(settings, "DB_PATH", test_db)
    monkeypatch.setattr(settings, "DATA_DIR", test_data)
    init_db()

def test_phrase_bank_word_counts_and_completeness():
    registry = AudioRegistry()
    phrases = registry.list_phrases()
    assert len(phrases) >= 50

    # Rule constraint: Maximum 8-10 words per French phrase!
    for p in phrases:
        actual_words = len(p.french_text.strip().split())
        assert actual_words <= 10, f"Phrase {p.phrase_id} dépasse 10 mots: '{p.french_text}' ({actual_words} mots)"
        assert len(p.ewe_text) > 0, f"Traduction éwé manquante pour {p.phrase_id}"
        assert len(p.kabiye_text) > 0, f"Traduction kabiyè manquante pour {p.phrase_id}"
        assert len(p.mina_text) > 0, f"Traduction mina manquante pour {p.phrase_id}"

def test_get_audio_phrases_endpoint():
    data = get_audio_phrases(lang="ewe")
    assert data["language"] == "ewe"
    assert data["count"] >= 50
    # Initial status is manquant
    statuses = [p["status"] for p in data["phrases"]]
    assert all(s == "manquant" for s in statuses)

def test_export_audio_csv():
    resp = export_audio_csv()
    assert resp.status_code == 200
    assert "text/csv" in resp.media_type
    assert "aurafarm_audio_phrase_bank.csv" in resp.headers["content-disposition"]

def test_upload_clip_consent_enforcement():
    fake_audio = io.BytesIO(b"RIFF....WAVEfmt....data....")
    upload_file = StarletteUploadFile(filename="test.wav", file=fake_audio)

    # 1. Refusal when consent_given is 0 (Loi Togolaise 2019-014)
    res_no_consent = upload_audio_clip(
        phrase_id="status_semer",
        language="ewe",
        speaker_id="Locutrice_01",
        consent_given=0,
        audio_file=upload_file
    )
    assert res_no_consent.status_code == 400
    assert "consentement" in res_no_consent.body.decode().lower()

    # 2. Success when consent_given is 1
    fake_audio.seek(0)
    res_ok = upload_audio_clip(
        phrase_id="status_semer",
        language="ewe",
        speaker_id="Locutrice_01",
        consent_given=1,
        audio_file=upload_file
    )
    assert res_ok["status"] == "SUCCESS"
    rec_id = res_ok["recording_id"]
    assert rec_id > 0

    # 3. Check status is now 'enregistre' in phrases query
    updated_phrases = get_audio_phrases(lang="ewe")
    semer_item = next(p for p in updated_phrases["phrases"] if p["phrase_id"] == "status_semer")
    assert semer_item["status"] == "enregistre"

    # 4. Update status to 'valide'
    update_res = update_clip_status(ClipStatusUpdatePayload(recording_id=rec_id, status="validated", review_notes="Accent parfait"))
    assert update_res["status"] == "SUCCESS"

    # 5. Check status is now 'valide'
    updated_phrases_2 = get_audio_phrases(lang="ewe")
    semer_item_2 = next(p for p in updated_phrases_2["phrases"] if p["phrase_id"] == "status_semer")
    assert semer_item_2["status"] == "valide"

def test_audio_recorder_view():
    html = audio_recorder_view()
    assert "<!DOCTYPE html>" in html
    assert "Studio Vocale Terroir" in html
    assert "Loi Togolaise 2019-014" in html
    assert "MediaRecorder" in html

