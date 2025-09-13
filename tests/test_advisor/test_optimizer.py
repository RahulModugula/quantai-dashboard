import numpy as np
import pandas as pd
import pytest

from src.advisor.optimizer import _build_price_df, _clean_weights


def test_clean_weights_removes_zeros():
    weights = {"AAPL": 0.5, "MSFT": 0.00001, "GOOGL": 0.4999}
    cleaned = _clean_weights(weights)
    assert "MSFT" not in cleaned
    assert cleaned["AAPL"] == 0.5
    assert cleaned["GOOGL"] == 0.4999


def test_clean_weights_sums_to_one():
    weights = {"A": 0.3, "B": 0.3, "C": 0.4}
    cleaned = _clean_weights(weights)
    assert abs(sum(cleaned.values()) - 1.0) < 0.01
