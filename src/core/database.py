"""SQLite Database manager for AuraFarm pre-computed records and field data."""
import json
import sqlite3
from typing import Optional, List, Dict, Any
from src.core.config import settings
from src.core.models import (
    PrecalculatedSheet,
    FarmerProfile,
    FieldRainObservation,
    AlertStatus,
    ConfidenceLevel,
    Language,
    CropType
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

def get_recent_field_observations(village_id: str, limit: int = 5) -> List[FieldRainObservation]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM field_observations
            WHERE village_id = ?
            ORDER BY observation_date DESC
            LIMIT ?;
        """, (village_id, limit))
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
