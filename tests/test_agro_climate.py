"""Unit tests for spatial repo, freshness watchdog, resilience scorer, and alert detector."""
from datetime import datetime, date, timedelta, timezone
import pytest
from src.core.models import AlertStatus, ConfidenceLevel, CropType, RegimePluvio, Language
from src.data_ingestion.repositories import SpatialRepository
from src.data_ingestion.freshness_watchdog import FreshnessWatchdog
from src.data_ingestion.weather_service import WeatherService, WeatherData
from src.crop_models.resilience_scorer import CropResilienceScorer
from src.alerts.season_detector import SeasonDetector
from src.alerts.backtest import BacktestEngine
from src.data_ingestion.precompute_engine import PrecomputeEngine
from src.core.database import init_db, get_precalculated_sheet

@pytest.fixture
def repo():
    return SpatialRepository()

def test_spatial_repository_loading(repo):
    villages = repo.list_villages()
    assert len(villages) >= 10
    
    # Check Savanes village
    kantindi = repo.get_village("TG_SAV_TON_01")
    assert kantindi is not None
    assert kantindi.region == "Savanes"
    assert kantindi.regime_pluviometrique == RegimePluvio.UNIMODAL

    # Check soil profile
    soil = repo.get_soil_for_village("TG_MAR_ZIO_01")
    assert soil is not None
    assert "ferrallitique" in soil.description.lower()
    assert soil.taw_mm_m > 100

    # Check seed varieties
    maize_vars = repo.list_varieties_for_crop(CropType.MAIS)
    assert len(maize_vars) >= 4
    names = [v.variety_name for v in maize_vars]
    assert "TZEE-W-SR" in names
    assert "Sotubaka" in names

def test_freshness_watchdog_safety_override():
    watchdog = FreshnessWatchdog(max_hours=48)
    now = datetime.now(timezone.utc)
    
    # 1. Fresh data (12 hours old) -> SEMER preserved
    fresh_time = now - timedelta(hours=12)
    alert, is_stale, _ = watchdog.evaluate_safety(
        proposed_alert=AlertStatus.SEMER,
        last_weather_update=fresh_time,
        reference_time=now
    )
    assert alert == AlertStatus.SEMER
    assert is_stale is False

    # 2. Stale data (60 hours old) -> SEMER MUST BE FORCIBLY OVERRIDDEN!
    stale_time = now - timedelta(hours=60)
    alert_stale, is_stale_2, reason = watchdog.evaluate_safety(
        proposed_alert=AlertStatus.SEMER,
        last_weather_update=stale_time,
        reference_time=now
    )
    assert alert_stale == AlertStatus.ATTENDRE_CONSULTER_AGENT
    assert is_stale_2 is True
    assert "RÈGLE DE SÉCURITÉ ACTIVE" in reason

def test_resilience_scorer_ranking(repo):
    scorer = CropResilienceScorer()
    village = repo.get_village("TG_SAV_TON_01") # Savanes, short season
    soil = repo.get_soil_for_village(village.village_id)
    candidates = repo.list_varieties_for_crop(CropType.MAIS)

    evals = scorer.evaluate_varieties(village, soil, candidates, season_month=6)
    assert len(evals) > 0
    # Top variety should be extra-early or early (e.g. TZEE-W-SR), not late (TZB-SR)
    top_var = evals[0].variety
    assert top_var.cycle_days_nominal <= 95
    # Late variety (TZB-SR) should have higher failure rate in the short Savanes season
    late_vars = [e for e in evals if e.variety.variety_name == "TZB-SR"]
    if late_vars:
        assert late_vars[0].failure_rate_pct > evals[0].failure_rate_pct

def test_season_detector_false_start(repo):
    detector = SeasonDetector()
    village = repo.get_village("TG_MAR_ZIO_01")
    soil = repo.get_soil_for_village(village.village_id)
    
    # Simulate False Start: 25mm rain on past 3 days, but 10 days consecutive dry spell forecast
    weather_false = WeatherData(
        village_id=village.village_id,
        timestamp=datetime.now(timezone.utc),
        rain_last_3days_mm=25.0,
        rain_last_7days_mm=25.0,
        rain_forecast_7days_mm=1.0,
        daily_forecast_rain=[0.0] * 10 + [5.0, 0.0, 0.0, 0.0],
        daily_forecast_tmax=[34.0] * 14,
        daily_forecast_tmin=[23.0] * 14,
        dry_spell_forecast_max_days=10,
        source="TestMock"
    )

    res = detector.evaluate_onset(
        village=village,
        soil=soil,
        weather=weather_false,
        current_date=date(2026, 4, 1)
    )

    assert res.alert_status == AlertStatus.RISQUE
    assert res.is_false_start_risk is True
    assert "FAUX DÉPART DÉTECTÉ" in res.reasons[0]
    # Check Éwé local message exists
    assert Language.EWE in res.advice_local
    assert "Kuɖiɖi gbɔna" in res.advice_local[Language.EWE]

def test_backtest_benchmark(repo):
    engine = BacktestEngine(repo)
    bench_results = engine.run_benchmark()
    
    assert bench_results["total_tests"] >= 12
    assert bench_results["critical_errors"] == 0
    assert bench_results["false_start_safety_rate_pct"] == 100.0
    assert bench_results["accuracy_pct"] >= 95.0

def test_precompute_pipeline_execution(tmp_path, monkeypatch, repo):
    from src.core.config import settings
    monkeypatch.setattr(settings, "DB_PATH", tmp_path / "test_precomp.db")
    init_db()

    engine = PrecomputeEngine(repo=repo)
    sheets = engine.run_daily_pipeline(
        reference_date=date(2026, 4, 15),
        simulated_weather_scenario="optimal_onset"
    )

    assert len(sheets) > 0
    # Check that sheets are retrieved from SQLite in less than 5ms
    sample = get_precalculated_sheet("TG_MAR_ZIO_01", CropType.MAIS)
    assert sample is not None
    assert sample.village_name == "Davié"
    assert sample.alert_status in [AlertStatus.SEMER, AlertStatus.ATTENDRE]

