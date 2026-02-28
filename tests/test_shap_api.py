"""Tests for the SHAP feature importance API endpoint and analysis module."""

import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from src.api.routes.shap import router


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_ensemble(n_features: int = 10):
    """Build a minimal mock ensemble with fitted sklearn tree models."""
    rng = np.random.default_rng(0)
    X = rng.standard_normal((120, n_features))
    y = (X[:, 0] > 0).astype(int)

    feature_names = [f"feature_{i}" for i in range(n_features)]

    rf = RandomForestClassifier(n_estimators=5, random_state=0).fit(X, y)
    xgb = RandomForestClassifier(n_estimators=5, random_state=1).fit(X, y)
    lgbm = RandomForestClassifier(n_estimators=5, random_state=2).fit(X, y)

    ensemble = MagicMock()
    ensemble.rf = rf
    ensemble.xgb = xgb
    ensemble.lgbm = lgbm
    ensemble.weights = {"rf": 0.3, "xgb": 0.3, "lgbm": 0.25}
    ensemble._feature_names = feature_names
    return ensemble, feature_names


def _make_test_app():
    app = FastAPI()
    # router already carries its own /shap prefix — include without additional prefix
    app.include_router(router)
    return app


# ---------------------------------------------------------------------------
# Test 1: no model returns 503
# ---------------------------------------------------------------------------


def test_shap_endpoint_no_model_returns_503():
    app = _make_test_app()
    client = TestClient(app)

    with patch("src.api.routes.shap.get_model_bundle", return_value=(None, {})):
        resp = client.get("/shap/importance/AAPL")

    assert resp.status_code == 503
    assert "model" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Test 2: missing features returns 404
# ---------------------------------------------------------------------------


def test_shap_endpoint_no_features_returns_404():
    app = _make_test_app()
    client = TestClient(app)

    import pandas as pd

    mock_bundle = {"model": MagicMock(), "scaler": StandardScaler()}
    mock_meta = {"feature_names": ["f0", "f1"]}

    with (
        patch("src.api.routes.shap.get_model_bundle", return_value=(mock_bundle, mock_meta)),
        patch("src.api.routes.shap.load_features", return_value=pd.DataFrame()),
    ):
        resp = client.get("/shap/importance/UNKNOWN")

    assert resp.status_code == 404
    assert "UNKNOWN" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Test 3: compute_shap_importance output shape
# ---------------------------------------------------------------------------


def test_compute_shap_importance_shape():
    from src.models.shap_analysis import compute_shap_importance

    ensemble, feature_names = _make_mock_ensemble(n_features=8)
    # Give ensemble a real feature_importances() fallback for when shap isn't installed
    ensemble.feature_importances = MagicMock(
        return_value={name: float(i + 1) for i, name in enumerate(feature_names)}
    )
    rng = np.random.default_rng(1)
    X = rng.standard_normal((50, 8))

    result = compute_shap_importance(ensemble, X, feature_names=feature_names, max_samples=50)

    assert "mean_abs_shap" in result
    assert "per_model" in result
    assert len(result["mean_abs_shap"]) == 8
    for name in feature_names:
        assert name in result["mean_abs_shap"]


# ---------------------------------------------------------------------------
# Test 4: SHAP importance list is sorted descending
# ---------------------------------------------------------------------------


def test_shap_importance_sorted_descending():
    from src.models.shap_analysis import compute_shap_importance

    ensemble, feature_names = _make_mock_ensemble(n_features=10)
    ensemble.feature_importances = MagicMock(
        return_value={name: float(10 - i) for i, name in enumerate(feature_names)}
    )
    rng = np.random.default_rng(2)
    X = rng.standard_normal((80, 10))

    result = compute_shap_importance(ensemble, X, feature_names=feature_names, max_samples=80)

    values = list(result["mean_abs_shap"].values())
    assert values == sorted(values, reverse=True), (
        "mean_abs_shap should be sorted in descending order"
    )
