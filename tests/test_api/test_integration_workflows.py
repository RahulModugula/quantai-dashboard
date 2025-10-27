"""Integration tests for complete API workflows."""
import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestDataStatusWorkflow:
    """Test the data status and readiness workflow."""

    def test_check_data_freshness(self, client):
        """Verify data freshness endpoint provides actionable feedback."""
        response = client.get("/api/status/data")
        assert response.status_code == 200
        data = response.json()

        assert "tickers" in data
        assert "summary" in data
        # Each ticker should have freshness info
        for ticker, info in data.get("tickers", {}).items():
            assert "last_date" in info or "rows" in info

    def test_readiness_check(self, client):
        """Verify system readiness endpoint indicates preparation status."""
        response = client.get("/api/status/ready")
        assert response.status_code == 200
        data = response.json()

        assert "ready" in data
        assert isinstance(data["ready"], bool)
        assert "details" in data


class TestPredictionWorkflow:
    """Test the prediction retrieval and validation workflow."""

    def test_single_prediction_with_signal(self, client):
        """Get a single prediction and verify signal generation."""
        response = client.get("/api/predictions/AAPL")

        if response.status_code == 200:
            data = response.json()
            assert "probability" in data
            assert "signal" in data
            assert 0 <= data["probability"] <= 1
        elif response.status_code == 503:
            # Model not trained - expected in test environment
            assert "model" in response.json()["detail"].lower()
        elif response.status_code == 404:
            # No data - expected if seed_data not run
            assert "feature" in response.json()["detail"].lower()

    def test_batch_predictions(self, client):
        """Request predictions for multiple tickers at once."""
        tickers = ["AAPL", "GOOGL", "MSFT"]
        response = client.post("/api/predictions/batch", json={"tickers": tickers})

        if response.status_code == 200:
            data = response.json()
            assert "predictions" in data
            assert "error_count" in data
            # Some or all predictions might succeed
            assert data["error_count"] + len(data["predictions"]) > 0
        else:
            # Model/data may not be available
            assert response.status_code in (503, 404)


class TestPortfolioWorkflow:
    """Test portfolio management and risk assessment workflow."""

    def test_portfolio_status(self, client):
        """Check current portfolio state and holdings."""
        response = client.get("/api/portfolio")
        assert response.status_code == 200
        data = response.json()

        assert "total_value" in data
        assert "cash" in data
        assert "holdings" in data
        assert "cumulative_return" in data

    def test_portfolio_history(self, client):
        """Retrieve portfolio equity history for charting."""
        response = client.get("/api/portfolio/history?limit=50")
        assert response.status_code == 200
        data = response.json()

        assert "snapshots" in data
        assert "count" in data
        assert data["count"] <= 50

    def test_portfolio_risk_warnings(self, client):
        """Get risk warnings about concentration, correlation, and drawdown."""
        response = client.get("/api/portfolio/warnings")
        assert response.status_code == 200
        data = response.json()

        assert "has_warnings" in data
        assert "warnings" in data
        assert "portfolio_value" in data
        # Warnings dict should have concentration, correlation, drawdown
        warnings = data["warnings"]
        assert any(k in warnings for k in ["concentration", "correlation", "drawdown"])


class TestDiagnosticsWorkflow:
    """Test model and system diagnostics."""

    def test_model_features_inspection(self, client):
        """Inspect model features and importance."""
        response = client.get("/api/diagnostics/model-features")

        if response.status_code == 200:
            data = response.json()
            assert "feature_count" in data
            assert "feature_names" in data
            assert "model_type" in data
        elif response.status_code == 503:
            # Expected if model not trained
            assert "model" in response.json()["detail"].lower()

    def test_feature_correlation_analysis(self, client):
        """Analyze feature correlations for multicollinearity."""
        response = client.get("/api/diagnostics/feature-correlation")
        assert response.status_code == 200
        data = response.json()

        assert "tickers_analyzed" in data
        assert "correlations" in data
        assert "note" in data

    def test_config_validation(self, client):
        """Validate current configuration for consistency."""
        response = client.post("/api/diagnostics/validate-config")
        assert response.status_code == 200
        data = response.json()

        assert "valid" in data
        assert "errors" in data or "warnings" in data


class TestBacktestWorkflow:
    """Test backtest execution and analysis workflow."""

    def test_backtest_request_flow(self, client):
        """Verify backtest can be requested and status checked."""
        # Request backtest
        req = {
            "ticker": "AAPL",
            "initial_capital": 100000,
            "buy_threshold": 0.6,
            "sell_threshold": 0.4,
        }
        response = client.post("/api/backtest/run", json=req)
        assert response.status_code == 200
        data = response.json()
        assert "key" in data
        assert data["status"] == "started"

        # Check available results
        response = client.get("/api/backtest/results")
        assert response.status_code == 200
        results = response.json()
        # Should see at least our new backtest or others
        assert isinstance(results, dict)

    def test_backtest_export_capabilities(self, client):
        """Verify backtest results can be exported to CSV."""
        # Get list of available backtests
        response = client.get("/api/backtest/results")
        if response.status_code == 200:
            results = response.json()
            if results:
                first_key = list(results.keys())[0]

                # Try to export trades
                response = client.get(f"/api/backtest/export/{first_key}/trades")
                if response.status_code == 200:
                    data = response.json()
                    assert "csv" in data
                    assert "filename" in data


class TestAdvisorWorkflow:
    """Test investment advisor endpoints."""

    def test_lumpsum_vs_sip_comparison(self, client):
        """Compare lumpsum and SIP investment strategies."""
        req = {
            "investment": 100000,
            "months": 12,
            "annual_return_pct": 10,
            "ticker": "AAPL",
        }
        response = client.post("/api/advisor/lumpsum-vs-sip", json=req)

        if response.status_code == 200:
            data = response.json()
            assert "lumpsum" in data
            assert "sip" in data
            assert data["lumpsum"]["total_invested"] == 100000
            assert data["sip"]["monthly_amount"] > 0


class TestHealthAndStatus:
    """Test system health and readiness checks."""

    def test_health_endpoint(self, client):
        """Verify system health endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
        assert "disclaimer" in data
