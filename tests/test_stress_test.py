"""Unit tests for portfolio stress testing: Monte Carlo and historical scenarios."""

import numpy as np
import pandas as pd

from src.trading.stress_test import (
    SCENARIOS,
    HistoricalScenarioTest,
    MonteCarloStressTest,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _synthetic_returns(n: int = 500, seed: int = 0) -> pd.Series:
    """Generate synthetic daily returns with slight positive drift."""
    rng = np.random.default_rng(seed)
    return pd.Series(rng.normal(0.0004, 0.012, size=n))


def _synthetic_prices(n_days: int = 1260, seed: int = 1) -> pd.DataFrame:
    """Generate 5-year synthetic price series with a DatetimeIndex."""
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0003, 0.010, size=n_days)
    prices = 100.0 * np.cumprod(1.0 + returns)
    index = pd.date_range(start="2019-01-01", periods=n_days, freq="B")
    return pd.DataFrame({"close": prices}, index=index)


# ---------------------------------------------------------------------------
# Monte Carlo tests
# ---------------------------------------------------------------------------


def test_monte_carlo_returns_correct_keys():
    """Result dict must contain all required keys."""
    mc = MonteCarloStressTest(n_simulations=100, horizon_days=60)
    result = mc.run(_synthetic_returns())
    required_keys = {
        "percentiles",
        "prob_loss",
        "expected_return",
        "var_95",
        "cvar_95",
        "max_drawdown_median",
        "paths",
    }
    assert required_keys == set(result.keys())
    # percentiles sub-dict
    assert set(result["percentiles"].keys()) == {5, 25, 50, 75, 95}


def test_prob_loss_between_0_and_1():
    """Probability of loss must be a valid probability."""
    mc = MonteCarloStressTest(n_simulations=200, horizon_days=252)
    result = mc.run(_synthetic_returns())
    assert 0.0 <= result["prob_loss"] <= 1.0


def test_percentile_ordering():
    """Percentiles must be weakly increasing: p5 <= p25 <= p50 <= p75 <= p95."""
    mc = MonteCarloStressTest(n_simulations=300, horizon_days=126)
    result = mc.run(_synthetic_returns())
    p = result["percentiles"]
    assert p[5] <= p[25] <= p[50] <= p[75] <= p[95], f"Percentile ordering violated: {p}"


def test_var_is_positive():
    """VaR and CVaR should be expressed as positive loss magnitudes."""
    mc = MonteCarloStressTest(n_simulations=100, horizon_days=63)
    # Use returns with some negative tail to ensure non-trivial VaR
    rng = np.random.default_rng(99)
    returns = pd.Series(rng.normal(0.0, 0.015, size=500))
    result = mc.run(returns)
    assert result["var_95"] >= 0.0, f"VaR should be >= 0, got {result['var_95']}"
    assert result["cvar_95"] >= result["var_95"], (
        f"CVaR ({result['cvar_95']}) should be >= VaR ({result['var_95']})"
    )


# ---------------------------------------------------------------------------
# Historical scenario tests
# ---------------------------------------------------------------------------


def test_historical_scenario_replay():
    """Scenario replay on data that covers the period should return available=True."""
    # Build price data spanning the covid_crash_2020 window (2020-02-19 to 2020-03-23)
    extended_index = pd.date_range(start="2019-01-01", end="2021-12-31", freq="B")
    rng = np.random.default_rng(7)
    ext_returns = rng.normal(0.0003, 0.015, size=len(extended_index))
    ext_prices = pd.DataFrame(
        {"close": 100.0 * np.cumprod(1.0 + ext_returns)},
        index=extended_index,
    )

    tester = HistoricalScenarioTest()
    result = tester.replay(ext_prices, "covid_crash_2020")

    assert result["scenario"] == "covid_crash_2020"
    assert result["available"] is True
    assert result["return"] is not None
    assert result["max_drawdown"] is not None
    assert result["max_drawdown"] <= 0.0, "Max drawdown should be <= 0"
    assert result["period"]["start"] == "2020-02-19"
    assert result["period"]["end"] == "2020-03-23"


def test_all_scenarios_run_without_crash():
    """run_all() on a 5-year synthetic series must not raise exceptions."""
    prices = _synthetic_prices(n_days=1260)
    tester = HistoricalScenarioTest()
    # Should not raise
    results = tester.run_all(prices)
    assert isinstance(results, list)
    assert len(results) == len(SCENARIOS)
    # Each result must have required keys
    required = {"scenario", "period", "return", "max_drawdown", "duration_days", "available"}
    for r in results:
        assert required.issubset(set(r.keys())), f"Missing keys in result: {r}"
