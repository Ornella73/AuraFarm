"""Free 'Bip' (Missed Call) Callback trigger for smallholder farmers."""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from src.core.models import Language, CropType
from src.core.security import hash_phone_number, mask_phone_number
from src.core.database import get_farmer_profile, get_precalculated_sheet
from src.channels.voice_ivr import VoiceIvrEngine

class MissedCallHandler:
    """Enables farmers to trigger free automated voice advice via a zero-cost missed call ('bip')."""

    def __init__(self, ivr_engine: Optional[VoiceIvrEngine] = None):
        self.ivr_engine = ivr_engine or VoiceIvrEngine()

    def process_incoming_bip(self, caller_phone: str) -> Dict[str, Any]:
        """Process incoming flash call / bip without answering (zero cost to farmer).
        Immediately schedules an outbound IVR callback.
        """
        phone_hash = hash_phone_number(caller_phone)
        profile = get_farmer_profile(phone_hash)

        if profile:
            village_id = profile.village_id
            crop = profile.primary_crop
            language = profile.language
        else:
            # Default to sentinel village & French/Ewe if caller is not yet profiled
            village_id = "TG_MAR_ZIO_01"
            crop = CropType.MAIS
            language = Language.FRANCAIS

        sheet = get_precalculated_sheet(village_id, crop)
        if not sheet:
            return {
                "status": "QUEUED_FALLBACK",
                "phone_masked": mask_phone_number(caller_phone),
                "action": "OUTBOUND_SMS",
                "message": "AuraFarm: Données en calcul. Votre agent vous contactera."
            }

        playlist = self.ivr_engine.generate_ivr_playlist(sheet, language)

        return {
            "status": "CALLBACK_QUEUED",
            "phone_masked": mask_phone_number(caller_phone),
            "phone_hash": phone_hash,
            "village_id": village_id,
            "language": language.value,
            "crop": crop.value,
            "alert_status": sheet.alert_status.value,
            "audio_files": playlist.audio_files,
            "duration_sec": playlist.estimated_duration_sec,
            "queued_at": datetime.now(timezone.utc).isoformat()
        }
