"""Advanced feature engineering for ML models."""

import numpy as np


class FeatureEngineer:
    """Create advanced features from price data."""

    @staticmethod
    def create_momentum_features(prices: list[float], windows: list[int] = [5, 10, 20]) -> dict:
        """Create momentum features at different time windows.

        Args:
            prices: List of closing prices
            windows: Time windows for momentum calculation

        Returns:
            Dictionary of momentum features
        """
        features = {}

        for window in windows:
            if len(prices) > window:
                momentum = (prices[-1] - prices[-window]) / prices[-window]
                features[f"momentum_{window}"] = momentum

        return features

    @staticmethod
    def create_volatility_features(returns: list[float], windows: list[int] = [5, 10, 20]) -> dict:
        """Create volatility features at different time windows.

        Args:
            returns: List of returns
            windows: Time windows for volatility calculation

        Returns:
            Dictionary of volatility features
        """
        features = {}
        returns = np.array(returns)

        for window in windows:
            if len(returns) > window:
                volatility = np.std(returns[-window:])
                features[f"volatility_{window}"] = volatility

        return features

    @staticmethod
    def create_trend_features(prices: list[float]) -> dict:
        """Create trend-based features."""
        if len(prices) < 20:
            return {}

        prices = np.array(prices)
        short_trend = np.mean(prices[-5:])
        medium_trend = np.mean(prices[-10:])
        long_trend = np.mean(prices[-20:])

        return {
            "short_trend": short_trend,
            "medium_trend": medium_trend,
            "long_trend": long_trend,
            "trend_alignment": 1 if short_trend > medium_trend > long_trend else 0,
        }

    @staticmethod
    def create_mean_reversion_features(prices: list[float], window: int = 20) -> dict:
        """Create mean reversion features."""
        if len(prices) < window:
            return {}

        prices = np.array(prices)
        mean = np.mean(prices[-window:])
        current = prices[-1]

        deviation = (current - mean) / mean
        zscore = deviation / np.std(prices[-window:]) if np.std(prices[-window:]) > 0 else 0

        return {
            "mean_deviation": deviation,
            "zscore": zscore,
            "overextended": 1 if abs(zscore) > 2 else 0,
        }

    @staticmethod
    def create_volume_features(prices: list[float], volumes: list[float]) -> dict:
        """Create volume-based features."""
        if len(prices) < 10 or len(volumes) < 10:
            return {}

        volumes = np.array(volumes)
        prices = np.array(prices)

        avg_volume = np.mean(volumes[-10:])
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

        return {
            "volume_ratio": volume_ratio,
            "high_volume": 1 if volume_ratio > 1.5 else 0,
            "avg_volume": avg_volume,
        }
