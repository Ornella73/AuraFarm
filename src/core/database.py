"""SQLite Database manager for AuraFarm pre-computed records, field data, and real-time events."""
import json
import sqlite3
from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any
from src.core.config import settings
from src.core.models import (
    PrecalculatedSheet,
    FarmerProfile,
    FieldRainObservation,
    AlertStatus,
    ConfidenceLevel,
    Language,
    CropType,
    ZoneProfile,
    MonthlyClimateNorm,
    VillageSoilSummary,
    RegimePluvio
)

def get_connection() -> sqlite3.Connection:
    """Return a connection with row factory enabled."""
    settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables with indexes."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Farmers table (pseudonymized)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS farmers (
                phone_hash TEXT PRIMARY KEY,
                village_id TEXT NOT NULL,
                language TEXT NOT NULL,
                primary_crop TEXT NOT NULL,
                opt_in_voice INTEGER NOT NULL DEFAULT 1,
                opt_in_sms INTEGER NOT NULL DEFAULT 1,
                registered_at TEXT NOT NULL
            );
        """)
        
        # Field observations (village rain gauges)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS field_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                village_id TEXT NOT NULL,
                observation_date TEXT NOT NULL,
                rainfall_mm REAL NOT NULL,
                reporter_type TEXT NOT NULL,
                reported_at TEXT NOT NULL
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_obs_village_date ON field_observations(village_id, observation_date);")
        
        # Precalculated daily decision sheets (Sub-second retrieval for 2G channels)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS precalculated_sheets (
                village_id TEXT NOT NULL,
                crop_type TEXT NOT NULL,
                calculation_date TEXT NOT NULL,
                data_json TEXT NOT NULL,
                PRIMARY KEY (village_id, crop_type)
            );
        """)
        
        # Data freshness supervision log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_freshness_log (
                source_name TEXT PRIMARY KEY,
                last_success_timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT
            );
        """)
        
        # Weather observations and forecast cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_cache (
                village_id TEXT NOT NULL,
                date TEXT NOT NULL,
                rainfall_observed_mm REAL,
                rainfall_forecast_mm REAL,
                temp_min_c REAL,
                temp_max_c REAL,
                et0_mm REAL,
                source TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (village_id, date)
            );
        """)

        # Audio recordings repository for native speaker voices (Step E1)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audio_recordings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phrase_id TEXT NOT NULL,
                language TEXT NOT NULL,
                speaker_id TEXT NOT NULL,
                consent_given INTEGER NOT NULL DEFAULT 0,
                file_path TEXT NOT NULL,
                file_size_bytes INTEGER DEFAULT 0,
                duration_sec REAL DEFAULT 0.0,
                status TEXT NOT NULL DEFAULT 'recorded',
                recorded_at TEXT NOT NULL,
                reviewed_at TEXT,
                review_notes TEXT
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audio_phrase_lang ON audio_recordings(phrase_id, language);")

        # Zone Agro-Climatic Profiles (Step E2)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS zone_profiles (
                zone_id TEXT PRIMARY KEY,
                zone_name TEXT NOT NULL,
                regime TEXT NOT NULL,
                annual_rainfall_mean_mm REAL NOT NULL,
                annual_rainfall_std_mm REAL NOT NULL,
                season_1_earliest_sowing_date TEXT NOT NULL,
                season_2_earliest_sowing_date TEXT,
                season_2_status TEXT,
                false_start_probability_baseline REAL NOT NULL,
                soil_default_taw_mm_m REAL NOT NULL,
                soil_default_depth_cm REAL NOT NULL,
                soil_default_drainage TEXT NOT NULL,
                data_json TEXT NOT NULL
            );
        """)

        # Real-time Events Stream (Step E5)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                village_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                payload TEXT NOT NULL,
                phone_hash TEXT NOT NULL
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_village ON events(village_id);")

        # Farmer Planting Declarations (Step E5 / E6)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS planting_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_hash TEXT NOT NULL,
                village_id TEXT NOT NULL,
                crop_type TEXT NOT NULL,
                variety_name TEXT,
                planted_date TEXT NOT NULL,
                reported_at TEXT NOT NULL
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_planting_village ON planting_reports(village_id);")

        # Audio evaluations by native speakers and juries (Step E10)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audio_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clip_id TEXT NOT NULL,
                language TEXT NOT NULL,
                evaluator_name TEXT,
                evaluator_origin_region TEXT,
                clarity_rating INTEGER NOT NULL,
                naturalness_rating INTEGER NOT NULL,
                accent_authenticity_rating INTEGER NOT NULL,
                comprehension_check_passed INTEGER NOT NULL DEFAULT 1,
                comments TEXT,
                evaluated_at TEXT NOT NULL
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audio_eval_lang ON audio_evaluations(language);")

        _seed_zone_profiles_if_empty(cursor)

        conn.commit()

# --- Precalculated Sheets Operations ---

def save_precalculated_sheet(sheet: PrecalculatedSheet):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO precalculated_sheets (village_id, crop_type, calculation_date, data_json)
            VALUES (?, ?, ?, ?);
        """, (sheet.village_id, sheet.crop_type.value, sheet.calculation_date, sheet.model_dump_json()))
        conn.commit()

