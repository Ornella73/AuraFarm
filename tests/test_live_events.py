"""Test suite for Step E5: Real-time Dashboard ↔ USSD Event Stream and Audit Trail."""
import json
import pytest
from datetime import datetime, timezone, timedelta
from src.core.database import (
    init_db,
    record_event,
    get_live_events,
    record_planting_report,
    get_planting_reports,
    save_field_observation
)
from src.core.models import FieldRainObservation
from src.channels.ussd_engine import UssdSessionEngine
from src.data_ingestion.repositories import SpatialRepository
from src.api.main import (
    get_dashboard_live,
    post_event,
    list_planting_reports,
    EventCreatePayload
)

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()

def test_record_and_get_live_events():
    """Verify that audit trail events are properly saved and retrieved in reverse chronological order."""
    phone_hash = "pseudonymized_hash_abc123"
    event_id = record_event(
        event_type="consultation",
        village_id="TG_MAR_ZIO_01",
        channel="USSD",
        payload={"query": "sowing_advice", "status": "SEMER"},
        phone_hash=phone_hash
    )
    assert event_id is not None
    assert event_id > 0

    events = get_live_events(limit=5)
    assert len(events) >= 1
    latest = events[0]
    assert latest["event_type"] == "consultation"
    assert latest["village_id"] == "TG_MAR_ZIO_01"
    assert latest["channel"] == "USSD"
    assert latest["phone_hash"] == phone_hash
    assert latest["payload"]["status"] == "SEMER"

def test_live_events_since_filter():
    """Verify time-based filtering with since_iso."""
    past_iso = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    record_event(
        event_type="test_marker",
        village_id="TG_PLA_HAH_04",
        channel="PWA",
        payload={"marker": True},
        phone_hash="hash_marker"
    )
    events_after = get_live_events(since_iso=past_iso, limit=10)
    assert any(e["event_type"] == "test_marker" for e in events_after)

    future_iso = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    events_future = get_live_events(since_iso=future_iso, limit=10)
    assert len(events_future) == 0

def test_ussd_emits_realtime_events():
    """Verify that USSD actions automatically log real-time stream events."""
    repo = SpatialRepository()
    engine = UssdSessionEngine(repo=repo)
    phone = "+22890998877"

    # Step 1: Language selection (Français)
    sess_id = "test_live_sess_01"
    resp1 = engine.process_request(sess_id, phone, "")
    assert not resp1.is_terminal

    resp2 = engine.process_request(sess_id, phone, "4") # Select French -> Menu
    assert "Dois-je semer ?" in resp2.text

    # Step 2: Option 1 (Dois-je semer ?)
    resp3 = engine.process_request(sess_id, phone, "4*1")
    assert resp3.text is not None

    # Verify event was recorded
    events = get_live_events(limit=5)
    consultation_evts = [e for e in events if e["event_type"] == "consultation"]
    assert len(consultation_evts) >= 1
    assert consultation_evts[0]["payload"]["type"] == "sowing_advice"

def test_planting_report_declaration_and_event():
    """Verify farmer planting declaration records row and triggers real-time event."""
    rep_id = record_planting_report(
        phone_hash="hash_farmer_semis_42",
        village_id="TG_SAV_TON_10",
        crop_type="sorgho",
        variety_name="Sorgho Blanc Local",
        planted_date="2026-06-15"
    )
    assert rep_id is not None
    assert rep_id > 0

    reports = get_planting_reports(village_id="TG_SAV_TON_10")
    assert len(reports) >= 1
    assert reports[0]["crop_type"] == "sorgho"
    assert reports[0]["variety_name"] == "Sorgho Blanc Local"

    # Check that a planting_report event was generated
    events = get_live_events(limit=5)
    planting_evts = [e for e in events if e["event_type"] == "planting_report"]
    assert len(planting_evts) >= 1
    assert planting_evts[0]["payload"]["variety"] == "Sorgho Blanc Local"

def test_api_dashboard_live_and_post_event():
    """Verify GET /api/dashboard/live and POST /api/events route functions."""
    # Post an event
    post_res = post_event(EventCreatePayload(
        event_type="field_alert",
        village_id="TG_CEN_TCH_07",
        channel="TEST_CLI",
        payload={"alert": "chenille_legionnaire"},
        phone_hash="anon_hash"
    ))
    assert post_res["status"] == "ok"
    assert "event_id" in post_res

    # Query live endpoint
    live_res = get_dashboard_live(limit=10)
    assert "events" in live_res
    assert "count" in live_res
    assert "timestamp" in live_res
    assert live_res["count"] > 0
    assert any(e["event_type"] == "field_alert" for e in live_res["events"])

