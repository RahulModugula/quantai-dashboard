"""Volume-weighted slippage model for realistic fill simulation.

Three models are provided:
- NoSlippage: passthrough; useful for baseline/testing comparisons.
- ParticipationRate: fill price moves against you proportional to order_size / avg_volume.
- SquareRootImpact: Kyle's square-root market impact (more conservative for large orders).

All models clamp slippage at max_slippage_bps (default 50bps = 0.5%) to prevent
unrealistic fills on illiquid names.  50bps is intentionally conservative — real
impact on liquid large-caps is typically <5bps for the order sizes this system uses.
"""

import math
from abc import ABC, abstractmethod


class SlippageModel(ABC):
    """Base class for slippage models."""

    @abstractmethod
    def apply(self, price: float, order_value: float, avg_daily_volume: float, side: str) -> float:
        """Return adjusted fill price (higher for buys, lower for sells).

        Args:
            price: Market price at time of fill.
            order_value: Notional value of the order in dollars.
            avg_daily_volume: Average daily traded volume in shares.
            side: "buy" or "sell".

        Returns:
            Adjusted fill price after slippage.
        """


class NoSlippage(SlippageModel):
    """Passthrough model — returns price unchanged. Useful for testing."""

    def apply(self, price: float, order_value: float, avg_daily_volume: float, side: str) -> float:
        return price


class ParticipationRateSlippage(SlippageModel):
    """Fill price moves against you proportional to order_size / avg_daily_volume.

    slippage_pct = participation_rate * (order_value / (avg_daily_volume * price)) * impact_per_pct
    Clamped to max_slippage_bps basis points.
    """

    def __init__(
        self,
        participation_rate: float = 0.1,
        impact_per_pct: float = 0.002,
        max_slippage_bps: float = 50.0,
    ):
        self.participation_rate = participation_rate
        self.impact_per_pct = impact_per_pct
        self.max_slippage_pct = max_slippage_bps / 10_000.0

    def apply(self, price: float, order_value: float, avg_daily_volume: float, side: str) -> float:
        adv_value = avg_daily_volume * price
        if adv_value <= 0:
            return price

        participation = order_value / adv_value
        slippage_pct = self.participation_rate * participation * self.impact_per_pct
        slippage_pct = min(slippage_pct, self.max_slippage_pct)

        if side == "buy":
            return price * (1.0 + slippage_pct)
        else:
            return price * (1.0 - slippage_pct)


class SquareRootImpact(SlippageModel):
    """Kyle's square-root market impact model.

    slippage_pct = impact_coeff * volatility * sqrt(order_value / (avg_daily_volume * price))
    Clamped to max_slippage_bps basis points.
    """

    def __init__(
        self,
        volatility: float = 0.02,
        impact_coeff: float = 0.1,
        max_slippage_bps: float = 50.0,
    ):
        self.volatility = volatility
        self.impact_coeff = impact_coeff
        self.max_slippage_pct = max_slippage_bps / 10_000.0

    def apply(self, price: float, order_value: float, avg_daily_volume: float, side: str) -> float:
        adv_value = avg_daily_volume * price
        if adv_value <= 0:
            return price

        participation = order_value / adv_value
        slippage_pct = self.impact_coeff * self.volatility * math.sqrt(participation)
        slippage_pct = min(slippage_pct, self.max_slippage_pct)

        if side == "buy":
            return price * (1.0 + slippage_pct)
        else:
            return price * (1.0 - slippage_pct)
