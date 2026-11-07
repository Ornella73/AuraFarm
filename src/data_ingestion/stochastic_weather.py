"""Stochastic Weather Generator for AuraFarm agro-climatic simulation.

Based on Richardson WGEN adapted for West African semi-arid and sub-humid regimes:
- Rainfall occurrence: First-order two-state Markov chain (P(W|D) and P(W|W))
- Rainfall intensity: Two-parameter Gamma distribution conditional on wet day
- Temperature cycle: Tmin/Tmax seasonal cycle with cloud/rain daytime cooling (Tmax drop on wet days)
- Interannual anomaly: Dry / Normal / Wet year factor
- False start injection: Early false onset (rain trigger followed by lethal 8-14 dry days)
- Deterministic reproducibility: Guaranteed identical output given identical random seed.
"""
import math
import random
from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from src.core.models import (
    ZoneProfile,
    MonthlyClimateNorm,
    DailySimulatedRecord,
    RegimePluvio
)
from src.core.database import get_zone_profile, list_zone_profiles

@dataclass
class SeasonSimulationResult:
    zone_id: str
    year: int
    annual_rainfall_mm: float
    rain_days_count: int
    mean_tmax_c: float
    mean_tmin_c: float
    onset_date: Optional[str]
    has_false_start: bool
    false_start_date: Optional[str]
    daily_records: List[DailySimulatedRecord]

@dataclass
class MultiSeasonSummary:
    zone_id: str
    zone_name: str
    seasons_count: int
    mean_annual_rainfall_mm: float
    std_annual_rainfall_mm: float
    mean_rain_days: float
    false_start_rate_pct: float
    median_onset_day_of_year: Optional[int]
    median_onset_date_str: Optional[str]
    seasons: List[SeasonSimulationResult]