def get_precalculated_sheet(village_id: str, crop_type: CropType) -> Optional[PrecalculatedSheet]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT data_json FROM precalculated_sheets
            WHERE village_id = ? AND crop_type = ?;
        """, (village_id, crop_type.value))
        row = cursor.fetchone()
        if row:
            data = json.loads(row["data_json"])
            return PrecalculatedSheet(**data)
        return None

def get_all_precalculated_sheets() -> List[PrecalculatedSheet]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT data_json FROM precalculated_sheets ORDER BY village_id, crop_type;")
        rows = cursor.fetchall()
        sheets = []
        for r in rows:
            data = json.loads(r["data_json"])
            sheets.append(PrecalculatedSheet(**data))
        return sheets

# --- Farmer Profiles Operations ---

def save_farmer_profile(profile: FarmerProfile):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO farmers (phone_hash, village_id, language, primary_crop, opt_in_voice, opt_in_sms, registered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            profile.phone_hash,
            profile.village_id,
            profile.language.value,
            profile.primary_crop.value,
            1 if profile.opt_in_voice else 0,
            1 if profile.opt_in_sms else 0,
            profile.registered_at
        ))
        conn.commit()

def get_farmer_profile(phone_hash: str) -> Optional[FarmerProfile]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM farmers WHERE phone_hash = ?;", (phone_hash,))
        row = cursor.fetchone()
        if row:
            return FarmerProfile(
                phone_hash=row["phone_hash"],
                village_id=row["village_id"],
                language=Language(row["language"]),
                primary_crop=CropType(row["primary_crop"]),
                opt_in_voice=bool(row["opt_in_voice"]),
                opt_in_sms=bool(row["opt_in_sms"]),
                registered_at=row["registered_at"]
            )
        return None

# --- Field Observations Operations ---

def save_field_observation(obs: FieldRainObservation):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO field_observations (village_id, observation_date, rainfall_mm, reporter_type, reported_at)
            VALUES (?, ?, ?, ?, ?);
        """, (obs.village_id, obs.observation_date, obs.rainfall_mm, obs.reporter_type, obs.reported_at))
        conn.commit()

def get_recent_field_observations(village_id: str = "", limit: int = 5) -> List[FieldRainObservation]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if village_id:
            cursor.execute("""
                SELECT village_id, observation_date, rainfall_mm, reporter_type, reported_at
                FROM field_observations
                WHERE village_id = ?
                ORDER BY observation_date DESC
                LIMIT ?;
            """, (village_id, limit))
        else:
            cursor.execute("""
                SELECT village_id, observation_date, rainfall_mm, reporter_type, reported_at
                FROM field_observations
                ORDER BY observation_date DESC
                LIMIT ?;
            """, (limit,))
        rows = cursor.fetchall()
        return [
            FieldRainObservation(
                village_id=r["village_id"],
                observation_date=r["observation_date"],
                rainfall_mm=r["rainfall_mm"],
                reporter_type=r["reporter_type"],
                reported_at=r["reported_at"]
            ) for r in rows
        ]

# --- Freshness Supervision Operations ---

def record_freshness(source_name: str, timestamp_iso: str, status: str, details: str = ""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO data_freshness_log (source_name, last_success_timestamp, status, details)
            VALUES (?, ?, ?, ?);
        """, (source_name, timestamp_iso, status, details))
        conn.commit()

def get_freshness_status(source_name: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM data_freshness_log WHERE source_name = ?;", (source_name,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

# --- Audio Recordings Repository (Step E1) ---

def save_audio_recording(
    phrase_id: str,
    language: str,
    speaker_id: str,
    consent_given: bool,
    file_path: str,
    file_size_bytes: int = 0,
    duration_sec: float = 0.0,
    status: str = "recorded"
) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        now_iso = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO audio_recordings (
                phrase_id, language, speaker_id, consent_given, file_path,
                file_size_bytes, duration_sec, status, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            phrase_id,
            language,
            speaker_id,
            1 if consent_given else 0,
            file_path,
            file_size_bytes,
            duration_sec,
            status,
            now_iso
        ))
        conn.commit()
        return cursor.lastrowid

def get_audio_recordings(language: Optional[str] = None, phrase_id: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM audio_recordings WHERE 1=1"
        params = []
        if language:
            query += " AND language = ?"
            params.append(language)
        if phrase_id:
            query += " AND phrase_id = ?"
            params.append(phrase_id)
        query += " ORDER BY recorded_at DESC;"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def update_audio_recording_status(recording_id: int, status: str, review_notes: str = "") -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        now_iso = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            UPDATE audio_recordings
            SET status = ?, review_notes = ?, reviewed_at = ?
            WHERE id = ?;
        """, (status, review_notes, now_iso, recording_id))
        conn.commit()
        return cursor.rowcount > 0

def get_phrase_recording_status_map(language: str) -> Dict[str, str]:
    recordings = get_audio_recordings(language=language)
    status_map: Dict[str, str] = {}
    for r in recordings:
        pid = r["phrase_id"]
        stat = r["status"]
        if status_map.get(pid) == "valide":
            continue
        if stat == "validated":
            status_map[pid] = "valide"
        elif stat == "recorded":
            status_map[pid] = "enregistre"
        elif stat == "rejected":
            status_map[pid] = "rejete"
    return status_map

