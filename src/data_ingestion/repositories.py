"""Repositories for static datasets: Villages, Soils, and Seed Varieties in Togo."""
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional
from src.core.config import settings
from src.core.models import Village, SoilProfile, Variety, CropType, Language, RegimePluvio

class SpatialRepository:
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.DATA_DIR
        self._villages: Dict[str, Village] = {}
        self._soils: Dict[str, SoilProfile] = {}
        self._varieties: Dict[str, Variety] = {}
        self._load_all()

    def _load_all(self):
        self._load_soils()
        self._load_villages()
        self._load_varieties()

    def _load_soils(self):
        soil_file = self.data_dir / "soil_profiles.json"
        if not soil_file.exists():
            return
        with open(soil_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for k, v in data.items():
                self._soils[k] = SoilProfile(**v)

    def _load_villages(self):
        village_file = self.data_dir / "villages_togo.csv"
        if not village_file.exists():
            return
        with open(village_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                v = Village(
                    village_id=row["village_id"],
                    village_name=row["village_name"],
                    canton=row["canton"],
                    prefecture=row["prefecture"],
                    region=row["region"],
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    regime_pluviometrique=RegimePluvio(row["regime_pluviometrique"]),
                    altitude_m=float(row["altitude_m"]),
                    sol_dominant=row["sol_dominant"],
                    culture_principale_1=CropType(row["culture_principale_1"]),
                    culture_principale_2=CropType(row["culture_principale_2"]),
                    langue_majoritaire=Language(row["langue_majoritaire"])
                )
                self._villages[v.village_id] = v

    def _load_varieties(self):
        variety_file = self.data_dir / "varieties_togo.csv"
        if not variety_file.exists():
            return
        with open(variety_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                var = Variety(
                    variety_id=row["variety_id"],
                    crop_type=CropType(row["crop_type"]),
                    variety_name=row["variety_name"],
                    cycle_days_min=int(row["cycle_days_min"]),
                    cycle_days_max=int(row["cycle_days_max"]),
                    cycle_days_nominal=int(row["cycle_days_nominal"]),
                    water_req_mm=float(row["water_req_mm"]),
                    drought_tolerance=row["drought_tolerance"],
                    photoperiod_sensitive=row["photoperiod_sensitive"].lower() == "true",
                    grain_color=row["grain_color"],
                    potential_yield_t_ha=float(row["potential_yield_t_ha"]),
                    source_organism=row["source_organism"],
                    zones_recommandees=row["zones_recommandees"],
                    disponibilite_locale_defaut=row.get("disponibilite_locale_defaut", "true").lower() == "true"
                )
                self._varieties[var.variety_id] = var

    # Village queries
    def get_village(self, village_id: str) -> Optional[Village]:
        return self._villages.get(village_id)

    def list_villages(self) -> List[Village]:
        return list(self._villages.values())

    def get_villages_by_region(self, region: str) -> List[Village]:
        return [v for v in self._villages.values() if v.region.lower() == region.lower()]

    def get_regions(self) -> List[str]:
        # Return unique regions in order: Maritime, Plateaux, Centrale, Kara, Savanes
        order = ["Maritime", "Plateaux", "Centrale", "Kara", "Savanes"]
        found = {v.region for v in self._villages.values()}
        return [r for r in order if r in found]

    def get_prefectures(self, region: str) -> List[str]:
        return sorted(list({v.prefecture for v in self._villages.values() if v.region.lower() == region.lower()}))

    def get_villages_in_prefecture(self, prefecture: str) -> List[Village]:
        return [v for v in self._villages.values() if v.prefecture.lower() == prefecture.lower()]

    # Soil queries
    def get_soil_profile(self, soil_name: str) -> Optional[SoilProfile]:
        return self._soils.get(soil_name)

    def get_soil_for_village(self, village_id: str) -> Optional[SoilProfile]:
        village = self.get_village(village_id)
        if not village:
            return None
        return self.get_soil_profile(village.sol_dominant)

    # Variety queries
    def get_variety(self, variety_id: str) -> Optional[Variety]:
        return self._varieties.get(variety_id)

    def list_varieties(self) -> List[Variety]:
        return list(self._varieties.values())

    def list_varieties_for_crop(self, crop: CropType) -> List[Variety]:
        return [v for v in self._varieties.values() if v.crop_type == crop]

    def get_varieties_for_village_and_crop(self, village: Village, crop: CropType) -> List[Variety]:
        """Return varieties suited for the village's region that are available locally."""
        candidates = []
        for v in self.list_varieties_for_crop(crop):
            # Check regional recommendation
            zones = [z.strip().lower() for z in v.zones_recommandees.split(",")]
            if village.region.lower() in zones and v.disponibilite_locale_defaut:
                candidates.append(v)
        return candidates

