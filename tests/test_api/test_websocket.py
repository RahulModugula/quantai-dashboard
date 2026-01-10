"""Tests for WebSocket price feed endpoint."""

import pytest
from starlette.testclient import TestClient

from src.api.main import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


class TestWebSocketPriceFeed:
    def test_websocket_connects(self, client):
        """WebSocket endpoint should accept connections."""
        with client.websocket_connect("/ws/prices") as ws:
            data = ws.receive_json()
            assert "timestamp" in data
            assert "prices" in data
            assert "disclaimer" in data

    def test_websocket_returns_prices_for_configured_tickers(self, client):
        """Prices dict should contain entries for configured tickers."""
        with client.websocket_connect("/ws/prices") as ws:
            data = ws.receive_json()
            prices = data["prices"]
            # Should have at least one ticker with a numeric price
            assert len(prices) > 0
            for ticker, price in prices.items():
                assert isinstance(price, (int, float))
                assert price > 0

    def test_websocket_multiple_messages(self, client):
        """Should be able to receive multiple price updates."""
        with client.websocket_connect("/ws/prices") as ws:
            msg1 = ws.receive_json()
            msg2 = ws.receive_json()
            assert msg1["timestamp"] != msg2["timestamp"]
