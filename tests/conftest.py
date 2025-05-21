import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_ohlcv():
    """Generate synthetic OHLCV data for testing."""
    np.random.seed(42)
    n = 300
    dates = pd.date_range("2023-01-02", periods=n, freq="B")

    close = 100 * (1 + np.random.randn(n) * 0.01).cumprod()
    high = close * (1 + np.abs(np.random.randn(n)) * 0.005)
    low = close * (1 - np.abs(np.random.randn(n)) * 0.005)
    open_ = close * (1 + np.random.randn(n) * 0.003)
    volume = np.random.randint(1_000_000, 10_000_000, n)

    return pd.DataFrame({
        "date": dates,
        "ticker": "TEST",
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


@pytest.fixture
def sample_features(sample_ohlcv):
    from src.data.features import build_feature_matrix
    return build_feature_matrix(sample_ohlcv)


@pytest.fixture
def tmp_db(tmp_path):
    """Temporary SQLite DB path for storage tests."""
    return str(tmp_path / "test.db")