class StochasticWeatherGenerator:
    """Generates synthetic daily weather series matching regional climate profiles in Togo."""

    def __init__(self, zone_profile: ZoneProfile, seed: Optional[int] = None):
        self.zone = zone_profile
        self.seed = seed
        self._rng = random.Random(seed)
        self._monthly_map: Dict[int, MonthlyClimateNorm] = {
            m.month: m for m in self.zone.monthly_climate
        }

    def reset_seed(self, seed: Optional[int] = None):
        self.seed = seed
        self._rng = random.Random(seed)

    def generate_season(
        self,
        year: int = 2026,
        force_anomaly_factor: Optional[float] = None,
        force_false_start: Optional[bool] = None
    ) -> SeasonSimulationResult:
        """Simulate a full 365-day calendar year for the zone."""
        # 1. Interannual climate anomaly factor (log-normal/truncated normal around 1.0)
        if force_anomaly_factor is not None:
            anomaly_factor = max(0.5, min(1.6, force_anomaly_factor))
        else:
            std_ratio = self.zone.annual_rainfall_std_mm / max(1.0, self.zone.annual_rainfall_mean_mm)
            anomaly_factor = max(0.65, min(1.45, self._rng.gauss(1.0, std_ratio)))

        # 2. Decide if this season suffers a false start episode
        if force_false_start is not None:
            inject_false_start = force_false_start
        else:
            inject_false_start = self._rng.random() < self.zone.false_start_probability_baseline

        start_date = date(year, 1, 1)
        is_prev_wet = False
        daily_records: List[DailySimulatedRecord] = []

        total_rain = 0.0
        rain_days = 0
        sum_tmax = 0.0
        sum_tmin = 0.0

        # Determine target false start calendar window (around zone earliest sowing date)
        earliest_month, earliest_day = map(int, self.zone.season_1_earliest_sowing_date.split("-"))
        false_start_trigger_date = date(year, earliest_month, earliest_day) - timedelta(days=self._rng.randint(2, 7))
        false_start_duration = self._rng.randint(9, 14)
        false_start_active_days_left = 0
        false_start_recorded_date: Optional[str] = None

        for day_offset in range(365):
            current_date = start_date + timedelta(days=day_offset)
            m = current_date.month
            norm = self._monthly_map.get(m, self.zone.monthly_climate[0])

            # False start trigger injection
            if inject_false_start and current_date == false_start_trigger_date and false_start_recorded_date is None:
                # Trigger an attractive initial rain (22-38 mm) that prompts sowing
                is_wet = True
                rain_amount = round(self._rng.uniform(22.0, 38.0), 1)
                false_start_active_days_left = false_start_duration
                false_start_recorded_date = current_date.isoformat()
            elif false_start_active_days_left > 0:
                # Severe dry spell immediately following the false start rain
                is_wet = False
                rain_amount = 0.0
                false_start_active_days_left -= 1
            else:
                # Standard Markov chain transition
                p_wet = (norm.p_wet_given_wet if is_prev_wet else norm.p_wet_given_dry) * anomaly_factor
                p_wet = max(0.005, min(0.95, p_wet))

                is_wet = self._rng.random() < p_wet
                if is_wet:
                    # Calibrate Gamma distribution scale to match monthly target mean intensity
                    mean_intensity_per_wet_day = norm.rain_mean_mm / max(0.1, norm.rain_days)
                    calibrated_scale = (mean_intensity_per_wet_day / max(0.1, norm.gamma_shape)) * anomaly_factor
                    raw_amount = self._rng.gammavariate(norm.gamma_shape, max(0.5, calibrated_scale))
                    rain_amount = round(max(0.2, min(140.0, raw_amount)), 1)
                else:
                    rain_amount = 0.0

            # Thermal cycle: Daytime cooling during rain (reduced solar radiation)
            if is_wet:
                tmax_offset = -self._rng.uniform(2.5, 4.2)
            else:
                tmax_offset = self._rng.uniform(0.2, 1.2)

            tmax = round(norm.tmax_mean_c + tmax_offset + self._rng.gauss(0.0, 0.8), 1)
            tmin = round(norm.tmin_mean_c + self._rng.gauss(0.0, 0.7), 1)

            # Strict physical constraint: Tmax must be at least 2°C higher than Tmin
            if tmax <= tmin + 1.8:
                tmax = round(tmin + 2.0, 1)

            # Hargreaves-Samani potential ET0 estimation
            # Ra approximated from latitude (Togo ~ 6°N - 11°N)
            lat_deg = 8.5
            rad_ext = 15.0 + 1.2 * math.sin((current_date.timetuple().tm_yday - 80) * 2 * math.pi / 365.0)
            t_mean = (tmax + tmin) / 2.0
            tdiff = max(1.0, tmax - tmin)
            et0_approx = round(0.0023 * (t_mean + 17.8) * math.sqrt(tdiff) * (rad_ext * 0.408), 2)
            et0_approx = max(1.5, min(8.5, et0_approx))

            record = DailySimulatedRecord(
                date=current_date.isoformat(),
                month=m,
                day_of_year=day_offset + 1,
                rainfall_mm=rain_amount,
                is_rain_day=is_wet,
                tmin_c=tmin,
                tmax_c=tmax,
                potential_et0_mm=et0_approx
            )
            daily_records.append(record)

            is_prev_wet = is_wet
            total_rain += rain_amount
            if is_wet:
                rain_days += 1
            sum_tmax += tmax
            sum_tmin += tmin

        # 3. Detect agronomic onset date and verified false start
        onset_date_str, detected_false_start = self._evaluate_agronomic_onset(daily_records, year)

        return SeasonSimulationResult(
            zone_id=self.zone.zone_id,
            year=year,
            annual_rainfall_mm=round(total_rain, 1),
            rain_days_count=rain_days,
            mean_tmax_c=round(sum_tmax / 365.0, 2),
            mean_tmin_c=round(sum_tmin / 365.0, 2),
            onset_date=onset_date_str,
            has_false_start=detected_false_start,
            false_start_date=false_start_recorded_date or (onset_date_str if detected_false_start else None),
            daily_records=daily_records
        )

    def _evaluate_agronomic_onset(
        self,
        records: List[DailySimulatedRecord],
        year: int
    ) -> Tuple[Optional[str], bool]:
        """Agronomic onset rule (Sivakumar / AGRHYMET standard for West Africa):
        - After zone baseline floor date:
          1. Cumulative rain over 1 to 3 days >= 20 mm.
          2. Verified onset if NO dry spell >= 8 days in the subsequent 21 days.
          3. False start if an initial trigger >= 20 mm is followed by >= 8 dry days in next 21 days.
        """
        earliest_month, earliest_day = map(int, self.zone.season_1_earliest_sowing_date.split("-"))
        floor_date = date(year, earliest_month, earliest_day)
        floor_doy = floor_date.timetuple().tm_yday

        first_false_start: bool = False
        valid_onset_date: Optional[str] = None

        n = len(records)
        for i in range(floor_doy - 1, min(n - 22, 280)):
            # Check 3-day rainfall sum
            r3 = sum(records[k].rainfall_mm for k in range(i, min(i + 3, n)))
            if r3 >= 20.0:
                # Check next 21 days for max dry spell
                post_onset = records[i + 3: min(i + 24, n)]
                max_dry = 0
                current_dry = 0
                for day in post_onset:
                    if day.rainfall_mm < 1.0:
                        current_dry += 1
                        if current_dry > max_dry:
                            max_dry = current_dry
                    else:
                        current_dry = 0

                if max_dry >= 8:
                    first_false_start = True
                    # Continue search for true onset later
                else:
                    valid_onset_date = records[i].date
                    break

        return valid_onset_date, first_false_start

    def simulate_n_seasons(self, n_seasons: int = 30) -> MultiSeasonSummary:
        """Run multi-season stochastic simulation (e.g. 30 historical/synthetic seasons)."""
        seasons: List[SeasonSimulationResult] = []
        base_year = 1995

        for idx in range(n_seasons):
            yr = base_year + idx
            season_res = self.generate_season(year=yr)
            seasons.append(season_res)

        annual_rains = [s.annual_rainfall_mm for s in seasons]
        rain_days = [s.rain_days_count for s in seasons]
        false_starts = sum(1 for s in seasons if s.has_false_start)

        mean_rain = sum(annual_rains) / max(1, len(annual_rains))
        variance = sum((r - mean_rain) ** 2 for r in annual_rains) / max(1, len(annual_rains))
        std_rain = math.sqrt(variance)

        # Onset day-of-year medians
        onset_doys: List[int] = []
        for s in seasons:
            if s.onset_date:
                dt = date.fromisoformat(s.onset_date)
                onset_doys.append(dt.timetuple().tm_yday)

        median_doy: Optional[int] = None
        median_date_str: Optional[str] = None
        if onset_doys:
            onset_doys.sort()
            median_doy = onset_doys[len(onset_doys) // 2]
            median_dt = date(2026, 1, 1) + timedelta(days=median_doy - 1)
            median_date_str = median_dt.strftime("%d %B")

        return MultiSeasonSummary(
            zone_id=self.zone.zone_id,
            zone_name=self.zone.zone_name,
            seasons_count=n_seasons,
            mean_annual_rainfall_mm=round(mean_rain, 1),
            std_annual_rainfall_mm=round(std_rain, 1),
            mean_rain_days=round(sum(rain_days) / max(1, len(rain_days)), 1),
            false_start_rate_pct=round((false_starts / max(1, len(seasons))) * 100.0, 1),
            median_onset_day_of_year=median_doy,
            median_onset_date_str=median_date_str,
            seasons=seasons
        )


def run_benchmark_simulation_across_all_zones(n_seasons: int = 30, seed: int = 42) -> Dict[str, MultiSeasonSummary]:
    """Generates 30 seasons for all 5 zones with identical master seed for fair comparison."""
    zones = list_zone_profiles()
    results = {}
    for idx, z in enumerate(zones):
        gen = StochasticWeatherGenerator(z, seed=seed + idx * 100)
        results[z.zone_id] = gen.simulate_n_seasons(n_seasons=n_seasons)
    return results
