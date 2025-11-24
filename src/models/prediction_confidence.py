"""Calculate and interpret prediction confidence scores."""

import numpy as np


class ConfidenceCalculator:
    """Calculate confidence in ML predictions."""

    @staticmethod
    def margin_of_certainty(probability: float) -> float:
        """Calculate how far probability is from 0.5 (neutral).

        Args:
            probability: Prediction probability (0-1)

        Returns:
            Margin of certainty (0-1)
        """
        return abs(probability - 0.5) * 2

    @staticmethod
    def ensemble_agreement(predictions: list[float]) -> float:
        """Calculate agreement among ensemble members.

        Args:
            predictions: List of probabilities from different models

        Returns:
            Agreement score (0-1)
        """
        if not predictions:
            return 0.0

        # Convert to discrete predictions
        discrete = [1 if p > 0.5 else 0 for p in predictions]
        agreement_rate = max(discrete.count(0), discrete.count(1)) / len(discrete)

        return agreement_rate

    @staticmethod
    def prediction_entropy(predictions: list[float]) -> float:
        """Calculate entropy (uncertainty) of predictions.

        Higher entropy = more uncertainty.

        Args:
            predictions: List of probabilities

        Returns:
            Entropy value
        """
        if not predictions:
            return 1.0

        # Average probability
        avg_prob = np.mean(predictions)

        # Entropy: -p*log(p) - (1-p)*log(1-p)
        if avg_prob <= 0 or avg_prob >= 1:
            return 0.0

        entropy = -(avg_prob * np.log(avg_prob) + (1 - avg_prob) * np.log(1 - avg_prob))

        # Normalize to 0-1
        return entropy / np.log(2)

    @staticmethod
    def get_confidence_level(probability: float, ensemble_agreement: float = 1.0) -> str:
        """Get human-readable confidence level.

        Args:
            probability: Prediction probability
            ensemble_agreement: Model agreement score

        Returns:
            Confidence level string
        """
        margin = ConfidenceCalculator.margin_of_certainty(probability)
        combined_score = margin * ensemble_agreement

        if combined_score >= 0.80:
            return "VERY_HIGH"
        elif combined_score >= 0.60:
            return "HIGH"
        elif combined_score >= 0.40:
            return "MEDIUM"
        elif combined_score >= 0.20:
            return "LOW"
        else:
            return "VERY_LOW"
