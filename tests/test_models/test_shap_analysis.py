"""Tests for SHAP feature importance analysis."""
import numpy as np
import pytest

from src.models.ensemble import EnsembleModel


@pytest.fixture
def fitted_ensemble():
    rng = np.random.default_rng(42)
    X = rng.standard_normal((200, 8))
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    names = [f"feat_{i}" for i in range(8)
    ]
    model = EnsembleModel(sequence_length=5)
    model.fit(X, y, feature_names=names)
    return model, X, names


class TestShapImportance:
    def test_returns_required_keys(self, fitted_ensemble):
        model, X, names = fitted_ensemble
        from src.models.shap_analysis import compute_shap_importance
        result = compute_shap_importance(model, X, names)
        assert "mean_abs_shap" in result
        assert "per_model" in result
        assert "shap_values" in result

    def test_importance_covers_all_features(self, fitted_ensemble):
        model, X, names = fitted_ensemble
        from src.models.shap_analysis import compute_shap_importance
        result = compute_shap_importance(model, X, names)
        assert len(result["mean_abs_shap"]) == len(names)

    def test_per_model_has_tree_models(self, fitted_ensemble):
        model, X, names = fitted_ensemble
        from src.models.shap_analysis import compute_shap_importance
        result = compute_shap_importance(model, X, names)
        assert "rf" in result["per_model"]
        assert "xgb" in result["per_model"]
        assert "lgbm" in result["per_model"]

    def test_shap_values_shape(self, fitted_ensemble):
        model, X, names = fitted_ensemble
        from src.models.shap_analysis import compute_shap_importance
        result = compute_shap_importance(model, X, names, max_samples=50)
        sv = result["shap_values"]
        assert sv is not None
        assert sv.shape == (50, len(names))

    def test_importance_sorted_descending(self, fitted_ensemble):
        model, X, names = fitted_ensemble
        from src.models.shap_analysis import compute_shap_importance
        result = compute_shap_importance(model, X, names)
        values = list(result["mean_abs_shap"].values())
        assert values == sorted(values, reverse=True)

    def test_subsampling_limits_rows(self, fitted_ensemble):
        model, X, names = fitted_ensemble
        from src.models.shap_analysis import compute_shap_importance
        result = compute_shap_importance(model, X, names, max_samples=10)
        assert result["shap_values"].shape[0] == 10
