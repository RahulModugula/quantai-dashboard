"""Generate comprehensive performance reports."""
import logging

logger = logging.getLogger(__name__)


class PerformanceReport:
    """Generate detailed performance analysis reports."""

    def __init__(self, trades: list[dict], equity_curve: list[float]):
        self.trades = trades
        self.equity_curve = equity_curve

    def generate_summary(self) -> dict:
        """Generate performance summary."""
        if not self.trades:
            return {"error": "No trades to analyze"}

        winning_trades = [t for t in self.trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in self.trades if t.get("pnl", 0) < 0]

        total_pnl = sum(t.get("pnl", 0) for t in self.trades)
        total_trades = len(self.trades)
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0

        return {
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(win_rate, 4),
            "total_pnl": round(total_pnl, 2),
            "avg_win": round(sum(t.get("pnl", 0) for t in winning_trades) / len(winning_trades), 2) if winning_trades else 0,
            "avg_loss": round(sum(t.get("pnl", 0) for t in losing_trades) / len(losing_trades), 2) if losing_trades else 0,
        }

    def monthly_breakdown(self) -> dict:
        """Break down performance by month."""
        monthly = {}

        for trade in self.trades:
            # Would extract month from trade timestamp
            month = "2025-06"  # Placeholder

            if month not in monthly:
                monthly[month] = {"trades": 0, "pnl": 0}

            monthly[month]["trades"] += 1
            monthly[month]["pnl"] += trade.get("pnl", 0)

        return monthly

    def get_report(self) -> str:
        """Get full text report."""
        summary = self.generate_summary()

        report = [
            "=" * 60,
            "PERFORMANCE REPORT",
            "=" * 60,
            f"Total Trades: {summary.get('total_trades', 0)}",
            f"Win Rate: {summary.get('win_rate', 0):.2%}",
            f"Total PnL: ${summary.get('total_pnl', 0):.2f}",
            "=" * 60,
        ]

        return "\n".join(report)
