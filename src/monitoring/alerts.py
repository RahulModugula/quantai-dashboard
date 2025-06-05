"""Alert system for monitoring important events."""
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertManager:
    """Manage system and trading alerts."""

    def __init__(self):
        self.alerts = []

    def create_alert(
        self,
        message: str,
        severity: AlertSeverity,
        category: str,
        metadata: dict = None,
    ):
        """Create a new alert."""
        alert = {
            "message": message,
            "severity": severity.value,
            "category": category,
            "metadata": metadata or {},
        }
        self.alerts.append(alert)
        logger.log(
            logging.WARNING if severity == AlertSeverity.WARNING else logging.INFO,
            f"[{severity.value}] {category}: {message}",
        )

    def get_critical_alerts(self) -> list:
        """Get all critical alerts."""
        return [a for a in self.alerts if a["severity"] == AlertSeverity.CRITICAL.value]

    def clear_alerts(self):
        """Clear all alerts."""
        self.alerts = []


# Global alert manager
_alert_manager = AlertManager()


def get_alert_manager() -> AlertManager:
    """Get global alert manager."""
    return _alert_manager
