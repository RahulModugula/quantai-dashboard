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


def lumpsum_vs_sip(
    monthly_amount: float,
    duration_years: int,
    expected_return: float,
    inflation_rate: float = 0.06,
    tax_rate: float = 0.10,
) -> dict:
    """Compare lumpsum (investing full amount upfront) vs SIP for same total capital.

    The total capital committed is monthly_amount * 12 * duration_years.
    Lumpsum invests the entire amount on day 1; SIP spreads it monthly.
    """
    total_capital = monthly_amount * 12 * duration_years

    # Lumpsum calculation
    lump_corpus = total_capital * (1 + expected_return) ** duration_years
    lump_gains = max(0, lump_corpus - total_capital)
    lump_post_tax = lump_corpus - lump_gains * tax_rate
    lump_real = lump_post_tax / (1 + inflation_rate) ** duration_years

    # SIP calculation
    sip_result = calculate_sip(monthly_amount, duration_years, expected_return, inflation_rate, tax_rate)

    return {
        "total_capital": round(total_capital, 2),
        "lumpsum": {
            "pre_tax_corpus": round(lump_corpus, 2),
            "post_tax_corpus": round(lump_post_tax, 2),
            "inflation_adjusted": round(lump_real, 2),
        },
        "sip": {
            "pre_tax_corpus": sip_result["pre_tax_corpus"],
            "post_tax_corpus": sip_result["post_tax_corpus"],
            "inflation_adjusted": sip_result["inflation_adjusted_value"],
        },
        "winner": "lumpsum" if lump_post_tax > sip_result["post_tax_corpus"] else "sip",
        "disclaimer": "For educational/illustrative purposes only. Returns are not guaranteed.",
    }


def reverse_sip(
    target_corpus: float,
    duration_years: int,
    expected_return: float,
    inflation_rate: float = 0.06,
    tax_rate: float = 0.10,
    step_up_pct: float = 0.0,
) -> dict:
    """
    Goal-based reverse SIP: given a target corpus, calculate the required monthly investment.

    Uses binary search to find the monthly amount that achieves the target
    post-tax corpus within the specified duration.
    """
    lo, hi = 100.0, target_corpus / duration_years
    for _ in range(100):
        mid = (lo + hi) / 2
        result = calculate_sip(mid, duration_years, expected_return, inflation_rate, tax_rate, step_up_pct)
        if result["post_tax_corpus"] < target_corpus:
            lo = mid
        else:
            hi = mid

    required_monthly = round((lo + hi) / 2, 2)
    final = calculate_sip(required_monthly, duration_years, expected_return, inflation_rate, tax_rate, step_up_pct)

    return {
        "target_corpus": target_corpus,
        "required_monthly": required_monthly,
        "duration_years": duration_years,
        "expected_return": expected_return,
        "total_invested": final["total_invested"],
        "projected_post_tax": final["post_tax_corpus"],
        "inflation_adjusted": final["inflation_adjusted_value"],
        "year_breakdown": final["year_breakdown"],
        "disclaimer": "For educational/illustrative purposes only. Returns are not guaranteed.",
    }
