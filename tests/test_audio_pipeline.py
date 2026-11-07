"""Test suite for Step E9: Audio Normalization, Telephone Bandpass Filter, and IVR Pipeline."""
import pytest
from pathlib import Path
from src.core.models import Language, CropType, AlertStatus, ConfidenceLevel, PrecalculatedSheet
from src.channels.audio_processor import (
    generate_synthetic_tone,
    inspect_wav_file,
    normalize_pcm16_wav,
    apply_telephone_bandpass
)
from src.channels.voice_ivr import VoiceIvrEngine

@pytest.fixture
def sample_sheet():
    return PrecalculatedSheet(
        village_id="TG_MAR_ZIO_01",
        village_name="Davié",
        crop_type=CropType.MAIS,
        calculation_date="2026-03-25",
        recommended_variety_id="TZEE_W_SR",
        recommended_variety_name="TZEE-W-SR",
        alert_status=AlertStatus.SEMER,
        confidence=ConfidenceLevel.SUR,
        rain_last_3days_mm=30.0,
        rain_forecast_7days_mm=45.0,
        dry_spell_risk_days=2,
        is_data_stale=False,
        advice_fr="SEMEZ dès maintenant.",
        advice_local="Tsi dza nyuie.",
        audio_key_sequence=["audio_intro"],
        last_weather_update="2026-03-25T06:00:00Z"
    )

def test_synthetic_tone_and_inspection(tmp_path):
    """Verify synthetic tone generation and telecom compliance inspection."""
    tone_path = tmp_path / "tone.wav"
    generate_synthetic_tone(tone_path, frequency_hz=440.0, duration_sec=0.5, sample_rate=8000)

    meta = inspect_wav_file(tone_path)
    assert meta["channels"] == 1
    assert meta["sample_rate"] == 8000
    assert meta["sample_width"] == 2
    assert meta["is_telecom_standard"] is True
    assert meta["duration_sec"] == 0.5

def test_normalize_pcm16_wav(tmp_path):
    """Verify resampling, loudness peak normalization (-1.0 dBFS), and silence trimming."""
    input_wav = tmp_path / "raw_16k.wav"
    generate_synthetic_tone(input_wav, frequency_hz=300.0, duration_sec=1.0, sample_rate=16000, amplitude=0.4)

    norm_wav = tmp_path / "norm_8k.wav"
    normalize_pcm16_wav(input_wav, norm_wav, target_sample_rate=8000, target_peak_dbfs=-1.0)

    meta = inspect_wav_file(norm_wav)
    assert meta["sample_rate"] == 8000
    assert meta["channels"] == 1
    assert -2.0 <= meta["peak_dbfs"] <= 0.0

def test_telephone_bandpass_filter(tmp_path):
    """Verify telephone filter (300 - 3400 Hz) execution without error."""
    tone_path = tmp_path / "tone.wav"
    generate_synthetic_tone(tone_path, frequency_hz=1000.0, duration_sec=0.5, sample_rate=8000)

    filtered_wav = tmp_path / "phone_sim.wav"
    apply_telephone_bandpass(tone_path, filtered_wav)

    meta = inspect_wav_file(filtered_wav)
    assert meta["sample_rate"] == 8000
    assert meta["channels"] == 1
    assert filtered_wav.stat().st_size > 0

def test_ivr_twiml_with_play_and_fallback(sample_sheet):
    """Verify TwiML generation supports both <Play> and <Say> fallback."""
    ivr = VoiceIvrEngine()

    # Fallback to <Say>
    twiml_say = ivr.generate_twiml(sample_sheet, Language.FRANCAIS)
    assert "<Say" in twiml_say
    assert "<Gather" in twiml_say

    # With recorded audio clip <Play>
    twiml_play = ivr.generate_twiml(sample_sheet, Language.EWE, force_play="/static/audio/ewe/clip_01.wav")
    assert "<Play>/static/audio/ewe/clip_01.wav</Play>" in twiml_play
    assert "<Gather" in twiml_play

def test_handset_preview_metadata(sample_sheet):
    """Verify handset preview metadata generation for web player."""
    ivr = VoiceIvrEngine()
    preview = ivr.generate_handset_preview(sample_sheet, Language.KABIYE)
    assert preview["language"] == "kabiye"
    assert "telephone_filter" in preview
    assert preview["telephone_filter"]["sample_rate_hz"] == 8000
    assert preview["telephone_filter"]["bandpass_hz"] == "300 - 3400 Hz"

