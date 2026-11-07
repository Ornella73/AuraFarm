"""Unit and integration tests for Step E2: Agro-Climatic Zone Profiles and Stochastic Weather Simulation."""
import pytest
from src.core.config import settings
from src.core.database import (
    init_db,
    get_zone_profile,
    list_zone_profiles,
    get_village_zone_mapping
)
from src.core.models import RegimePluvio
from src.data_ingestion.stochastic_weather import (
    StochasticWeatherGenerator,
    run_benchmark_simulation_across_all_zones
)
from src.api.main import (
    get_zones,
    get_zone_detail,
    simulate_seasons,
    SimulateSeasonsPayload,
    zones_overview_view
)

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_zones.db"
    monkeypatch.setattr(settings, "DB_PATH", test_db)
    init_db()

def test_zone_profiles_completeness_and_attachment():
    """Verify all 5 regions of Togo are populated with correct regimes and village attachments."""
    zones = list_zone_profiles()
    assert len(zones) == 5

    zone_map = {z.zone_id: z for z in zones}
    expected_zones = ["SAVANES", "KARA", "CENTRALE", "PLATEAUX", "MARITIME"]
    for zid in expected_zones:
        assert zid in zone_map, f"Zone {zid} missing from database"

    # Regimes and Bimodal Season 2 'a_valider' requirement
    assert zone_map["SAVANES"].regime == RegimePluvio.UNIMODAL
    assert zone_map["SAVANES"].season_2_status is None

    assert zone_map["KARA"].regime == RegimePluvio.UNIMODAL
    assert zone_map["CENTRALE"].regime == RegimePluvio.TRANSITION_UNIMODAL

    assert zone_map["PLATEAUX"].regime == RegimePluvio.BIMODAL
    assert zone_map["PLATEAUX"].season_2_earliest_sowing_date == "09-01"
    assert zone_map["PLATEAUX"].season_2_status == "a_valider"

    assert zone_map["MARITIME"].regime == RegimePluvio.BIMODAL
    assert zone_map["MARITIME"].season_2_earliest_sowing_date == "09-15"
    assert zone_map["MARITIME"].season_2_status == "a_valider"

    # Total sentinel villages attached must be 12
    all_attached_villages = []
    for z in zones:
        for v in z.sentinel_villages:
            all_attached_villages.append(v.village_id)
            assert v.taw_mm_m > 50.0, f"Unrealistic low TAW for {v.village_id}"
            assert v.depth_cm >= 70.0, f"Unrealistic low soil depth for {v.village_id}"
            assert len(v.texture) > 0

    assert len(all_attached_villages) == 12
    assert len(set(all_attached_villages)) == 12, "Duplicate sentinel village attachments"

def test_stochastic_generator_determinism():
    """Verify identical random seeds generate bit-for-bit identical weather time series."""
    z = get_zone_profile("SAVANES")
    assert z is not None

    gen1 = StochasticWeatherGenerator(z, seed=98765)
    s1 = gen1.generate_season(year=2026)

    gen2 = StochasticWeatherGenerator(z, seed=98765)
    s2 = gen2.generate_season(year=2026)

    assert s1.annual_rainfall_mm == s2.annual_rainfall_mm
    assert s1.rain_days_count == s2.rain_days_count
    assert s1.onset_date == s2.onset_date
    assert s1.has_false_start == s2.has_false_start
    assert len(s1.daily_records) == 365

    for d1, d2 in zip(s1.daily_records, s2.daily_records):
        assert d1.rainfall_mm == d2.rainfall_mm
        assert d1.tmax_c == d2.tmax_c
        assert d1.tmin_c == d2.tmin_c

def test_inter_zone_climatic_disparity():
    """Verify distinct regional climate signatures (Savanes Sahelian dry vs Plateaux wet forest)."""
    results = run_benchmark_simulation_across_all_zones(n_seasons=30, seed=42)

    sav = results["SAVANES"]
    pla = results["PLATEAUX"]
    mar = results["MARITIME"]

    # Plateaux should be significantly wetter than Maritime and Savanes
    assert pla.mean_annual_rainfall_mm > sav.mean_annual_rainfall_mm
    assert pla.mean_annual_rainfall_mm > mar.mean_annual_rainfall_mm

    # False start risk in Savanes must reflect baseline high vulnerability (>= 25%)
    assert sav.false_start_rate_pct >= 25.0

    # Onset in Plateaux (March) must be earlier than Savanes (May/June)
    assert pla.median_onset_day_of_year is not None
    assert sav.median_onset_day_of_year is not None
    assert pla.median_onset_day_of_year < sav.median_onset_day_of_year

def test_physical_laws_and_thermal_cooling():
    """Verify Tmax > Tmin on all days and cloud/rain cooling delta."""
    z = get_zone_profile("PLATEAUX")
    assert z is not None

    gen = StochasticWeatherGenerator(z, seed=123)
    season = gen.generate_season(year=2026)

    for d in season.daily_records:
        assert d.rainfall_mm >= 0.0
        assert d.tmax_c >= d.tmin_c + 1.8, f"Thermal inversion violated on {d.date}: {d.tmax_c} vs {d.tmin_c}"

    wet_tmax = [d.tmax_c for d in season.daily_records if d.is_rain_day]
    dry_tmax = [d.tmax_c for d in season.daily_records if not d.is_rain_day]

    assert len(wet_tmax) > 20
    assert len(dry_tmax) > 50

    avg_wet_tmax = sum(wet_tmax) / len(wet_tmax)
    avg_dry_tmax = sum(dry_tmax) / len(dry_tmax)

    # Rainy days must be cooler in daytime due to cloud cover
    cooling_delta = avg_dry_tmax - avg_wet_tmax
    assert cooling_delta > 1.5, f"Cooling delta too weak: {cooling_delta:.2f} °C"

def test_api_zones_endpoints():
    """Test API route functions directly without socket deadlocks."""
    zones = get_zones()
    assert len(zones) == 5

    sav = get_zone_detail("SAVANES")
    assert sav["zone_id"] == "SAVANES"
    assert len(sav["monthly_climate"]) == 12

    # Simulate seasons endpoint
    req = SimulateSeasonsPayload(zone_id="SAVANES", n_seasons=10, seed=42)
    sim_res = simulate_seasons(req)
    assert sim_res["zone_id"] == "SAVANES"
    assert sim_res["seasons_count"] == 10
    assert sim_res["mean_annual_rainfall_mm"] > 500.0

    # HTML overview view
    resp = zones_overview_view()
    assert resp.status_code == 200
    assert "text/html" in resp.media_type
    content = resp.body.decode("utf-8")
    assert "AuraFarm • Profils Agro-Climatiques Régionaux" in content
    assert "zones-container" in content
    assert "sim-tbody" in content

