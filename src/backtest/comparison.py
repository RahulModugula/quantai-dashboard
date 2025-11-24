"""Tools for comparing multiple backtest results and analyzing differences."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BacktestDiff:
    """Differences between two backtest results."""

    name_a: str
    name_b: str
    total_return_diff: float  # percentage points
    sharpe_diff: float
    max_drawdown_diff: float  # percentage points
    win_rate_diff: float  # percentage points
    trade_count_diff: int

    def summary(self) -> str:
        """Get human-readable comparison summary."""
        return (
            f"Comparison: {self.name_a} vs {self.name_b}\n"
            f"  Return diff: {self.total_return_diff:+.2f}%\n"
            f"  Sharpe diff: {self.sharpe_diff:+.2f}\n"
            f"  Max drawdown diff: {self.max_drawdown_diff:+.2f}%\n"
            f"  Win rate diff: {self.win_rate_diff:+.2f}%\n"
            f"  Trade count diff: {self.trade_count_diff:+d}"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "comparison": f"{self.name_a} vs {self.name_b}",
            "total_return_diff_pct": round(self.total_return_diff, 2),
            "sharpe_diff": round(self.sharpe_diff, 3),
            "max_drawdown_diff_pct": round(self.max_drawdown_diff, 2),
            "win_rate_diff_pct": round(self.win_rate_diff, 2),
            "trade_count_diff": self.trade_count_diff,
        }


def compare_backtests(
    result_a: dict, result_b: dict, name_a: str = "A", name_b: str = "B"
) -> BacktestDiff:
    """Compare two backtest results and return key differences.

    Args:
        result_a: First backtest result dict with metrics
        result_b: Second backtest result dict with metrics
        name_a: Label for first backtest
        name_b: Label for second backtest

    Returns:
        BacktestDiff with key differences
    """
    metrics_a = result_a.get("metrics", {})
    metrics_b = result_b.get("metrics", {})

    total_return_a = metrics_a.get("total_return", 0.0) * 100
    total_return_b = metrics_b.get("total_return", 0.0) * 100

    sharpe_a = metrics_a.get("sharpe_ratio", 0.0)
    sharpe_b = metrics_b.get("sharpe_ratio", 0.0)

    max_dd_a = abs(metrics_a.get("max_drawdown", 0.0)) * 100
    max_dd_b = abs(metrics_b.get("max_drawdown", 0.0)) * 100

    win_rate_a = metrics_a.get("win_rate", 0.0) * 100
    win_rate_b = metrics_b.get("win_rate", 0.0) * 100

    trades_a = metrics_a.get("total_trades", 0)
    trades_b = metrics_b.get("total_trades", 0)

    return BacktestDiff(
        name_a=name_a,
        name_b=name_b,
        total_return_diff=total_return_b - total_return_a,
        sharpe_diff=sharpe_b - sharpe_a,
        max_drawdown_diff=max_dd_a - max_dd_b,  # Improvement is positive
        win_rate_diff=win_rate_b - win_rate_a,
        trade_count_diff=trades_b - trades_a,
    )


def find_outlier_trades(trades: list[dict], quantile: float = 0.95) -> list[dict]:
    """Identify unusually large or small trades.

    Args:
        trades: List of trade dicts with 'quantity' and 'entry_price' fields
        quantile: Percentile threshold (default 95th percentile)

    Returns:
        List of trades that are outliers
    """
    if not trades or len(trades) < 10:
        return []

    import numpy as np

    sizes = [abs(t.get("quantity", 0)) for t in trades]
    threshold = np.quantile(sizes, quantile)

    outliers = [t for t in trades if abs(t.get("quantity", 0)) > threshold]
    logger.info(f"Found {len(outliers)} outlier trades (>{threshold:.0f} shares)")

    return outliers
