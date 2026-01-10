"""SHAP explainability endpoints — feature importance per ticker."""

import logging

from fastapi import APIRouter, HTTPException

from src.api.dependencies import get_model_bundle
from src.data.storage import load_features
from src.models.shap_analysis import compute_shap_importance

router = APIRouter(prefix="/shap", tags=["explainability"])
logger = logging.getLogger(__name__)


@router.get("/importance/{ticker}")
def get_shap_importance(ticker: str, normalize: bool = True) -> dict:
    """Get SHAP feature importance for current model on ticker's feature data.

    Args:
        ticker: Stock ticker symbol.
        normalize: When True (default), SHAP values are normalized to sum to 1.0
            across features, enabling cross-ticker comparison on the same scale.
    """
    bundle, meta = get_model_bundle()
    if bundle is None:
        raise HTTPException(status_code=503, detail="No trained model available")

    model = bundle["model"]
    scaler = bundle["scaler"]
    feature_names = meta.get("feature_names", [])

    try:
        df = load_features(ticker)
    except Exception:
        df = None

    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"No feature data found for ticker: {ticker}")

    cols = feature_names if feature_names else list(df.columns)
    try:
        X = df[cols].values
    except KeyError as exc:
        raise HTTPException(status_code=422, detail=f"Feature column mismatch: {exc}") from exc

    try:
        X_scaled = scaler.transform(X)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scaler transform failed: {exc}") from exc

    result = compute_shap_importance(model, X_scaled, feature_names=cols, max_samples=200)

    mean_abs = result["mean_abs_shap"]
    per_model = result["per_model"]

    sorted_items = sorted(mean_abs.items(), key=lambda x: x[1], reverse=True)

    if normalize:
        total = sum(v for _, v in sorted_items)
        sorted_items = [(k, v / total if total > 0 else 0.0) for k, v in sorted_items]

    feature_importance = [
        {"feature": feat, "shap_value": round(val, 8)} for feat, val in sorted_items
    ]

    top_features = [item["feature"] for item in feature_importance[:10]]

    return {
        "ticker": ticker,
        "feature_importance": feature_importance,
        "per_model": per_model,
        "top_features": top_features,
        "normalized": normalize,
        "disclaimer": "SHAP values reflect model behavior, not fundamental causality",
    }
