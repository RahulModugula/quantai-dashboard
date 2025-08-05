"""Drawdown and loss analysis utilities."""
import numpy as np


class DrawdownAnalyzer:
    """Analyze portfolio drawdowns in detail."""

    @staticmethod
    def calculate_drawdown_periods(equity_curve: list[float]) -> list[dict]:
        """Identify all drawdown periods in equity curve.

        Args:
            equity_curve: List of portfolio values over time

        Returns:
            List of drawdown periods with start, end, magnitude, and duration
        """
        if len(equity_curve) < 2:
            return []

        equity = np.array(equity_curve)
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max

        drawdown_periods = []
        in_drawdown = False
        start_idx = 0
        peak_value = 0

        for i in range(len(drawdown)):
            if drawdown[i] < 0 and not in_drawdown:
                in_drawdown = True
                start_idx = i
                peak_value = equity[i]
            elif drawdown[i] >= 0 and in_drawdown:
                in_drawdown = False
                end_idx = i
                drawdown_periods.append({
                    "start_idx": start_idx,
                    "end_idx": end_idx,
                    "duration": end_idx - start_idx,
                    "peak_value": float(peak_value),
                    "trough_value": float(np.min(equity[start_idx:end_idx])),
                    "magnitude": float(np.min(drawdown[start_idx:end_idx])),
                    "recovery_time": end_idx - start_idx,
                })

        return drawdown_periods

    @staticmethod
    def longest_drawdown(equity_curve: list[float]) -> dict:
        """Find the longest drawdown period."""
        periods = DrawdownAnalyzer.calculate_drawdown_periods(equity_curve)

        if not periods:
            return {"message": "No drawdowns detected"}

        longest = max(periods, key=lambda x: x["duration"])

        return {
            "duration_days": longest["duration"],
            "magnitude_pct": round(longest["magnitude"] * 100, 2),
            "recovery_time": longest["recovery_time"],
        }

    @staticmethod
    def drawdown_statistics(equity_curve: list[float]) -> dict:
        """Get comprehensive drawdown statistics."""
        periods = DrawdownAnalyzer.calculate_drawdown_periods(equity_curve)

        if not periods:
            return {
                "total_drawdown_periods": 0,
                "average_duration": 0,
                "average_magnitude": 0,
            }

        durations = [p["duration"] for p in periods]
        magnitudes = [abs(p["magnitude"]) for p in periods]

        return {
            "total_drawdown_periods": len(periods),
            "average_duration": round(np.mean(durations), 1),
            "median_duration": round(np.median(durations), 1),
            "average_magnitude_pct": round(np.mean(magnitudes) * 100, 2),
            "median_magnitude_pct": round(np.median(magnitudes) * 100, 2),
            "worst_magnitude_pct": round(max(magnitudes) * 100, 2),
        }

    @staticmethod
    def calmar_ratio_detailed(annual_return: float, max_drawdown: float, days: int = 252) -> float:
        """Calculate Calmar ratio (return / max drawdown)."""
        if max_drawdown == 0:
            return 0.0

        return annual_return / abs(max_drawdown)
