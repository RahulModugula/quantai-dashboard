import numpy as np
import pandas as pd
import pytest

from src.data.features import (
    build_feature_matrix,
    compute_atr,
    compute_bollinger_bands,
    compute_macd,
    compute_rsi,
    compute_rolling_stats,
    compute_volume_features,
)


@pytest.fixture
def price_series():
    np.random.seed(0)
    close = pd.Series(100 * (1 + np.random.randn(200) * 0.01).cumprod())
    return close


@pytest.fixture
def ohlcv_df(price_series):
    n = len(price_series)
    return pd.DataFrame({
        "date": pd.date_range("2023-01-01", periods=n, freq="B"),
        "ticker": "TEST",
        "open": price_series * 0.999,
        "high": price_series * 1.005,
        "low": price_series * 0.995,
        "close": price_series,
        "volume": np.random.randint(1_000_000, 5_000_000, n),
    })


def test_rsi_bounds(price_series):
    rsi = compute_rsi(price_series)
    valid = rsi.dropna()
    assert (valid >= 0).all(), "RSI must be >= 0"
    assert (valid <= 100).all(), "RSI must be <= 100"


def test_rsi_length(price_series):
    rsi = compute_rsi(price_series)
    assert len(rsi) == len(price_series)


def test_macd_columns(price_series):
    macd = compute_macd(price_series)
    assert set(macd.columns) == {"macd", "macd_signal", "macd_hist"}
    assert len(macd) == len(price_series)


def test_bollinger_bands_ordering(price_series):
    bb = compute_bollinger_bands(price_series).dropna()
    assert (bb["bb_upper"] >= bb["bb_middle"]).all()
    assert (bb["bb_middle"] >= bb["bb_lower"]).all()


def test_atr_positive(ohlcv_df):
    atr = compute_atr(ohlcv_df["high"], ohlcv_df["low"], ohlcv_df["close"])
    assert (atr.dropna() >= 0).all()


def test_rolling_stats_columns(ohlcv_df):
    result = compute_rolling_stats(ohlcv_df, windows=[5, 20])
    assert "volatility_5" in result.columns
    assert "volatility_20" in result.columns
    assert "momentum_5" in result.columns
    assert "mean_reversion_20" in result.columns


def test_volume_features_columns(ohlcv_df):
    result = compute_volume_features(ohlcv_df)
    assert "volume_ratio" in result.columns
    assert "obv" in result.columns


def test_build_feature_matrix_no_nans(ohlcv_df):
    features = build_feature_matrix(ohlcv_df)
    assert not features.isnull().any().any(), "Feature matrix should have no NaNs"


def test_build_feature_matrix_target_binary(ohlcv_df):
    features = build_feature_matrix(ohlcv_df)
    assert features["target"].isin([0, 1]).all()


def test_build_feature_matrix_shorter_than_input(ohlcv_df):
    features = build_feature_matrix(ohlcv_df)
    assert len(features) < len(ohlcv_df), "Warmup rows should be dropped"
