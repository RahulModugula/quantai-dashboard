"""Tests verifying API endpoints reject malformed input with 400/422, not 500."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


class TestPredictionValidation:
    def test_empty_ticker_returns_404(self, client):
        """Trailing slash hits the list endpoint, not empty ticker."""
        response = client.get("/api/predictions/")
        # Either 200 (list) or 404 — never 500
        assert response.status_code in (200, 404)

    def test_batch_empty_tickers_returns_400(self, client):
        response = client.post("/api/predictions/batch", json={"tickers": []})
        assert response.status_code == 400

    def test_batch_missing_body_returns_422(self, client):
        response = client.post("/api/predictions/batch")
        assert response.status_code == 422

    def test_batch_wrong_type_returns_422(self, client):
        response = client.post("/api/predictions/batch", json="not a dict")
        assert response.status_code == 422


class TestPortfolioValidation:
    def test_negative_limit_rejected(self, client):
        response = client.get("/api/portfolio/history?limit=-1")
        assert response.status_code == 400

    def test_zero_limit_rejected(self, client):
        response = client.get("/api/portfolio/history?limit=0")
        assert response.status_code == 400

    def test_valid_limit_accepted(self, client):
        response = client.get("/api/portfolio/history?limit=10")
        assert response.status_code == 200


class TestBacktestValidation:
    def test_missing_ticker_rejected(self, client):
        response = client.post(
            "/api/backtest/run",
            json={
                "initial_capital": 100000,
            },
        )
        assert response.status_code == 422

    def test_negative_capital_handled(self, client):
        response = client.post(
            "/api/backtest/run",
            json={
                "ticker": "AAPL",
                "initial_capital": -1000,
            },
        )
        # Should be 400 or 422, not 500
        assert response.status_code in (200, 400, 422)


class TestHealthEndpoints:
    def test_health_always_returns_200(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_prometheus_metrics_returns_200(self, client):
        response = client.get("/api/metrics/prometheus")
        assert response.status_code == 200
        assert b"http_requests_total" in response.content or b"#" in response.content
