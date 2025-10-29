"""Slippage modeling for more realistic backtests."""
import logging

logger = logging.getLogger(__name__)


class SlippageModel:
    """Model execution slippage for trades."""

    @staticmethod
    def fixed_slippage(price: float, slippage_bps: int = 5) -> float:
        """Apply fixed basis points slippage.

        Args:
            price: Execution price
            slippage_bps: Slippage in basis points (default 5 = 0.05%)

        Returns:
            Adjusted price with slippage
        """
        slippage_pct = slippage_bps / 10000
        return price * (1 + slippage_pct)

    @staticmethod
    def volume_dependent_slippage(
        price: float,
        order_size: int,
        daily_volume: int,
        base_slippage_bps: int = 2,
    ) -> float:
        """Calculate slippage based on order size vs daily volume.

        Larger orders relative to volume get worse slippage.

        Args:
            price: Execution price
            order_size: Number of shares ordered
            daily_volume: Daily trading volume
            base_slippage_bps: Base slippage in basis points

        Returns:
            Adjusted price with slippage
        """
        if daily_volume == 0:
            return price

        # Order size as % of daily volume
        volume_ratio = order_size / daily_volume

        # Slippage increases with order size
        slippage_bps = base_slippage_bps + (volume_ratio * 50)  # +50bps per % of volume

        return SlippageModel.fixed_slippage(price, min(int(slippage_bps), 100))

    @staticmethod
    def bid_ask_slippage(
        price: float,
        bid_ask_spread_pct: float = 0.01,
        buy_side: bool = True,
    ) -> float:
        """Model bid-ask spread slippage.

        Args:
            price: Mid price
            bid_ask_spread_pct: Spread as % (default 0.01% = 1 bp)
            buy_side: True for buy orders (pay ask), False for sell (get bid)

        Returns:
            Adjusted price
        """
        half_spread = (price * bid_ask_spread_pct) / 2

        if buy_side:
            return price + half_spread  # Pay ask
        else:
            return price - half_spread  # Get bid

    @staticmethod
    def market_impact_slippage(
        price: float,
        order_value: float,
        market_cap: float,
        impact_elasticity: float = 0.5,
    ) -> float:
        """Model market impact slippage.

        Larger orders move the market.

        Args:
            price: Current price
            order_value: Dollar value of order
            market_cap: Market cap of stock
            impact_elasticity: How much price moves with order size

        Returns:
            Adjusted price
        """
        if market_cap == 0:
            return price

        order_ratio = order_value / market_cap
        impact = (order_ratio ** impact_elasticity) * 0.01  # Up to 1% impact

        return price * (1 + impact)
