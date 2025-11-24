"""Webhook management and delivery."""

import logging
import asyncio
import json
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class WebhookEvent(str, Enum):
    """Webhook event types."""

    PREDICTION_READY = "prediction.ready"
    TRADE_EXECUTED = "trade.executed"
    ALERT_TRIGGERED = "alert.triggered"
    DATA_UPDATED = "data.updated"
    ERROR_OCCURRED = "error.occurred"


class WebhookSubscription:
    """Webhook subscription."""

    def __init__(
        self,
        subscription_id: str,
        event: str,
        url: str,
        secret: str = None,
    ):
        """Initialize webhook subscription."""
        self.subscription_id = subscription_id
        self.event = event
        self.url = url
        self.secret = secret
        self.active = True
        self.created_at = datetime.now()
        self.last_triggered = None
        self.failure_count = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "subscription_id": self.subscription_id,
            "event": self.event,
            "url": self.url,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
            "failure_count": self.failure_count,
        }


class WebhookManager:
    """Manage webhooks for trading events."""

    def __init__(self):
        """Initialize webhook manager."""
        self.webhooks = {}
        self.subscriptions: Dict[str, WebhookSubscription] = {}

    def register_webhook(self, event: str, url: str):
        """Register webhook for an event."""
        if event not in self.webhooks:
            self.webhooks[event] = []
        self.webhooks[event].append(url)
        logger.info(f"Webhook registered for {event}: {url}")

    def subscribe(
        self,
        subscription_id: str,
        event: str,
        url: str,
        secret: str = None,
    ) -> WebhookSubscription:
        """Subscribe to webhook event."""
        subscription = WebhookSubscription(subscription_id, event, url, secret)
        self.subscriptions[subscription_id] = subscription
        logger.info(f"Webhook subscribed: {subscription_id} for {event}")
        return subscription

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from webhook."""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            logger.info(f"Webhook unsubscribed: {subscription_id}")
            return True
        return False

    async def trigger_webhook(self, event: str, data: dict):
        """Trigger webhooks for an event."""
        if event not in self.webhooks:
            return

        subscriptions = [s for s in self.subscriptions.values() if s.event == event and s.active]

        tasks = []
        for url in self.webhooks.get(event, []):
            tasks.append(self._deliver_webhook(url, data))

        for subscription in subscriptions:
            tasks.append(self._deliver_subscription_webhook(subscription, data))

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _deliver_webhook(self, url: str, data: dict) -> bool:
        """Deliver webhook."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=data,
                    timeout=10.0,
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Webhook delivery error: {e}")
            return False

    async def _deliver_subscription_webhook(
        self,
        subscription: WebhookSubscription,
        data: dict,
    ) -> bool:
        """Deliver webhook to subscription."""
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Content-Type": "application/json"}

                if subscription.secret:
                    import hmac
                    import hashlib

                    signature = hmac.new(
                        subscription.secret.encode(),
                        json.dumps(data).encode(),
                        hashlib.sha256,
                    ).hexdigest()
                    headers["X-Webhook-Signature"] = signature

                response = await client.post(
                    subscription.url,
                    json=data,
                    headers=headers,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    subscription.last_triggered = datetime.now()
                    subscription.failure_count = 0
                else:
                    subscription.failure_count += 1

                return response.status_code == 200
        except Exception as e:
            subscription.failure_count += 1
            logger.error(f"Webhook delivery error: {e}")
            return False

    def get_webhooks(self, event: str = None) -> dict:
        """Get registered webhooks."""
        if event:
            return {event: self.webhooks.get(event, [])}
        return self.webhooks

    def get_subscriptions(self, event: Optional[str] = None) -> List[Dict]:
        """Get webhooks."""
        subscriptions = list(self.subscriptions.values())

        if event:
            subscriptions = [s for s in subscriptions if s.event == event]

        return [s.to_dict() for s in subscriptions]

    def get_stats(self) -> dict:
        """Get webhook statistics."""
        return {
            "total_subscriptions": len(self.subscriptions),
            "active_subscriptions": len([s for s in self.subscriptions.values() if s.active]),
            "total_webhooks": sum(len(urls) for urls in self.webhooks.values()),
            "by_event": {event: len(urls) for event, urls in self.webhooks.items()},
        }
