"""Stress test API endpoints: Monte Carlo simulation and historical scenario replay."""

import logging

import pandas as pd
from fastapi import APIRouter, HTTPException

from src.data.storage import load_ohlcv
from src.trading.stress_test import SCENARIOS, HistoricalScenarioTest, MonteCarloStressTest

router = APIRouter(prefix="/stress-test", tags=["risk"])
logger = logging.getLogger(__name__)


@router.get("/monte-carlo/{ticker}")
def monte_carlo_stress(
    ticker: str,
    n_simulations: int = 500,
    horizon_days: int = 252,
) -> dict:
    """Run Monte Carlo stress test on ticker's historical returns.

    Uses block bootstrap (block_size=20) to preserve autocorrelation in the
    return series.  Returns percentile fan, VaR/CVaR, probability of loss,
    and 100 representative simulated equity paths.
    """
    try:
        ohlcv = load_ohlcv(ticker)
    except Exception as exc:
        logger.error("Failed to load OHLCV for %s: %s", ticker, exc)
        raise HTTPException(status_code=404, detail=f"No data found for ticker '{ticker}'") from exc

    if ohlcv.empty:
        raise HTTPException(status_code=404, detail=f"No OHLCV data available for '{ticker}'")

    if "close" not in ohlcv.columns:
        raise HTTPException(
            status_code=422,
            detail="OHLCV data missing 'close' column",
        )

    close = pd.Series(ohlcv["close"].values, dtype=float)
    daily_returns = close.pct_change().dropna()

    if len(daily_returns) < 40:
        raise HTTPException(
            status_code=422,
            detail=f"Insufficient history for '{ticker}': need at least 40 days",
        )

    mc = MonteCarloStressTest(n_simulations=n_simulations, horizon_days=horizon_days)
    result = mc.run(daily_returns)

    return {
        "ticker": ticker,
        "n_simulations": n_simulations,
        "horizon_days": horizon_days,
        **result,
    }


@router.get("/scenarios/{ticker}")
def historical_scenarios(ticker: str) -> dict:
    """Run all historical crisis scenario replays for a ticker.

    Returns each scenario's period return, max drawdown, and availability flag,
    sorted from worst to best performing.
    """
    try:
        ohlcv = load_ohlcv(ticker)
    except Exception as exc:
        logger.error("Failed to load OHLCV for %s: %s", ticker, exc)
        raise HTTPException(status_code=404, detail=f"No data found for ticker '{ticker}'") from exc

    if ohlcv.empty:
        raise HTTPException(status_code=404, detail=f"No OHLCV data available for '{ticker}'")

    if "close" not in ohlcv.columns:
        raise HTTPException(
            status_code=422,
            detail="OHLCV data missing 'close' column",
        )

    # Build a single-column DataFrame with a DatetimeIndex
    dates = pd.to_datetime(ohlcv["date"] if "date" in ohlcv.columns else ohlcv.index)
    prices = pd.DataFrame({"close": ohlcv["close"].values}, index=dates)

    tester = HistoricalScenarioTest()
    scenarios = tester.run_all(prices)

    return {
        "ticker": ticker,
        "scenarios": scenarios,
        "total_scenarios": len(SCENARIOS),
        "available_scenarios": sum(1 for s in scenarios if s["available"]),
    }


@router.get("/scenarios")
def list_scenarios() -> dict:
    """List all available historical stress scenarios with their date ranges."""
    return {
        "scenarios": [
            {"name": name, "start": start, "end": end} for name, (start, end) in SCENARIOS.items()
        ]
    }
