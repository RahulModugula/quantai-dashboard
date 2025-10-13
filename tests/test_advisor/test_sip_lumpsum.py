"""Tests for lumpsum_vs_sip comparison."""
import pytest

from src.advisor.sip import lumpsum_vs_sip


def test_lumpsum_vs_sip_returns_structure():
    result = lumpsum_vs_sip(
        monthly_amount=10_000.0,
        duration_years=10,
        expected_return=0.12,
    )
    assert "total_capital" in result
    assert "lumpsum" in result
    assert "sip" in result
    assert "winner" in result
    assert result["winner"] in ("lumpsum", "sip")


def test_lumpsum_vs_sip_total_capital():
    result = lumpsum_vs_sip(10_000.0, 5, 0.10)
    expected = 10_000.0 * 12 * 5
    assert result["total_capital"] == pytest.approx(expected, rel=1e-4)


def test_lumpsum_wins_long_horizon():
    """Lumpsum generally outperforms SIP over long horizons at fixed return."""
    result = lumpsum_vs_sip(5_000.0, 20, 0.12)
    assert result["winner"] == "lumpsum"
    assert result["lumpsum"]["post_tax_corpus"] > result["sip"]["post_tax_corpus"]


def test_lumpsum_vs_sip_nested_keys():
    result = lumpsum_vs_sip(5_000.0, 10, 0.10)
    for key in ("pre_tax_corpus", "post_tax_corpus", "inflation_adjusted"):
        assert key in result["lumpsum"]
        assert key in result["sip"]


def test_lumpsum_vs_sip_all_positive():
    result = lumpsum_vs_sip(2_000.0, 15, 0.08)
    assert result["lumpsum"]["post_tax_corpus"] > 0
    assert result["sip"]["post_tax_corpus"] > 0
    assert result["total_capital"] > 0
