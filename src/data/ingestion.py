import logging
from abc import ABC, abstractmethod
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

    # Keep only the columns we need; adj_close absent for some tickers
    expected = ["open", "high", "low", "close", "volume"]
    df = df[[c for c in expected if c in df.columns]]

    df["ticker"] = ticker
    df.index.name = "date"
    df = df.reset_index()

    # yfinance returns timezone-aware timestamps on some systems — strip tz
    if hasattr(df["date"], "dt") and df["date"].dt.tz is not None:
        df["date"] = df["date"].dt.tz_localize(None)

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


def download_multiple(
    tickers: list[str],
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    **kwargs,
) -> dict[str, pd.DataFrame]:
    """Download data for multiple tickers with retry and exponential backoff."""
    import time

    results = {}
    for ticker in tickers:
        for attempt in range(max_retries):
            try:
                results[ticker] = download_ohlcv(ticker, **kwargs)
                break
            except Exception as e:
                wait = backoff_factor * (2 ** attempt)
                if attempt < max_retries - 1:
                    logger.warning(f"{ticker} attempt {attempt + 1} failed: {e}. Retrying in {wait:.1f}s")
                    time.sleep(wait)
                else:
                    logger.error(f"Failed to download {ticker} after {max_retries} attempts: {e}")
    return results


# ---------------------------------------------------------------------------
# Data provider abstraction with fallback support
# ---------------------------------------------------------------------------


class DataProvider(ABC):
    """Abstract base for data providers."""

    @abstractmethod
    def fetch_ohlcv(
        self,
        ticker: str,
        start: str | datetime | None = None,
        end: str | datetime | None = None,
        period: str = "5y",
    ) -> pd.DataFrame:
        """Fetch OHLCV data for *ticker*."""


class YFinanceProvider(DataProvider):
    """Provider that wraps the existing ``download_ohlcv`` helper."""

    def fetch_ohlcv(self, ticker, start=None, end=None, period="5y"):
        return download_ohlcv(ticker, start=start, end=end, period=period)


class FREDProvider(DataProvider):
    """Provider for macro indicators available as yfinance tickers (e.g. ^VIX, ^TNX)."""

    # Mapping of friendly names to yfinance tickers
    MACRO_TICKERS = {"VIX": "^VIX", "TNX": "^TNX"}

    def fetch_ohlcv(self, ticker, start=None, end=None, period="5y"):
        resolved = self.MACRO_TICKERS.get(ticker.upper(), ticker)
        return download_ohlcv(resolved, start=start, end=end, period=period)


def download_with_fallback(
    ticker: str,
    providers: list[DataProvider] | None = None,
    **kwargs,
) -> pd.DataFrame:
    """Try each provider in order, returning the first successful result."""
    if providers is None:
        providers = [YFinanceProvider()]

    last_err: Exception | None = None
    for provider in providers:
        try:
            return provider.fetch_ohlcv(ticker, **kwargs)
        except Exception as e:
            logger.warning(f"{provider.__class__.__name__} failed for {ticker}: {e}")
            last_err = e

    raise DataValidationError(
        f"All providers failed for {ticker}: {last_err}"
    )


def download_macro_features(
    tickers: dict[str, str] | None = None,
    **kwargs,
) -> pd.DataFrame:
    """Download macro indicators and return a DataFrame with date, vix_close, tnx_close.

    Parameters
    ----------
    tickers : dict, optional
        Mapping of column-prefix to yfinance ticker.
        Defaults to ``{"vix": "^VIX", "tnx": "^TNX"}``.
    **kwargs : passed through to ``download_ohlcv`` (e.g. start, end, period).
    """
    if tickers is None:
        tickers = {"vix": "^VIX", "tnx": "^TNX"}

    frames: list[pd.DataFrame] = []
    for name, symbol in tickers.items():
        df = download_ohlcv(symbol, **kwargs)
        df = df[["date", "close"]].rename(columns={"close": f"{name}_close"})
        frames.append(df)

    merged = frames[0]
    for df in frames[1:]:
        merged = merged.merge(df, on="date", how="outer")

    merged = merged.sort_values("date").reset_index(drop=True)
    return merged
