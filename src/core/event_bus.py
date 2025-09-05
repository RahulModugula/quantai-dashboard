"""Event bus for decoupled event handling."""
import logging
import asyncio
from typing import Callable, Dict, List, Type
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Base event class."""

    timestamp: datetime = None

    def __post_init__(self):
        """Initialize event."""
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def get_event_type(self) -> str:
        """Get event type name."""
        return self.__class__.__name__


class EventHandler:
    """Base event handler."""

    async def handle(self, event: Event):
        """Handle an event."""
        raise NotImplementedError


class EventBus:
    """Central event bus for event handling."""

    def __init__(self):
        """Initialize event bus."""
        self.handlers: Dict[Type[Event], List[Callable]] = {}
        self.event_history: List[Event] = []
        self.max_history = 1000

    def subscribe(self, event_type: Type[Event], handler: Callable):
        """Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Handler function or callable
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []

        self.handlers[event_type].append(handler)

        logger.info(
            f"Handler registered for {event_type.__name__}: {handler.__name__}"
        )

    def unsubscribe(self, event_type: Type[Event], handler: Callable):
        """Unsubscribe from an event type."""
        if event_type in self.handlers:
            self.handlers[event_type] = [
                h for h in self.handlers[event_type] if h != handler
            ]

            if not self.handlers[event_type]:
                del self.handlers[event_type]

            logger.info(
                f"Handler unregistered for {event_type.__name__}: {handler.__name__}"
            )

    async def publish(self, event: Event):
        """Publish an event.

        Args:
            event: Event to publish
        """
        event_type = type(event)

        # Store in history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)

        logger.info(f"Event published: {event_type.__name__}")

        if event_type not in self.handlers:
            return

        # Call all handlers
        tasks = []
        for handler in self.handlers[event_type]:
            if asyncio.iscoroutinefunction(handler):
                tasks.append(handler(event))
            else:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(
                        f"Error in handler {handler.__name__} for {event_type.__name__}: {e}"
                    )

        # Wait for async handlers
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def publish_sync(self, event: Event):
        """Publish event synchronously."""
        event_type = type(event)

        # Store in history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)

        logger.info(f"Event published: {event_type.__name__}")

        if event_type not in self.handlers:
            return

        # Call all handlers
        for handler in self.handlers[event_type]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    # Skip async handlers in sync publish
                    logger.warning(
                        f"Cannot call async handler {handler.__name__} "
                        f"from sync publish"
                    )
                else:
                    handler(event)
            except Exception as e:
                logger.error(
                    f"Error in handler {handler.__name__} for {event_type.__name__}: {e}"
                )

    def get_event_history(self, event_type: Type[Event] = None, limit: int = 100) -> List:
        """Get event history.

        Args:
            event_type: Filter by event type
            limit: Maximum number of events to return

        Returns:
            List of events
        """
        history = self.event_history

        if event_type:
            history = [e for e in history if isinstance(e, event_type)]

        return history[-limit:]

    def get_stats(self) -> dict:
        """Get event bus statistics."""
        return {
            "total_events": len(self.event_history),
            "total_handlers": sum(len(h) for h in self.handlers.values()),
            "subscribed_types": len(self.handlers),
            "handler_distribution": {
                event_type.__name__: len(handlers)
                for event_type, handlers in self.handlers.items()
            },
        }

    def clear_history(self):
        """Clear event history."""
        self.event_history.clear()

        logger.info("Event history cleared")


# Global event bus
_bus = EventBus()


def get_event_bus() -> EventBus:
    """Get global event bus."""
    return _bus


def subscribe(event_type: Type[Event], handler: Callable):
    """Subscribe to event globally."""
    bus = get_event_bus()
    bus.subscribe(event_type, handler)


def publish(event: Event):
    """Publish event globally (async)."""
    bus = get_event_bus()
    return bus.publish(event)


def publish_sync(event: Event):
    """Publish event globally (sync)."""
    bus = get_event_bus()
    return bus.publish_sync(event)


# Common events

class ApplicationStartedEvent(Event):
    """Fired when application starts."""

    pass


class ApplicationShutdownEvent(Event):
    """Fired when application shuts down."""

    pass


class DataModifiedEvent(Event):
    """Fired when data is modified."""

    resource: str
    action: str

    def __init__(self, resource: str, action: str):
        """Initialize event."""
        super().__init__()
        self.resource = resource
        self.action = action


class ErrorOccurredEvent(Event):
    """Fired when error occurs."""

    error: Exception
    context: str

    def __init__(self, error: Exception, context: str = ""):
        """Initialize event."""
        super().__init__()
        self.error = error
        self.context = context
