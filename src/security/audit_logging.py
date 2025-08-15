"""Audit logging for security and compliance."""
import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Audit event types."""

    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    PERMISSION_CHANGE = "permission_change"
    CONFIG_CHANGE = "config_change"
    SECURITY_EVENT = "security_event"


class AuditEvent:
    """Audit log event."""

    def __init__(
        self,
        event_type: AuditEventType,
        user_id: str,
        action: str,
        resource: str,
        status: str,
        details: Dict[str, Any] = None,
    ):
        """Initialize audit event.

        Args:
            event_type: Type of event
            user_id: User performing action
            action: Action performed
            resource: Resource affected
            status: Success or failure
            details: Additional details
        """
        self.event_type = event_type
        self.user_id = user_id
        self.action = action
        self.resource = resource
        self.status = status
        self.details = details or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "action": self.action,
            "resource": self.resource,
            "status": self.status,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class AuditLogger:
    """Audit logger for security events."""

    def __init__(self, name: str = "audit"):
        """Initialize audit logger."""
        self.logger = logging.getLogger(name)
        self.events = []
        self.max_events = 10000

    def log_event(self, event: AuditEvent):
        """Log an audit event."""
        self.events.append(event)

        # Keep events list manageable
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]

        # Log to audit logger
        self.logger.info(event.to_json())

    def log_auth_success(self, user_id: str, method: str = "password", details: Dict = None):
        """Log successful authentication."""
        event = AuditEvent(
            AuditEventType.AUTH_SUCCESS,
            user_id,
            f"Login via {method}",
            "authentication",
            "success",
            details,
        )
        self.log_event(event)

    def log_auth_failure(self, user_id: str, reason: str, details: Dict = None):
        """Log failed authentication."""
        event = AuditEvent(
            AuditEventType.AUTH_FAILURE,
            user_id or "unknown",
            "Login attempt",
            "authentication",
            "failure",
            {"reason": reason, **(details or {})},
        )
        self.log_event(event)

    def log_data_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        details: Dict = None,
    ):
        """Log data access."""
        event = AuditEvent(
            AuditEventType.DATA_ACCESS,
            user_id,
            action,
            resource,
            "success",
            details,
        )
        self.log_event(event)

    def log_data_modification(
        self,
        user_id: str,
        resource: str,
        changes: Dict,
        details: Dict = None,
    ):
        """Log data modification."""
        event = AuditEvent(
            AuditEventType.DATA_MODIFICATION,
            user_id,
            "Modify",
            resource,
            "success",
            {"changes": changes, **(details or {})},
        )
        self.log_event(event)

    def log_data_deletion(
        self,
        user_id: str,
        resource: str,
        reason: str,
        details: Dict = None,
    ):
        """Log data deletion."""
        event = AuditEvent(
            AuditEventType.DATA_DELETION,
            user_id,
            "Delete",
            resource,
            "success",
            {"reason": reason, **(details or {})},
        )
        self.log_event(event)

    def log_permission_change(
        self,
        user_id: str,
        target_user: str,
        old_permission: str,
        new_permission: str,
        details: Dict = None,
    ):
        """Log permission change."""
        event = AuditEvent(
            AuditEventType.PERMISSION_CHANGE,
            user_id,
            f"Change permission for {target_user}",
            f"user:{target_user}",
            "success",
            {
                "old_permission": old_permission,
                "new_permission": new_permission,
                **(details or {}),
            },
        )
        self.log_event(event)

    def log_security_event(
        self,
        user_id: str,
        event_description: str,
        severity: str,
        details: Dict = None,
    ):
        """Log security event."""
        event = AuditEvent(
            AuditEventType.SECURITY_EVENT,
            user_id or "system",
            event_description,
            "security",
            "success",
            {"severity": severity, **(details or {})},
        )
        self.log_event(event)

    def get_events(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> list:
        """Get audit events."""
        filtered = self.events

        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]

        if user_id:
            filtered = [e for e in filtered if e.user_id == user_id]

        # Return most recent first
        return [e.to_dict() for e in filtered[-limit:][::-1]]

    def get_user_activity(self, user_id: str, limit: int = 100) -> list:
        """Get activity for specific user."""
        events = [e for e in self.events if e.user_id == user_id]
        return [e.to_dict() for e in events[-limit:][::-1]]

    def get_summary(self) -> dict:
        """Get audit log summary."""
        by_type = {}
        by_user = {}

        for event in self.events:
            # By type
            event_type = event.event_type.value
            by_type[event_type] = by_type.get(event_type, 0) + 1

            # By user
            user_id = event.user_id
            by_user[user_id] = by_user.get(user_id, 0) + 1

        return {
            "total_events": len(self.events),
            "by_type": by_type,
            "by_user": by_user,
        }


# Global audit logger
_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """Get global audit logger."""
    return _logger


def log_audit_event(
    event_type: AuditEventType,
    user_id: str,
    action: str,
    resource: str,
    status: str = "success",
    details: Dict = None,
):
    """Log an audit event."""
    logger = get_audit_logger()
    event = AuditEvent(event_type, user_id, action, resource, status, details)
    logger.log_event(event)
