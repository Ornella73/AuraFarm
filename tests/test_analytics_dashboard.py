"""Test suite for Step E8: Dashboard Analytics Tab and Interactive What-If Visualizations."""
import pytest
from pathlib import Path
from src.dashboard.views import render_dashboard_html
from src.api.main import (
    get_dashboard_charts,
    post_simulate,
    get_sensitivity,
    SimulationPayload
)

def test_dashboard_html_contains_analytics_tab_and_charts():
    """Verify that dashboard HTML incorporates Tab 5, What-If controls, and all 6 chart containers."""
    html = render_dashboard_html()
    assert "tab-analytics" in html
    assert "btn-tab-analytics" in html
    assert "Analyse & Simulations (E8)" in html

    # Sliders
    assert "slider-rain-factor" in html
    assert "slider-temp-delta" in html
    assert "slider-taw-factor" in html
    assert "slider-delay-days" in html
    assert "slider-dry-spell" in html

    # Presets
    assert "applyPreset('normal')" in html
    assert "applyPreset('dry_year')" in html
    assert "applyPreset('warming')" in html
    assert "applyPreset('false_start')" in html

    # 6 Chart Containers
    assert "chart-rain-container" in html
    assert "chart-temp-container" in html
    assert "chart-soil-container" in html
    assert "chart-windows-container" in html
    assert "chart-zones-container" in html
    assert "chart-tornado-container" in html

    # Local chart engine script tag
    assert "/static/auracharts.js" in html

def test_local_auracharts_file_exists_and_implements_6_charts():
    """Verify offline-first constraint: static/auracharts.js exists and exports 6 chart renderers."""
    js_path = Path("static/auracharts.js")
    assert js_path.exists(), "static/auracharts.js must exist locally without external CDN"
    content = js_path.read_text(encoding="utf-8")
    assert "rainChart" in content
    assert "tempChart" in content
    assert "soilChart" in content
    assert "windowsChart" in content
    assert "zonesChart" in content
    assert "tornadoChart" in content

def test_analytics_api_integration():
    """Verify end-to-end data flow between simulation API and chart payloads."""
    # 1. Charts endpoint
    charts = get_dashboard_charts(village_id="TG_MAR_ZIO_01", crop_type="mais")
    assert len(charts["chart_rain"]["daily_rain_mm"]) > 0
    assert len(charts["chart_temp"]["tmin_c"]) > 0
    assert len(charts["chart_soil"]["soil_moisture_pct"]) > 0
    assert len(charts["chart_windows"]) > 0
    assert len(charts["chart_zones"]) == 5
    assert len(charts["chart_tornado"]) > 0

    # 2. What-If perturbation with dry year preset
    sim_dry = post_simulate(SimulationPayload(
        village_id="TG_MAR_ZIO_01",
        crop_type="mais",
        rain_factor=0.70,
        temp_delta_c=1.0
    ))
    assert sim_dry["parameters"]["rain_factor"] == 0.70
    assert sim_dry["delta"]["rainfall_delta_mm"] < 0

