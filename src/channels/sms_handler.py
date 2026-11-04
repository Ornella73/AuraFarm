"""SMS notification handler with GSM 7-bit vs UCS-2 length constraints."""
import unicodedata
from typing import Dict, Any, Tuple
from src.core.models import PrecalculatedSheet, Language, AlertStatus

class SmsHandler:
    """Formats ultra-short trigger SMS keeping messages within single-segment cost boundaries."""

    # Specific African letters requiring UCS-2 (max 70 chars instead of 160)
    UCS2_TRIGGER_CHARS = set("ɛɔŋɖƒɣʋɩʊ")

    def format_alert_sms(self, sheet: PrecalculatedSheet, language: Language = Language.FRANCAIS) -> Dict[str, Any]:
        """Construct SMS advice and compute GSM segments."""
        v_name = sheet.village_name
        var_name = sheet.recommended_variety_name

        if sheet.alert_status == AlertStatus.SEMER:
            # 140 chars GSM-7 safe text
            body = (
                f"AuraFarm {v_name}: SEMEZ le mais des maintenant. "
                f"Variete: {var_name}. Bipez le 90000000 pour ecouter conseil gratuit."
            )
        elif sheet.alert_status == AlertStatus.RISQUE:
            body = (
                f"AuraFarm {v_name}: ALERTE RISQUE faux depart! "
                f"Secheresse de {sheet.dry_spell_risk_days}j prevue. Ne semez pas! Bipez 90000000."
            )
        elif sheet.alert_status == AlertStatus.ATTENDRE_CONSULTER_AGENT:
            body = (
                f"AuraFarm {v_name}: Donnees meteo en cours d'actualisation. "
                "Ne semez pas, consultez agent ICAT. Bipez 90000000."
            )
        else:
            body = (
                f"AuraFarm {v_name}: Pluie insuffisante. ATTENDEZ avant de semer. "
                "Bipez le 90000000 pour rappel gratuit."
            )

        encoding, max_len, segments = self.calculate_encoding_and_segments(body)

        return {
            "text": body,
            "char_count": len(body),
            "encoding": encoding,
            "segments": segments,
            "single_sms_compliant": segments == 1
        }

    def calculate_encoding_and_segments(self, text: str) -> Tuple[str, int, int]:
        """Determine if text needs UCS-2 (70 chars) or GSM 7-bit (160 chars)."""
        has_ucs2 = any(c in self.UCS2_TRIGGER_CHARS for c in text.lower())
        if has_ucs2:
            encoding = "UCS-2"
            max_single = 70
        else:
            encoding = "GSM-7"
            max_single = 160

        length = len(text)
        segments = 1 if length <= max_single else ((length - 1) // (max_single - 7)) + 1
        return encoding, max_single, segments

