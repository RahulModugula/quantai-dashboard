from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException

from src.api.dependencies import get_model_bundle, get_paper_trader
from src.data.schemas import PredictionResponse
from src.data.storage import load_features
from src.trading.signals import generate_signal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predictions", tags=["predictions"])

DISCLAIMER = "Educational purposes only. Not financial advice. Backtested results are theoretical."


@router.get("/{ticker}", response_model=PredictionResponse)
def get_prediction(ticker: str) -> PredictionResponse:
    """Get the latest model prediction for a ticker."""
    try:
        trader = get_paper_trader()
        bundle, meta = get_model_bundle()

        if bundle is None:
            raise HTTPException(status_code=503, detail="No trained model available. Run train_model.py first.")

        model = bundle["model"]
        scaler = bundle["scaler"]
        feature_names = meta.get("feature_names", [])

        df = load_features(ticker.upper())
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No feature data for {ticker}. Run seed_data.py first.")

        row = df[feature_names].iloc[-1:].values
        row_scaled = scaler.transform(row)

        proba = model.predict_proba(row_scaled)
        prob_up = float(proba[-1]) if len(proba) > 0 else 0.5

        portfolio_value = trader.portfolio.get_value({})
        has_position = ticker.upper() in trader.portfolio.positions

        # Fetch rough price estimate from features
        current_price = float(df["close"].iloc[-1]) if "close" in df.columns else 1.0

        signal = generate_signal(
            ticker=ticker.upper(),
            probability_up=prob_up,
            portfolio_value=portfolio_value,
            current_price=current_price,
            has_position=has_position,
        )

        feature_importances = {}
        try:
            feature_importances = model.feature_importances()
        except Exception as e:
            logger.warning(f"Could not extract feature importances: {e}")

        return PredictionResponse(
            ticker=ticker.upper(),
            timestamp=datetime.now(),
            probability_up=prob_up,
            signal=signal.signal_type.value,
            confidence=signal.confidence,
            feature_importances=feature_importances,
            disclaimer=DISCLAIMER,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prediction for {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/", response_model=list)
def list_predictions() -> list[dict]:
    """Get predictions for all configured tickers."""
    from src.config import settings
    results = []
    for ticker in settings.tickers:
        try:
            pred = get_prediction(ticker)
            results.append(pred.model_dump())
        except HTTPException as e:
            logger.warning(f"Prediction failed for {ticker}: {e.detail}")
            results.append({"ticker": ticker, "error": "prediction unavailable"})
        except Exception as e:
            logger.error(f"Unexpected error for {ticker}: {e}")
            results.append({"ticker": ticker, "error": "prediction failed"})
    return results


@router.post("/batch")
def batch_predictions(request: dict) -> dict:
    """Get predictions for a list of tickers in one request."""
    tickers = request.get("tickers", [])
    if not tickers:
        raise HTTPException(status_code=400, detail="At least one ticker required")

    predictions = []
    errors = []

    for ticker in tickers:
        try:
            pred = get_prediction(ticker)
            predictions.append(pred.model_dump())
        except HTTPException as e:
            errors.append({"ticker": ticker, "error": e.detail})
        except Exception as e:
            logger.error(f"Unexpected error for {ticker}: {e}")
            errors.append({"ticker": ticker, "error": "prediction failed"})

    return {
        "predictions": predictions,
        "errors": errors,
        "success_count": len(predictions),
        "error_count": len(errors),
    }
