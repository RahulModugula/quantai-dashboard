"""Tests for configuration validation."""

import pytest
from pydantic import ValidationError

from src.config import Settings


class TestSettingsValidation:
    def test_default_settings_valid(self):
        s = Settings()
        assert s.initial_capital > 0
        assert 0.5 <= s.buy_threshold <= 1.0
        assert 0.0 <= s.sell_threshold <= 0.5

    def test_ensemble_weights_sum_to_one(self):
        s = Settings()
        total = sum(s.ensemble_weights.values())
        assert abs(total - 1.0) < 0.01

    def test_invalid_buy_threshold_rejected(self):
        with pytest.raises(ValidationError):
            Settings(buy_threshold=0.3)  # below 0.5

    def test_invalid_sell_threshold_rejected(self):
        with pytest.raises(ValidationError):
            Settings(sell_threshold=0.8)  # above 0.5

    def test_negative_capital_rejected(self):
        with pytest.raises(ValidationError):
            Settings(initial_capital=-1000)

    def test_excessive_commission_rejected(self):
        with pytest.raises(ValidationError):
            Settings(commission_pct=0.10)  # above 5%

    def test_tickers_default_populated(self):
        s = Settings()
        assert len(s.tickers) > 0
        assert all(isinstance(t, str) for t in s.tickers)

    def test_db_path_has_default(self):
        s = Settings()
        assert s.db_path.endswith(".db")
