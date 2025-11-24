"""Alert and notification system."""

import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    ERROR = "error"


class AlertChannel(str, Enum):
    """Alert delivery channels."""

    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH = "push"
    DASHBOARD = "dashboard"


class Alert:
    """Alert message."""

    def __init__(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.INFO,
        source: str = None,
    ):
        """Initialize alert.

        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity
            source: Alert source
        """
        self.alert_id = f"alert_{datetime.now().timestamp()}"
        self.title = title
        self.message = message
        self.severity = severity
        self.source = source
        self.created_at = datetime.now()
        self.acknowledged = False
        self.acknowledged_at = None
        self.channels_notified = []

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
        }

    def acknowledge(self):
        """Acknowledge the alert."""
        self.acknowledged = True
        self.acknowledged_at = datetime.now()


class AlertManager:
    """Manage alerts and notifications."""

    def __init__(self):
        """Initialize alert manager."""
        self.alerts: Dict[str, Alert] = {}
        self.subscriptions: Dict[str, List[Dict]] = {}
        self.handlers: Dict[AlertChannel, Callable] = {}

    def create_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.INFO,
        source: str = None,
    ) -> Alert:
        """Create an alert.

        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity
            source: Alert source

        Returns:
            Created alert
        """
        alert = Alert(title, message, severity, source)
        self.alerts[alert.alert_id] = alert

        logger.log(
            logging.WARNING if severity == AlertSeverity.WARNING else logging.ERROR,
            f"Alert created: {title}",
        )

        return alert

    def subscribe(
        self,
        user_id: str,
        channels: List[AlertChannel],
        severity_filter: Optional[AlertSeverity] = None,
    ):
        """Subscribe user to alerts.

        Args:
            user_id: User ID
            channels: Alert channels
            severity_filter: Filter by severity
        """
        self.subscriptions[user_id] = {
            "channels": channels,
            "severity_filter": severity_filter,
        }

        logger.info(f"User subscribed to alerts: {user_id}")

    def register_handler(self, channel: AlertChannel, handler: Callable):
        """Register handler for alert channel.

        Args:
            channel: Alert channel
            handler: Handler function
        """
        self.handlers[channel] = handler

        logger.info(f"Handler registered for channel: {channel.value}")

    async def notify(self, alert: Alert):
        """Notify subscribers about alert.

        Args:
            alert: Alert to notify about
        """
        for user_id, subscription in self.subscriptions.items():
            # Check severity filter
            if subscription["severity_filter"]:
                # Only notify if severity matches or is higher
                if self._get_severity_level(alert.severity) < self._get_severity_level(
                    subscription["severity_filter"]
                ):
                    continue

            # Send to subscribed channels
            for channel in subscription["channels"]:
                if channel in self.handlers:
                    try:
                        handler = self.handlers[channel]
                        await handler(user_id, alert)
                        alert.channels_notified.append(channel.value)
                    except Exception as e:
                        logger.error(f"Failed to notify via {channel.value}: {e}")

    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        acknowledged: Optional[bool] = None,
    ) -> List[Dict]:
        """Get alerts.

        Args:
            severity: Filter by severity
            acknowledged: Filter by acknowledgment status

        Returns:
            List of alerts
        """
        alerts = list(self.alerts.values())

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]

        return [
            a.to_dict()
            for a in sorted(
                alerts,
                key=lambda a: a.created_at,
                reverse=True,
            )
        ]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        if alert_id in self.alerts:
            self.alerts[alert_id].acknowledge()
            return True

        return False

    def get_unacknowledged_count(self) -> int:
        """Get count of unacknowledged alerts."""
        return sum(1 for a in self.alerts.values() if not a.acknowledged)

    def _get_severity_level(self, severity: AlertSeverity) -> int:
        """Get numeric severity level."""
        levels = {
            AlertSeverity.INFO: 0,
            AlertSeverity.WARNING: 1,
            AlertSeverity.ERROR: 2,
            AlertSeverity.CRITICAL: 3,
        }
        return levels.get(severity, 0)


# Global alert manager
_manager = AlertManager()


def get_manager() -> AlertManager:
    """Get global alert manager."""
    return _manager


def create_alert(
    title: str,
    message: str,
    severity: AlertSeverity = AlertSeverity.INFO,
) -> Alert:
    """Create alert globally."""
    manager = get_manager()
    return manager.create_alert(title, message, severity)


def notify_alert(alert: Alert):
    """Notify about alert globally."""
    manager = get_manager()
    return manager.notify(alert)