# --- Zone Profiles & Agro-Climatic Data (Step E2) ---

def _build_default_zone_profiles() -> List[ZoneProfile]:
    return [
        ZoneProfile(
            zone_id="SAVANES",
            zone_name="Région des Savanes (Soudano-Sahélien)",
            regime=RegimePluvio.UNIMODAL,
            annual_rainfall_mean_mm=1020.0,
            annual_rainfall_std_mm=140.0,
            season_1_earliest_sowing_date="05-20",
            season_2_earliest_sowing_date=None,
            season_2_status=None,
            false_start_probability_baseline=0.38,
            soil_default_taw_mm_m=85.0,
            soil_default_depth_cm=80.0,
            soil_default_drainage="rapide",
            monthly_climate=[
                MonthlyClimateNorm(month=1, rain_mean_mm=1.5, rain_days=0.2, tmin_mean_c=19.5, tmax_mean_c=35.5, p_wet_given_dry=0.01, p_wet_given_wet=0.10, gamma_shape=0.9, gamma_scale=4.0),
                MonthlyClimateNorm(month=2, rain_mean_mm=5.0, rain_days=0.5, tmin_mean_c=22.5, tmax_mean_c=38.0, p_wet_given_dry=0.02, p_wet_given_wet=0.15, gamma_shape=1.0, gamma_scale=5.0),
                MonthlyClimateNorm(month=3, rain_mean_mm=18.0, rain_days=1.8, tmin_mean_c=25.0, tmax_mean_c=39.0, p_wet_given_dry=0.06, p_wet_given_wet=0.25, gamma_shape=1.1, gamma_scale=8.0),
                MonthlyClimateNorm(month=4, rain_mean_mm=45.0, rain_days=4.2, tmin_mean_c=25.5, tmax_mean_c=37.5, p_wet_given_dry=0.14, p_wet_given_wet=0.35, gamma_shape=1.2, gamma_scale=9.0),
                MonthlyClimateNorm(month=5, rain_mean_mm=95.0, rain_days=7.8, tmin_mean_c=24.5, tmax_mean_c=34.5, p_wet_given_dry=0.24, p_wet_given_wet=0.45, gamma_shape=1.3, gamma_scale=10.0),
                MonthlyClimateNorm(month=6, rain_mean_mm=135.0, rain_days=10.5, tmin_mean_c=23.0, tmax_mean_c=32.0, p_wet_given_dry=0.33, p_wet_given_wet=0.55, gamma_shape=1.4, gamma_scale=11.5),
                MonthlyClimateNorm(month=7, rain_mean_mm=190.0, rain_days=14.0, tmin_mean_c=22.0, tmax_mean_c=30.0, p_wet_given_dry=0.42, p_wet_given_wet=0.65, gamma_shape=1.5, gamma_scale=12.5),
                MonthlyClimateNorm(month=8, rain_mean_mm=245.0, rain_days=17.5, tmin_mean_c=21.8, tmax_mean_c=29.5, p_wet_given_dry=0.50, p_wet_given_wet=0.72, gamma_shape=1.6, gamma_scale=14.0),
                MonthlyClimateNorm(month=9, rain_mean_mm=180.0, rain_days=13.5, tmin_mean_c=22.0, tmax_mean_c=30.5, p_wet_given_dry=0.40, p_wet_given_wet=0.62, gamma_shape=1.4, gamma_scale=13.0),
                MonthlyClimateNorm(month=10, rain_mean_mm=45.0, rain_days=4.5, tmin_mean_c=22.2, tmax_mean_c=33.5, p_wet_given_dry=0.14, p_wet_given_wet=0.35, gamma_shape=1.1, gamma_scale=9.5),
                MonthlyClimateNorm(month=11, rain_mean_mm=5.0, rain_days=0.6, tmin_mean_c=20.5, tmax_mean_c=35.0, p_wet_given_dry=0.02, p_wet_given_wet=0.15, gamma_shape=0.9, gamma_scale=5.0),
                MonthlyClimateNorm(month=12, rain_mean_mm=1.0, rain_days=0.1, tmin_mean_c=18.5, tmax_mean_c=34.5, p_wet_given_dry=0.01, p_wet_given_wet=0.05, gamma_shape=0.8, gamma_scale=3.5)
            ],
            sentinel_villages=[
                VillageSoilSummary(village_id="TG_SAV_TON_01", village_name="Kantindi", texture="sablo-limoneux", taw_mm_m=82.0, depth_cm=80.0, drainage="rapide"),
                VillageSoilSummary(village_id="TG_SAV_OTI_02", village_name="Gando", texture="vertique_hydromorphe", taw_mm_m=115.0, depth_cm=95.0, drainage="lent")
            ]
        ),
        ZoneProfile(
            zone_id="KARA",
            zone_name="Région de la Kara (Soudano-Guinéen Nord)",
            regime=RegimePluvio.UNIMODAL,
            annual_rainfall_mean_mm=1180.0,
            annual_rainfall_std_mm=125.0,
            season_1_earliest_sowing_date="05-01",
            season_2_earliest_sowing_date=None,
            season_2_status=None,
            false_start_probability_baseline=0.24,
            soil_default_taw_mm_m=100.0,
            soil_default_depth_cm=95.0,
            soil_default_drainage="bon",
            monthly_climate=[
                MonthlyClimateNorm(month=1, rain_mean_mm=3.0, rain_days=0.3, tmin_mean_c=19.0, tmax_mean_c=35.0, p_wet_given_dry=0.01, p_wet_given_wet=0.10, gamma_shape=0.9, gamma_scale=5.0),
                MonthlyClimateNorm(month=2, rain_mean_mm=12.0, rain_days=1.2, tmin_mean_c=21.5, tmax_mean_c=36.5, p_wet_given_dry=0.04, p_wet_given_wet=0.20, gamma_shape=1.0, gamma_scale=6.0),
                MonthlyClimateNorm(month=3, rain_mean_mm=35.0, rain_days=3.2, tmin_mean_c=23.5, tmax_mean_c=37.0, p_wet_given_dry=0.10, p_wet_given_wet=0.30, gamma_shape=1.1, gamma_scale=8.0),
                MonthlyClimateNorm(month=4, rain_mean_mm=75.0, rain_days=6.5, tmin_mean_c=24.0, tmax_mean_c=35.5, p_wet_given_dry=0.20, p_wet_given_wet=0.40, gamma_shape=1.2, gamma_scale=9.5),
                MonthlyClimateNorm(month=5, rain_mean_mm=125.0, rain_days=9.8, tmin_mean_c=23.0, tmax_mean_c=33.5, p_wet_given_dry=0.30, p_wet_given_wet=0.50, gamma_shape=1.3, gamma_scale=11.0),
                MonthlyClimateNorm(month=6, rain_mean_mm=160.0, rain_days=12.0, tmin_mean_c=22.0, tmax_mean_c=31.5, p_wet_given_dry=0.38, p_wet_given_wet=0.58, gamma_shape=1.4, gamma_scale=12.0),
                MonthlyClimateNorm(month=7, rain_mean_mm=215.0, rain_days=15.5, tmin_mean_c=21.5, tmax_mean_c=29.5, p_wet_given_dry=0.46, p_wet_given_wet=0.68, gamma_shape=1.5, gamma_scale=13.0),
                MonthlyClimateNorm(month=8, rain_mean_mm=260.0, rain_days=18.0, tmin_mean_c=21.2, tmax_mean_c=29.0, p_wet_given_dry=0.52, p_wet_given_wet=0.74, gamma_shape=1.6, gamma_scale=14.5),
                MonthlyClimateNorm(month=9, rain_mean_mm=210.0, rain_days=15.0, tmin_mean_c=21.5, tmax_mean_c=30.0, p_wet_given_dry=0.45, p_wet_given_wet=0.65, gamma_shape=1.4, gamma_scale=13.5),
                MonthlyClimateNorm(month=10, rain_mean_mm=70.0, rain_days=6.0, tmin_mean_c=22.0, tmax_mean_c=32.5, p_wet_given_dry=0.18, p_wet_given_wet=0.38, gamma_shape=1.2, gamma_scale=10.0),
                MonthlyClimateNorm(month=11, rain_mean_mm=12.0, rain_days=1.2, tmin_mean_c=20.0, tmax_mean_c=34.0, p_wet_given_dry=0.04, p_wet_given_wet=0.20, gamma_shape=1.0, gamma_scale=6.0),
                MonthlyClimateNorm(month=12, rain_mean_mm=3.0, rain_days=0.3, tmin_mean_c=18.5, tmax_mean_c=34.5, p_wet_given_dry=0.01, p_wet_given_wet=0.10, gamma_shape=0.8, gamma_scale=4.0)
            ],
            sentinel_villages=[
                VillageSoilSummary(village_id="TG_KAR_KOZ_01", village_name="Lama", texture="ferrugineux_sur_socle", taw_mm_m=102.0, depth_cm=95.0, drainage="bon"),
                VillageSoilSummary(village_id="TG_KAR_BAS_02", village_name="Kabou", texture="ferrugineux_gravillonnaire", taw_mm_m=94.0, depth_cm=90.0, drainage="rapide")
            ]
        ),
        ZoneProfile(
            zone_id="CENTRALE",
            zone_name="Région Centrale (Zone de transition)",
            regime=RegimePluvio.TRANSITION_UNIMODAL,
            annual_rainfall_mean_mm=1290.0,
            annual_rainfall_std_mm=120.0,
            season_1_earliest_sowing_date="04-20",
            season_2_earliest_sowing_date=None,
            season_2_status=None,
            false_start_probability_baseline=0.18,
            soil_default_taw_mm_m=115.0,
            soil_default_depth_cm=110.0,
            soil_default_drainage="moyen",
            monthly_climate=[
                MonthlyClimateNorm(month=1, rain_mean_mm=5.0, rain_days=0.5, tmin_mean_c=19.5, tmax_mean_c=34.5, p_wet_given_dry=0.02, p_wet_given_wet=0.15, gamma_shape=0.9, gamma_scale=5.0),
                MonthlyClimateNorm(month=2, rain_mean_mm=18.0, rain_days=1.8, tmin_mean_c=22.0, tmax_mean_c=36.0, p_wet_given_dry=0.06, p_wet_given_wet=0.25, gamma_shape=1.0, gamma_scale=7.0),
                MonthlyClimateNorm(month=3, rain_mean_mm=55.0, rain_days=4.5, tmin_mean_c=23.5, tmax_mean_c=36.5, p_wet_given_dry=0.15, p_wet_given_wet=0.35, gamma_shape=1.2, gamma_scale=9.0),
                MonthlyClimateNorm(month=4, rain_mean_mm=95.0, rain_days=7.5, tmin_mean_c=23.5, tmax_mean_c=34.5, p_wet_given_dry=0.24, p_wet_given_wet=0.45, gamma_shape=1.3, gamma_scale=10.5),
                MonthlyClimateNorm(month=5, rain_mean_mm=145.0, rain_days=10.5, tmin_mean_c=22.8, tmax_mean_c=33.0, p_wet_given_dry=0.33, p_wet_given_wet=0.54, gamma_shape=1.4, gamma_scale=12.0),
                MonthlyClimateNorm(month=6, rain_mean_mm=175.0, rain_days=13.0, tmin_mean_c=22.0, tmax_mean_c=31.0, p_wet_given_dry=0.40, p_wet_given_wet=0.60, gamma_shape=1.4, gamma_scale=12.5),
                MonthlyClimateNorm(month=7, rain_mean_mm=225.0, rain_days=16.0, tmin_mean_c=21.5, tmax_mean_c=29.5, p_wet_given_dry=0.48, p_wet_given_wet=0.70, gamma_shape=1.5, gamma_scale=13.5),
                MonthlyClimateNorm(month=8, rain_mean_mm=255.0, rain_days=18.5, tmin_mean_c=21.2, tmax_mean_c=29.0, p_wet_given_dry=0.54, p_wet_given_wet=0.75, gamma_shape=1.6, gamma_scale=14.5),
                MonthlyClimateNorm(month=9, rain_mean_mm=225.0, rain_days=16.0, tmin_mean_c=21.5, tmax_mean_c=29.8, p_wet_given_dry=0.48, p_wet_given_wet=0.68, gamma_shape=1.5, gamma_scale=13.5),
                MonthlyClimateNorm(month=10, rain_mean_mm=95.0, rain_days=8.0, tmin_mean_c=22.0, tmax_mean_c=32.0, p_wet_given_dry=0.24, p_wet_given_wet=0.45, gamma_shape=1.3, gamma_scale=10.5),
                MonthlyClimateNorm(month=11, rain_mean_mm=20.0, rain_days=2.0, tmin_mean_c=20.5, tmax_mean_c=33.5, p_wet_given_dry=0.07, p_wet_given_wet=0.25, gamma_shape=1.0, gamma_scale=7.0),
                MonthlyClimateNorm(month=12, rain_mean_mm=6.0, rain_days=0.6, tmin_mean_c=19.0, tmax_mean_c=34.0, p_wet_given_dry=0.02, p_wet_given_wet=0.15, gamma_shape=0.9, gamma_scale=5.0)
            ],
            sentinel_villages=[
                VillageSoilSummary(village_id="TG_CEN_TCH_01", village_name="Komah", texture="ferrugineux_concretionne", taw_mm_m=108.0, depth_cm=100.0, drainage="moyen"),
                VillageSoilSummary(village_id="TG_CEN_SOT_02", village_name="Adjengré", texture="ferrugineux_tropical", taw_mm_m=122.0, depth_cm=115.0, drainage="bon")
            ]
        ),
        ZoneProfile(
            zone_id="PLATEAUX",
            zone_name="Région des Plateaux (Guinéen forestier & humide)",
            regime=RegimePluvio.BIMODAL,
            annual_rainfall_mean_mm=1460.0,
            annual_rainfall_std_mm=145.0,
            season_1_earliest_sowing_date="03-15",
            season_2_earliest_sowing_date="09-01",
            season_2_status="a_valider",
            false_start_probability_baseline=0.12,
            soil_default_taw_mm_m=135.0,
            soil_default_depth_cm=130.0,
            soil_default_drainage="bon",
            monthly_climate=[
                MonthlyClimateNorm(month=1, rain_mean_mm=25.0, rain_days=2.0, tmin_mean_c=20.0, tmax_mean_c=32.5, p_wet_given_dry=0.07, p_wet_given_wet=0.25, gamma_shape=1.1, gamma_scale=7.0),
                MonthlyClimateNorm(month=2, rain_mean_mm=50.0, rain_days=4.0, tmin_mean_c=21.5, tmax_mean_c=34.0, p_wet_given_dry=0.13, p_wet_given_wet=0.35, gamma_shape=1.2, gamma_scale=9.0),
                MonthlyClimateNorm(month=3, rain_mean_mm=110.0, rain_days=8.5, tmin_mean_c=22.5, tmax_mean_c=34.5, p_wet_given_dry=0.26, p_wet_given_wet=0.48, gamma_shape=1.3, gamma_scale=11.0),
                MonthlyClimateNorm(month=4, rain_mean_mm=145.0, rain_days=11.0, tmin_mean_c=22.5, tmax_mean_c=33.5, p_wet_given_dry=0.35, p_wet_given_wet=0.55, gamma_shape=1.4, gamma_scale=12.0),
                MonthlyClimateNorm(month=5, rain_mean_mm=175.0, rain_days=13.5, tmin_mean_c=22.0, tmax_mean_c=32.0, p_wet_given_dry=0.40, p_wet_given_wet=0.60, gamma_shape=1.4, gamma_scale=12.5),
                MonthlyClimateNorm(month=6, rain_mean_mm=215.0, rain_days=16.0, tmin_mean_c=21.5, tmax_mean_c=30.0, p_wet_given_dry=0.48, p_wet_given_wet=0.68, gamma_shape=1.5, gamma_scale=13.5),
                MonthlyClimateNorm(month=7, rain_mean_mm=140.0, rain_days=12.0, tmin_mean_c=21.0, tmax_mean_c=28.5, p_wet_given_dry=0.36, p_wet_given_wet=0.56, gamma_shape=1.3, gamma_scale=11.5),
                MonthlyClimateNorm(month=8, rain_mean_mm=115.0, rain_days=10.5, tmin_mean_c=20.8, tmax_mean_c=28.0, p_wet_given_dry=0.32, p_wet_given_wet=0.52, gamma_shape=1.3, gamma_scale=11.0),
                MonthlyClimateNorm(month=9, rain_mean_mm=180.0, rain_days=14.5, tmin_mean_c=21.2, tmax_mean_c=29.5, p_wet_given_dry=0.44, p_wet_given_wet=0.64, gamma_shape=1.5, gamma_scale=13.0),
                MonthlyClimateNorm(month=10, rain_mean_mm=210.0, rain_days=16.0, tmin_mean_c=21.5, tmax_mean_c=30.5, p_wet_given_dry=0.48, p_wet_given_wet=0.68, gamma_shape=1.5, gamma_scale=13.5),
                MonthlyClimateNorm(month=11, rain_mean_mm=65.0, rain_days=6.0, tmin_mean_c=21.0, tmax_mean_c=32.0, p_wet_given_dry=0.18, p_wet_given_wet=0.38, gamma_shape=1.2, gamma_scale=9.5),
                MonthlyClimateNorm(month=12, rain_mean_mm=25.0, rain_days=2.2, tmin_mean_c=19.8, tmax_mean_c=32.0, p_wet_given_dry=0.07, p_wet_given_wet=0.25, gamma_shape=1.1, gamma_scale=7.0)
            ],
            sentinel_villages=[
                VillageSoilSummary(village_id="TG_PLA_HAH_01", village_name="Alinou", texture="ferrugineux_profond", taw_mm_m=130.0, depth_cm=130.0, drainage="bon"),
                VillageSoilSummary(village_id="TG_PLA_OGO_02", village_name="Datcha", texture="ferrugineux_lessive", taw_mm_m=118.0, depth_cm=120.0, drainage="bon"),
                VillageSoilSummary(village_id="TG_PLA_KLO_03", village_name="Agou-Nyogbo", texture="ferrallitique_humifere", taw_mm_m=148.0, depth_cm=140.0, drainage="excellent")
            ]
        ),
        ZoneProfile(
            zone_id="MARITIME",
            zone_name="Région Maritime (Littoral & Terres de barre)",
            regime=RegimePluvio.BIMODAL,
            annual_rainfall_mean_mm=910.0,
            annual_rainfall_std_mm=105.0,
            season_1_earliest_sowing_date="03-25",
            season_2_earliest_sowing_date="09-15",
            season_2_status="a_valider",
            false_start_probability_baseline=0.22,
            soil_default_taw_mm_m=110.0,
            soil_default_depth_cm=115.0,
            soil_default_drainage="bon",
            monthly_climate=[
                MonthlyClimateNorm(month=1, rain_mean_mm=12.0, rain_days=1.2, tmin_mean_c=23.0, tmax_mean_c=32.0, p_wet_given_dry=0.04, p_wet_given_wet=0.20, gamma_shape=1.0, gamma_scale=6.0),
                MonthlyClimateNorm(month=2, rain_mean_mm=28.0, rain_days=2.5, tmin_mean_c=24.5, tmax_mean_c=33.0, p_wet_given_dry=0.08, p_wet_given_wet=0.28, gamma_shape=1.1, gamma_scale=8.0),
                MonthlyClimateNorm(month=3, rain_mean_mm=70.0, rain_days=5.5, tmin_mean_c=25.0, tmax_mean_c=33.5, p_wet_given_dry=0.17, p_wet_given_wet=0.38, gamma_shape=1.2, gamma_scale=10.0),
                MonthlyClimateNorm(month=4, rain_mean_mm=110.0, rain_days=8.0, tmin_mean_c=25.0, tmax_mean_c=33.0, p_wet_given_dry=0.25, p_wet_given_wet=0.48, gamma_shape=1.3, gamma_scale=11.5),
                MonthlyClimateNorm(month=5, rain_mean_mm=160.0, rain_days=11.5, tmin_mean_c=24.5, tmax_mean_c=32.0, p_wet_given_dry=0.35, p_wet_given_wet=0.58, gamma_shape=1.4, gamma_scale=12.5),
                MonthlyClimateNorm(month=6, rain_mean_mm=220.0, rain_days=15.0, tmin_mean_c=23.5, tmax_mean_c=29.5, p_wet_given_dry=0.46, p_wet_given_wet=0.68, gamma_shape=1.5, gamma_scale=13.5),
                MonthlyClimateNorm(month=7, rain_mean_mm=65.0, rain_days=6.5, tmin_mean_c=23.0, tmax_mean_c=28.0, p_wet_given_dry=0.18, p_wet_given_wet=0.38, gamma_shape=1.2, gamma_scale=9.5),
                MonthlyClimateNorm(month=8, rain_mean_mm=30.0, rain_days=3.5, tmin_mean_c=22.5, tmax_mean_c=27.5, p_wet_given_dry=0.10, p_wet_given_wet=0.30, gamma_shape=1.1, gamma_scale=8.0),
                MonthlyClimateNorm(month=9, rain_mean_mm=70.0, rain_days=6.5, tmin_mean_c=23.0, tmax_mean_c=28.5, p_wet_given_dry=0.18, p_wet_given_wet=0.38, gamma_shape=1.2, gamma_scale=9.5),
                MonthlyClimateNorm(month=10, rain_mean_mm=115.0, rain_days=9.0, tmin_mean_c=23.5, tmax_mean_c=30.5, p_wet_given_dry=0.28, p_wet_given_wet=0.50, gamma_shape=1.3, gamma_scale=11.5),
                MonthlyClimateNorm(month=11, rain_mean_mm=45.0, rain_days=4.0, tmin_mean_c=24.0, tmax_mean_c=32.0, p_wet_given_dry=0.12, p_wet_given_wet=0.32, gamma_shape=1.1, gamma_scale=8.5),
                MonthlyClimateNorm(month=12, rain_mean_mm=15.0, rain_days=1.5, tmin_mean_c=23.5, tmax_mean_c=32.0, p_wet_given_dry=0.05, p_wet_given_wet=0.22, gamma_shape=1.0, gamma_scale=6.5)
            ],
            sentinel_villages=[
                VillageSoilSummary(village_id="TG_MAR_ZIO_01", village_name="Davié", texture="ferrallitique_terre_de_barre", taw_mm_m=120.0, depth_cm=120.0, drainage="bon"),
                VillageSoilSummary(village_id="TG_MAR_LAC_02", village_name="Glidji", texture="sablo_littoral", taw_mm_m=72.0, depth_cm=90.0, drainage="tres_rapide"),
                VillageSoilSummary(village_id="TG_MAR_YOT_03", village_name="Ahépé", texture="ferrallitique_argileux", taw_mm_m=143.0, depth_cm=110.0, drainage="modere")
            ]
        )
    ]

