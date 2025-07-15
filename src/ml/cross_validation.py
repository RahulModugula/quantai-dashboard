"""Cross-validation utilities for model evaluation."""
import numpy as np


def time_series_split(data: np.ndarray, n_splits: int = 5):
    """Time series aware cross-validation split.

    Splits data chronologically to avoid look-ahead bias.

    Args:
        data: Time series data
        n_splits: Number of splits

    Returns:
        List of (train_idx, test_idx) tuples
    """
    n_samples = len(data)
    test_size = n_samples // (n_splits + 1)

    splits = []
    for i in range(1, n_splits + 1):
        test_start = i * test_size
        test_end = test_start + test_size
        train_idx = np.arange(0, test_start)
        test_idx = np.arange(test_start, min(test_end, n_samples))
        splits.append((train_idx, test_idx))

    return splits


def walk_forward_split(data: np.ndarray, train_size: int, test_size: int):
    """Walk-forward cross-validation for time series.

    Args:
        data: Time series data
        train_size: Training set size
        test_size: Test set size

    Returns:
        List of (train_idx, test_idx) tuples
    """
    splits = []
    i = 0
    while i + train_size + test_size <= len(data):
        train_idx = np.arange(i, i + train_size)
        test_idx = np.arange(i + train_size, i + train_size + test_size)
        splits.append((train_idx, test_idx))
        i += test_size

    return splits
