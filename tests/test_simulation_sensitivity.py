"""Test suite for Step E7: Agro-climatic What-If Simulation and Sensitivity API."""
import time
import pytest
from src.core.database import init_db
from src.agro_climate.sensitivity import (
    run_perturbation_simulation,
    compute_sensitivity_tornado,
    get_dashboard_charts_data
)
from src.api.main import (
    post_simulate,
    get_sensitivity,
    get_dashboard_charts,
    SimulationPayload
)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_simulation_latency_and_response_structure():
    """Verify simulation executes within < 500ms and returns structured metrics."""
    t0 = time.perf_counter()
    res = run_perturbation_simulation(
        village_id="TG_MAR_ZIO_01",
        crop_type="mais",
        rain_factor=1.2,
        temp_delta_c=1.5,
        seed=42
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert elapsed_ms < 500, f"Simulation took {elapsed_ms:.1f}ms, expected < 500ms"

    assert "baseline" in res
    assert "perturbed" in res
    assert "delta" in res
    assert "series" in res
    assert len(res["series"]["days"]) >= 180
    assert len(res["series"]["rain_perturbed_mm"]) == len(res["series"]["days"])
    assert len(res["series"]["et0_mm"]) == len(res["series"]["days"])
    assert len(res["series"]["soil_moisture_pct"]) == len(res["series"]["days"])

def test_simulation_rainfall_monotonicity():
    """Verify that +30% rain yields higher total rainfall and reduces false start risk."""
    sim_dry = run_perturbation_simulation(village_id="TG_MAR_ZIO_01", rain_factor=0.7, seed=42)
    sim_wet = run_perturbation_simulation(village_id="TG_MAR_ZIO_01", rain_factor=1.3, seed=42)

    assert sim_wet["perturbed"]["total_rainfall_mm"] > sim_dry["perturbed"]["total_rainfall_mm"]
    assert sim_dry["perturbed"]["false_start_risk_pct"] >= sim_wet["perturbed"]["false_start_risk_pct"]

def test_simulation_temperature_increase_raises_et0():
    """Verify that +3°C temperature shift increases reference evapotranspiration."""
    sim_norm = run_perturbation_simulation(village_id="TG_PLA_HAH_04", temp_delta_c=0.0, seed=42)
    sim_hot = run_perturbation_simulation(village_id="TG_PLA_HAH_04", temp_delta_c=3.0, seed=42)

    mean_et0_norm = sum(sim_norm["series"]["et0_mm"]) / len(sim_norm["series"]["et0_mm"])
    mean_et0_hot = sum(sim_hot["series"]["et0_mm"]) / len(sim_hot["series"]["et0_mm"])
    assert mean_et0_hot > mean_et0_norm

def test_dry_spell_injection_triggers_risk():
    """Verify that injecting a 12-day dry spell post-sowing detects risk and stress."""
    sim = run_perturbation_simulation(
        village_id="TG_CEN_TCH_07",
        dry_spell_injection=12,
        dry_spell_start_day=5,
        seed=42
    )
    assert sim["perturbed"]["has_false_start"] is True
    assert sim["delta"]["stress_days"] > 0

def test_sensitivity_tornado_ranking():
    """Verify tornado analysis returns ranked factors with impact scores."""
    tornado = compute_sensitivity_tornado(village_id="TG_MAR_ZIO_01", crop_type="mais", seed=42)
    assert "tornado" in tornado
    items = tornado["tornado"]
    assert len(items) >= 5
    # Verify descending sort by impact score
    for i in range(len(items) - 1):
        assert items[i]["impact_score"] >= items[i + 1]["impact_score"]

def test_dashboard_charts_data_generator():
    """Verify chart generator supplies all 6 chart datasets."""
    charts = get_dashboard_charts_data(village_id="TG_SAV_TON_10", crop_type="sorgho")
    assert "chart_rain" in charts
    assert "chart_temp" in charts
    assert "chart_soil" in charts
    assert "chart_windows" in charts
    assert "chart_zones" in charts
    assert "chart_tornado" in charts

    # Check chart_zones covers 5 regions
    assert len(charts["chart_zones"]) == 5

def test_api_simulation_endpoints():
    """Verify FastAPI route handlers for simulation, sensitivity, and charts."""
    payload = SimulationPayload(
        village_id="TG_MAR_LAC_02",
        crop_type="mais",
        rain_factor=1.1,
        temp_delta_c=0.5
    )
    sim_res = post_simulate(payload)
    assert sim_res["village_id"] == "TG_MAR_LAC_02"
    assert "series" in sim_res

    sens_res = get_sensitivity(village_id="TG_MAR_LAC_02")
    assert "tornado" in sens_res

    charts_res = get_dashboard_charts(village_id="TG_MAR_LAC_02")
    assert "chart_rain" in charts_res
    assert "chart_temp" in charts_res

