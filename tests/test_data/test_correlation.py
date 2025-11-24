"""Tests for correlation utilities."""

import numpy as np
import pandas as pd
import pytest

from src.data.correlation import high_correlation_pairs, correlation_to_dict


@pytest.fixture
def corr_matrix():
    """Build a synthetic 3x3 correlation matrix."""
    tickers = ["AAPL", "MSFT", "GOOGL"]
    data = np.array(
        [
            [1.00, 0.85, 0.40],
            [0.85, 1.00, 0.35],
            [0.40, 0.35, 1.00],
        ]
    )
    return pd.DataFrame(data, index=tickers, columns=tickers)


def test_high_correlation_pairs_detects_above_threshold(corr_matrix):
    pairs = high_correlation_pairs(corr_matrix, threshold=0.80)
    assert len(pairs) == 1
    assert pairs[0]["ticker_a"] == "AAPL"
    assert pairs[0]["ticker_b"] == "MSFT"
    assert pairs[0]["correlation"] == 0.85


def test_high_correlation_pairs_no_pairs_above_threshold(corr_matrix):
    pairs = high_correlation_pairs(corr_matrix, threshold=0.90)
    assert pairs == []


def test_high_correlation_pairs_sorted_descending(corr_matrix):
    pairs = high_correlation_pairs(corr_matrix, threshold=0.30)
    correlations = [abs(p["correlation"]) for p in pairs]
    assert correlations == sorted(correlations, reverse=True)


def test_high_correlation_pairs_empty_matrix():
    pairs = high_correlation_pairs(pd.DataFrame(), threshold=0.80)
    assert pairs == []


def test_correlation_to_dict_structure(corr_matrix):
    result = correlation_to_dict(corr_matrix)
    assert "tickers" in result
    assert "matrix" in result
    assert result["tickers"] == ["AAPL", "MSFT", "GOOGL"]
    assert len(result["matrix"]) == 3
    assert len(result["matrix"][0]) == 3


def test_correlation_to_dict_diagonal_is_one(corr_matrix):
    result = correlation_to_dict(corr_matrix)
    for i, row in enumerate(result["matrix"]):
        assert row[i] == 1.0


def test_correlation_to_dict_empty():
    result = correlation_to_dict(pd.DataFrame())
    assert result == {"tickers": [], "matrix": []}
