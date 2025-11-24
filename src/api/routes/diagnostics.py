"""Diagnostics endpoints for troubleshooting and model analysis."""

import logging
from fastapi import APIRouter, HTTPException

from src.api.dependencies import get_model_bundle
from src.data.storage import load_features
from src.data.correlation import high_correlation_pairs
from src.config import settings

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])
logger = logging.getLogger(__name__)


@router.get("/model-features")
def model_features() -> dict:
    """Inspect model's feature engineering and importance."""
    try:
        bundle, meta = get_model_bundle()
        if bundle is None:
            raise HTTPException(status_code=503, detail="No trained model available")

        model = bundle["model"]
        scaler = bundle["scaler"]
        feature_names = meta.get("feature_names", [])

        importances = {}
        try:
            importances = model.feature_importances()
        except Exception as e:
            logger.warning(f"Could not extract importances: {e}")

        return {
            "feature_count": len(feature_names),
            "feature_names": feature_names,
            "feature_importances": importances,
            "scaler_type": type(scaler).__name__,
            "model_type": type(model).__name__,
        }
    except Exception as e:
        logger.error(f"Diagnostics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feature-correlation")
def feature_correlation() -> dict:
    """Analyze correlations between features across all tickers."""
    try:
        correlations = {}
        for ticker in settings.tickers:
            df = load_features(ticker)
            if df.empty:
                continue

            # Extract numeric feature columns (exclude date, ticker)
            feature_cols = [c for c in df.columns if c not in ("date", "ticker", "target")]
            if len(feature_cols) < 2:
                continue

            feat_df = df[feature_cols].dropna()
            corr_matrix = feat_df.corr()
            correlations[ticker] = {
                "high_pairs": high_correlation_pairs(corr_matrix, threshold=0.85),
                "feature_count": len(feature_cols),
            }

        return {
            "tickers_analyzed": len(correlations),
            "correlations": correlations,
            "note": "High correlation between features may indicate multicollinearity.",
        }
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-config")
def validate_config() -> dict:
    """Check if current configuration is valid and consistent."""
    warnings = []
    errors = []

    # Check buy/sell thresholds
    if settings.buy_threshold <= settings.sell_threshold:
        errors.append("buy_threshold must be > sell_threshold")

    # Check ensemble weights
    weight_sum = sum(settings.ensemble_weights.values())
    if abs(weight_sum - 1.0) > 0.01:
        errors.append(f"ensemble_weights don't sum to 1.0 (got {weight_sum:.3f})")

    # Check capital and position sizing
    if settings.max_position_pct * settings.initial_capital < 100:
        warnings.append("max_position_pct * initial_capital < $100, may lead to very small trades")

    # Check commission
    if settings.commission_pct > 0.01:
        warnings.append(
            f"commission_pct={settings.commission_pct} is unusually high (typical: 0.1%)"
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }
