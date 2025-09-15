import numpy as np
import pandas as pd


def sharpe_ratio(returns: pd.Series, risk_free: float = 0.04, periods_per_year: int = 252) -> float:
    """Annualized Sharpe ratio."""
    if returns.std() < 1e-10:
        return 0.0
    excess = returns - risk_free / periods_per_year
    return float(excess.mean() / excess.std() * np.sqrt(periods_per_year))


def sortino_ratio(returns: pd.Series, risk_free: float = 0.04, periods_per_year: int = 252) -> float:
    """Annualized Sortino ratio (uses downside deviation only)."""
    excess = returns - risk_free / periods_per_year
    downside = excess[excess < 0]
    if len(downside) == 0:
        return 0.0
    downside_std = downside.std()
    if downside_std < 1e-10:
        # All downside returns are identical; sign indicates direction
        return float(-1.0 if excess.mean() < 0 else 0.0)
    return float(excess.mean() / downside_std * np.sqrt(periods_per_year))


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
    if mdd < 1e-10:
        return cagr * 100 if cagr > 0 else 0.0  # near-zero drawdown
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


def rolling_sharpe(returns: pd.Series, window: int = 126, risk_free: float = 0.04) -> pd.Series:
    """Rolling Sharpe ratio over a trailing window (default 6 months)."""
    excess = returns - risk_free / 252
    rolling_mean = excess.rolling(window=window).mean()
    rolling_std = excess.rolling(window=window).std().replace(0, np.nan)
    return rolling_mean / rolling_std * np.sqrt(252)


def benchmark_comparison(
    equity_curve: pd.Series,
    benchmark_prices: pd.Series,
    risk_free: float = 0.04,
) -> dict:
    """Compare strategy equity curve against a benchmark (e.g. SPY buy-and-hold)."""
    bench_returns = benchmark_prices.pct_change().dropna()
    strat_returns = equity_curve.pct_change().dropna()

    # Align on common dates
    common = strat_returns.index.intersection(bench_returns.index)
    if len(common) == 0:
        return {"alpha": 0.0, "beta": 0.0, "benchmark_return": 0.0}

    sr = strat_returns.loc[common]
    br = bench_returns.loc[common]

    # Beta = Cov(strategy, benchmark) / Var(benchmark)
    cov = np.cov(sr, br)
    beta = float(cov[0, 1] / cov[1, 1]) if cov[1, 1] != 0 else 0.0

    # Alpha (annualized Jensen's alpha)
    strat_annual = float(sr.mean() * 252)
    bench_annual = float(br.mean() * 252)
    alpha = strat_annual - (risk_free + beta * (bench_annual - risk_free))

    bench_total = float(benchmark_prices.iloc[-1] / benchmark_prices.iloc[0] - 1)

    return {
        "alpha": round(alpha, 4),
        "beta": round(beta, 4),
        "benchmark_return": round(bench_total, 4),
        "benchmark_sharpe": round(float(sharpe_ratio(br, risk_free)), 4),
    }


def expectancy(trades: pd.DataFrame) -> float:
    """Expected profit per trade: (win_rate * avg_win) - (loss_rate * avg_loss)."""
    if trades.empty or "pnl" not in trades.columns:
        return 0.0
    closed = trades[trades["pnl"].notna()]
    if closed.empty:
        return 0.0
    wins = closed[closed["pnl"] > 0]["pnl"]
    losses = closed[closed["pnl"] < 0]["pnl"]
    w_rate = len(wins) / len(closed)
    avg_w = float(wins.mean()) if len(wins) > 0 else 0.0
    avg_l = float(abs(losses.mean())) if len(losses) > 0 else 0.0
    return round(w_rate * avg_w - (1 - w_rate) * avg_l, 2)


def recovery_factor(equity_curve: pd.Series) -> float:
    """Total net profit / abs(max drawdown dollar value)."""
    net_profit = float(equity_curve.iloc[-1] - equity_curve.iloc[0])
    rolling_max = equity_curve.cummax()
    dollar_dd = (equity_curve - rolling_max).min()
    if abs(dollar_dd) < 1e-10:
        return 0.0
    return round(net_profit / abs(dollar_dd), 4)


def compute_all_metrics(
    equity_curve: pd.Series,
    trades: pd.DataFrame,
    risk_free: float = 0.04,
) -> dict:
    """Compute all risk/performance metrics from equity curve and trade log."""
    returns = equity_curve.pct_change().dropna()
    closed = trades[trades["pnl"].notna()] if not trades.empty else pd.DataFrame()
    wins = closed[closed["pnl"] > 0]["pnl"] if not closed.empty else pd.Series(dtype=float)
    losses = closed[closed["pnl"] < 0]["pnl"] if not closed.empty else pd.Series(dtype=float)

    return {
        "sharpe_ratio": sharpe_ratio(returns, risk_free),
        "sortino_ratio": sortino_ratio(returns, risk_free),
        "max_drawdown": max_drawdown(equity_curve),
        "calmar_ratio": calmar_ratio(returns, equity_curve),
        "win_rate": win_rate(trades),
        "profit_factor": profit_factor(trades),
        "expectancy": expectancy(trades),
        "recovery_factor": recovery_factor(equity_curve),
        "avg_win": round(float(wins.mean()), 2) if len(wins) > 0 else 0.0,
        "avg_loss": round(float(losses.mean()), 2) if len(losses) > 0 else 0.0,
        "total_return": float(equity_curve.iloc[-1] / equity_curve.iloc[0] - 1),
        "total_trades": len(closed),
    }
