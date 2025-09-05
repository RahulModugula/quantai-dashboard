"""WebSocket endpoint for simulated real-time price feed."""

import asyncio
import logging
import random
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()

# Seed prices for simulation
_last_prices: dict[str, float] = {
    "AAPL": 195.0,
    "MSFT": 415.0,
    "GOOGL": 175.0,
    "AMZN": 185.0,
    "SPY": 525.0,
}


def _simulate_tick(ticker: str) -> float:
    """Simulate a realistic price tick with random walk + slight mean reversion."""
    prev = _last_prices.get(ticker, 100.0)
    drift = 0.0001
    vol = 0.002
    change = drift + vol * random.gauss(0, 1)
    new_price = round(prev * (1 + change), 2)
    _last_prices[ticker] = new_price
    return new_price


async def price_feed_endpoint(websocket: WebSocket):
    """WebSocket handler for simulated real-time price feed."""
    from src.config import settings

    await manager.connect(websocket)
    logger.info(f"WebSocket client connected: {websocket.client}")

    try:
        while True:
            prices = {}
            for ticker in settings.tickers:
                # Try Redis first
                price = None
                try:
                    import redis
                    r = redis.from_url(settings.redis_url, decode_responses=True)
                    price_str = r.get(f"price:{ticker}")
                    if price_str:
                        price = float(price_str)
                except Exception:
                    pass

                prices[ticker] = price or _simulate_tick(ticker)

            payload = {
                "timestamp": datetime.now().isoformat(),
                "prices": prices,
                "disclaimer": "Simulated prices for educational purposes only.",
            }
            await websocket.send_json(payload)
            await asyncio.sleep(settings.ws_update_interval)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        manager.disconnect(websocket)
        logger.error(f"WebSocket error: {e}")
