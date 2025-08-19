"""Analytics and user event tracking."""
import logging
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class EventCategory(str, Enum):
    """Event categories."""

    USER = "user"
    SYSTEM = "system"
    FEATURE = "feature"
    ERROR = "error"
    PERFORMANCE = "performance"


class AnalyticsEvent:
    """Analytics event."""

    def __init__(
        self,
        category: EventCategory,
        action: str,
        user_id: str = None,
        properties: Dict[str, Any] = None,
    ):
        """Initialize analytics event.

        Args:
            category: Event category
            action: Action name
            user_id: User ID
            properties: Additional properties
        """
        self.category = category
        self.action = action
        self.user_id = user_id
        self.properties = properties or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "action": self.action,
            "user_id": self.user_id,
            "properties": self.properties,
            "timestamp": self.timestamp.isoformat(),
        }


class AnalyticsCollector:
    """Collect and store analytics events."""

    def __init__(self, max_events: int = 10000):
        """Initialize collector.

        Args:
            max_events: Maximum events to keep in memory
        """
        self.max_events = max_events
        self.events: List[AnalyticsEvent] = []
        self.stats = {
            "total_events": 0,
            "by_category": {},
            "by_action": {},
            "by_user": {},
        }

    def track_event(
        self,
        category: EventCategory,
        action: str,
        user_id: str = None,
        properties: Dict = None,
    ):
        """Track an event.

        Args:
            category: Event category
            action: Action name
            user_id: User ID
            properties: Additional properties
        """
        event = AnalyticsEvent(category, action, user_id, properties)
        self.events.append(event)

        # Keep list manageable
        if len(self.events) > self.max_events:
            self.events.pop(0)

        # Update stats
        self.stats["total_events"] += 1

        cat = category.value
        self.stats["by_category"][cat] = self.stats["by_category"].get(cat, 0) + 1

        self.stats["by_action"][action] = self.stats["by_action"].get(action, 0) + 1

        if user_id:
            self.stats["by_user"][user_id] = self.stats["by_user"].get(user_id, 0) + 1

        logger.debug(f"Event tracked: {category.value}/{action}")

    def get_events(
        self,
        category: Optional[EventCategory] = None,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Get events with optional filtering.

        Args:
            category: Filter by category
            action: Filter by action
            user_id: Filter by user
            limit: Maximum events to return

        Returns:
            List of events
        """
        filtered = self.events

        if category:
            filtered = [e for e in filtered if e.category == category]

        if action:
            filtered = [e for e in filtered if e.action == action]

        if user_id:
            filtered = [e for e in filtered if e.user_id == user_id]

        # Return most recent first
        return [e.to_dict() for e in filtered[-limit:][::-1]]

    def get_user_events(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Get events for a specific user."""
        return self.get_events(user_id=user_id, limit=limit)

    def get_funnel_analysis(
        self,
        actions: List[str],
        user_id: Optional[str] = None,
    ) -> Dict:
        """Analyze conversion funnel.

        Args:
            actions: Sequence of actions to track
            user_id: Optional user to analyze

        Returns:
            Funnel analysis results
        """
        filtered_events = self.events

        if user_id:
            filtered_events = [e for e in filtered_events if e.user_id == user_id]

        funnel = {}
        completed_count = 0

        for i, action in enumerate(actions):
            action_events = [e for e in filtered_events if e.action == action]
            count = len(action_events)

            completion_rate = 0
            if i > 0 and funnel.get(actions[i - 1], {}).get("count", 0) > 0:
                completion_rate = (
                    count / funnel[actions[i - 1]]["count"] * 100
                )

            funnel[action] = {
                "count": count,
                "completion_rate": round(completion_rate, 2),
            }

            if count > 0:
                completed_count = count

        return {
            "actions": actions,
            "funnel": funnel,
            "completion_rate": round(
                (completed_count / len(actions) * 100) if actions else 0, 2
            ),
        }

    def get_summary(self) -> Dict:
        """Get analytics summary."""
        return {
            "total_events": self.stats["total_events"],
            "categories": self.stats["by_category"],
            "top_actions": sorted(
                self.stats["by_action"].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10],
            "unique_users": len(self.stats["by_user"]),
            "top_users": sorted(
                self.stats["by_user"].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10],
        }

    def reset(self):
        """Reset all analytics."""
        self.events.clear()
        self.stats = {
            "total_events": 0,
            "by_category": {},
            "by_action": {},
            "by_user": {},
        }
        logger.info("Analytics reset")


# Global analytics collector
_collector = AnalyticsCollector()


def get_collector() -> AnalyticsCollector:
    """Get global analytics collector."""
    return _collector


def track_event(
    category: EventCategory,
    action: str,
    user_id: str = None,
    properties: Dict = None,
):
    """Track event globally."""
    collector = get_collector()
    collector.track_event(category, action, user_id, properties)


def track_user_action(action: str, user_id: str, properties: Dict = None):
    """Track user action."""
    track_event(EventCategory.USER, action, user_id, properties)


def track_feature_use(feature: str, user_id: str = None):
    """Track feature usage."""
    track_event(EventCategory.FEATURE, feature, user_id)
