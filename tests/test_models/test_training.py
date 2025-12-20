"""Tests for the walk-forward training pipeline."""

import numpy as np
import pandas as pd
import pytest

from src.models.training import get_feature_cols, EXCLUDED_COLS


class TestGetFeatureCols:
    def test_excludes_metadata_columns(self):
        df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=3),
                "ticker": "TEST",
                "close": [100, 101, 102],
                "volume": [1000, 1100, 1200],
                "target": [1, 0, 1],
                "rsi_14": [50.0, 55.0, 60.0],
                "macd": [0.1, 0.2, 0.3],
            }
        )
        cols = get_feature_cols(df)
        assert "rsi_14" in cols
        assert "macd" in cols
        assert "date" not in cols
        assert "ticker" not in cols
        assert "target" not in cols
        assert "close" not in cols
        assert "volume" not in cols

    def test_returns_sorted(self):
        df = pd.DataFrame({"z_feature": [1], "a_feature": [2], "date": ["2024-01-01"]})
        cols = get_feature_cols(df)
        assert cols == sorted(cols)

    def test_empty_when_only_excluded(self):
        df = pd.DataFrame({"date": ["2024-01-01"], "ticker": ["T"], "target": [1]})
        cols = get_feature_cols(df)
        assert cols == []

    def test_picks_up_new_features_automatically(self):
        """Any column not in EXCLUDED_COLS is a feature — no hardcoding needed."""
        df = pd.DataFrame(
            {
                "date": ["2024-01-01"],
                "ticker": ["T"],
                "target": [1],
                "new_fancy_feature": [42.0],
                "another_indicator": [0.5],
            }
        )
        cols = get_feature_cols(df)
        assert "new_fancy_feature" in cols
        assert "another_indicator" in cols


class TestExcludedCols:
    def test_excluded_contains_expected_columns(self):
        expected = {"id", "date", "ticker", "open", "high", "low", "close", "volume", "target"}
        assert EXCLUDED_COLS == expected
