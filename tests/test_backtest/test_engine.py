"""Unit tests for the walk-forward backtest engine."""

import numpy as np
import pandas as pd
import pytest

from src.backtest.engine import WalkForwardBacktester, BacktestRun


@pytest.fixture
def sample_predictions():
    """OOS predictions for 20 trading days."""
    dates = pd.bdate_range("2024-01-02", periods=20)
    rng = np.random.default_rng(42)
    probs = rng.uniform(0.3, 0.8, size=20)
    return pd.DataFrame(
        {
            "date": dates,
            "ticker": "TEST",
            "probability_up": probs,
        }
    )


@pytest.fixture
def sample_prices():
    """Price data covering the prediction period + 1 day for next_close."""
    dates = pd.bdate_range("2024-01-02", periods=21)
    prices = [100.0]
    rng = np.random.default_rng(42)
    for _ in range(20):
        prices.append(prices[-1] * (1 + rng.normal(0.001, 0.02)))
    return pd.DataFrame(
        {
            "date": dates,
            "ticker": "TEST",
            "close": prices,
        }
    )


class TestBacktestRun:
    def test_returns_backtest_result(self, sample_predictions, sample_prices):
        bt = WalkForwardBacktester()
        result = bt.run(sample_predictions, sample_prices)
        assert isinstance(result, BacktestRun)

    def test_initial_capital_preserved_in_result(self, sample_predictions, sample_prices):
        bt = WalkForwardBacktester(initial_capital=50_000)
        result = bt.run(sample_predictions, sample_prices)
        assert result.initial_capital == 50_000

    def test_equity_curve_length(self, sample_predictions, sample_prices):
        bt = WalkForwardBacktester()
        result = bt.run(sample_predictions, sample_prices)
        # Should have one entry per overlapping date
        assert len(result.equity_curve) > 0
        assert len(result.equity_curve) <= len(sample_predictions)

    def test_equity_curve_starts_near_initial_capital(self, sample_predictions, sample_prices):
        bt = WalkForwardBacktester(initial_capital=100_000)
        result = bt.run(sample_predictions, sample_prices)
        # First equity value should be close to initial capital
        # (may differ slightly if first prediction triggers a buy)
        assert 90_000 <= result.equity_curve.iloc[0] <= 110_000

    def test_metrics_contain_required_keys(self, sample_predictions, sample_prices):
        bt = WalkForwardBacktester()
        result = bt.run(sample_predictions, sample_prices)
        required = {"total_return", "sharpe_ratio", "max_drawdown"}
        assert required.issubset(set(result.metrics.keys()))

    def test_final_value_matches_equity_curve_end(self, sample_predictions, sample_prices):
        bt = WalkForwardBacktester()
        result = bt.run(sample_predictions, sample_prices)
        assert abs(result.final_value - result.equity_curve.iloc[-1]) < 0.01


class TestTradeExecution:
    def test_buy_above_threshold(self, sample_prices):
        """High probability should trigger a buy."""
        dates = pd.bdate_range("2024-01-02", periods=5)
        preds = pd.DataFrame(
            {
                "date": dates,
                "ticker": "TEST",
                "probability_up": [0.8, 0.5, 0.5, 0.5, 0.5],
            }
        )
        bt = WalkForwardBacktester(buy_threshold=0.6, sell_threshold=0.4)
        result = bt.run(preds, sample_prices)
        buys = result.trades[result.trades["side"] == "buy"]
        assert len(buys) >= 1

    def test_sell_below_threshold(self, sample_prices):
        """Low probability should trigger a sell after holding."""
        dates = pd.bdate_range("2024-01-02", periods=5)
        preds = pd.DataFrame(
            {
                "date": dates,
                "ticker": "TEST",
                "probability_up": [0.8, 0.3, 0.5, 0.5, 0.5],
            }
        )
        bt = WalkForwardBacktester(buy_threshold=0.6, sell_threshold=0.4)
        result = bt.run(preds, sample_prices)
        sells = result.trades[result.trades["side"] == "sell"]
        assert len(sells) >= 1

    def test_no_trade_in_hold_zone(self, sample_prices):
        """Probabilities between thresholds should not trigger trades."""
        dates = pd.bdate_range("2024-01-02", periods=5)
        preds = pd.DataFrame(
            {
                "date": dates,
                "ticker": "TEST",
                "probability_up": [0.5, 0.5, 0.5, 0.5, 0.5],
            }
        )
        bt = WalkForwardBacktester(buy_threshold=0.6, sell_threshold=0.4)
        result = bt.run(preds, sample_prices)
        assert len(result.trades) == 0

    def test_commission_reduces_equity(self, sample_prices):
        """Higher commission should produce lower final equity."""
        dates = pd.bdate_range("2024-01-02", periods=5)
        preds = pd.DataFrame(
            {
                "date": dates,
                "ticker": "TEST",
                "probability_up": [0.8, 0.3, 0.8, 0.3, 0.5],
            }
        )
        bt_low = WalkForwardBacktester(commission_pct=0.0)
        bt_high = WalkForwardBacktester(commission_pct=0.05)
        r_low = bt_low.run(preds, sample_prices)
        r_high = bt_high.run(preds, sample_prices)
        assert r_low.final_value >= r_high.final_value


class TestEdgeCases:
    def test_no_overlapping_dates_raises(self):
        preds = pd.DataFrame(
            {
                "date": pd.bdate_range("2020-01-02", periods=5),
                "ticker": "TEST",
                "probability_up": [0.5] * 5,
            }
        )
        prices = pd.DataFrame(
            {
                "date": pd.bdate_range("2024-01-02", periods=5),
                "ticker": "TEST",
                "close": [100.0] * 5,
            }
        )
        bt = WalkForwardBacktester()
        with pytest.raises(ValueError, match="No overlapping dates"):
            bt.run(preds, prices)

    def test_single_prediction(self, sample_prices):
        """Should handle a single prediction without crashing."""
        preds = pd.DataFrame(
            {
                "date": [pd.Timestamp("2024-01-02")],
                "ticker": "TEST",
                "probability_up": [0.7],
            }
        )
        bt = WalkForwardBacktester()
        result = bt.run(preds, sample_prices)
        assert len(result.equity_curve) == 1
