"""Watchdog supervising data freshness and enforcing strict agro-climatic safety guards."""
from datetime import datetime, timezone
from typing import Tuple, Optional
from src.core.config import settings
from src.core.models import AlertStatus

class FreshnessWatchdog:
    """Monitors ingestion timestamps and enforces the non-negotiable rule:
    If weather data is older than max_hours, NEVER emit SEMER;
    always emit ATTENDRE_CONSULTER_AGENT.
    """
    def __init__(self, max_hours: int = settings.DATA_FRESHNESS_MAX_HOURS):
        self.max_hours = max_hours

    def calculate_age_hours(self, timestamp: datetime, reference_time: Optional[datetime] = None) -> float:
        """Calculate difference in hours between timestamp and reference (or current UTC)."""
        ref = reference_time or datetime.now(timezone.utc)
        if timestamp.tzinfo is None:
            # Assume UTC if naive
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=timezone.utc)
        delta = ref - timestamp
        return max(0.0, delta.total_seconds() / 3600.0)

    def is_stale(self, timestamp: datetime, reference_time: Optional[datetime] = None) -> bool:
        age = self.calculate_age_hours(timestamp, reference_time)
        return age > self.max_hours

    def evaluate_safety(
        self,
        proposed_alert: AlertStatus,
        last_weather_update: datetime,
        has_recent_field_rain: bool = False,
        reference_time: Optional[datetime] = None
    ) -> Tuple[AlertStatus, bool, str]:
        """Enforce safety guard on alert status.
        
        Returns:
            (final_alert, is_stale, reason_fr)
        """
        age_hours = self.calculate_age_hours(last_weather_update, reference_time)
        stale = age_hours > self.max_hours and not has_recent_field_rain

        if stale:
            # SAFETY RULE: Overwrite SEMER with ATTENDRE_CONSULTER_AGENT
            reason = (
                f"RÈGLE DE SÉCURITÉ ACTIVE : Les données météo ont {age_hours:.1f}h de retard "
                f"(seuil limite: {self.max_hours}h). Ne prenez pas de risque de semis prématuré. "
                "Consultez immédiatement votre agent de vulgarisation ICAT/ITRA."
            )
            return AlertStatus.ATTENDRE_CONSULTER_AGENT, True, reason

        return proposed_alert, False, "Données météorologiques à jour."
