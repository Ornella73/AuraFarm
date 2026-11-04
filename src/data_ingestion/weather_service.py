"""Weather data provider interfacing Open-Meteo (ECMWF/GFS), satellite products, and rain gauges."""
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional, Any
import requests
from src.core.config import settings
from src.core.models import Village, FieldRainObservation, RegimePluvio
from src.core.database import get_recent_field_observations

class WeatherData:
    def __init__(
        self,
        village_id: str,
        timestamp: datetime,
        rain_last_3days_mm: float,
        rain_last_7days_mm: float,
        rain_forecast_7days_mm: float,
        daily_forecast_rain: List[float],
        daily_forecast_tmax: List[float],
        daily_forecast_tmin: List[float],
        dry_spell_forecast_max_days: int,
        source: str,
        ground_obs_corrected: bool = False
    ):
        self.village_id = village_id
        self.timestamp = timestamp
        self.rain_last_3days_mm = rain_last_3days_mm
        self.rain_last_7days_mm = rain_last_7days_mm
        self.rain_forecast_7days_mm = rain_forecast_7days_mm
        self.daily_forecast_rain = daily_forecast_rain
        self.daily_forecast_tmax = daily_forecast_tmax
        self.daily_forecast_tmin = daily_forecast_tmin
        self.dry_spell_forecast_max_days = dry_spell_forecast_max_days
        self.source = source
        self.ground_obs_corrected = ground_obs_corrected

