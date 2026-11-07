"""Unit and integration tests for Step E3: Soil Water Balance (Hargreaves-Samani + TAW) and Unified Sowing Decision."""
from datetime import date
import pytest
from src.core.config import settings
from src.core.database import init_db
from src.core.models import (
    Village,
    SoilProfile,
    Variety,
    CropType,
    RegimePluvio,
    AlertStatus,
    ConfidenceLevel
)
from src.data_ingestion.repositories import SpatialRepository
from src.data_ingestion.weather_service import WeatherData
from src.alerts.season_detector import SeasonDetector
from src.agro_climate.water_balance import (
    calculate_hargreaves_samani_et0,
    SoilWaterReservoir,
    simulate_post_sowing_21days,
    calculate_sowing_window
)
from src.api.main import get_water_balance, get_sowing_window

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_wb.db"
    monkeypatch.setattr(settings, "DB_PATH", test_db)
    init_db()

def test_hargreaves_samani_et0_physics_and_monotonicity():
    """Verify ET0 formula and physical monotonicity: Higher temperature strictly increases ET0."""
    lat_togo = 8.5
    doy_april = 105

    # 1. Monotonicity: Tmax up -> ET0 strictly up
    et0_30 = calculate_hargreaves_samani_et0(tmin_c=22.0, tmax_c=30.0, latitude_deg=lat_togo, day_of_year=doy_april)
    et0_35 = calculate_hargreaves_samani_et0(tmin_c=22.0, tmax_c=35.0, latitude_deg=lat_togo, day_of_year=doy_april)
    et0_40 = calculate_hargreaves_samani_et0(tmin_c=22.0, tmax_c=40.0, latitude_deg=lat_togo, day_of_year=doy_april)

    assert et0_30 < et0_35 < et0_40, f"Monotonicity violated: {et0_30} < {et0_35} < {et0_40}"

    # 2. Realistic West African bounds (3.0 to 8.5 mm/day)
    assert 3.0 <= et0_30 <= 6.0
    assert 4.5 <= et0_40 <= 8.5

def test_soil_water_reservoir_dynamics():
    """Verify soil root-zone reservoir infiltration, depletion, and stress factor."""
    # Davié 'terre de barre': TAW = 120 mm/m, depth = 100 cm -> TAW_mm = 120 mm
    res = SoilWaterReservoir(taw_mm_m=120.0, depth_cm=100.0, initial_fill_fraction=0.50)
    assert res.taw_mm == 120.0
    assert res.current_water_mm == 60.0
    assert res.soil_moisture_pct == 50.0
    assert res.depletion_mm == 60.0
    assert not res.is_at_wilting_point

    # Heavy rainfall (80 mm): 60mm infiltrates to reach full capacity (120mm), 20mm is runoff
    step1 = res.step(rainfall_mm=80.0, et0_mm=5.0, crop_stage_kc=0.40)
    assert res.current_water_mm > 115.0
    assert step1["runoff_mm"] > 15.0  # Runoff captured

    # Severe continuous dry period (30 days without rain, ET0=6.0 mm/day, Kc=0.40)
    for _ in range(30):
        res.step(rainfall_mm=0.0, et0_mm=6.0, crop_stage_kc=0.40)

    # Soil moisture must have dropped substantially
    assert res.soil_moisture_pct < 50.0
    assert res.depletion_mm > 60.0

def test_monotonicity_soil_retention_and_false_start():
    """Verify Monotonicity: Lower soil TAW strictly increases vulnerability to false starts."""
    # Compare Sandy littoral soil (Glidji: TAW=72 mm/m, depth=90cm -> 64.8mm)
    # vs Deep Ferrallitic soil (Agou: TAW=148 mm/m, depth=140cm -> 207.2mm)
    sandy_res = SoilWaterReservoir(taw_mm_m=72.0, depth_cm=90.0, initial_fill_fraction=0.40)
    clay_res = SoilWaterReservoir(taw_mm_m=148.0, depth_cm=140.0, initial_fill_fraction=0.40)

    # Identical 14-day dry spell with high temperature (36°C)
    dry_spell_rain = [0.0] * 21
    dry_spell_tmax = [36.0] * 21
    dry_spell_tmin = [24.0] * 21

    eval_sandy = simulate_post_sowing_21days(
        reservoir=sandy_res,
        daily_rain=dry_spell_rain,
        daily_tmax=dry_spell_tmax,
        daily_tmin=dry_spell_tmin,
        latitude_deg=6.5,
        start_doy=90
    )

    eval_clay = simulate_post_sowing_21days(
        reservoir=clay_res,
        daily_rain=dry_spell_rain,
        daily_tmax=dry_spell_tmax,
        daily_tmin=dry_spell_tmin,
        latitude_deg=6.5,
        start_doy=90
    )

    # Sandy soil must dry out faster and have more wilting days than deep clay soil
    assert eval_sandy["min_soil_moisture_pct"] <= eval_clay["min_soil_moisture_pct"]
    assert eval_sandy["max_consecutive_wilting_days"] >= eval_clay["max_consecutive_wilting_days"]
    assert eval_sandy["is_false_start_risk"] is True

