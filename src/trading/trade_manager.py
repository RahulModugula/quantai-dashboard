"""Trade execution and management."""

import logging

logger = logging.getLogger(__name__)


class TradeManager:
    """Manage trade execution and lifecycle."""

    def __init__(self, commission_pct: float = 0.001):
        self.commission_pct = commission_pct
        self.active_trades = []
        self.closed_trades = []

    def execute_buy(self, ticker: str, shares: int, price: float) -> dict:
        """Execute a buy trade."""
        commission = (shares * price) * self.commission_pct
        total_cost = (shares * price) + commission

        trade = {
            "ticker": ticker,
            "side": "BUY",
            "shares": shares,
            "entry_price": price,
            "commission": commission,
            "total_cost": total_cost,
            "status": "OPEN",
        }

        self.active_trades.append(trade)
        logger.info(f"Executed BUY: {shares} {ticker} @ ${price:.2f}")

        return trade

    def execute_sell(self, ticker: str, shares: int, price: float) -> dict:
        """Execute a sell trade."""
        commission = (shares * price) * self.commission_pct
        proceeds = (shares * price) - commission

        trade = {
            "ticker": ticker,
            "side": "SELL",
            "shares": shares,
            "exit_price": price,
            "commission": commission,
            "proceeds": proceeds,
            "status": "OPEN",
        }

        self.active_trades.append(trade)
        logger.info(f"Executed SELL: {shares} {ticker} @ ${price:.2f}")

        return trade

    def close_trade(self, trade_id: int, exit_price: float = None):
        """Close an open trade."""
        if trade_id < len(self.active_trades):
            trade = self.active_trades.pop(trade_id)
            trade["status"] = "CLOSED"

            if exit_price and trade["side"] == "BUY":
                trade["exit_price"] = exit_price
                pnl = (exit_price - trade["entry_price"]) * trade["shares"]
                trade["pnl"] = pnl

            self.closed_trades.append(trade)
            logger.info(f"Closed trade: {trade['ticker']} PnL: ${trade.get('pnl', 0):.2f}")

    def get_active_trades(self) -> list:
        """Get list of active trades."""
        return self.active_trades

    def get_closed_trades(self) -> list:
        """Get list of closed trades."""
        return self.closed_trades
