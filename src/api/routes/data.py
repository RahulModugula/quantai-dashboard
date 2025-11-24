"""Data validation and quality check endpoints."""

import logging
from fastapi import APIRouter, HTTPException

from src.config import settings
from src.data.storage import load_features, load_ohlcv

router = APIRouter(prefix="/data", tags=["data"])
logger = logging.getLogger(__name__)


@router.post("/validate/{ticker}")
def validate_ticker_data(ticker: str) -> dict:
    """Validate data quality for a specific ticker.

    Checks for missing values, date continuity, and price validity.
    """
    try:
        ticker = ticker.upper()

        # Check OHLCV data
        ohlcv = load_ohlcv(ticker)
        if ohlcv.empty:
            return {
                "ticker": ticker,
                "valid": False,
                "errors": [f"No OHLCV data found for {ticker}"],
                "warnings": [],
            }

        errors = []
        warnings = []

        # Check for null values
        null_cols = ohlcv.isnull().sum()
        for col, count in null_cols.items():
            if count > 0:
                pct = (count / len(ohlcv)) * 100
                if pct > 5:
                    errors.append(f"{col} has {count} null values ({pct:.1f}%)")
                else:
                    warnings.append(f"{col} has {count} null values ({pct:.1f}%)")

        # Check for price anomalies (negative prices, zero volume)
        if "close" in ohlcv.columns:
            if (ohlcv["close"] <= 0).any():
                errors.append("Close prices contain invalid values (≤0)")
            if ohlcv["close"].std() / ohlcv["close"].mean() > 0.5:
                warnings.append("Close price volatility is unusually high")

        if "volume" in ohlcv.columns:
            if (ohlcv["volume"] < 0).any():
                errors.append("Volume contains negative values")
            if (ohlcv["volume"] == 0).sum() > len(ohlcv) * 0.1:
                warnings.append("More than 10% of trading days have zero volume")

        # Check date continuity (allow some gaps for weekends/holidays)
        if "date" in ohlcv.columns or ohlcv.index.name == "date":
            dates = ohlcv.index if ohlcv.index.name == "date" else ohlcv["date"]
            date_gaps = (dates.diff().dt.days > 3).sum()
            if date_gaps > 20:
                warnings.append(
                    f"Data has {date_gaps} gaps > 3 days (may indicate missing holidays)"
                )

        # Check features
        features = load_features(ticker)
        if features.empty:
            warnings.append("No feature data available for predictions")
        else:
            feature_nulls = features.isnull().sum()
            if (feature_nulls > 0).any():
                bad_features = feature_nulls[feature_nulls > 0]
                warnings.append(f"{len(bad_features)} features have null values")

        return {
            "ticker": ticker,
            "valid": len(errors) == 0,
            "ohlcv_rows": len(ohlcv),
            "feature_rows": len(features),
            "errors": errors,
            "warnings": warnings,
            "last_date": str(ohlcv.index.max()) if len(ohlcv) > 0 else None,
        }
    except Exception as e:
        logger.error(f"Data validation failed for {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/summary")
def get_data_quality_summary() -> dict:
    """Get overall data quality summary across all configured tickers."""
    try:
        summary = {
            "tickers_checked": 0,
            "tickers_valid": 0,
            "tickers_with_issues": 0,
            "total_rows": 0,
            "issues": [],
        }

        for ticker in settings.tickers:
            try:
                ohlcv = load_ohlcv(ticker)
                features = load_features(ticker)

                if not ohlcv.empty:
                    summary["tickers_checked"] += 1
                    summary["total_rows"] += len(ohlcv)

                    if features.empty:
                        summary["tickers_with_issues"] += 1
                        summary["issues"].append(f"{ticker}: No feature data")
                    else:
                        summary["tickers_valid"] += 1
                else:
                    summary["tickers_with_issues"] += 1
                    summary["issues"].append(f"{ticker}: No OHLCV data")

            except Exception as e:
                summary["tickers_with_issues"] += 1
                summary["issues"].append(f"{ticker}: {str(e)}")

        return {
            "summary": summary,
            "overall_health": "Good"
            if summary["tickers_with_issues"] == 0
            else "Fair"
            if summary["tickers_with_issues"] < len(settings.tickers) / 2
            else "Poor",
            "recommendation": (
                "Ready for training"
                if summary["tickers_valid"] > 0
                else "Run seed_data.py to populate database"
            ),
        }
    except Exception as e:
        logger.error(f"Summary generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Summary failed: {str(e)}")


@router.get("/missing-tickers")
def get_missing_tickers() -> dict:
    """Identify tickers that haven't been seeded yet."""
    try:
        missing = []
        ready = []

        for ticker in settings.tickers:
            try:
                ohlcv = load_ohlcv(ticker)
                if ohlcv.empty:
                    missing.append(ticker)
                else:
                    ready.append(ticker)
            except Exception as e:
                logger.debug(f"Error checking {ticker}: {e}")
                missing.append(ticker)

        return {
            "ready_tickers": ready,
            "ready_count": len(ready),
            "missing_tickers": missing,
            "missing_count": len(missing),
            "next_step": (
                f"Run: python -m scripts.seed_data --tickers {' '.join(missing)}"
                if missing
                else "All tickers are ready!"
            ),
        }
    except Exception as e:
        logger.error(f"Missing tickers check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Check failed: {str(e)}")
