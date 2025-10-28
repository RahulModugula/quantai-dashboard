"""Portfolio rebalancing suggestions and helper tools."""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RebalanceAction:
    """A single rebalancing action (buy or sell)."""

    ticker: str
    action: str  # "BUY" or "SELL"
    current_pct: float  # Current allocation %
    target_pct: float  # Target allocation %
    shares_to_trade: int
    estimated_value: float
    reason: str


class PortfolioRebalancer:
    """Suggest portfolio rebalancing actions."""

    @staticmethod
    def suggest_equal_weight(positions: dict, portfolio_value: float) -> list[RebalanceAction]:
        """Suggest equal-weight rebalancing for current holdings.

        Args:
            positions: {ticker: Position} dict
            portfolio_value: Total portfolio value

        Returns:
            List of RebalanceAction objects
        """
        if not positions or portfolio_value == 0:
            return []

        actions = []
        target_weight = 1.0 / len(positions)

        for ticker, position in positions.items():
            current_value = position.cost_basis
            current_pct = current_value / portfolio_value if portfolio_value > 0 else 0
            target_value = portfolio_value * target_weight
            diff_value = target_value - current_value

            if abs(diff_value) < 100:  # Skip tiny adjustments
                continue

            shares_to_trade = int(diff_value / (position.avg_price or 1))

            action = "BUY" if diff_value > 0 else "SELL"
            actions.append(
                RebalanceAction(
                    ticker=ticker,
                    action=action,
                    current_pct=current_pct * 100,
                    target_pct=target_weight * 100,
                    shares_to_trade=abs(shares_to_trade),
                    estimated_value=abs(diff_value),
                    reason=f"Align {ticker} from {current_pct*100:.1f}% to {target_weight*100:.1f}%",
                )
            )

        return sorted(actions, key=lambda a: a.estimated_value, reverse=True)

    @staticmethod
    def suggest_risk_reduction(positions: dict, portfolio_value: float, max_position_pct: float = 0.30) -> list[RebalanceAction]:
        """Suggest selling positions that exceed max allocation.

        Args:
            positions: {ticker: Position} dict
            portfolio_value: Total portfolio value
            max_position_pct: Maximum allowed position size (default 30%)

        Returns:
            List of RebalanceAction objects (mostly SELLs)
        """
        if not positions or portfolio_value == 0:
            return []

        actions = []
        max_value = portfolio_value * max_position_pct

        for ticker, position in positions.items():
            current_value = position.cost_basis
            if current_value > max_value:
                excess = current_value - max_value
                shares_to_sell = int(excess / (position.avg_price or 1))

                actions.append(
                    RebalanceAction(
                        ticker=ticker,
                        action="SELL",
                        current_pct=(current_value / portfolio_value * 100),
                        target_pct=(max_value / portfolio_value * 100),
                        shares_to_trade=shares_to_sell,
                        estimated_value=excess,
                        reason=f"Reduce {ticker} from {current_value/portfolio_value*100:.1f}% to {max_position_pct*100:.0f}%",
                    )
                )

        return sorted(actions, key=lambda a: a.estimated_value, reverse=True)

    @staticmethod
    def estimate_tax_impact(actions: list[RebalanceAction], cost_basis_pct: float = 1.0) -> dict:
        """Estimate tax impact of rebalancing actions.

        Args:
            actions: List of rebalance actions
            cost_basis_pct: Cost basis as % of current value (for gains/losses)

        Returns:
            Dict with estimated capital gains, losses, and net tax liability
        """
        long_term_gains = 0.0
        long_term_losses = 0.0
        short_term_gains = 0.0
        short_term_losses = 0.0

        for action in actions:
            if action.action != "SELL":
                continue

            unrealized_gain = action.estimated_value * (1 - cost_basis_pct)
            if unrealized_gain > 0:
                # Assume 60% long-term, 40% short-term
                long_term_gains += unrealized_gain * 0.6
                short_term_gains += unrealized_gain * 0.4
            else:
                loss = abs(unrealized_gain)
                long_term_losses += loss * 0.6
                short_term_losses += loss * 0.4

        # Rough tax estimates (not legal advice)
        lt_tax = long_term_gains * 0.15 if long_term_gains > 0 else 0
        st_tax = short_term_gains * 0.37 if short_term_gains > 0 else 0

        return {
            "long_term_gains": round(long_term_gains, 2),
            "long_term_losses": round(long_term_losses, 2),
            "short_term_gains": round(short_term_gains, 2),
            "short_term_losses": round(short_term_losses, 2),
            "estimated_lt_tax": round(lt_tax, 2),
            "estimated_st_tax": round(st_tax, 2),
            "total_estimated_tax": round(lt_tax + st_tax, 2),
            "note": "Estimates only - consult a tax professional",
        }
