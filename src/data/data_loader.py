"""Unified data loading interface."""
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class DataLoader:
    """Load price and feature data with caching."""

    def __init__(self, cache_enabled: bool = True):
        self.cache_enabled = cache_enabled
        self._cache = {}

    def load_prices(self, ticker: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Load OHLCV price data.

        Args:
            ticker: Stock ticker
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with price data
        """
        from src.data.storage import load_ohlcv

        cache_key = f"prices_{ticker}_{start_date}_{end_date}"

        if self.cache_enabled and cache_key in self._cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self._cache[cache_key]

        df = load_ohlcv(ticker)

        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]

        if self.cache_enabled:
            self._cache[cache_key] = df

        return df

    def load_features(self, ticker: str) -> pd.DataFrame:
        """Load engineered features for ML model.

        Args:
            ticker: Stock ticker

        Returns:
            DataFrame with features
        """
        from src.data.storage import load_features

        cache_key = f"features_{ticker}"

        if self.cache_enabled and cache_key in self._cache:
            return self._cache[cache_key]

        df = load_features(ticker)

        if self.cache_enabled:
            self._cache[cache_key] = df

        return df

    def clear_cache(self):
        """Clear data cache."""
        self._cache.clear()
        logger.info("Data cache cleared")
