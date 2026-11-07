"""Unit and integration tests for Step E4: Dashboard Fiches in 4 Traceable Blocks."""
from datetime import datetime, date, timezone
import pytest
from src.core.config import settings
from src.core.database import (
    init_db,
    save_precalculated_sheet,
    get_all_precalculated_sheets
)
from src.core.models import (
    PrecalculatedSheet,
    CropType,
    AlertStatus,
    ConfidenceLevel
)
from src.data_ingestion.repositories import SpatialRepository
from src.data_ingestion.precompute_engine import PrecomputeEngine
from src.dashboard.fiche_builder import (
    build_enriched_fiche_data,
    render_fiche_card_html,
    VILLAGE_PCODES
)
from src.api.main import get_dashboard_fiches

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_fiches.db"
    monkeypatch.setattr(settings, "DB_PATH", test_db)
    init_db()

def _create_sample_sheet(village_id: str, crop: CropType, alert: AlertStatus, is_stale: bool = False) -> PrecalculatedSheet:
    return PrecalculatedSheet(
        village_id=village_id,
        village_name="VillageTest",
        crop_type=crop,
        calculation_date=datetime.now(timezone.utc).isoformat(),
        recommended_variety_id="VAR_TEST_01",
        recommended_variety_name="TZEE-W-SR",
        alert_status=alert,
        confidence=ConfidenceLevel.SUR,
        rain_last_3days_mm=26.0,
        rain_forecast_7days_mm=18.0,
        dry_spell_risk_days=4,
        is_data_stale=is_stale,
        advice_fr="Semez dès maintenant.",
        advice_local="Mido nu azɔ.",
        audio_key_sequence=["audio_intro", "audio_semer"],
        last_weather_update=datetime.now(timezone.utc).isoformat()
    )

def test_fiche_4_blocks_structure_and_data_fields():
    """Verify that 4 distinct blocks (A, B, C, D) are populated with all required fields across >= 3 fiches."""
    repo = SpatialRepository()
    test_villages = ["TG_SAV_TON_01", "TG_MAR_ZIO_01", "TG_PLA_KLO_03"]

    for vid in test_villages:
        v = repo.get_village(vid)
        sheet = _create_sample_sheet(vid, CropType.MAIS, AlertStatus.SEMER)
        sheet.village_name = v.village_name

        f_data = build_enriched_fiche_data(sheet, repo, force_stale_hours=12)

        # 1. Pcode
        assert f_data["pcode"] == VILLAGE_PCODES[vid]
        assert f_data["village_name"] == v.village_name

        # 2. Bloc D : Banner
        assert "control_banner" in f_data
        assert f_data["control_banner"]["type"] == "ok"
        assert "banner-ok" in f_data["control_banner"]["css_class"]

        # 3. Bloc A : Entrées
        assert "rain_source" in f_data
        assert "coordinates" in f_data
        assert "village_readings_summary" in f_data
        assert f_data["is_stale"] is False

        # 4. Bloc B : Calcul
        assert f_data["rain_last_3days_mm"] == 26.0
        assert f_data["rain_decade_10days_mm"] > 26.0
        assert f_data["soil_retention"] in ["Faible", "Moyenne", "Forte"]
        assert f_data["daily_et0_mm"] > 2.0
        assert "triggered_rule" in f_data
        assert len(f_data["triggered_rule"]) > 10

        # 5. Bloc C : Sortie
        assert f_data["alert_status"] == AlertStatus.SEMER.value
        assert "SEMER" in f_data["status_label"]
        assert f_data["confidence"] == ConfidenceLevel.SUR.value
        assert f_data["recommended_variety_name"] == "TZEE-W-SR"
        assert f_data["cycle_days"] > 0
        assert len(f_data["advice_fr"]) > 0
        assert len(f_data["advice_local"]) > 0
        assert not f_data["is_translation_missing"]
        assert "USSD *384*228#" in f_data["channels"]

        # 6. Render HTML check
        html = render_fiche_card_html(f_data)
        assert "fiche-card" in html
        assert "bloc-d-banner" in html
        assert "bloc-a-entries" in html
        assert "bloc-b-calc" in html
        assert "bloc-c-output" in html
        assert f_data["pcode"] in html

