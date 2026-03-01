"""Tests for data ingestion and validation."""

import pandas as pd
import pytest

from src.data.ingestion import validate_ohlcv, DataValidationError


@pytest.fixture
def valid_ohlcv():
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-02", periods=100, freq="B"),
            "ticker": "TEST",
            "open": [100.0] * 100,
            "high": [105.0] * 100,
            "low": [95.0] * 100,
            "close": [102.0] * 100,
            "volume": [1_000_000] * 100,
        }
    )


class TestValidateOhlcv:
    def test_valid_data_passes(self, valid_ohlcv):
        result = validate_ohlcv(valid_ohlcv, "TEST")
        assert len(result) == 100

    def test_empty_df_raises(self):
        with pytest.raises(DataValidationError, match="Empty"):
            validate_ohlcv(pd.DataFrame(), "TEST")

    def test_negative_prices_raise(self, valid_ohlcv):
        valid_ohlcv.loc[0, "close"] = -10
        with pytest.raises(DataValidationError, match="Negative"):
            validate_ohlcv(valid_ohlcv, "TEST")

    def test_duplicate_dates_removed(self, valid_ohlcv):
        # Add a duplicate date
        dup = valid_ohlcv.iloc[[0]].copy()
        df = pd.concat([valid_ohlcv, dup], ignore_index=True)
        result = validate_ohlcv(df, "TEST")
        assert len(result) == 100  # duplicate removed

    def test_zero_volume_warns_but_passes(self, valid_ohlcv):
        valid_ohlcv.loc[0, "volume"] = 0
        result = validate_ohlcv(valid_ohlcv, "TEST")
        assert len(result) == 100

    def test_forward_fills_nan(self, valid_ohlcv):
        valid_ohlcv.loc[5, "close"] = None
        result = validate_ohlcv(valid_ohlcv, "TEST")
        assert result["close"].isna().sum() == 0
