import pytest

from src.advisor.sip import calculate_sip


def test_sip_total_invested():
    result = calculate_sip(
        monthly_amount=10_000,
        duration_years=10,
        expected_return=0.12,
        inflation_rate=0.06,
        tax_rate=0.10,
    )
    expected_invested = 10_000 * 12 * 10
    assert result["total_invested"] == pytest.approx(expected_invested, rel=0.01)


def test_sip_pretax_greater_than_invested():
    result = calculate_sip(
        monthly_amount=5_000,
        duration_years=15,
        expected_return=0.12,
        inflation_rate=0.06,
        tax_rate=0.10,
    )
    assert result["pre_tax_corpus"] > result["total_invested"]


def test_sip_posttax_less_than_pretax():
    result = calculate_sip(
        monthly_amount=10_000,
        duration_years=20,
        expected_return=0.12,
        inflation_rate=0.06,
        tax_rate=0.10,
    )
    assert result["post_tax_corpus"] <= result["pre_tax_corpus"]


def test_sip_real_value_less_than_posttax():
    result = calculate_sip(
        monthly_amount=10_000,
        duration_years=20,
        expected_return=0.12,
        inflation_rate=0.06,
        tax_rate=0.10,
    )
    assert result["inflation_adjusted_value"] < result["post_tax_corpus"]


def test_sip_zero_tax():
    result = calculate_sip(
        monthly_amount=10_000,
        duration_years=10,
        expected_return=0.12,
        inflation_rate=0.06,
        tax_rate=0.0,
    )
    assert result["post_tax_corpus"] == pytest.approx(result["pre_tax_corpus"], rel=0.001)


def test_sip_year_breakdown_length():
    years = 15
    result = calculate_sip(
        monthly_amount=10_000,
        duration_years=years,
        expected_return=0.12,
        inflation_rate=0.06,
        tax_rate=0.10,
    )
    assert len(result["year_breakdown"]) == years


def test_sip_step_up_increases_corpus():
    no_stepup = calculate_sip(10_000, 20, 0.12, 0.06, 0.10, step_up_pct=0.0)
    with_stepup = calculate_sip(10_000, 20, 0.12, 0.06, 0.10, step_up_pct=0.10)
    assert with_stepup["pre_tax_corpus"] > no_stepup["pre_tax_corpus"]


def test_sip_known_value():
    """
    Validate against a rough manually computed SIP value.
    ₹10,000/month for 1 year at 12% annual = ~126,825 (approx)
    """
    result = calculate_sip(10_000, 1, 0.12, 0.0, 0.0)
    # Should be close to FV of annuity
    assert 120_000 < result["pre_tax_corpus"] < 135_000


# --- Reverse SIP tests ---

from src.advisor.sip import reverse_sip


def test_reverse_sip_finds_monthly_amount():
    result = reverse_sip(
        target_corpus=10_000_000,
        duration_years=20,
        expected_return=0.12,
        inflation_rate=0.06,
        tax_rate=0.10,
    )
    assert result["required_monthly"] > 0
    assert result["projected_post_tax"] >= result["target_corpus"] * 0.99


def test_reverse_sip_short_duration_needs_more():
    short = reverse_sip(5_000_000, 5, 0.12, 0.06, 0.10)
    long = reverse_sip(5_000_000, 20, 0.12, 0.06, 0.10)
    assert short["required_monthly"] > long["required_monthly"]


def test_reverse_sip_includes_breakdown():
    result = reverse_sip(1_000_000, 10, 0.12, 0.06, 0.10)
    assert len(result["year_breakdown"]) == 10