def test_bloc_d_priority_and_error_cases():
    """Verify strict priority ordering of control alerts in Bloc D."""
    repo = SpatialRepository()
    sheet = _create_sample_sheet("TG_SAV_TON_01", CropType.SORGHO, AlertStatus.SEMER)

    # Priority 1: Data > 48h stale (J-10 = 240 hours) -> Red banner, forced ATTENDRE_CONSULTER_AGENT
    f_stale = build_enriched_fiche_data(sheet, repo, force_stale_hours=240)
    assert f_stale["control_banner"]["type"] == "stale"
    assert "banner-stale" in f_stale["control_banner"]["css_class"]
    assert "DONNÉE PÉRIMÉE" in f_stale["control_banner"]["label"]
    assert f_stale["alert_status"] == AlertStatus.ATTENDRE_CONSULTER_AGENT.value
    assert f_stale["confidence"] == ConfidenceLevel.INCERTAIN.value

    # Priority 2: Soil fallback
    f_fallback = build_enriched_fiche_data(sheet, repo, force_stale_hours=10, force_soil_fallback=True)
    assert f_fallback["control_banner"]["type"] == "fallback"
    assert "banner-fallback" in f_fallback["control_banner"]["css_class"]

    # Priority 3: Contradictory observations
    f_contra = build_enriched_fiche_data(sheet, repo, force_stale_hours=10, force_contradiction=True)
    assert f_contra["control_banner"]["type"] == "contradiction"
    assert "banner-contradiction" in f_contra["control_banner"]["css_class"]
    assert f_contra["confidence"] == ConfidenceLevel.INCERTAIN.value

    # Priority 4: Seed rupture
    f_rupture = build_enriched_fiche_data(sheet, repo, force_stale_hours=10, force_rupture=True)
    assert f_rupture["control_banner"]["type"] == "rupture"
    assert "banner-rupture" in f_rupture["control_banner"]["css_class"]

    # Priority 5: Simulation mode
    f_sim = build_enriched_fiche_data(sheet, repo, force_stale_hours=10, is_simulated=True, sim_seed=42)
    assert f_sim["control_banner"]["type"] == "simulation"
    assert "banner-simulation" in f_sim["control_banner"]["css_class"]
    assert "42" in f_sim["control_banner"]["label"]

def test_api_dashboard_fiches_endpoint():
    """Verify GET /api/dashboard/fiches endpoint returns enriched sheets with HTML."""
    repo = SpatialRepository()
    sheet = _create_sample_sheet("TG_MAR_ZIO_01", CropType.MAIS, AlertStatus.SEMER)
    save_precalculated_sheet(sheet)

    fiches = get_dashboard_fiches(village_id="TG_MAR_ZIO_01", crop="mais")
    assert len(fiches) == 1
    f = fiches[0]

    assert f["village_id"] == "TG_MAR_ZIO_01"
    assert f["pcode"] == "TG01"
    assert "html" in f
    assert "bloc-d-banner" in f["html"]
    assert "bloc-a-entries" in f["html"]
    assert "bloc-b-calc" in f["html"]
    assert "bloc-c-output" in f["html"]

    # Test error case over API: forcing stale hours (J-10)
    stale_fiches = get_dashboard_fiches(village_id="TG_MAR_ZIO_01", force_stale_hours=240)
    assert len(stale_fiches) == 1
    sf = stale_fiches[0]
    assert sf["control_banner"]["type"] == "stale"
    assert sf["alert_status"] == AlertStatus.ATTENDRE_CONSULTER_AGENT.value
    assert "banner-stale" in sf["html"]

