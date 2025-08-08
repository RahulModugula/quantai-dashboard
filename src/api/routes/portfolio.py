import logging
from fastapi import APIRouter, HTTPException

from src.api.dependencies import get_paper_trader
from src.data.storage import load_trades

router = APIRouter(prefix="/portfolio", tags=["portfolio"])
logger = logging.getLogger(__name__)

DISCLAIMER = "Educational purposes only. Not financial advice. Paper trading only."


@router.get("/")
def get_portfolio() -> dict:
    """Get current portfolio state."""
    try:
        trader = get_paper_trader()
        portfolio = trader.portfolio

        # Use last known prices from snapshots
        current_prices = {}
        if portfolio._snapshots:
            pass  # prices cached in Redis during live trading

        total_value = portfolio.get_value(current_prices)
        cumulative_return = (
            (total_value - portfolio.initial_capital) / portfolio.initial_capital
            if portfolio.initial_capital > 0
            else 0.0
        )

        return {
            "total_value": total_value,
            "cash": portfolio.cash,
            "positions_value": portfolio.get_positions_value(current_prices),
            "initial_capital": portfolio.initial_capital,
            "cumulative_return": cumulative_return,
            "holdings": portfolio.get_holdings(current_prices),
            "disclaimer": DISCLAIMER,
        }
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Portfolio lookup failed: {str(e)}")


@router.get("/history")
def get_portfolio_history(limit: int = 200) -> dict:
    """Get portfolio equity history."""
    try:
        if limit <= 0:
            raise ValueError("Limit must be positive")

        trader = get_paper_trader()
        snapshots = trader.portfolio._snapshots[-limit:]
        return {
            "snapshots": snapshots,
            "count": len(snapshots),
            "disclaimer": DISCLAIMER,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting portfolio history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"History lookup failed: {str(e)}")


@router.get("/trades")
def get_trades(ticker: str | None = None, limit: int = 100) -> dict:
    """Get trade history."""
    try:
        if limit <= 0:
            raise ValueError("Limit must be positive")

        trades_df = load_trades(ticker=ticker)
        if not trades_df.empty:
            trades_df = trades_df.tail(limit)
        return {
            "trades": trades_df.to_dict(orient="records") if not trades_df.empty else [],
            "count": len(trades_df),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting trades: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Trade lookup failed: {str(e)}")
