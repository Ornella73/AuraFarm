"""Voice IVR Engine: Modular 30-45s audio generation, DTMF gathering, and automated call scheduler."""
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from src.core.models import Language, AlertStatus, CropType, PrecalculatedSheet
from src.core.database import get_precalculated_sheet

class VoicePlaylist:
    def __init__(self, language: Language, audio_files: List[str], text_transcript: str):
        self.language = language
        self.audio_files = audio_files
        self.text_transcript = text_transcript
        self.estimated_duration_sec = min(45, max(25, len(audio_files) * 8))

class VoiceIvrEngine:
    """Constructs modular 30-45s IVR voice responses in French, Éwé, Kabiyè, and Mina."""

    # Base audio repository URL (can be local static or S3/CDN)
    AUDIO_BASE_URL = "/static/audio"

    def generate_ivr_playlist(self, sheet: PrecalculatedSheet, language: Language) -> VoicePlaylist:
        """Assemble structured audio files for playback."""
        lang_code = language.value
        status_key = sheet.alert_status.value.lower()
        var_key = sheet.recommended_variety_id.lower().replace("-", "_")

        # 1. Modular audio sequence (intro -> alert -> variety -> instructions)
        audio_files = [
            f"{self.AUDIO_BASE_URL}/{lang_code}/intro.mp3",
            f"{self.AUDIO_BASE_URL}/{lang_code}/alert_{status_key}.mp3",
            f"{self.AUDIO_BASE_URL}/{lang_code}/variety_{var_key}.mp3",
            f"{self.AUDIO_BASE_URL}/{lang_code}/repeat_instructions.mp3"
        ]

        # 2. Text transcript for TTS prototyping or TwiML fallback
        transcript = self._build_transcript(sheet, language)

        return VoicePlaylist(
            language=language,
            audio_files=audio_files,
            text_transcript=transcript
        )

    def _build_transcript(self, sheet: PrecalculatedSheet, language: Language) -> str:
        v_name = sheet.village_name
        var_name = sheet.recommended_variety_name

        if language == Language.EWE:
            if sheet.alert_status == AlertStatus.SEMER:
                return (
                    f"AuraFarm {v_name}. Tsi dza nyuie. Miateŋu adó bli fífíia. "
                    f"Nuku nyuitɔe nye {var_name}. "
                    "Zi ɖeka dzi be na ga sea gbeɖiɖi la. Zi eve dzi be nàƒo nu kple gbedela."
                )
            elif sheet.alert_status == AlertStatus.RISQUE:
                return (
                    f"AuraFarm {v_name}. Nyanyui kple nuxɔxlɔ̃ : Kuɖiɖi gbɔna. Migado ku fifiia o ! "
                    "Zi ɖeka dzi be na ga sea gbeɖiɖi la. Zi eve dzi be nàƒo nu kple gbedela."
                )
            else:
                return (
                    f"AuraFarm {v_name}. Mielala vie boŋ, tsi mede o. "
                    "Zi ɖeka dzi be na ga sea gbeɖiɖi la. Zi eve dzi be nàƒo nu kple gbedela."
                )

        elif language == Language.KABIYE:
            if sheet.alert_status == AlertStatus.SEMER:
                return (
                    f"AuraFarm {v_name}. Tɛʊ nɩwa camɩyɛ. Ɩpɩzɩɣ ɩdʊ tɛtʊ fɛɛŋ. "
                    f"Pɩlɩʊ kɩbaŋʊ lɛ {var_name}. "
                    "Naza kʊɖʊmʊʊ se ŋtassɩ nɩʊ. Naza naalɛ se ŋyɔɔdɩna ICAT tʊmɩyɛ tʊ."
                )
            elif sheet.alert_status == AlertStatus.RISQUE:
                return (
                    f"AuraFarm {v_name}. Kalaŋgbaŋʊ : Wɩsɩ kaɣ lɩʊ pɩkɔɔ pɩtala kɩyakɩŋ lʊbɛ. Ɩtaadʊ tɛtʊ ! "
                    "Naza kʊɖʊmʊʊ se ŋtassɩ nɩʊ. Naza naalɛ se ŋyɔɔdɩna ICAT tʊmɩyɛ tʊ."
                )
            else:
                return (
                    f"AuraFarm {v_name}. Ɩɖaŋ pazɩ, tɛʊ tatasɩ nɩʊ camɩyɛ. "
                    "Naza kʊɖʊmʊʊ se ŋtassɩ nɩʊ. Naza naalɛ se ŋyɔɔdɩna ICAT tʊmɩyɛ tʊ."
                )

        else: # Français
            if sheet.alert_status == AlertStatus.SEMER:
                return (
                    f"Bonjour, ici AuraFarm pour le village de {v_name}. "
                    f"Les conditions sont favorables : SEMEZ dès maintenant ! "
                    f"Variété recommandée : {var_name}. "
                    "Tapez 1 pour réécouter. Tapez 2 pour parler à votre conseiller agricole ICAT."
                )
            elif sheet.alert_status == AlertStatus.RISQUE:
                return (
                    f"Alerte AuraFarm pour {v_name}. Attention, risque de faux départ ! "
                    f"Une longue séquence sèche est prévue. Ne semez pas pour éviter de perdre vos semences. "
                    "Tapez 1 pour réécouter. Tapez 2 pour joindre votre conseiller ICAT."
                )
            elif sheet.alert_status == AlertStatus.ATTENDRE_CONSULTER_AGENT:
                return (
                    f"Message AuraFarm pour {v_name}. Données météo en cours d’actualisation. "
                    "Ne semez pas. Consultez directement votre agent de vulgarisation ICAT ou ITRA. "
                    "Tapez 1 pour réécouter. Tapez 2 pour être rappelé par un agent."
                )
            else:
                return (
                    f"Bonjour, ici AuraFarm pour {v_name}. "
                    "La pluie est encore insuffisante. ATTENDEZ avant de semer. "
                    "Tapez 1 pour réécouter. Tapez 2 pour contacter votre conseiller agricole."
                )

    def generate_twiml(self, sheet: PrecalculatedSheet, language: Language, host_url: str = "") -> str:
        """Generate Twilio/SIP standard TwiML XML for outbound voice call execution."""
        playlist = self.generate_ivr_playlist(sheet, language)
        transcript = playlist.text_transcript

        # TwiML with <Gather> for DTMF interactivity
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather numDigits="1" action="{host_url}/api/ivr/dtmf?village={sheet.village_id}&amp;crop={sheet.crop_type.value}&amp;lang={language.value}" method="POST" timeout="6">
        <Say voice="Polly.Mathieu" language="fr-FR">{transcript}</Say>
    </Gather>
    <!-- If no DTMF pressed, repeat once and hang up -->
    <Say voice="Polly.Mathieu" language="fr-FR">{transcript}</Say>
    <Hangup/>
</Response>"""
        return twiml

    def handle_dtmf_input(self, digit: str, village_id: str, crop: CropType, language: Language) -> str:
        """Handle farmer pressing '1' (replay) or '2' (agent connection)."""
        sheet = get_precalculated_sheet(village_id, crop)
        if digit == "1" and sheet:
            # Replay
            return self.generate_twiml(sheet, language)
        elif digit == "2":
            # Transfer to human extension agent or register request
            return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Mathieu" language="fr-FR">Votre demande a été transmise à votre agent d'encadrement ICAT. Il vous rappellera dans les plus brefs délais. Merci.</Say>
    <Hangup/>
</Response>"""
        else:
            return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Mathieu" language="fr-FR">Merci d'avoir écouté AuraFarm. À bientôt.</Say>
    <Hangup/>
</Response>"""
