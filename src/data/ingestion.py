import logging
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    pass


def download_ohlcv(
    ticker: str,
    start: str | datetime | None = None,
    end: str | datetime | None = None,
    period: str = "5y",
) -> pd.DataFrame:
    """Download OHLCV data from Yahoo Finance."""
    logger.info(f"Downloading {ticker} data...")

    kwargs = {"auto_adjust": True}
    if start and end:
        kwargs["start"] = start
        kwargs["end"] = end
    else:
        kwargs["period"] = period

    df = yf.download(ticker, progress=False, **kwargs)

    if df.empty:
        raise DataValidationError(f"No data returned for {ticker}")

    # Flatten multi-level columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    })

    # Keep only the columns we need
    expected = ["open", "high", "low", "close", "volume"]
    df = df[[c for c in expected if c in df.columns]]

    df["ticker"] = ticker
    df.index.name = "date"
    df = df.reset_index()

    df = validate_ohlcv(df, ticker)

    logger.info(f"Downloaded {len(df)} rows for {ticker}")
    return df


def validate_ohlcv(df: pd.DataFrame, ticker: str = "") -> pd.DataFrame:
    """Validate OHLCV data quality."""
    if df.empty:
        raise DataValidationError(f"Empty dataframe for {ticker}")

    # Check for negative prices
    price_cols = ["open", "high", "low", "close"]
    for col in price_cols:
        if col in df.columns and (df[col] < 0).any():
            raise DataValidationError(f"Negative prices found in {col} for {ticker}")

    # Check for zero volume days
    if "volume" in df.columns:
        zero_vol = (df["volume"] == 0).sum()
        if zero_vol > 0:
            logger.warning(f"{zero_vol} zero-volume days for {ticker}")

    # Forward fill missing values, then drop leading NaNs
    df = df.ffill().dropna(subset=price_cols)

    # Check for large gaps (> 5 trading days)
    if "date" in df.columns:
        date_col = pd.to_datetime(df["date"])
        gaps = date_col.diff().dt.days
        large_gaps = gaps[gaps > 7]  # 7 calendar days ~ 5 trading days
        if len(large_gaps) > 0:
            logger.warning(f"{len(large_gaps)} gaps > 5 trading days for {ticker}")

    # Drop duplicate dates
    if "date" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["date"], keep="last")
        if len(df) < before:
            logger.warning(f"Dropped {before - len(df)} duplicate dates for {ticker}")

    return df


def download_multiple(tickers: list[str], **kwargs) -> dict[str, pd.DataFrame]:
    """Download data for multiple tickers."""
    results = {}
    for ticker in tickers:
        try:
            results[ticker] = download_ohlcv(ticker, **kwargs)
        except Exception as e:
            logger.error(f"Failed to download {ticker}: {e}")
    return results
