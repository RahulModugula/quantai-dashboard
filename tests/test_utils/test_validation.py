"""Tests for input validation utilities."""
import pytest

from src.utils.validation import (
    validate_ticker,
    validate_date_format,
    validate_positive_number,
    validate_percentage,
    sanitize_ticker,
    sanitize_float,
)


class TestTickerValidation:
    def test_valid_ticker(self):
        assert validate_ticker("AAPL")
        assert validate_ticker("MSFT")
        assert validate_ticker("A")

    def test_invalid_ticker(self):
        assert not validate_ticker("aapl")  # lowercase
        assert not validate_ticker("AAPL1")  # contains number
        assert not validate_ticker("")  # empty
        assert not validate_ticker("TOOLONGTICKER")  # too long


class TestDateValidation:
    def test_valid_date(self):
        assert validate_date_format("2025-10-27")
        assert validate_date_format("2024-01-01")

    def test_invalid_date(self):
        assert not validate_date_format("10-27-2025")  # wrong format
        assert not validate_date_format("2025/10/27")  # wrong separator
        assert not validate_date_format("2025-13-01")  # invalid month


class TestNumberValidation:
    def test_positive_number(self):
        assert validate_positive_number(1)
        assert validate_positive_number(1.5)
        assert validate_positive_number(0.001)

    def test_negative_number(self):
        assert not validate_positive_number(-1)
        assert not validate_positive_number(0)
        assert not validate_positive_number("1")


class TestPercentageValidation:
    def test_valid_percentage(self):
        assert validate_percentage(0)
        assert validate_percentage(0.5)
        assert validate_percentage(1)

    def test_invalid_percentage(self):
        assert not validate_percentage(-0.1)
        assert not validate_percentage(1.1)
        assert not validate_percentage("0.5")


class TestSanitization:
    def test_sanitize_ticker(self):
        assert sanitize_ticker("aapl") == "AAPL"
        assert sanitize_ticker("  AAPL  ") == "AAPL"
        assert sanitize_ticker("AaPl") == "AAPL"

    def test_sanitize_float(self):
        assert sanitize_float(1.5) == 1.5
        assert sanitize_float("2.5") == 2.5
        assert sanitize_float("invalid") == 0.0
        assert sanitize_float(None) == 0.0
