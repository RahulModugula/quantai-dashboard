"""Status and diagnostics endpoints."""
import logging
from datetime import datetime

from fastapi import APIRouter

from src.data.storage import load_ohlcv
from src.config import settings

router = APIRouter(prefix="/status", tags=["status"])
logger = logging.getLogger(__name__)


@router.get("/data")
def data_status() -> dict:
    """Check data availability and freshness for all configured tickers."""
    status = {
        "timestamp": datetime.now().isoformat(),
        "tickers": {},
        "all_available": True,
    }

    for ticker in settings.tickers:
        try:
            df = load_ohlcv(ticker)
            if df.empty:
                status["tickers"][ticker] = {
                    "available": False,
                    "last_date": None,
                    "row_count": 0,
                }
                status["all_available"] = False
            else:
                last_date = df["date"].max()
                status["tickers"][ticker] = {
                    "available": True,
                    "last_date": str(last_date),
                    "row_count": len(df),
                    "days_old": (datetime.now() - last_date).days,
                }
        except Exception as e:
            logger.warning(f"Error checking data for {ticker}: {e}")
            status["tickers"][ticker] = {
                "available": False,
                "error": str(e),
            }
            status["all_available"] = False

    return status


@router.get("/ready")
def readiness_check() -> dict:
    """Liveness probe - 200 if API is ready to serve requests."""
    status_data = data_status()
    ready = status_data["all_available"]

    return {
        "ready": ready,
        "data_available": status_data["all_available"],
        "configured_tickers": len(settings.tickers),
        "available_tickers": sum(1 for t in status_data["tickers"].values() if t.get("available")),
        "timestamp": datetime.now().isoformat(),
    }
