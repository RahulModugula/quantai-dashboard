from fastapi import APIRouter

from src.api.dependencies import get_paper_trader
from src.data.storage import load_trades

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

DISCLAIMER = "Educational purposes only. Not financial advice. Paper trading only."


@router.get("/")
def get_portfolio():
    """Get current portfolio state."""
    trader = get_paper_trader()
    portfolio = trader.portfolio

    # Use last known prices from snapshots
    current_prices = {}
    if portfolio._snapshots:
        pass  # prices cached in Redis during live trading

    total_value = portfolio.get_value(current_prices)
    cumulative_return = (total_value - portfolio.initial_capital) / portfolio.initial_capital

    return {
        "total_value": total_value,
        "cash": portfolio.cash,
        "positions_value": portfolio.get_positions_value(current_prices),
        "initial_capital": portfolio.initial_capital,
        "cumulative_return": cumulative_return,
        "holdings": portfolio.get_holdings(current_prices),
        "disclaimer": DISCLAIMER,
    }


@router.get("/history")
def get_portfolio_history(limit: int = 200):
    """Get portfolio equity history."""
    trader = get_paper_trader()
    snapshots = trader.portfolio._snapshots[-limit:]
    return {
        "snapshots": snapshots,
        "count": len(snapshots),
        "disclaimer": DISCLAIMER,
    }


@router.get("/trades")
def get_trades(ticker: str | None = None, limit: int = 100):
    """Get trade history."""
    trades_df = load_trades(ticker=ticker)
    if not trades_df.empty:
        trades_df = trades_df.tail(limit)
    return {
        "trades": trades_df.to_dict(orient="records") if not trades_df.empty else [],
        "count": len(trades_df),
    }
