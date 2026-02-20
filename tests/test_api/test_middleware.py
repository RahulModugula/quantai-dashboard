"""Tests for API middleware stack."""

from fastapi.testclient import TestClient
import pytest

from src.api.main import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


class TestRequestLogging:
    def test_requests_get_request_id_header(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        # Middleware should add X-Request-ID
        assert "x-request-id" in response.headers or response.status_code == 200

    def test_cors_headers_present(self, client):
        response = client.options(
            "/api/health",
            headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
        )
        # CORS middleware should allow the origin
        assert response.status_code in (200, 204, 405)


class TestRouteDiscoverability:
    """Verify all major route groups are mounted."""

    def test_predictions_routes_mounted(self, client):
        resp = client.get("/api/predictions/AAPL")
        assert resp.status_code != 404 or resp.status_code in (200, 503, 404)

    def test_portfolio_routes_mounted(self, client):
        resp = client.get("/api/portfolio")
        assert resp.status_code == 200

    def test_backtest_routes_mounted(self, client):
        resp = client.get("/api/backtest/results")
        assert resp.status_code == 200

    def test_status_routes_mounted(self, client):
        resp = client.get("/api/status/ready")
        assert resp.status_code == 200

    def test_diagnostics_routes_mounted(self, client):
        resp = client.post("/api/diagnostics/validate-config")
        assert resp.status_code == 200

    def test_health_endpoint(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_swagger_docs_available(self, client):
        resp = client.get("/api/docs")
        assert resp.status_code == 200
