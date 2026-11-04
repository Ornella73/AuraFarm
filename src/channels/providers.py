"""ChannelProvider concrete implementations: Mock provider and Twilio/Telecom provider."""
from typing import List, Optional, Dict, Any
from src.core.config import settings
from src.core.models import Language
from src.channels.base import ChannelProvider, UssdResponse
from src.channels.ussd_engine import UssdSessionEngine

class MockChannelProvider(ChannelProvider):
    """Mock provider recording all SMS, Voice, and USSD interactions in memory for tests & local demo."""

    def __init__(self, ussd_engine: Optional[UssdSessionEngine] = None):
        self.ussd_engine = ussd_engine or UssdSessionEngine()
        self.sent_sms: List[Dict[str, Any]] = []
        self.placed_calls: List[Dict[str, Any]] = []

    def send_sms(self, to_phone: str, text: str) -> bool:
        self.sent_sms.append({
            "to": to_phone,
            "text": text,
            "status": "DELIVERED_MOCK"
        })
        return True

    def make_voice_call(
        self,
        to_phone: str,
        audio_sequence: List[str],
        language: Language,
        callback_webhook_url: Optional[str] = None
    ) -> bool:
        self.placed_calls.append({
            "to": to_phone,
            "audio_sequence": audio_sequence,
            "language": language.value,
            "status": "INITIATED_MOCK"
        })
        return True

    def handle_ussd_session(
        self,
        session_id: str,
        phone_number: str,
        user_input: str
    ) -> UssdResponse:
        return self.ussd_engine.process_request(session_id, phone_number, user_input)

class TwilioChannelProvider(ChannelProvider):
    """Twilio provider for outbound voice calls and SMS to Togolese mobile networks."""

    def __init__(self, ussd_engine: Optional[UssdSessionEngine] = None):
        self.ussd_engine = ussd_engine or UssdSessionEngine()
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_number = settings.TWILIO_CALLER_ID

    def send_sms(self, to_phone: str, text: str) -> bool:
        if not (self.account_sid and self.auth_token):
            return False
        import requests
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        data = {
            "From": self.from_number,
            "To": to_phone,
            "Body": text
        }
        resp = requests.post(url, data=data, auth=(self.account_sid, self.auth_token), timeout=5)
        return resp.status_code in (200, 201)

    def make_voice_call(
        self,
        to_phone: str,
        audio_sequence: List[str],
        language: Language,
        callback_webhook_url: Optional[str] = None
    ) -> bool:
        if not (self.account_sid and self.auth_token):
            return False
        import requests
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Calls.json"
        data = {
            "From": self.from_number,
            "To": to_phone,
            "Url": callback_webhook_url or "http://localhost:8000/api/ivr/webhook"
        }
        resp = requests.post(url, data=data, auth=(self.account_sid, self.auth_token), timeout=5)
        return resp.status_code in (200, 201)

    def handle_ussd_session(
        self,
        session_id: str,
        phone_number: str,
        user_input: str
    ) -> UssdResponse:
        return self.ussd_engine.process_request(session_id, phone_number, user_input)

