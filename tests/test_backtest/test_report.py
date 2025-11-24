import pandas as pd

from src.backtest.report import monte_carlo_simulation, monthly_returns_pivot


def test_monte_carlo_returns_percentiles():
    trades = pd.DataFrame({"pnl": [100, -50, 200, -30, 150, -20, 80]})
    mc = monte_carlo_simulation(trades, initial_capital=100_000)
    assert mc["p5"] < mc["p50"] < mc["p95"]
    assert 0 <= mc["prob_profit"] <= 1


def test_monte_carlo_empty_trades():
    trades = pd.DataFrame({"pnl": [None, None]})
    mc = monte_carlo_simulation(trades, initial_capital=100_000)
    assert mc["p50"] == 100_000


def test_monte_carlo_all_profitable():
    trades = pd.DataFrame({"pnl": [100, 200, 300]})
    mc = monte_carlo_simulation(trades, initial_capital=10_000)
    assert mc["prob_profit"] == 1.0


def test_monthly_returns_pivot_structure():
    dates = pd.date_range("2023-01-01", periods=252, freq="B")
    equity = pd.Series([100 * (1.001**i) for i in range(252)], index=dates)
    result = monthly_returns_pivot(equity)
    assert "years" in result
    assert "months" in result
    assert "data" in result
    assert len(result["months"]) == 12
