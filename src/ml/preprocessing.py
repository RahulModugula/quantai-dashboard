"""ML data preprocessing pipeline."""

import numpy as np


def remove_outliers_iqr(data: np.ndarray, multiplier: float = 1.5) -> np.ndarray:
    """Remove outliers using IQR method."""
    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)
    IQR = Q3 - Q1
    lower = Q1 - multiplier * IQR
    upper = Q3 + multiplier * IQR
    return data[(data >= lower) & (data <= upper)]


def handle_missing_values(data: np.ndarray, method: str = "forward_fill") -> np.ndarray:
    """Handle missing values in time series."""
    if method == "forward_fill":
        mask = np.isnan(data)
        idx = np.where(~mask, np.arange(mask.size), 0)
        idx = np.maximum.accumulate(idx)
        return data[idx]
    elif method == "interpolate":
        return np.interp(np.arange(len(data)), np.where(~np.isnan(data))[0], data[~np.isnan(data)])
    return data


def create_lagged_features(data: np.ndarray, lags: list[int]) -> np.ndarray:
    """Create lagged features for time series."""
    features = [data]
    for lag in lags:
        features.append(np.roll(data, lag))
    return np.column_stack(features)[max(lags) :]
