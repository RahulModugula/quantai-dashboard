import numpy as np
import pandas as pd


def sharpe_ratio(returns: pd.Series, risk_free: float = 0.04, periods_per_year: int = 252) -> float:
    """Annualized Sharpe ratio."""
    excess = returns - risk_free / periods_per_year
    if excess.std() == 0:
        return 0.0
    return float(excess.mean() / excess.std() * np.sqrt(periods_per_year))


def sortino_ratio(returns: pd.Series, risk_free: float = 0.04, periods_per_year: int = 252) -> float:
    """Annualized Sortino ratio (uses downside deviation only)."""
    excess = returns - risk_free / periods_per_year
    downside = excess[excess < 0]
    if len(downside) == 0 or downside.std() == 0:
        return 0.0
    return float(excess.mean() / downside.std() * np.sqrt(periods_per_year))


def max_drawdown(equity_curve: pd.Series) -> float:
    """Maximum drawdown as a percentage (negative value).

    Returns 0.0 for flat or monotonically increasing equity curves.
    """
    rolling_max = equity_curve.cummax()
    denominator = rolling_max.replace(0, np.nan)
    drawdown = (equity_curve - rolling_max) / denominator
    return float(drawdown.min()) if not drawdown.isna().all() else 0.0


def calmar_ratio(returns: pd.Series, equity_curve: pd.Series, periods_per_year: int = 252) -> float:
    """Calmar ratio: CAGR / abs(max drawdown)."""
    n_years = len(returns) / periods_per_year
    if n_years == 0:
        return 0.0
    cagr = float((equity_curve.iloc[-1] / equity_curve.iloc[0]) ** (1 / n_years) - 1)
    mdd = abs(max_drawdown(equity_curve))
    if mdd == 0:
        return 0.0
    return cagr / mdd


def win_rate(trades: pd.DataFrame) -> float:
    """Fraction of trades with positive PnL."""
    if trades.empty or "pnl" not in trades.columns:
        return 0.0
    closed = trades[trades["pnl"].notna()]
    if len(closed) == 0:
        return 0.0
    return float((closed["pnl"] > 0).mean())


def profit_factor(trades: pd.DataFrame) -> float:
    """Ratio of gross profit to gross loss."""
    if trades.empty or "pnl" not in trades.columns:
        return 0.0
    closed = trades[trades["pnl"].notna()]
    gross_profit = closed[closed["pnl"] > 0]["pnl"].sum()
    gross_loss = abs(closed[closed["pnl"] < 0]["pnl"].sum())
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return float(gross_profit / gross_loss)


def compute_all_metrics(
    equity_curve: pd.Series,
    trades: pd.DataFrame,
    risk_free: float = 0.04,
) -> dict:
    """Compute all risk/performance metrics from equity curve and trade log."""
    returns = equity_curve.pct_change().dropna()

    return {
        "sharpe_ratio": sharpe_ratio(returns, risk_free),
        "sortino_ratio": sortino_ratio(returns, risk_free),
        "max_drawdown": max_drawdown(equity_curve),
        "calmar_ratio": calmar_ratio(returns, equity_curve),
        "win_rate": win_rate(trades),
        "profit_factor": profit_factor(trades),
        "total_return": float(equity_curve.iloc[-1] / equity_curve.iloc[0] - 1),
        "total_trades": len(trades[trades["pnl"].notna()]) if not trades.empty else 0,
    }
