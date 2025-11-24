"""Detailed trade-level analysis and categorization."""

import logging
from enum import Enum

logger = logging.getLogger(__name__)


class TradeType(str, Enum):
    """Classification of trades."""

    WINNING = "WINNING"
    LOSING = "LOSING"
    BREAKEVEN = "BREAKEVEN"


class TradeAnalyzer:
    """Analyze individual trades for patterns and insights."""

    @staticmethod
    def classify_trade(entry_price: float, exit_price: float, commission: float = 0) -> TradeType:
        """Classify a trade as winning, losing, or breakeven."""
        net_profit = (exit_price - entry_price) - commission

        if net_profit > 0:
            return TradeType.WINNING
        elif net_profit < 0:
            return TradeType.LOSING
        else:
            return TradeType.BREAKEVEN

    @staticmethod
    def analyze_trades(trades: list[dict]) -> dict:
        """Comprehensive analysis of trade performance."""
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "breakeven_trades": 0,
                "win_rate": 0.0,
            }

        win_count = 0
        loss_count = 0
        breakeven_count = 0
        total_profit = 0
        max_profit = 0
        max_loss = 0

        for trade in trades:
            entry = trade.get("entry_price", 0)
            exit_val = trade.get("exit_price", 0)
            commission = trade.get("commission", 0)

            pnl = (exit_val - entry) - commission

            if pnl > 0:
                win_count += 1
                max_profit = max(max_profit, pnl)
            elif pnl < 0:
                loss_count += 1
                max_loss = min(max_loss, pnl)
            else:
                breakeven_count += 1

            total_profit += pnl

        total = len(trades)
        win_rate = (win_count / total * 100) if total > 0 else 0

        return {
            "total_trades": total,
            "winning_trades": win_count,
            "losing_trades": loss_count,
            "breakeven_trades": breakeven_count,
            "win_rate": round(win_rate, 2),
            "total_profit": round(total_profit, 2),
            "biggest_win": round(max_profit, 2),
            "biggest_loss": round(max_loss, 2),
            "profit_factor": round(abs(total_profit / max_loss), 2) if max_loss != 0 else 0.0,
        }

    @staticmethod
    def find_winning_patterns(trades: list[dict], min_trades: int = 5) -> dict:
        """Identify patterns in winning trades."""
        winning_trades = [
            t for t in trades if (t.get("exit_price", 0) - t.get("entry_price", 0)) > 0
        ]

        if len(winning_trades) < min_trades:
            return {"message": f"Not enough winning trades (need {min_trades})"}

        # Analyze common characteristics
        avg_hold_time = sum(t.get("hold_days", 1) for t in winning_trades) / len(winning_trades)
        avg_profit = sum(t.get("profit", 0) for t in winning_trades) / len(winning_trades)

        return {
            "winning_trades_count": len(winning_trades),
            "average_hold_time_days": round(avg_hold_time, 1),
            "average_profit_per_trade": round(avg_profit, 2),
            "recommendation": "Focus on these characteristics to improve strategy",
        }
