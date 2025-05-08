"""Detect and handle anomalous price data."""
import logging
import numpy as np

logger = logging.getLogger(__name__)


class PriceAnomalyDetector:
    """Detect price anomalies and data quality issues."""

    @staticmethod
    def detect_gaps(prices: list[float], threshold_pct: float = 0.10) -> list[int]:
        """Detect abnormal price gaps (> threshold).

        Args:
            prices: List of prices
            threshold_pct: Gap threshold as percentage (default 10%)

        Returns:
            List of indices where gaps occur
        """
        if len(prices) < 2:
            return []

        gaps = []
        for i in range(1, len(prices)):
            pct_change = abs(prices[i] - prices[i - 1]) / prices[i - 1]
            if pct_change > threshold_pct:
                gaps.append(i)

        return gaps

    @staticmethod
    def detect_outliers_zscore(prices: list[float], threshold: float = 3.0) -> list[int]:
        """Detect price outliers using z-score method.

        Args:
            prices: List of prices
            threshold: Z-score threshold (default 3.0)

        Returns:
            List of outlier indices
        """
        prices = np.array(prices)
        mean = np.mean(prices)
        std = np.std(prices)

        if std == 0:
            return []

        z_scores = np.abs((prices - mean) / std)
        outliers = np.where(z_scores > threshold)[0].tolist()

        return outliers

    @staticmethod
    def detect_stale_prices(prices: list[float], threshold: int = 5) -> list[int]:
        """Detect periods of unchanged prices (potential stale data).

        Args:
            prices: List of prices
            threshold: Number of identical values before flagging

        Returns:
            List of stale price indices
        """
        stale = []
        consecutive = 0
        last_price = None

        for i, price in enumerate(prices):
            if price == last_price:
                consecutive += 1
            else:
                consecutive = 0

            if consecutive >= threshold:
                stale.append(i)

            last_price = price

        return stale

    @staticmethod
    def validate_ohlc_consistency(open_: float, high: float, low: float, close: float) -> tuple[bool, str]:
        """Validate OHLC data consistency.

        Args:
            open_: Opening price
            high: High price
            low: Low price
            close: Closing price

        Returns:
            (is_valid, error_message)
        """
        if not (high >= open_ and high >= close and high >= low):
            return False, "High price is not highest"

        if not (low <= open_ and low <= close and low <= high):
            return False, "Low price is not lowest"

        if any(p <= 0 for p in [open_, high, low, close]):
            return False, "Negative or zero price detected"

        return True, ""

    @staticmethod
    def suggest_data_cleaning(issues: list[str]) -> list[str]:
        """Suggest how to handle detected issues."""
        suggestions = []

        if "gaps" in str(issues):
            suggestions.append("Investigate price gaps - may indicate stock splits or corporate actions")

        if "outliers" in str(issues):
            suggestions.append("Review outlier prices - may be data entry errors")

        if "stale" in str(issues):
            suggestions.append("Check for stale data - market may have been closed")

        return suggestions
