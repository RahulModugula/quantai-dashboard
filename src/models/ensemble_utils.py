"""Helper utilities for ensemble model operations."""

import logging

logger = logging.getLogger(__name__)


def average_model_predictions(predictions: dict[str, list]) -> list:
    """Average predictions from multiple models.

    Args:
        predictions: {model_name: [predictions]} dict

    Returns:
        Averaged predictions
    """
    if not predictions:
        return []

    num_samples = len(next(iter(predictions.values())))
    averaged = []

    for i in range(num_samples):
        values = [preds[i] for preds in predictions.values()]
        averaged.append(sum(values) / len(values))

    return averaged


def get_prediction_confidence(probability: float) -> float:
    """Calculate confidence score from probability.

    Confidence is highest at extremes (0 or 1), lowest at 0.5.
    Formula: 2 * abs(probability - 0.5)
    """
    return 2 * abs(probability - 0.5)


def signal_strength(probability: float) -> str:
    """Get human-readable signal strength."""
    if probability < 0.3:
        return "STRONG_SELL"
    elif probability < 0.4:
        return "SELL"
    elif probability < 0.55:
        return "HOLD"
    elif probability < 0.7:
        return "BUY"
    else:
        return "STRONG_BUY"
