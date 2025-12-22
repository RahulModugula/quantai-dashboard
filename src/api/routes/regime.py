"""Market regime detection API endpoints."""

import logging

from fastapi import APIRouter, HTTPException

from src.analysis.regime import RegimeDetector

router = APIRouter(prefix="/regime", tags=["regime"])
logger = logging.getLogger(__name__)

_detector = RegimeDetector()


@router.get("/{ticker}")
def get_regime(ticker: str) -> dict:
    """Get current market regime for a ticker."""
    try:
        from src.data.storage import load_ohlcv

        ticker = ticker.upper()
        df = load_ohlcv(ticker)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for ticker {ticker}")

        try:
            regime = _detector.current_regime(df)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        return {"ticker": ticker, **regime}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Regime detection failed for {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Regime detection failed: {str(e)}")


@router.get("/{ticker}/history")
def get_regime_history(ticker: str, lookback_days: int = 252) -> dict:
    """Get regime classification history for last N trading days."""
    try:
        from src.data.storage import load_ohlcv

        ticker = ticker.upper()
        df = load_ohlcv(ticker)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for ticker {ticker}")

        try:
            classified = _detector.classify(df)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        # Take the last lookback_days rows after classification
        window = classified.tail(lookback_days)

        records = []
        for _, row in window.iterrows():
            date_val = row["date"] if "date" in row.index else row.name
            realized_vol = row["realized_vol"]
            records.append(
                {
                    "date": str(date_val),
                    "regime": row["regime"],
                    "vol_regime": row["vol_regime"],
                    "trend_regime": row["trend_regime"],
                    "realized_vol": round(float(realized_vol), 6)
                    if not __import__("math").isnan(
                        float(realized_vol) if realized_vol == realized_vol else float("nan")
                    )
                    else None,
                }
            )

        return {
            "ticker": ticker,
            "lookback_days": lookback_days,
            "count": len(records),
            "history": records,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Regime history failed for {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Regime history failed: {str(e)}")


@router.get("/{ticker}/performance")
def get_regime_performance(ticker: str) -> dict:
    """Get strategy performance broken down by market regime.

    Uses buy-and-hold close returns as the equity curve.
    """
    try:
        from src.data.storage import load_ohlcv

        ticker = ticker.upper()
        df = load_ohlcv(ticker)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for ticker {ticker}")

        try:
            classified = _detector.classify(df)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        equity_curve = classified["close"]
        performance = _detector.regime_performance(classified, equity_curve)

        return {
            "ticker": ticker,
            "performance_by_regime": performance,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Regime performance failed for {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Regime performance failed: {str(e)}")
