from datetime import datetime

import numpy as np
import pandas as pd

from src.backtest.engine import BacktestRun


def monte_carlo_simulation(
    trades: pd.DataFrame,
    initial_capital: float = 100_000.0,
    n_simulations: int = 1000,
    seed: int = 42,
) -> dict:
    """Resample trade returns with replacement to build confidence intervals.

    Returns percentile-based statistics on terminal portfolio value
    to assess whether observed performance is statistically significant.
    """
    closed = trades[trades["pnl"].notna()]
    if closed.empty:
        return {"p5": initial_capital, "p25": initial_capital, "p50": initial_capital,
                "p75": initial_capital, "p95": initial_capital, "mean": initial_capital}

    trade_returns = closed["pnl"].values
    rng = np.random.default_rng(seed)
    n_trades = len(trade_returns)
    terminal_values = []

    for _ in range(n_simulations):
        sampled = rng.choice(trade_returns, size=n_trades, replace=True)
        terminal = initial_capital + sampled.sum()
        terminal_values.append(terminal)

    terminal_values = np.array(terminal_values)
    return {
        "p5": round(float(np.percentile(terminal_values, 5)), 2),
        "p25": round(float(np.percentile(terminal_values, 25)), 2),
        "p50": round(float(np.percentile(terminal_values, 50)), 2),
        "p75": round(float(np.percentile(terminal_values, 75)), 2),
        "p95": round(float(np.percentile(terminal_values, 95)), 2),
        "mean": round(float(terminal_values.mean()), 2),
        "prob_profit": round(float((terminal_values > initial_capital).mean()), 4),
    }


def drawdown_periods(equity_curve: pd.Series) -> list[dict]:
    """Extract significant drawdown periods (drawdown > 5%)."""
    rolling_max = equity_curve.cummax()
    drawdown = (equity_curve - rolling_max) / rolling_max

    periods = []
    in_drawdown = False
    start_date = None
    peak_value = None

    for date, dd in drawdown.items():
        if dd < -0.05 and not in_drawdown:
            in_drawdown = True
            start_date = date
            peak_value = float(rolling_max[date])
        elif dd >= -0.001 and in_drawdown:
            in_drawdown = False
            duration_days = (pd.Timestamp(date) - pd.Timestamp(start_date)).days
            periods.append({
                "start": str(start_date),
                "end": str(date),
                "duration_days": duration_days,
                "max_drawdown": float(drawdown[start_date:date].min()),
                "peak_value": peak_value,
                "trough_value": float(equity_curve[start_date:date].min()),
            })

    return periods


def monthly_returns(equity_curve: pd.Series) -> pd.DataFrame:
    """Compute monthly return matrix for heatmap."""
    returns = equity_curve.resample("ME").last().pct_change().dropna()
    returns.index = pd.to_datetime(returns.index)
    result = pd.DataFrame({
        "year": returns.index.year,
        "month": returns.index.month,
        "return": returns.values,
    })
    return result


def monthly_returns_pivot(equity_curve: pd.Series) -> dict:
    """Pivot monthly returns into a year x month matrix for heatmap rendering."""
    monthly = monthly_returns(equity_curve)
    if monthly.empty:
        return {"years": [], "months": list(range(1, 13)), "data": []}

    pivot = monthly.pivot_table(index="year", columns="month", values="return", aggfunc="first")
    pivot = pivot.reindex(columns=range(1, 13))

    return {
        "years": [int(y) for y in pivot.index],
        "months": list(range(1, 13)),
        "data": [[None if pd.isna(v) else round(float(v) * 100, 2) for v in row] for row in pivot.values],
    }


def generate_report(run: BacktestRun) -> dict:
    """
    Generate a complete serializable backtest report.

    Returns a dict suitable for API responses and dashboard consumption.
    """
    equity = run.equity_curve
    trades = run.trades

    # Equity curve data
    equity_data = [
        {"date": str(date), "value": float(val)}
        for date, val in equity.items()
    ]

    # Drawdown series
    rolling_max = equity.cummax()
    drawdown = ((equity - rolling_max) / rolling_max).fillna(0)
    drawdown_data = [
        {"date": str(date), "drawdown": float(val)}
        for date, val in drawdown.items()
    ]

    # Trade summary
    trade_data = trades.to_dict(orient="records") if not trades.empty else []

    # Monthly returns
    monthly = monthly_returns(equity)
    monthly_data = monthly.to_dict(orient="records")

    # Drawdown periods
    dd_periods = drawdown_periods(equity)

    # Monte Carlo confidence intervals
    mc = monte_carlo_simulation(trades, run.initial_capital)

    return {
        "ticker": run.ticker,
        "initial_capital": run.initial_capital,
        "final_value": run.final_value,
        "metrics": run.metrics,
        "equity_curve": equity_data,
        "drawdown_series": drawdown_data,
        "drawdown_periods": dd_periods,
        "monthly_returns": monthly_data,
        "monthly_heatmap": monthly_returns_pivot(equity),
        "trades": trade_data,
        "monte_carlo": mc,
        "generated_at": datetime.now().isoformat(),
        "disclaimer": (
            "Educational purposes only. Past performance is not indicative of future results. "
            "Backtested results are theoretical and do not account for real-world market impact."
        ),
    }
