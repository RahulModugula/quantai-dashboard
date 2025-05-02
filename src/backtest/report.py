from datetime import datetime

import numpy as np
import pandas as pd

from src.backtest.engine import BacktestRun


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
            periods.append({
                "start": str(start_date),
                "end": str(date),
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

    return {
        "ticker": run.ticker,
        "initial_capital": run.initial_capital,
        "final_value": run.final_value,
        "metrics": run.metrics,
        "equity_curve": equity_data,
        "drawdown_series": drawdown_data,
        "drawdown_periods": dd_periods,
        "monthly_returns": monthly_data,
        "trades": trade_data,
        "generated_at": datetime.now().isoformat(),
        "disclaimer": (
            "Educational purposes only. Past performance is not indicative of future results. "
            "Backtested results are theoretical and do not account for real-world market impact."
        ),
    }
