"""Advanced risk metrics and exposure analysis."""

import numpy as np


class RiskMetrics:
    """Calculate advanced portfolio risk metrics."""

    @staticmethod
    def value_at_risk(returns: list[float], confidence_level: float = 0.95) -> float:
        """Calculate Value at Risk (VaR).

        Args:
            returns: List of portfolio returns
            confidence_level: Confidence level (default 95%)

        Returns:
            VaR at specified confidence level
        """
        return np.percentile(returns, (1 - confidence_level) * 100)

    @staticmethod
    def conditional_var(returns: list[float], confidence_level: float = 0.95) -> float:
        """Calculate Conditional VaR (CVaR / Expected Shortfall).

        Average loss beyond VaR.

        Args:
            returns: List of portfolio returns
            confidence_level: Confidence level (default 95%)

        Returns:
            CVaR at specified confidence level
        """
        var = RiskMetrics.value_at_risk(returns, confidence_level)
        return np.mean([r for r in returns if r <= var])

    @staticmethod
    def maximum_loss(returns: list[float]) -> float:
        """Get worst-case daily loss."""
        return min(returns) if returns else 0.0

    @staticmethod
    def average_loss(returns: list[float]) -> float:
        """Get average of negative returns."""
        losses = [r for r in returns if r < 0]
        return np.mean(losses) if losses else 0.0

    @staticmethod
    def tail_ratio(returns: list[float]) -> float:
        """Calculate ratio of extreme gains to extreme losses.

        Higher is better (more upside than downside).

        Args:
            returns: List of returns

        Returns:
            Tail ratio
        """
        losses = [abs(r) for r in returns if r < 0]
        gains = [r for r in returns if r > 0]

        avg_loss = np.mean(losses) if losses else 0.0001
        avg_gain = np.mean(gains) if gains else 0.0001

        return avg_gain / avg_loss

    @staticmethod
    def omega_ratio(returns: list[float], threshold: float = 0.0) -> float:
        """Calculate Omega ratio (probability of exceeding threshold).

        Args:
            returns: List of returns
            threshold: Minimum acceptable return (default 0%)

        Returns:
            Omega ratio
        """
        returns = np.array(returns)
        excess = returns - threshold

        gains = sum([r for r in excess if r > 0])
        losses = sum([abs(r) for r in excess if r < 0])

        if losses == 0:
            return float("inf") if gains > 0 else 0.0

        return gains / losses
