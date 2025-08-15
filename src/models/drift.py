"""Model performance monitoring and drift detection.

Tracks prediction accuracy over time and flags when recent accuracy
drops significantly below historical average.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def detect_drift(
    predictions: pd.DataFrame,
    lookback_window: int = 63,
    baseline_window: int = 252,
    threshold: float = 0.05,
) -> dict:
    """Check if recent model accuracy has degraded vs historical baseline.

    Args:
        predictions: DataFrame with columns [date, prediction, actual]
        lookback_window: Recent window to evaluate (default ~3 months)
        baseline_window: Historical window for baseline (default ~1 year)
        threshold: Minimum accuracy drop to flag as drift

    Returns:
        Dict with drift status, recent and baseline accuracy
    """
    if len(predictions) < lookback_window + baseline_window:
        return {"drift_detected": False, "reason": "insufficient data"}

    predictions = predictions.sort_values("date").reset_index(drop=True)
    correct = (predictions["prediction"] == predictions["actual"]).astype(int)

    recent = correct.tail(lookback_window)
    baseline = correct.iloc[-(lookback_window + baseline_window):-lookback_window]

    recent_acc = float(recent.mean())
    baseline_acc = float(baseline.mean())
    delta = baseline_acc - recent_acc

    drift_detected = delta > threshold

    if drift_detected:
        logger.warning(
            f"Model drift detected: recent accuracy {recent_acc:.3f} "
            f"vs baseline {baseline_acc:.3f} (delta={delta:.3f})"
        )

    return {
        "drift_detected": drift_detected,
        "recent_accuracy": round(recent_acc, 4),
        "baseline_accuracy": round(baseline_acc, 4),
        "accuracy_delta": round(delta, 4),
        "lookback_days": lookback_window,
        "baseline_days": baseline_window,
    }


def rolling_accuracy(
    predictions: pd.DataFrame,
    window: int = 63,
) -> pd.Series:
    """Compute rolling prediction accuracy over a trailing window."""
    correct = (predictions["prediction"] == predictions["actual"]).astype(int)
    return correct.rolling(window=window).mean()
