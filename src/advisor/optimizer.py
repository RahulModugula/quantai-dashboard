"""Portfolio optimization using PyPortfolioOpt.

Provides mathematically optimized portfolio weights via mean-variance
optimization, minimum volatility, and Hierarchical Risk Parity (HRP).
Complements the static risk-based allocations in allocation.py.
"""

import logging

import pandas as pd
from pypfopt import EfficientFrontier, HRPOpt, expected_returns, risk_models

from src.data.storage import load_ohlcv

logger = logging.getLogger(__name__)


def _build_price_df(tickers: list[str], period: int = 252, db_path: str | None = None) -> pd.DataFrame:
    """Load closing prices for all tickers into a single DataFrame.

    Returns a DataFrame indexed by date with one column per ticker.
    Tickers with no data are silently dropped.
    """
    frames = {}
    for ticker in tickers:
        df = load_ohlcv(ticker, db_path=db_path)
        if df.empty:
            logger.warning("No data for %s, skipping", ticker)
            continue
        series = df.set_index("date")["close"].sort_index()
        series = series[~series.index.duplicated(keep="last")]
        frames[ticker] = series

    if not frames:
        raise ValueError("No price data found for any of the provided tickers")

    prices = pd.DataFrame(frames).dropna()
    if len(prices) < 2:
        raise ValueError("Insufficient overlapping price history across tickers")

    # Trim to the requested look-back period
    prices = prices.iloc[-period:]
    return prices


def _clean_weights(weights: dict) -> dict:
    """Round weights and drop near-zero allocations."""
    return {t: round(w, 4) for t, w in weights.items() if round(w, 4) > 0}


def compute_efficient_frontier(
    tickers: list[str],
    period: int = 252,
    db_path: str | None = None,
    n_points: int = 50,
) -> dict:
    """Compute efficient frontier curve and the max-Sharpe portfolio.

    Args:
        tickers: List of ticker symbols.
        period: Trading days of history to use.
        db_path: Optional path to the SQLite database.
        n_points: Number of points along the frontier.

    Returns:
        Dict with keys:
            frontier: list of {return, risk, sharpe} dicts for plotting.
            max_sharpe_weights: dict of {ticker: weight} for the tangency portfolio.
    """
    if len(tickers) < 2:
        raise ValueError("Need at least 2 tickers to compute an efficient frontier")

    prices = _build_price_df(tickers, period, db_path)
    mu = expected_returns.mean_historical_return(prices)
    cov = risk_models.sample_cov(prices)

    # Max-Sharpe portfolio
    ef = EfficientFrontier(mu, cov)
    ef.max_sharpe()
    max_sharpe_weights = _clean_weights(ef.clean_weights())

    # Build frontier curve by sweeping target returns
    min_ret = mu.min()
    max_ret = mu.max()
    frontier = []
    for target in [min_ret + i * (max_ret - min_ret) / (n_points - 1) for i in range(n_points)]:
        try:
            ef_point = EfficientFrontier(mu, cov)
            ef_point.efficient_return(target)
            perf = ef_point.portfolio_performance(risk_free_rate=0.04)
            frontier.append({
                "return": round(perf[0], 4),
                "risk": round(perf[1], 4),
                "sharpe": round(perf[2], 4),
            })
        except Exception:
            continue

    return {
        "frontier": frontier,
        "max_sharpe_weights": max_sharpe_weights,
    }


def optimize_max_sharpe(
    tickers: list[str],
    period: int = 252,
    risk_free: float = 0.04,
    db_path: str | None = None,
) -> dict:
    """Return portfolio weights that maximise the Sharpe ratio.

    Args:
        tickers: List of ticker symbols.
        period: Trading days of history.
        risk_free: Annual risk-free rate assumption.
        db_path: Optional database path.

    Returns:
        Dict of {ticker: weight} with near-zero holdings removed.
    """
    if len(tickers) < 2:
        return {tickers[0]: 1.0} if tickers else {}

    prices = _build_price_df(tickers, period, db_path)
    mu = expected_returns.mean_historical_return(prices)
    cov = risk_models.sample_cov(prices)

    ef = EfficientFrontier(mu, cov)
    ef.max_sharpe(risk_free_rate=risk_free)
    return _clean_weights(ef.clean_weights())


def optimize_min_volatility(
    tickers: list[str],
    period: int = 252,
    db_path: str | None = None,
) -> dict:
    """Return portfolio weights that minimise overall volatility.

    Args:
        tickers: List of ticker symbols.
        period: Trading days of history.
        db_path: Optional database path.

    Returns:
        Dict of {ticker: weight} with near-zero holdings removed.
    """
    if len(tickers) < 2:
        return {tickers[0]: 1.0} if tickers else {}

    prices = _build_price_df(tickers, period, db_path)
    mu = expected_returns.mean_historical_return(prices)
    cov = risk_models.sample_cov(prices)

    ef = EfficientFrontier(mu, cov)
    ef.min_volatility()
    return _clean_weights(ef.clean_weights())


def optimize_hrp(
    tickers: list[str],
    period: int = 252,
    db_path: str | None = None,
) -> dict:
    """Return portfolio weights using Hierarchical Risk Parity.

    HRP does not require expected returns estimates, making it more robust
    to estimation error than mean-variance approaches.

    Args:
        tickers: List of ticker symbols.
        period: Trading days of history.
        db_path: Optional database path.

    Returns:
        Dict of {ticker: weight} with near-zero holdings removed.
    """
    if len(tickers) < 2:
        return {tickers[0]: 1.0} if tickers else {}

    prices = _build_price_df(tickers, period, db_path)
    returns = prices.pct_change().dropna()

    hrp = HRPOpt(returns)
    hrp.optimize()
    return _clean_weights(hrp.clean_weights())
