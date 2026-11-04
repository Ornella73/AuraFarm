"""Security and Data Privacy utilities conforming to Togolese Law N° 2019-014."""
import hashlib
import hmac
import re
from src.core.config import settings

def normalize_phone_number(phone: str) -> str:
    """Normalize Togolese and international phone numbers.
    E.g. '+228 90 12 34 56' -> '+22890123456'
         '90123456' -> '+22890123456'
    """
    cleaned = re.sub(r"[\s\-\.\(\)]", "", str(phone).strip())
    if cleaned.startswith("00228"):
        cleaned = "+" + cleaned[2:]
    elif cleaned.startswith("228") and not cleaned.startswith("+228"):
        cleaned = "+" + cleaned
    elif not cleaned.startswith("+") and len(cleaned) == 8:
        # 8 digits local Togolese format (Yas/Moov)
        cleaned = f"+228{cleaned}"
    return cleaned

def hash_phone_number(phone: str) -> str:
    """Hash phone number with HMAC-SHA256 to ensure pseudonymization.
    Complies with Togo Law N° 2019-014 on personal data protection.
    """
    normalized = normalize_phone_number(phone)
    digest = hmac.new(
        settings.PHONE_HASH_SALT.encode("utf-8"),
        normalized.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return f"msisdn_{digest[:16]}"

def mask_phone_number(phone: str) -> str:
    """Mask phone number for safe display in UI or logs.
    E.g. '+22890123456' -> '+228 90 •• •• 56'
    """
    norm = normalize_phone_number(phone)
    if len(norm) >= 8:
        prefix = norm[:7]
        suffix = norm[-2:]
        return f"{prefix}••••{suffix}"
    return "••••••••"

