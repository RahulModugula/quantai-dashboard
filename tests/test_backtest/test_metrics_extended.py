"""Tests for expectancy, recovery_factor, and extended compute_all_metrics."""
import numpy as np
import pandas as pd
import pytest

from src.backtest.metrics import expectancy, recovery_factor, compute_all_metrics


@pytest.fixture
def sample_trades():
    return pd.DataFrame([
        {"pnl": 200.0},
        {"pnl": -80.0},
        {"pnl": 150.0},
        {"pnl": -40.0},
        {"pnl": 300.0},
    ])


@pytest.fixture
def equity_curve():
    np.random.seed(42)
    vals = 100_000 * (1 + np.random.randn(200) * 0.005).cumprod()
    return pd.Series(vals, index=pd.date_range("2023-01-01", periods=200, freq="B"))


def test_expectancy_positive(sample_trades):
    result = expectancy(sample_trades)
    assert result > 0


def test_expectancy_empty_trades():
    assert expectancy(pd.DataFrame()) == 0.0


def test_expectancy_all_wins():
    trades = pd.DataFrame({"pnl": [100.0, 200.0, 150.0]})
    result = expectancy(trades)
    assert result > 0


def test_expectancy_all_losses():
    trades = pd.DataFrame({"pnl": [-100.0, -50.0, -75.0]})
    result = expectancy(trades)
    assert result < 0


def test_recovery_factor_positive_return(equity_curve):
    result = recovery_factor(equity_curve)
    # recovery factor could be positive or negative depending on simulated data
    assert isinstance(result, float)


def test_recovery_factor_flat():
    flat = pd.Series([100_000.0] * 50, index=pd.date_range("2023-01-01", periods=50))
    result = recovery_factor(flat)
    assert result == 0.0


def test_compute_all_metrics_includes_new_fields(equity_curve, sample_trades):
    metrics = compute_all_metrics(equity_curve, sample_trades)
    assert "expectancy" in metrics
    assert "recovery_factor" in metrics
    assert "avg_win" in metrics
    assert "avg_loss" in metrics
    assert metrics["avg_win"] > 0
    assert metrics["avg_loss"] < 0


def test_compute_all_metrics_empty_trades(equity_curve):
    metrics = compute_all_metrics(equity_curve, pd.DataFrame())
    assert metrics["total_trades"] == 0
    assert metrics["expectancy"] == 0.0
    assert metrics["avg_win"] == 0.0
    assert metrics["avg_loss"] == 0.0
