"""Unit tests for the ensemble model."""
import numpy as np
import pytest

from src.models.ensemble import EnsembleModel


@pytest.fixture
def training_data():
    """Synthetic binary classification data."""
    rng = np.random.default_rng(42)
    n_samples, n_features = 200, 10
    X = rng.standard_normal((n_samples, n_features))
    # Simple linear boundary so models can learn something
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    return X, y


@pytest.fixture
def fitted_model(training_data):
    """Pre-fitted ensemble for prediction tests."""
    X, y = training_data
    model = EnsembleModel(
        weights={"rf": 0.3, "xgb": 0.3, "lgbm": 0.25, "lstm": 0.15},
        sequence_length=5,
    )
    model.fit(X, y, feature_names=[f"feat_{i}" for i in range(X.shape[1])])
    return model


class TestEnsembleFit:
    def test_fit_marks_model_as_fitted(self, training_data):
        X, y = training_data
        model = EnsembleModel(sequence_length=5)
        assert not model._is_fitted
        model.fit(X, y)
        assert model._is_fitted

    def test_fit_stores_feature_names(self, training_data):
        X, y = training_data
        names = [f"f{i}" for i in range(X.shape[1])]
        model = EnsembleModel(sequence_length=5)
        model.fit(X, y, feature_names=names)
        assert model._feature_names == names

    def test_fit_generates_default_names(self, training_data):
        X, y = training_data
        model = EnsembleModel(sequence_length=5)
        model.fit(X, y)
        assert len(model._feature_names) == X.shape[1]
        assert model._feature_names[0] == "f0"


class TestEnsemblePredict:
    def test_predict_proba_returns_array(self, fitted_model, training_data):
        X, _ = training_data
        probs = fitted_model.predict_proba(X)
        assert isinstance(probs, np.ndarray)

    def test_predict_proba_in_range(self, fitted_model, training_data):
        X, _ = training_data
        probs = fitted_model.predict_proba(X)
        assert np.all(probs >= 0)
        assert np.all(probs <= 1)

    def test_predict_binary_output(self, fitted_model, training_data):
        X, _ = training_data
        preds = fitted_model.predict(X)
        assert set(np.unique(preds)).issubset({0, 1})

    def test_predict_length_matches_lstm_truncation(self, fitted_model, training_data):
        """LSTM produces fewer predictions due to sequence windowing.
        Ensemble should align all models to the shortest output."""
        X, _ = training_data
        probs = fitted_model.predict_proba(X)
        lstm_probs = fitted_model.lstm.predict_proba(X)
        assert len(probs) == len(lstm_probs)

    def test_custom_weights_affect_output(self, training_data):
        X, y = training_data
        model_a = EnsembleModel(
            weights={"rf": 1.0, "xgb": 0.0, "lgbm": 0.0, "lstm": 0.0},
            sequence_length=5,
        )
        model_b = EnsembleModel(
            weights={"rf": 0.0, "xgb": 1.0, "lgbm": 0.0, "lstm": 0.0},
            sequence_length=5,
        )
        model_a.fit(X, y)
        model_b.fit(X, y)
        probs_a = model_a.predict_proba(X)
        probs_b = model_b.predict_proba(X)
        # Different weights should produce different probabilities
        assert not np.allclose(probs_a, probs_b, atol=0.01)


class TestFeatureImportances:
    def test_importances_returns_dict(self, fitted_model):
        imp = fitted_model.feature_importances()
        assert isinstance(imp, dict)

    def test_importances_covers_all_features(self, fitted_model):
        imp = fitted_model.feature_importances()
        assert len(imp) == 10

    def test_importances_sum_to_approximately_one(self, fitted_model):
        imp = fitted_model.feature_importances()
        total = sum(imp.values())
        # Averaged normalized importances should sum close to 1
        assert 0.95 <= total <= 1.05

    def test_importances_sorted_descending(self, fitted_model):
        imp = fitted_model.feature_importances()
        values = list(imp.values())
        assert values == sorted(values, reverse=True)
