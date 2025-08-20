"""Different order types and execution strategies."""
from enum import Enum


class OrderType(str, Enum):
    """Order types."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderSide(str, Enum):
    """Order side."""

    BUY = "BUY"
    SELL = "SELL"


class Order:
    """Represents a single order."""

    def __init__(
        self,
        ticker: str,
        side: OrderSide,
        quantity: int,
        order_type: OrderType = OrderType.MARKET,
        limit_price: float = None,
        stop_price: float = None,
    ):
        self.ticker = ticker
        self.side = side
        self.quantity = quantity
        self.order_type = order_type
        self.limit_price = limit_price
        self.stop_price = stop_price
        self.status = "PENDING"

    def can_execute(self, current_price: float) -> bool:
        """Check if order can execute at current price."""
        if self.order_type == OrderType.MARKET:
            return True
        elif self.order_type == OrderType.LIMIT:
            if self.side == OrderSide.BUY:
                return current_price <= self.limit_price
            else:
                return current_price >= self.limit_price
        elif self.order_type == OrderType.STOP:
            if self.side == OrderSide.BUY:
                return current_price >= self.stop_price
            else:
                return current_price <= self.stop_price
        return False