class WeatherService:
    # Circuit breaker: if external API fails (e.g. offline sandbox or downtime), fallback immediately
    _api_available: bool = True

    def __init__(self, timeout_sec: int = 2):
        self.timeout_sec = timeout_sec

    def get_weather_for_village(
        self,
        village: Village,
        simulated_scenario: Optional[str] = None,
        reference_date: Optional[date] = None
    ) -> WeatherData:
        """Fetch weather data for a village.
        
        Args:
            village: Target village with coordinates and climatic regime.
            simulated_scenario: Used for testing specific agro-climatic scenarios:
                - 'optimal_onset': good rains, no dry spell
                - 'false_start': initial rain > 20mm followed by > 8 dry days
                - 'drought': zero rain
                - 'excess_rain': heavy continuous downpour
            reference_date: Reference calendar date (defaults to today)
        """
        ref_date = reference_date or date.today()
        ref_dt = datetime(ref_date.year, ref_date.month, ref_date.day, 6, 0, tzinfo=timezone.utc)

        # 1. Check if an explicit scenario is requested (for unit tests / backtest)
        if simulated_scenario:
            return self._generate_scenario_weather(village, ref_dt, simulated_scenario)

        # 2. Try fetching from Open-Meteo if API is available
        if WeatherService._api_available:
            try:
                params = {
                    "latitude": village.latitude,
                    "longitude": village.longitude,
                    "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min,et0_fao_evapotranspiration",
                    "past_days": 7,
                    "forecast_days": 14,
                    "timezone": "UTC"
                }
                resp = requests.get(settings.OPEN_METEO_API_URL, params=params, timeout=self.timeout_sec)
                if resp.status_code == 200:
                    data = resp.json()
                    return self._parse_open_meteo_response(village, data, ref_dt)
                else:
                    WeatherService._api_available = False
            except Exception:
                # Network or DNS unreachable -> trip circuit breaker immediately
                WeatherService._api_available = False

        # 3. Fallback to calibrated climatology for Togo
        return self._generate_climatological_weather(village, ref_dt)

    def _parse_open_meteo_response(self, village: Village, data: Dict[str, Any], timestamp: datetime) -> WeatherData:
        daily = data.get("daily", {})
        precip = daily.get("precipitation_sum", [])
        tmax = daily.get("temperature_2m_max", [])
        tmin = daily.get("temperature_2m_min", [])
        
        # past_days=7 means index 0..6 are past, index 7 is today, index 8..20 are forecast
        past_rain = precip[:7] if len(precip) >= 7 else [0.0] * 7
        forecast_rain = precip[7:] if len(precip) >= 7 else [0.0] * 14
        
        rain_3d = sum(past_rain[-3:]) if len(past_rain) >= 3 else 0.0
        rain_7d = sum(past_rain)
        rain_fc_7d = sum(forecast_rain[:7]) if len(forecast_rain) >= 7 else sum(forecast_rain)

        # Dry spell calculation: max consecutive days with rain < 1.0 mm in forecast
        max_dry = self._calc_max_dry_spell(forecast_rain)

        # Check for local rain gauge correction
        corrected_rain_3d, corrected = self._apply_ground_gauge_correction(village.village_id, rain_3d)

        return WeatherData(
            village_id=village.village_id,
            timestamp=timestamp,
            rain_last_3days_mm=round(corrected_rain_3d, 1),
            rain_last_7days_mm=round(rain_7d, 1),
            rain_forecast_7days_mm=round(rain_fc_7d, 1),
            daily_forecast_rain=[round(r, 1) for r in forecast_rain[:14]],
            daily_forecast_tmax=tmax[7:21] if len(tmax) >= 21 else [32.0] * 14,
            daily_forecast_tmin=tmin[7:21] if len(tmin) >= 21 else [22.0] * 14,
            dry_spell_forecast_max_days=max_dry,
            source="ECMWF_OpenMeteo",
            ground_obs_corrected=corrected
        )

    def _apply_ground_gauge_correction(self, village_id: str, satellite_rain_3d: float) -> (float, bool):
        """Blend village rain gauge observations with satellite estimates."""
        recent_obs = get_recent_field_observations(village_id, limit=3)
        if not recent_obs:
            return satellite_rain_3d, False
        
        obs_sum = sum(o.rainfall_mm for o in recent_obs)
        # Weighted combination: 70% farmer rain gauge, 30% satellite
        blended = (0.7 * obs_sum) + (0.3 * satellite_rain_3d)
        return blended, True

    def _calc_max_dry_spell(self, daily_rain: List[float], dry_threshold_mm: float = 1.0) -> int:
        """Count the longest consecutive run of dry days (< dry_threshold_mm)."""
        max_run = 0
        current_run = 0
        for r in daily_rain:
            if r < dry_threshold_mm:
                current_run += 1
                if current_run > max_run:
                    max_run = current_run
            else:
                current_run = 0
        return max_run

    def _generate_climatological_weather(self, village: Village, ref_dt: datetime) -> WeatherData:
        """Calibrated climatological model based on historical averages (1991-2025) for Togo."""
        month = ref_dt.month
        day = ref_dt.day

        # South (Bimodal: Maritime, Plateaux)
        if village.regime_pluviometrique == RegimePluvio.BIMODAL:
            # Main season: mid-March to mid-July
            in_season = (month == 3 and day >= 15) or (4 <= month <= 7) or (month == 9) or (month == 10)
            if in_season:
                past_3d = 24.5
                past_7d = 48.0
                fc_7d = 38.0
                fc_rain = [8.5, 0.0, 12.0, 4.0, 0.5, 9.0, 4.0, 0.0, 11.0, 3.0, 0.0, 7.0, 5.0, 0.0]
                max_dry = 2
            else:
                past_3d = 2.0
                past_7d = 5.0
                fc_7d = 4.0
                fc_rain = [0.0] * 14
                max_dry = 14

        # Transition / Unimodal (Centrale, Kara, Savanes)
        else:
            # Single season: May to October
            in_season = (5 <= month <= 10)
            if in_season:
                past_3d = 28.0
                past_7d = 55.0
                fc_7d = 42.0
                fc_rain = [10.0, 15.0, 0.0, 8.0, 0.0, 5.0, 4.0, 0.0, 12.0, 6.0, 0.0, 9.0, 2.0, 0.0]
                max_dry = 2
            else:
                past_3d = 0.0
                past_7d = 0.0
                fc_7d = 0.0
                fc_rain = [0.0] * 14
                max_dry = 14

        corrected_3d, corrected = self._apply_ground_gauge_correction(village.village_id, past_3d)

        return WeatherData(
            village_id=village.village_id,
            timestamp=ref_dt,
            rain_last_3days_mm=corrected_3d,
            rain_last_7days_mm=past_7d,
            rain_forecast_7days_mm=fc_7d,
            daily_forecast_rain=fc_rain,
            daily_forecast_tmax=[32.5] * 14,
            daily_forecast_tmin=[22.8] * 14,
            dry_spell_forecast_max_days=max_dry,
            source="Climatologie_Calibree_Togo",
            ground_obs_corrected=corrected
        )

    def _generate_scenario_weather(self, village: Village, ref_dt: datetime, scenario: str) -> WeatherData:
        """Inject specific conditions for unit testing and backtesting."""
        if scenario == "optimal_onset":
            # 28mm rain on past 3 days, regular forecast, no dry spell > 3 days
            fc_rain = [6.0, 12.0, 0.0, 8.0, 14.0, 0.0, 7.0, 9.0, 0.0, 11.0, 5.0, 0.0, 8.0, 4.0]
            return WeatherData(
                village_id=village.village_id,
                timestamp=ref_dt,
                rain_last_3days_mm=28.4,
                rain_last_7days_mm=45.0,
                rain_forecast_7days_mm=47.0,
                daily_forecast_rain=fc_rain,
                daily_forecast_tmax=[31.0] * 14,
                daily_forecast_tmin=[22.0] * 14,
                dry_spell_forecast_max_days=2,
                source="Scenario_OptimalOnset"
            )
        elif scenario == "false_start":
            # 22mm isolated downpour, but forecast is 10 consecutive dry days (< 1mm)!
            fc_rain = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.0, 3.0, 0.0, 0.0, 0.0]
            return WeatherData(
                village_id=village.village_id,
                timestamp=ref_dt,
                rain_last_3days_mm=22.0,
                rain_last_7days_mm=22.0,
                rain_forecast_7days_mm=0.2,
                daily_forecast_rain=fc_rain,
                daily_forecast_tmax=[35.5] * 14,
                daily_forecast_tmin=[23.0] * 14,
                dry_spell_forecast_max_days=9,
                source="Scenario_FalseStart"
            )
        elif scenario == "insufficient_rain":
            # Only 8mm on past 3 days (below threshold of 20mm)
            fc_rain = [2.0, 0.0, 3.0, 0.0, 1.0, 0.0, 0.0, 4.0, 0.0, 2.0, 0.0, 0.0, 1.0, 0.0]
            return WeatherData(
                village_id=village.village_id,
                timestamp=ref_dt,
                rain_last_3days_mm=8.0,
                rain_last_7days_mm=12.0,
                rain_forecast_7days_mm=6.0,
                daily_forecast_rain=fc_rain,
                daily_forecast_tmax=[33.0] * 14,
                daily_forecast_tmin=[22.5] * 14,
                dry_spell_forecast_max_days=4,
                source="Scenario_InsufficientRain"
            )
        else: # drought or off-season
            fc_rain = [0.0] * 14
            return WeatherData(
                village_id=village.village_id,
                timestamp=ref_dt,
                rain_last_3days_mm=0.0,
                rain_last_7days_mm=0.0,
                rain_forecast_7days_mm=0.0,
                daily_forecast_rain=fc_rain,
                daily_forecast_tmax=[36.0] * 14,
                daily_forecast_tmin=[24.0] * 14,
                dry_spell_forecast_max_days=14,
                source="Scenario_Drought"
            )
