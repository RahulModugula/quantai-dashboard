import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Position:
    ticker: str
    shares: float
    avg_price: float

    @property
    def cost_basis(self) -> float:
        return self.shares * self.avg_price

    def current_value(self, price: float) -> float:
        return self.shares * price

    def unrealized_pnl(self, price: float) -> float:
        return self.current_value(price) - self.cost_basis


@dataclass
class Trade:
    timestamp: datetime
    ticker: str
    side: str
    shares: float
    price: float
    commission: float
    pnl: float | None = None


class Portfolio:
    def __init__(
        self,
        initial_capital: float = 100_000.0,
        commission_pct: float = 0.001,
        max_drawdown_limit: float = 0.20,
    ):
        self.cash = initial_capital
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct
        self.max_drawdown_limit = max_drawdown_limit
        self.positions: dict[str, Position] = {}
        self.trade_history: list[Trade] = []
        self._snapshots: list[dict] = []
        self._peak_value: float = initial_capital

    def buy(self, ticker: str, shares: float, price: float, timestamp: datetime | None = None) -> Trade | None:
        cost = shares * price
        commission = cost * self.commission_pct
        total = cost + commission

        if total > self.cash:
            logger.warning(f"Insufficient cash for {ticker}: need {total:.2f}, have {self.cash:.2f}")
            return None

        self.cash -= total

        if ticker in self.positions:
            pos = self.positions[ticker]
            total_shares = pos.shares + shares
            pos.avg_price = (pos.shares * pos.avg_price + shares * price) / total_shares
            pos.shares = total_shares
        else:
            self.positions[ticker] = Position(ticker=ticker, shares=shares, avg_price=price)

        trade = Trade(
            timestamp=timestamp or datetime.now(),
            ticker=ticker,
            side="buy",
            shares=shares,
            price=price,
            commission=commission,
        )
        self.trade_history.append(trade)
        logger.info(f"BUY {shares:.4f} {ticker} @ {price:.2f} | cash={self.cash:.2f}")
        return trade

    def sell(self, ticker: str, shares: float, price: float, timestamp: datetime | None = None) -> Trade | None:
        if ticker not in self.positions or self.positions[ticker].shares < shares:
            logger.warning(f"Cannot sell {shares} {ticker}: not enough shares")
            return None

        proceeds = shares * price
        commission = proceeds * self.commission_pct
        net_proceeds = proceeds - commission

        pos = self.positions[ticker]
        realized_pnl = (price - pos.avg_price) * shares - commission

        pos.shares -= shares
        if pos.shares <= 1e-9:
            del self.positions[ticker]

        self.cash += net_proceeds

        trade = Trade(
            timestamp=timestamp or datetime.now(),
            ticker=ticker,
            side="sell",
            shares=shares,
            price=price,
            commission=commission,
            pnl=realized_pnl,
        )
        self.trade_history.append(trade)
        logger.info(f"SELL {shares:.4f} {ticker} @ {price:.2f} | pnl={realized_pnl:.2f} | cash={self.cash:.2f}")
        return trade

    def current_drawdown(self, current_prices: dict[str, float]) -> float:
        """Current drawdown from peak portfolio value."""
        value = self.get_value(current_prices)
        if value >= self._peak_value:
            self._peak_value = value
            return 0.0
        return (value - self._peak_value) / self._peak_value

    def is_drawdown_breached(self, current_prices: dict[str, float]) -> bool:
        """Check if current drawdown exceeds the configured limit."""
        return abs(self.current_drawdown(current_prices)) >= self.max_drawdown_limit

    def get_value(self, current_prices: dict[str, float]) -> float:
        positions_value = sum(
            pos.shares * current_prices.get(ticker, pos.avg_price)
            for ticker, pos in self.positions.items()
        )
        return self.cash + positions_value

    def get_positions_value(self, current_prices: dict[str, float]) -> float:
        return sum(
            pos.shares * current_prices.get(ticker, pos.avg_price)
            for ticker, pos in self.positions.items()
        )

    def snapshot(self, current_prices: dict[str, float], timestamp: datetime | None = None) -> dict:
        total_value = self.get_value(current_prices)
        positions_value = self.get_positions_value(current_prices)
        cumulative_return = (total_value - self.initial_capital) / self.initial_capital

        snap = {
            "timestamp": (timestamp or datetime.now()).isoformat(),
            "total_value": total_value,
            "cash": self.cash,
            "positions_value": positions_value,
            "cumulative_return": cumulative_return,
        }
        self._snapshots.append(snap)
        return snap

    def get_holdings(self, current_prices: dict[str, float]) -> list[dict]:
        return [
            {
                "ticker": ticker,
                "shares": pos.shares,
                "avg_price": pos.avg_price,
                "current_price": current_prices.get(ticker, pos.avg_price),
                "current_value": pos.current_value(current_prices.get(ticker, pos.avg_price)),
                "unrealized_pnl": pos.unrealized_pnl(current_prices.get(ticker, pos.avg_price)),
                "pnl_pct": pos.unrealized_pnl(current_prices.get(ticker, pos.avg_price)) / pos.cost_basis,
            }
            for ticker, pos in self.positions.items()
        ]

    @property
    def realized_pnl_total(self) -> float:
        """Sum of realized PnL across all closed trades."""
        return sum(t.pnl for t in self.trade_history if t.pnl is not None)

    @property
    def total_commissions(self) -> float:
        """Total commissions paid across all trades."""
        return sum(t.commission for t in self.trade_history)

    @property
    def total_trades_count(self) -> int:
        """Number of completed round-trip trades (sell-side entries with PnL)."""
        return sum(1 for t in self.trade_history if t.pnl is not None)
