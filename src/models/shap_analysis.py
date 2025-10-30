"""SHAP-based feature importance analysis for the ensemble model.

Uses TreeExplainer for RF/XGBoost/LightGBM (exact Shapley values in
polynomial time) and averages across ensemble members weighted by
their ensemble weights. This avoids the bias inherent in built-in
feature importances (split-based importances overweight high-cardinality
and correlated features).
"""
import logging

import numpy as np

logger = logging.getLogger(__name__)


def compute_shap_importance(
    ensemble,
    X: np.ndarray,
    feature_names: list[str] | None = None,
    max_samples: int = 500,
) -> dict:
    """Compute SHAP values for the tree-based ensemble members.

    Args:
        ensemble: Fitted EnsembleModel instance.
        X: Feature matrix (n_samples, n_features).
        feature_names: Feature names. Falls back to ensemble._feature_names.
        max_samples: Subsample X to this many rows for speed.

    Returns:
        Dict with keys:
        - mean_abs_shap: {feature: mean(|SHAP|)} averaged across models
        - per_model: {model_name: {feature: mean(|SHAP|)}}
        - shap_values: raw SHAP matrix (n_samples, n_features) — weighted avg
    """
    try:
        import shap
    except ImportError:
        logger.warning("shap not installed — falling back to built-in importances")
        return {"mean_abs_shap": ensemble.feature_importances(), "per_model": {}, "shap_values": None}

    names = feature_names or ensemble._feature_names
    if not names:
        names = [f"f{i}" for i in range(X.shape[1])]

    # Subsample for performance
    if len(X) > max_samples:
        idx = np.random.default_rng(42).choice(len(X), max_samples, replace=False)
        X_sample = X[idx]
    else:
        X_sample = X

    models = {
        "rf": (ensemble.rf, ensemble.weights.get("rf", 0.3)),
        "xgb": (ensemble.xgb, ensemble.weights.get("xgb", 0.3)),
        "lgbm": (ensemble.lgbm, ensemble.weights.get("lgbm", 0.25)),
    }

    per_model = {}
    weighted_shap = np.zeros((len(X_sample), X_sample.shape[1]))
    total_weight = 0.0

    for model_name, (model, weight) in models.items():
        try:
            explainer = shap.TreeExplainer(model)
            sv = explainer.shap_values(X_sample)

            # For binary classification, shap_values may be a list [class_0, class_1]
            if isinstance(sv, list):
                sv = sv[1]  # class 1 = "up" direction

            mean_abs = np.abs(sv).mean(axis=0)
            per_model[model_name] = {
                name: float(val) for name, val in zip(names, mean_abs)
            }
            weighted_shap += weight * sv
            total_weight += weight
        except Exception as e:
            logger.warning("SHAP failed for %s: %s", model_name, e)

    if total_weight > 0:
        weighted_shap /= total_weight

    # Aggregate: weighted mean of per-model mean(|SHAP|)
    mean_abs_shap = {}
    for i, name in enumerate(names):
        val = 0.0
        w_sum = 0.0
        for model_name, (_, weight) in models.items():
            if model_name in per_model:
                val += weight * per_model[model_name][name]
                w_sum += weight
        mean_abs_shap[name] = val / w_sum if w_sum > 0 else 0.0

    # Sort descending
    mean_abs_shap = dict(sorted(mean_abs_shap.items(), key=lambda x: x[1], reverse=True))

    return {
        "mean_abs_shap": mean_abs_shap,
        "per_model": per_model,
        "shap_values": weighted_shap,
    }