def _seed_zone_profiles_if_empty(cursor: sqlite3.Cursor):
    cursor.execute("SELECT COUNT(*) as cnt FROM zone_profiles;")
    row = cursor.fetchone()
    if row and row["cnt"] > 0:
        return
    for zp in _build_default_zone_profiles():
        cursor.execute("""
            INSERT OR REPLACE INTO zone_profiles (
                zone_id, zone_name, regime, annual_rainfall_mean_mm, annual_rainfall_std_mm,
                season_1_earliest_sowing_date, season_2_earliest_sowing_date, season_2_status,
                false_start_probability_baseline, soil_default_taw_mm_m, soil_default_depth_cm,
                soil_default_drainage, data_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            zp.zone_id,
            zp.zone_name,
            zp.regime.value,
            zp.annual_rainfall_mean_mm,
            zp.annual_rainfall_std_mm,
            zp.season_1_earliest_sowing_date,
            zp.season_2_earliest_sowing_date,
            zp.season_2_status,
            zp.false_start_probability_baseline,
            zp.soil_default_taw_mm_m,
            zp.soil_default_depth_cm,
            zp.soil_default_drainage,
            zp.model_dump_json()
        ))

def get_zone_profile(zone_id: str) -> Optional[ZoneProfile]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT data_json FROM zone_profiles WHERE zone_id = ?;", (zone_id.upper(),))
        row = cursor.fetchone()
        if row:
            return ZoneProfile(**json.loads(row["data_json"]))
        return None

def list_zone_profiles() -> List[ZoneProfile]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT data_json FROM zone_profiles ORDER BY zone_id;")
        rows = cursor.fetchall()
        return [ZoneProfile(**json.loads(r["data_json"])) for r in rows]

def get_village_zone_mapping(village_id: str) -> Optional[Dict[str, Any]]:
    zones = list_zone_profiles()
    for z in zones:
        for v in z.sentinel_villages:
            if v.village_id == village_id:
                return {
                    "zone": z,
                    "village_soil": v
                }
    return None

# --- Real-Time Events & Field Actions (Step E5) ---

def record_event(
    event_type: str,
    village_id: str,
    channel: str,
    payload: Dict[str, Any],
    phone_hash: str
) -> int:
    """Record an audit trail event for real-time dashboard notification."""
    with get_connection() as conn:
        cursor = conn.cursor()
        now_iso = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO events (timestamp, event_type, village_id, channel, payload, phone_hash)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (now_iso, event_type, village_id, channel, json.dumps(payload, ensure_ascii=False), phone_hash))
        conn.commit()
        return cursor.lastrowid

def get_live_events(since_iso: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieve recent stream events ordered by latest first."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if since_iso:
            cursor.execute("""
                SELECT id, timestamp, event_type, village_id, channel, payload, phone_hash
                FROM events
                WHERE timestamp > ?
                ORDER BY timestamp DESC
                LIMIT ?;
            """, (since_iso, limit))
        else:
            cursor.execute("""
                SELECT id, timestamp, event_type, village_id, channel, payload, phone_hash
                FROM events
                ORDER BY timestamp DESC
                LIMIT ?;
            """, (limit,))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["payload"] = json.loads(d["payload"])
            except Exception:
                pass
            result.append(d)
        return result

def record_planting_report(
    phone_hash: str,
    village_id: str,
    crop_type: str,
    variety_name: str,
    planted_date: Optional[str] = None
) -> int:
    """Record a farmer's planting declaration ('J'ai semé')."""
    with get_connection() as conn:
        cursor = conn.cursor()
        now_iso = datetime.now(timezone.utc).isoformat()
        p_date = planted_date or date.today().isoformat()
        cursor.execute("""
            INSERT INTO planting_reports (phone_hash, village_id, crop_type, variety_name, planted_date, reported_at)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (phone_hash, village_id, crop_type, variety_name, p_date, now_iso))
        conn.commit()
        rep_id = cursor.lastrowid

        # Also emit a real-time event
        record_event(
            event_type="planting_report",
            village_id=village_id,
            channel="USSD",
            payload={
                "report_id": rep_id,
                "crop": crop_type,
                "variety": variety_name,
                "planted_date": p_date
            },
            phone_hash=phone_hash
        )
        return rep_id

