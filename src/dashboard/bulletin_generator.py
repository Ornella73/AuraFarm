"""Community Radio Bulletin Generator for extension agents and local radio broadcasts."""
from datetime import date
from typing import Dict, List, Optional, Any
from src.core.models import Language, AlertStatus, CropType, RegimePluvio
from src.core.database import get_precalculated_sheet
from src.data_ingestion.repositories import SpatialRepository

class CommunityRadioBulletinGenerator:
    """Generates weekly agricultural radio scripts in French, Éwé, Kabiyè, and Mina.
    Enables broadcasting vital climate warnings to illiterate farmers without phones.
    """

    def __init__(self, repo: Optional[SpatialRepository] = None):
        self.repo = repo or SpatialRepository()

    def generate_all_regions(self, broadcast_date: Optional[date] = None) -> Dict[str, Any]:
        """Generate bulletins across all 5 agro-ecological regions in Togo."""
        regions = ["Maritime", "Plateaux", "Centrale", "Kara", "Savanes"]
        return {
            r.lower(): self.generate_regional_bulletin(r, broadcast_date=broadcast_date)
            for r in regions
        }

    def generate_regional_bulletin(self, region: str, broadcast_date: Optional[date] = None) -> Dict[str, Any]:
        """Generate structured radio bulletin for a specific Togolese region."""
        b_date = broadcast_date or date.today()
        villages = self.repo.get_villages_by_region(region)
        if not villages:
            villages = self.repo.list_villages()[:2]

        sheets = []
        for v in villages:
            for crop in [CropType.MAIS, CropType.SORGHO]:
                sheet = get_precalculated_sheet(v.village_id, crop)
                if sheet:
                    sheets.append((v, sheet))

        # Summarize alert counts
        count_semer = sum(1 for _, s in sheets if s.alert_status == AlertStatus.SEMER)
        count_risque = sum(1 for _, s in sheets if s.alert_status == AlertStatus.RISQUE)
        count_attendre = sum(1 for _, s in sheets if s.alert_status == AlertStatus.ATTENDRE)

        # 1. French Broadcast Script
        script_fr = self._build_french_script(region, b_date, sheets, count_semer, count_risque)

        # 2. Local Language Broadcast Script (Éwé/Mina for South, Kabiyè for North)
        reg_lower = region.lower()
        if reg_lower == "maritime":
            script_local_lang = Language.MINA
            script_local = self._build_mina_script(region, b_date, sheets, count_semer, count_risque)
        elif reg_lower == "plateaux":
            script_local_lang = Language.EWE
            script_local = self._build_ewe_script(region, b_date, sheets, count_semer, count_risque)
        else:
            script_local_lang = Language.KABIYE
            script_local = self._build_kabiye_script(region, b_date, sheets, count_semer, count_risque)

        return {
            "region": region,
            "date": b_date.strftime("%d/%m/%Y"),
            "villages_covered": len(villages),
            "summary": {
                "semer": count_semer,
                "risque_faux_depart": count_risque,
                "attendre": count_attendre
            },
            "script_fr": script_fr,
            "script_local": script_local,
            "script_local_language": script_local_lang.value
        }

    def _build_french_script(self, region: str, b_date: date, sheets: list, count_semer: int, count_risque: int) -> str:
        date_str = b_date.strftime("%d %B %Y")
        lines = [
            f"=== BULLETIN RADIO COMMUNAUTAIRE AURAFARM — RÉGION {region.upper()} ===",
            f"Diffusion de la semaine du {date_str} (en partenariat avec l'ICAT et l'ITRA)",
            "",
            "Chers producteurs, chères productrices de maïs et sorgho,",
            "Voici les conseils agro-météorologiques pour vos terroirs cette semaine :"
        ]

        if count_risque > 0:
            lines.append("")
            lines.append("⚠️ ATTENTION — RISQUE DE FAUX DÉPART DE SAISON :")
            for v, s in sheets:
                if s.alert_status == AlertStatus.RISQUE:
                    lines.append(f"- Secteur de {v.village_name} ({v.prefecture}) : Ne semez pas ! Une poche de sécheresse de {s.dry_spell_risk_days} jours est prévue après les pluies.")

        if count_semer > 0:
            lines.append("")
            lines.append("🌱 ZONES FAVORABLES AU SEMIS :")
            for v, s in sheets:
                if s.alert_status == AlertStatus.SEMER:
                    lines.append(f"- Secteur de {v.village_name} ({v.prefecture}) : Vous pouvez semer le {s.crop_type.value}. Variété homologuée ITRA recommandée : {s.recommended_variety_name}.")

        lines.extend([
            "",
            "Pour écouter votre conseil vocal gratuit personnalisé sur téléphone basique :",
            "Bipez le numéro gratuit 90 00 00 00 ou composez le code USSD *384*228#.",
            "Bonne semaine et bonne campagne agricole à tous !"
        ])
        return "\n".join(lines)

    def _build_ewe_script(self, region: str, b_date: date, sheets: list, count_semer: int, count_risque: int) -> str:
        lines = [
            f"=== AURAFARM RADIO GBEFÃ — {region.upper()} NUTOME ===",
            f"Kɔsiɖa sia ƒe gbefãɖeɖe le ICAT kple ITRA ƒe dɔwɔwɔ me.",
            "",
            "Agbledela lɔlɔ̃tɔwo, mise agbledede ƒe nya vevi siawo :",
        ]
        if count_risque > 0:
            lines.append("⚠️ NUXƆXLƆ̃ VEVI — KUÐIÐI LE VAVAM :")
            for v, s in sheets:
                if s.alert_status == AlertStatus.RISQUE:
                    lines.append(f"- {v.village_name} kɔƒe me : Migado ku fifiia o ! Kuɖiɖi gbɔna le tsi la megbe.")
        if count_semer > 0:
            lines.append("🌱 TEƑE SIWO TSI DZA NYUIE :")
            for v, s in sheets:
                if s.alert_status == AlertStatus.SEMER:
                    lines.append(f"- {v.village_name} kɔƒe me : Miateŋu adó bli. Nuku nyuitɔe nye {s.recommended_variety_name}.")

        lines.extend([
            "",
            "Ne èdi be yea se gbeɖiɖi la faa le wò ka dzi la, bipe 90 00 00 00 alo zi *384*228# dzi.",
            "Mawu nayra miaƒe agbledede !"
        ])
        return "\n".join(lines)

    def _build_kabiye_script(self, region: str, b_date: date, sheets: list, count_semer: int, count_risque: int) -> str:
        lines = [
            f"=== AURAFARM RADIO ƐSƆ KƐLƐ — {region.upper()} TƐTƲ ===",
            "ICAT nɛ ITRA tɔmɩyɛ lɩzɩ tɔm kɩbaŋtʊ tɛʊ nɩʊ nɔɔ yɔɔ.",
            "",
            "Haɖaa lɔlɔ̃aa, ɩnɩɩ tɔm pɔzaa kɩyakʊ kʊnɛ :",
        ]
        if count_risque > 0:
            lines.append("⚠️ KALAŊGBAŊƲ — WƖSƖ KAƔ LƖƲ :")
            for v, s in sheets:
                if s.alert_status == AlertStatus.RISQUE:
                    lines.append(f"- {v.village_name} tɛtʊ taa : Ɩtaadʊ tɛtʊ lɔŋ ! Wɩsɩ kaɣ lɩʊ pɩtala kɩyakɩŋ {s.dry_spell_risk_days}.")
        if count_semer > 0:
            lines.append("🌱 ƖPƖZƖƔ ƖDƲ TƐTƲ :")
            for v, s in sheets:
                if s.alert_status == AlertStatus.SEMER:
                    lines.append(f"- {v.village_name} tɛtʊ taa : Ɩdʊ mɩsɩ. Pɩlɩʊ kɩbaŋʊ lɛ {s.recommended_variety_name}.")

        lines.extend([
            "",
            "Ye ŋsɔɔlaa se ŋnɩɩ tɔm ndʊ tɛŋ fɛɛŋ kaŋkaŋ kɔyɔ, yaa 90 00 00 00 yaa ŋma *384*228#.",
            "Ɛsɔ ɛwazɩ mɩ haɖɛ !"
        ])
        return "\n".join(lines)

    def _build_mina_script(self, region: str, b_date: date, sheets: list, count_semer: int, count_risque: int) -> str:
        lines = [
            f"=== AURAFARM RADIO GBEFÃ — {region.upper()} (MINA) ===",
            "Kɔsiɖa sia ƒe gbefã le ICAT kple ITRA ƒe dɔwɔwɔ dzi.",
            "",
            "Agbledolawo, mise agbledede ƒe gbe kple nuxɔxlɔ̃wo :",
        ]
        if count_risque > 0:
            lines.append("⚠️ NUXƆXLƆ̃ : Faux départ le vavãm le agblea me :")
            for v, s in sheets:
                if s.alert_status == AlertStatus.RISQUE:
                    lines.append(f"- {v.village_name} me : Migado nuku o ! Kuɖiɖi gbɔna tsi la gblɔm.")
        if count_semer > 0:
            lines.append("🌱 NYƆNA WOATEŊ ADO NUKU :")
            for v, s in sheets:
                if s.alert_status == AlertStatus.SEMER:
                    lines.append(f"- {v.village_name} me : Miado {s.crop_type.value}. Variété nyuitɔe nye {s.recommended_variety_name}.")
        lines.extend([
            "",
            "Ne èdi be yea se gbeɖiɖi faa le ka dzi la, bipe 90 00 00 00 alo zi *384*228# dzi.",
            "Mawu nayra miaƒe agble !"
        ])
        return "\n".join(lines)
