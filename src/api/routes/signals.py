"""Real-time trading signals and alert management."""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException

from src.api.dependencies import get_paper_trader
from src.trading.signals import generate_signal

router = APIRouter(prefix="/signals", tags=["signals"])
logger = logging.getLogger(__name__)

# In-memory signal history
_signal_history = {}


@router.get("/latest/{ticker}")
def get_latest_signal(ticker: str) -> dict:
    """Get latest trading signal for a ticker with trend history."""
    try:
        from src.data.storage import load_features

        ticker = ticker.upper()
        features = load_features(ticker)

        if features.empty:
            raise HTTPException(status_code=404, detail=f"No data for {ticker}")

        trader = get_paper_trader()
        signal = generate_signal(
            ticker=ticker,
            probability=0.5,  # Would be from model
            portfolio=trader.portfolio,
        )

        # Store in history
        if ticker not in _signal_history:
            _signal_history[ticker] = []
        _signal_history[ticker].append({
            "timestamp": datetime.now().isoformat(),
            "signal": signal.signal_type.value,
            "strength": signal.strength,
        })

        # Keep only last 100 signals
        _signal_history[ticker] = _signal_history[ticker][-100:]

        return {
            "ticker": ticker,
            "current_signal": signal.signal_type.value,
            "strength": signal.strength,
            "timestamp": datetime.now().isoformat(),
            "history_count": len(_signal_history[ticker]),
        }
    except Exception as e:
        logger.error(f"Signal retrieval failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Signal failed: {str(e)}")


@router.get("/strength/{ticker}")
def get_signal_strength_trend(ticker: str, limit: int = 20) -> dict:
    """Get signal strength trend over time."""
    try:
        ticker = ticker.upper()

        if ticker not in _signal_history:
            return {
                "ticker": ticker,
                "trend": [],
                "average_strength": 0,
                "message": "No signal history available",
            }

        history = _signal_history[ticker][-limit:]
        strengths = [s["strength"] for s in history]

        return {
            "ticker": ticker,
            "trend": history,
            "count": len(history),
            "average_strength": sum(strengths) / len(strengths) if strengths else 0,
            "min_strength": min(strengths) if strengths else 0,
            "max_strength": max(strengths) if strengths else 0,
        }
    except Exception as e:
        logger.error(f"Trend analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Trend failed: {str(e)}")


@router.get("/consensus")
def get_signal_consensus(tickers: str = "AAPL,GOOGL,MSFT") -> dict:
    """Get consensus signals across multiple tickers."""
    try:
        ticker_list = [t.strip().upper() for t in tickers.split(",")]

        signals = {}
        buy_count = 0
        sell_count = 0
        hold_count = 0

        for ticker in ticker_list:
            if ticker in _signal_history and _signal_history[ticker]:
                latest = _signal_history[ticker][-1]
                signals[ticker] = latest["signal"]

                if "BUY" in latest["signal"]:
                    buy_count += 1
                elif "SELL" in latest["signal"]:
                    sell_count += 1
                else:
                    hold_count += 1

        total = buy_count + sell_count + hold_count

        return {
            "tickers": len(ticker_list),
            "signals": signals,
            "consensus": {
                "buy_pct": (buy_count / total * 100) if total > 0 else 0,
                "sell_pct": (sell_count / total * 100) if total > 0 else 0,
                "hold_pct": (hold_count / total * 100) if total > 0 else 0,
            },
            "overall_signal": "BUY" if buy_count > total / 2 else "SELL" if sell_count > total / 2 else "HOLD",
        }
    except Exception as e:
        logger.error(f"Consensus failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Consensus failed: {str(e)}")
