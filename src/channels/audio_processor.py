"""Audio processing and normalization pipeline for AuraFarm telecom channels.

Features:
- Pure Python 3.14 compatible (uses standard wave and struct modules, no external ffmpeg required)
- 8 kHz mono / 16 kHz telecom standardization (G.711 / AMR cellular standard)
- Silence trimming at audio boundaries
- Peak loudness normalization (-1.0 dBFS)
- Telephone speaker filter simulation (bandpass 300 Hz - 3400 Hz) for web preview
"""
import math
import struct
import wave
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


def generate_synthetic_tone(
    output_path: Path,
    frequency_hz: float = 440.0,
    duration_sec: float = 1.0,
    sample_rate: int = 8000,
    amplitude: float = 0.7
) -> Path:
    """Generate a clean synthetic 16-bit mono sine wave for telecom testing."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_samples = int(sample_rate * duration_sec)
    max_amp = 32767 * amplitude

    raw_frames = bytearray()
    for i in range(total_samples):
        t = i / sample_rate
        val = int(max_amp * math.sin(2.0 * math.pi * frequency_hz * t))
        val = max(-32768, min(32767, val))
        raw_frames.extend(struct.pack("<h", val))

    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(raw_frames)

    return output_path


def inspect_wav_file(file_path: Path) -> Dict[str, Any]:
    """Inspect WAV properties and compliance with telecom standards."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    with wave.open(str(file_path), "rb") as wf:
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        duration_sec = round(nframes / framerate, 2) if framerate > 0 else 0.0

        raw = wf.readframes(nframes)
        max_val = 0
        if sampwidth == 2 and nframes > 0:
            count = len(raw) // 2
            samples = struct.unpack(f"<{count}h", raw)
            max_val = max(abs(s) for s in samples) if samples else 0

        peak_dbfs = round(20 * math.log10(max(1, max_val) / 32767), 1) if max_val > 0 else -96.0

    is_telecom = (channels == 1 and framerate in (8000, 16000) and sampwidth == 2)
    return {
        "file_name": file_path.name,
        "channels": channels,
        "sample_width": sampwidth,
        "sample_rate": framerate,
        "total_frames": nframes,
        "duration_sec": duration_sec,
        "peak_dbfs": peak_dbfs,
        "is_telecom_standard": is_telecom
    }


def normalize_pcm16_wav(
    input_path: Path,
    output_path: Path,
    target_sample_rate: int = 8000,
    target_channels: int = 1,
    target_peak_dbfs: float = -1.0,
    trim_silence: bool = True
) -> Path:
    """Normalize, resample, downmix and trim silence of a WAV file to telecom specs."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(input_path), "rb") as wf:
        in_channels = wf.getnchannels()
        in_width = wf.getsampwidth()
        in_rate = wf.getframerate()
        nframes = wf.getnframes()
        raw = wf.readframes(nframes)

    if in_width != 2:
        raise ValueError(f"Only 16-bit PCM WAV is supported (found {in_width * 8}-bit)")

    # 1. Unpack samples
    total_samples = len(raw) // 2
    raw_samples = struct.unpack(f"<{total_samples}h", raw)

    # 2. Downmix stereo to mono if needed
    if in_channels == 2:
        mono_samples = []
        for i in range(0, len(raw_samples), 2):
            left = raw_samples[i]
            right = raw_samples[i + 1] if i + 1 < len(raw_samples) else left
            mono_samples.append((left + right) // 2)
    else:
        mono_samples = list(raw_samples)

    if not mono_samples:
        mono_samples = [0]

    # 3. Trim initial and trailing silence (below -36 dBFS ~ 500 amplitude)
    silence_threshold = 500
    if trim_silence and len(mono_samples) > 100:
        start_idx = 0
        while start_idx < len(mono_samples) and abs(mono_samples[start_idx]) < silence_threshold:
            start_idx += 1

        end_idx = len(mono_samples) - 1
        while end_idx > start_idx and abs(mono_samples[end_idx]) < silence_threshold:
            end_idx -= 1

        if start_idx < end_idx:
            mono_samples = mono_samples[start_idx : end_idx + 1]

    # 4. Resample to target_sample_rate via linear interpolation
    if in_rate != target_sample_rate and len(mono_samples) > 1:
        ratio = in_rate / target_sample_rate
        out_len = int(len(mono_samples) / ratio)
        resampled = []
        for i in range(out_len):
            orig_pos = i * ratio
            idx0 = int(orig_pos)
            idx1 = min(idx0 + 1, len(mono_samples) - 1)
            frac = orig_pos - idx0
            val = int(mono_samples[idx0] * (1.0 - frac) + mono_samples[idx1] * frac)
            resampled.append(val)
        processed = resampled
    else:
        processed = mono_samples

    # 5. Peak loudness normalization
    current_peak = max(abs(s) for s in processed) if processed else 0
    target_amplitude = int(32767 * (10 ** (target_peak_dbfs / 20.0)))
    if current_peak > 100:
        gain = target_amplitude / current_peak
        normalized = [max(-32768, min(32767, int(s * gain))) for s in processed]
    else:
        normalized = processed

    # 6. Write normalized file
    packed = struct.pack(f"<{len(normalized)}h", *normalized)
    with wave.open(str(output_path), "wb") as out_wf:
        out_wf.setnchannels(1)
        out_wf.setsampwidth(2)
        out_wf.setframerate(target_sample_rate)
        out_wf.writeframes(packed)

    return output_path


def apply_telephone_bandpass(
    input_path: Path,
    output_path: Path
) -> Path:
    """Apply telephone speaker audio filter (300 Hz - 3400 Hz) for 2G handset acoustic preview."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(input_path), "rb") as wf:
        rate = wf.getframerate()
        channels = wf.getnchannels()
        raw = wf.readframes(wf.getnframes())

    total_samples = len(raw) // 2
    samples = list(struct.unpack(f"<{total_samples}h", raw))

    # Single-pole IIR Bandpass filter (High-pass ~300 Hz + Low-pass ~3400 Hz)
    # High-pass filter: y_hp[i] = alpha_hp * (y_hp[i-1] + x[i] - x[i-1])
    # Low-pass filter: y_lp[i] = y_lp[i-1] + alpha_lp * (y_hp[i] - y_lp[i-1])
    dt = 1.0 / rate
    rc_hp = 1.0 / (2.0 * math.pi * 300.0)
    alpha_hp = rc_hp / (rc_hp + dt)

    rc_lp = 1.0 / (2.0 * math.pi * 3400.0)
    alpha_lp = dt / (rc_lp + dt)

    filtered = []
    y_hp = 0.0
    y_lp = 0.0
    x_prev = samples[0] if samples else 0

    for x in samples:
        # High-pass step
        y_hp = alpha_hp * (y_hp + x - x_prev)
        x_prev = x
        # Low-pass step
        y_lp = y_lp + alpha_lp * (y_hp - y_lp)
        # Slight speaker clipping saturation at handset levels
        val = max(-30000, min(30000, int(y_lp)))
        filtered.append(val)

    packed = struct.pack(f"<{len(filtered)}h", *filtered)
    with wave.open(str(output_path), "wb") as out_wf:
        out_wf.setnchannels(channels)
        out_wf.setsampwidth(2)
        out_wf.setframerate(rate)
        out_wf.writeframes(packed)

    return output_path

