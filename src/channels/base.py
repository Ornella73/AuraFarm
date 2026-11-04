"""Channel provider interfaces for 2G telecoms (USSD, Voice IVR, SMS)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict
from src.core.models import Language

@dataclass
class UssdResponse:
    text: str
    is_terminal: bool = False  # True: session closes (END), False: waits for input (CON)

    def validate_gsm_length(self) -> bool:
        """Check GSM 03.38 standard (max 160 characters per USSD screen)."""
        return len(self.text) <= 160

class ChannelProvider(ABC):
    """Abstract interface decoupling telecom carriers (Yas, Moov, Twilio) from core logic."""

    @abstractmethod
    def send_sms(self, to_phone: str, text: str) -> bool:
        pass

    @abstractmethod
    def make_voice_call(
        self,
        to_phone: str,
        audio_sequence: List[str],
        language: Language,
        callback_webhook_url: Optional[str] = None
    ) -> bool:
        pass

    @abstractmethod
    def handle_ussd_session(
        self,
        session_id: str,
        phone_number: str,
        user_input: str
    ) -> UssdResponse:
        pass
