"""Webhook support for event notifications."""
import logging

logger = logging.getLogger(__name__)


class WebhookManager:
    """Manage webhooks for trading events."""

    def __init__(self):
        self.webhooks = {}

    def register_webhook(self, event: str, url: str):
        """Register webhook for an event."""
        if event not in self.webhooks:
            self.webhooks[event] = []
        self.webhooks[event].append(url)
        logger.info(f"Webhook registered for {event}: {url}")

    def trigger_webhook(self, event: str, data: dict):
        """Trigger webhooks for an event."""
        if event not in self.webhooks:
            return

        for url in self.webhooks[event]:
            try:
                # In real implementation, POST to URL
                logger.debug(f"Would POST to {url} with data: {data}")
            except Exception as e:
                logger.error(f"Webhook failed: {e}")

    def get_webhooks(self, event: str = None) -> dict:
        """Get registered webhooks."""
        if event:
            return {event: self.webhooks.get(event, [])}
        return self.webhooks