def get_planting_reports(village_id: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if village_id:
            cursor.execute("SELECT * FROM planting_reports WHERE village_id = ? ORDER BY reported_at DESC;", (village_id,))
        else:
            cursor.execute("SELECT * FROM planting_reports ORDER BY reported_at DESC;")
        return [dict(r) for r in cursor.fetchall()]

def save_audio_evaluation(
    clip_id: str,
    language: str,
    clarity_rating: int,
    naturalness_rating: int,
    accent_authenticity_rating: int,
    comprehension_check_passed: bool = True,
    evaluator_name: Optional[str] = None,
    evaluator_origin_region: Optional[str] = None,
    comments: Optional[str] = None
) -> int:
    """Save an evaluation from a native speaker or jury (Step E10)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        now_iso = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO audio_evaluations (
                clip_id, language, evaluator_name, evaluator_origin_region,
                clarity_rating, naturalness_rating, accent_authenticity_rating,
                comprehension_check_passed, comments, evaluated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            clip_id,
            language.lower(),
            evaluator_name or "Anonyme",
            evaluator_origin_region or "Maritime",
            max(1, min(5, int(clarity_rating))),
            max(1, min(5, int(naturalness_rating))),
            max(1, min(5, int(accent_authenticity_rating))),
            1 if comprehension_check_passed else 0,
            comments or "",
            now_iso
        ))
        conn.commit()
        return cursor.lastrowid

def list_audio_evaluations(language: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve individual audio evaluations, optionally filtered by language."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if language:
            cursor.execute("SELECT * FROM audio_evaluations WHERE language = ? ORDER BY evaluated_at DESC;", (language.lower(),))
        else:
            cursor.execute("SELECT * FROM audio_evaluations ORDER BY evaluated_at DESC;")
        return [dict(r) for r in cursor.fetchall()]

def get_audio_evaluations_summary() -> Dict[str, Any]:
    """Calculate aggregated evaluation metrics per language and overall."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                language,
                COUNT(*) as count,
                AVG(clarity_rating) as avg_clarity,
                AVG(naturalness_rating) as avg_naturalness,
                AVG(accent_authenticity_rating) as avg_authenticity,
                AVG(comprehension_check_passed) * 100.0 as comprehension_rate_pct
            FROM audio_evaluations
            GROUP BY language;
        """)
        rows = cursor.fetchall()
        by_language = {}
        total_evals = 0
        sum_clarity = 0.0
        sum_naturalness = 0.0
        sum_authenticity = 0.0
        sum_comprehension = 0.0

        for r in rows:
            cnt = r["count"]
            lang = r["language"]
            c = round(r["avg_clarity"], 2) if r["avg_clarity"] is not None else 0.0
            n = round(r["avg_naturalness"], 2) if r["avg_naturalness"] is not None else 0.0
            a = round(r["avg_authenticity"], 2) if r["avg_authenticity"] is not None else 0.0
            comp = round(r["comprehension_rate_pct"], 1) if r["comprehension_rate_pct"] is not None else 0.0
            
            by_language[lang] = {
                "count": cnt,
                "avg_clarity": c,
                "avg_naturalness": n,
                "avg_authenticity": a,
                "comprehension_rate_pct": comp,
                "mean_overall_score": round((c + n + a) / 3.0, 2)
            }
            total_evals += cnt
            sum_clarity += c * cnt
            sum_naturalness += n * cnt
            sum_authenticity += a * cnt
            sum_comprehension += comp * cnt

        overall = {
            "total_evaluations": total_evals,
            "overall_avg_clarity": round(sum_clarity / total_evals, 2) if total_evals else 0.0,
            "overall_avg_naturalness": round(sum_naturalness / total_evals, 2) if total_evals else 0.0,
            "overall_avg_authenticity": round(sum_authenticity / total_evals, 2) if total_evals else 0.0,
            "overall_comprehension_rate_pct": round(sum_comprehension / total_evals, 1) if total_evals else 0.0
        }
        return {
            "by_language": by_language,
            "overall": overall
        }
