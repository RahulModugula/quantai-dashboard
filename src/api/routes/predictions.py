from datetime import datetime

import numpy as np
from fastapi import APIRouter, HTTPException

from src.api.dependencies import get_model_bundle, get_paper_trader
from src.data.storage import load_features
from src.trading.signals import SignalType, generate_signal

router = APIRouter(prefix="/predictions", tags=["predictions"])

DISCLAIMER = "Educational purposes only. Not financial advice. Backtested results are theoretical."


@router.get("/{ticker}")
def get_prediction(ticker: str):
    """Get the latest model prediction for a ticker."""
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
    except Exception:
        pass

    return {
        "ticker": ticker.upper(),
        "timestamp": datetime.now().isoformat(),
        "probability_up": prob_up,
        "signal": signal.signal_type.value,
        "confidence": signal.confidence,
        "feature_importances": feature_importances,
        "disclaimer": DISCLAIMER,
    }


@router.get("/")
def list_predictions():
    """Get predictions for all configured tickers."""
    from src.config import settings
    results = []
    for ticker in settings.tickers:
        try:
            pred = get_prediction(ticker)
            results.append(pred)
        except HTTPException:
            results.append({"ticker": ticker, "error": "prediction unavailable"})
    return results
