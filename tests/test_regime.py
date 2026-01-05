"""Unit tests for market regime detection."""

import numpy as np
import pandas as pd
import pytest

from src.analysis.regime import MIN_BARS, RegimeDetector


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ohlcv(n: int = 300, seed: int = 42, daily_vol: float = 0.01) -> pd.DataFrame:
    """Generate a synthetic OHLCV DataFrame with a random-walk close price."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2023-01-02", periods=n, freq="B")
    returns = rng.normal(0, daily_vol, size=n)
    close = 100.0 * (1 + returns).cumprod()
    high = close * (1 + np.abs(rng.normal(0, 0.005, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.005, n)))
    open_ = close * (1 + rng.normal(0, 0.003, n))
    volume = rng.integers(1_000_000, 10_000_000, n)
    return pd.DataFrame(
        {
            "date": dates,
            "ticker": "TEST",
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


def _make_trending_up_ohlcv(n: int = 300) -> pd.DataFrame:
    """Synthetic data with a strong uptrend so 50d MA > 200d MA and price > 50d MA."""
    dates = pd.date_range("2023-01-02", periods=n, freq="B")
    # Deterministic steady uptrend
    close = np.linspace(50.0, 300.0, n)
    high = close * 1.002
    low = close * 0.998
    open_ = close * 0.999
    volume = np.full(n, 5_000_000)
    return pd.DataFrame(
        {
            "date": dates,
            "ticker": "TEST",
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestClassifyColumns:
    def test_classify_returns_regime_columns(self):
        """classify() must add regime, vol_regime, and trend_regime columns."""
        df = _make_ohlcv(n=300)
        detector = RegimeDetector()
        result = detector.classify(df)

        assert "regime" in result.columns
        assert "vol_regime" in result.columns
        assert "trend_regime" in result.columns
        assert "realized_vol" in result.columns
        # Original columns still present
        assert "close" in result.columns


class TestVolRegime:
    def test_vol_regime_high_vol_detected(self):
        """High daily volatility (>30% annualized) should produce high_vol label."""
        # daily_vol=0.025 -> annualized ~0.025 * sqrt(252) ≈ 0.397 > 0.30
        df = _make_ohlcv(n=300, daily_vol=0.025)
        detector = RegimeDetector(vol_window=20)
        result = detector.classify(df)
        non_null = result["vol_regime"].dropna()
        assert (non_null == "high_vol").any(), (
            "Expected at least some 'high_vol' rows for high daily-vol data"
        )

    def test_vol_regime_low_vol_detected(self):
        """Low daily volatility (<15% annualized) should produce low_vol label."""
        # daily_vol=0.005 -> annualized ~0.005 * sqrt(252) ≈ 0.079 < 0.15
        df = _make_ohlcv(n=300, daily_vol=0.005)
        detector = RegimeDetector(vol_window=20)
        result = detector.classify(df)
        non_null = result["vol_regime"].dropna()
        assert (non_null == "low_vol").any(), (
            "Expected at least some 'low_vol' rows for low daily-vol data"
        )


class TestTrendRegime:
    def test_trend_regime_trending_up(self):
        """Steady uptrend data should produce trending_up labels in the tail."""
        df = _make_trending_up_ohlcv(n=300)
        detector = RegimeDetector(trend_short=50, trend_long=200)
        result = detector.classify(df)
        # Check the last 50 rows — by then all MAs are well established
        tail = result.tail(50)
        assert (tail["trend_regime"] == "trending_up").all(), (
            "Expected trending_up for all tail rows in a steady uptrend"
        )


class TestCurrentRegime:
    def test_current_regime_returns_dict(self):
        """current_regime() should return a dict with the expected keys."""
        df = _make_ohlcv(n=300)
        detector = RegimeDetector()
        result = detector.current_regime(df)

        assert isinstance(result, dict)
        for key in ("date", "regime", "vol_regime", "trend_regime", "realized_vol"):
            assert key in result, f"Missing key: {key}"

        assert result["regime"] in {"bull_low_vol", "bull_high_vol", "bear", "sideways"}
        assert result["vol_regime"] in {"low_vol", "normal_vol", "high_vol"}
        assert result["trend_regime"] in {"trending_up", "trending_down", "sideways"}


class TestRegimePerformance:
    def test_regime_performance_returns_per_regime(self):
        """regime_performance() should return a dict keyed by regime labels."""
        df = _make_ohlcv(n=300)
        detector = RegimeDetector()
        classified = detector.classify(df)
        equity_curve = classified["close"]

        result = detector.regime_performance(classified, equity_curve)

        assert isinstance(result, dict)
        assert len(result) > 0

        for label, stats in result.items():
            assert "mean_daily_return" in stats
            assert "count" in stats
            assert "sharpe" in stats
            assert stats["count"] > 0
            assert isinstance(stats["mean_daily_return"], float)


class TestInsufficientHistory:
    def test_classify_raises_on_insufficient_data(self):
        """classify() must raise ValueError when fewer than MIN_BARS rows are provided."""
        df = _make_ohlcv(n=MIN_BARS - 1)
        detector = RegimeDetector()
        with pytest.raises(ValueError, match="Insufficient history"):
            detector.classify(df)