def test_monotonicity_rain_and_onset_date():
    """Verify Monotonicity: Higher rainfall leads to earlier or equal sowing onset date."""
    repo = SpatialRepository()
    v = repo.get_village("TG_MAR_ZIO_01")
    soil = repo.get_soil_for_village(v.village_id)
    detector = SeasonDetector()

    # Moderate rain (15mm over 3 days) -> Below 20mm threshold -> ATTENDRE
    w_moderate = WeatherData(
        village_id=v.village_id,
        timestamp=date(2026, 4, 5),
        rain_last_3days_mm=15.0,
        rain_last_7days_mm=18.0,
        rain_forecast_7days_mm=20.0,
        daily_forecast_rain=[4.0, 5.0, 3.0, 0.0, 2.0, 4.0, 2.0],
        daily_forecast_tmax=[32.0] * 7,
        daily_forecast_tmin=[23.0] * 7,
        dry_spell_forecast_max_days=2,
        source="TestMock"
    )
    res_mod = detector.evaluate_onset(v, soil, w_moderate, current_date=date(2026, 4, 5))
    assert res_mod.alert_status == AlertStatus.ATTENDRE

    # Abundant rain (30mm over 3 days) -> Reaches threshold -> SEMER
    w_abundant = WeatherData(
        village_id=v.village_id,
        timestamp=date(2026, 4, 5),
        rain_last_3days_mm=30.0,
        rain_last_7days_mm=35.0,
        rain_forecast_7days_mm=25.0,
        daily_forecast_rain=[8.0, 6.0, 4.0, 0.0, 3.0, 5.0, 3.0] + [2.0]*14,
        daily_forecast_tmax=[31.0] * 21,
        daily_forecast_tmin=[22.5] * 21,
        dry_spell_forecast_max_days=2,
        source="TestMock"
    )
    res_abun = detector.evaluate_onset(v, soil, w_abundant, current_date=date(2026, 4, 5))
    assert res_abun.alert_status == AlertStatus.SEMER

def test_variety_sowing_window():
    """Verify sowing window respects crop cycle length and cessation of rains."""
    repo = SpatialRepository()
    village = repo.get_village("TG_SAV_TON_01") # Savanes, unimodal, short season
    soil = repo.get_soil_for_village(village.village_id)

    # Extra-early maize (80-85 days: TZEE-W-SR) vs Late sorghum (120 days: Sorvato-28)
    var_maize = next(v for v in repo.list_varieties_for_crop(CropType.MAIS) if "TZEE" in v.variety_name)
    var_sorgho = next(v for v in repo.list_varieties_for_crop(CropType.SORGHO) if "Sorvato" in v.variety_name or v.cycle_days_nominal >= 110)

    win_maize = calculate_sowing_window(village, var_maize, current_soil=soil, reference_date=date(2026, 5, 20))
    win_sorgho = calculate_sowing_window(village, var_sorgho, current_soil=soil, reference_date=date(2026, 5, 20))

    # Both windows must start after Savanes floor date (May 20)
    assert win_maize.window_start >= "2026-05-20"
    assert win_sorgho.window_start >= "2026-05-20"

    # Because sorghum has a longer cycle (120 days vs 85 days), its latest safe sowing date MUST be earlier than maize!
    # Otherwise sorghum will run out of water before mid-October cessation
    assert win_sorgho.window_end <= win_maize.window_end
    assert win_maize.cycle_days < win_sorgho.cycle_days

def test_api_water_balance_and_sowing_window_endpoints():
    """Verify REST API handlers for water balance and sowing window."""
    # Water balance endpoint
    wb_data = get_water_balance(village_id="TG_MAR_ZIO_01")
    assert wb_data["village_id"] == "TG_MAR_ZIO_01"
    assert wb_data["taw_mm"] > 50.0
    assert wb_data["daily_et0_mm"] > 2.0
    assert "soil_moisture_pct" in wb_data

    # Sowing window endpoint
    win_data = get_sowing_window(village_id="TG_SAV_TON_01", crop="mais")
    assert win_data["village_id"] == "TG_SAV_TON_01"
    assert win_data["crop_type"] == CropType.MAIS
    assert "window_start" in win_data
    assert "window_end" in win_data
    assert "best_sowing_date" in win_data
    assert win_data["water_satisfaction_index_pct"] > 50.0
