"""
SIP (Systematic Investment Plan) Calculator

Supports:
  - Pre-tax corpus calculation
  - Post-tax corpus (LTCG on equity gains)
  - Inflation-adjusted real value
  - Annual step-up SIP
  - Year-by-year breakdown
"""


def calculate_sip(
    monthly_amount: float,
    duration_years: int,
    expected_return: float,
    inflation_rate: float = 0.06,
    tax_rate: float = 0.10,
    step_up_pct: float = 0.0,
) -> dict:
    """
    Calculate SIP corpus with pre-tax, post-tax, and inflation-adjusted values.

    Args:
        monthly_amount: Monthly SIP investment amount
        duration_years: Investment duration in years
        expected_return: Expected annualized return (e.g., 0.12 for 12%)
        inflation_rate: Annual inflation rate (e.g., 0.06 for 6%)
        tax_rate: Tax rate on gains (e.g., 0.10 for 10% LTCG)
        step_up_pct: Annual increase in SIP amount (e.g., 0.10 for 10% step-up)

    Returns:
        dict with pre_tax_corpus, post_tax_corpus, inflation_adjusted_value, year_breakdown
    """
    monthly_rate = expected_return / 12
    total_invested = 0.0
    corpus = 0.0
    year_breakdown = []
    current_monthly = monthly_amount

    for year in range(1, duration_years + 1):
        year_invested = 0.0

        for month in range(12):
            corpus = (corpus + current_monthly) * (1 + monthly_rate)
            year_invested += current_monthly

        total_invested += year_invested

        pre_tax = corpus
        gains = max(0, pre_tax - total_invested)
        tax = gains * tax_rate
        post_tax = pre_tax - tax

        # Inflation-adjusted value (real purchasing power)
        inflation_factor = (1 + inflation_rate) ** year
        real_value = post_tax / inflation_factor

        year_breakdown.append({
            "year": year,
            "monthly_sip": round(current_monthly, 2),
            "total_invested": round(total_invested, 2),
            "pre_tax_corpus": round(pre_tax, 2),
            "post_tax_corpus": round(post_tax, 2),
            "inflation_adjusted": round(real_value, 2),
            "wealth_gain_pct": round((pre_tax / total_invested - 1) * 100, 2) if total_invested > 0 else 0,
        })

        # Step-up SIP at start of each new year
        if step_up_pct > 0:
            current_monthly *= (1 + step_up_pct)

    pre_tax_corpus = corpus
    gains = max(0, pre_tax_corpus - total_invested)
    tax_amount = gains * tax_rate
    post_tax_corpus = pre_tax_corpus - tax_amount
    inflation_adjusted = post_tax_corpus / ((1 + inflation_rate) ** duration_years)

    return {
        "monthly_amount": monthly_amount,
        "duration_years": duration_years,
        "expected_return": expected_return,
        "inflation_rate": inflation_rate,
        "tax_rate": tax_rate,
        "step_up_pct": step_up_pct,
        "total_invested": round(total_invested, 2),
        "pre_tax_corpus": round(pre_tax_corpus, 2),
        "gains": round(gains, 2),
        "tax_amount": round(tax_amount, 2),
        "post_tax_corpus": round(post_tax_corpus, 2),
        "inflation_adjusted_value": round(inflation_adjusted, 2),
        "wealth_gain": round(pre_tax_corpus - total_invested, 2),
        "wealth_gain_pct": round((pre_tax_corpus / total_invested - 1) * 100, 2) if total_invested > 0 else 0,
        "effective_return_post_tax": round(
            ((post_tax_corpus / total_invested) ** (1 / duration_years) - 1) * 100, 2
        ) if total_invested > 0 else 0,
        "year_breakdown": year_breakdown,
        "disclaimer": "For educational/illustrative purposes only. Returns are not guaranteed.",
    }
