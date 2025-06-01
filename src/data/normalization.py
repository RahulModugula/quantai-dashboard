"""Feature normalization and scaling utilities."""
import logging
import numpy as np

logger = logging.getLogger(__name__)


class FeatureNormalizer:
    """Normalize features for consistent ML model input."""

    @staticmethod
    def minmax_scale(data: np.ndarray, min_val: float = 0, max_val: float = 1) -> tuple[np.ndarray, tuple]:
        """MinMax scaling to [min_val, max_val] range.

        Args:
            data: Input array
            min_val: Target minimum
            max_val: Target maximum

        Returns:
            Scaled data and (original_min, original_max) for inverse transform
        """
        original_min = np.min(data)
        original_max = np.max(data)

        if original_max == original_min:
            return np.full_like(data, (min_val + max_val) / 2), (original_min, original_max)

        scaled = (data - original_min) / (original_max - original_min)
        scaled = scaled * (max_val - min_val) + min_val

        return scaled, (original_min, original_max)

    @staticmethod
    def inverse_minmax(data: np.ndarray, original_min: float, original_max: float) -> np.ndarray:
        """Inverse MinMax scaling."""
        return data * (original_max - original_min) + original_min

    @staticmethod
    def zscore_normalize(data: np.ndarray) -> tuple[np.ndarray, tuple]:
        """Z-score normalization (zero mean, unit variance).

        Args:
            data: Input array

        Returns:
            Normalized data and (mean, std) for inverse transform
        """
        mean = np.mean(data)
        std = np.std(data)

        if std == 0:
            return np.zeros_like(data), (mean, std)

        normalized = (data - mean) / std

        return normalized, (mean, std)

    @staticmethod
    def inverse_zscore(data: np.ndarray, mean: float, std: float) -> np.ndarray:
        """Inverse Z-score normalization."""
        return data * std + mean

    @staticmethod
    def robust_scale(data: np.ndarray) -> tuple[np.ndarray, tuple]:
        """Robust scaling using median and IQR.

        Less sensitive to outliers than z-score.

        Args:
            data: Input array

        Returns:
            Scaled data and (median, iqr) for inverse transform
        """
        median = np.median(data)
        q75 = np.percentile(data, 75)
        q25 = np.percentile(data, 25)
        iqr = q75 - q25

        if iqr == 0:
            return np.zeros_like(data), (median, iqr)

        scaled = (data - median) / iqr

        return scaled, (median, iqr)

    @staticmethod
    def log_transform(data: np.ndarray, epsilon: float = 1e-8) -> np.ndarray:
        """Log transformation for right-skewed data.

        Args:
            data: Input array (must be positive)
            epsilon: Small value to avoid log(0)

        Returns:
            Log-transformed data
        """
        return np.log(np.maximum(data, epsilon))
