import logging

import numpy as np
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from src.config import settings
from src.models.lstm import LSTMWrapper

logger = logging.getLogger(__name__)


class EnsembleModel:
    """Weighted ensemble of Random Forest, XGBoost, LightGBM, and LSTM."""

    def __init__(self, weights: dict | None = None, sequence_length: int = 20):
        self.weights = weights or settings.ensemble_weights
        self.sequence_length = sequence_length

        self.rf = RandomForestClassifier(
            n_estimators=300,
            max_depth=12,
            min_samples_split=20,
            min_samples_leaf=10,
            max_features="sqrt",
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )

        self.xgb = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            eval_metric="logloss",
        )

        self.lgbm = LGBMClassifier(
            n_estimators=250,
            max_depth=8,
            learning_rate=0.05,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            class_weight="balanced",
            random_state=42,
            verbose=-1,
        )

        self.lstm = LSTMWrapper(
            sequence_length=sequence_length,
            hidden_dim=64,
            epochs=30,
            lr=1e-3,
        )

        self._feature_names: list[str] = []
        self._is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: list[str] | None = None):
        """Train all four models on the same data."""
        self._feature_names = feature_names or [f"f{i}" for i in range(X.shape[1])]

        logger.info(f"Training RF on {X.shape[0]} samples, {X.shape[1]} features")
        self.rf.fit(X, y)

        logger.info("Training XGBoost")
        self.xgb.fit(X, y)

        logger.info("Training LightGBM")
        self.lgbm.fit(X, y)

        logger.info("Training LSTM")
        self.lstm.fit(X, y)

        self._is_fitted = True
        logger.info("Ensemble training complete")

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Weighted average of predicted probabilities."""
        w_rf = self.weights.get("rf", 0.3)
        w_xgb = self.weights.get("xgb", 0.3)
        w_lgbm = self.weights.get("lgbm", 0.25)
        w_lstm = self.weights.get("lstm", 0.15)

        p_rf = self.rf.predict_proba(X)[:, 1]
        p_xgb = self.xgb.predict_proba(X)[:, 1]
        p_lgbm = self.lgbm.predict_proba(X)[:, 1]
        p_lstm = self.lstm.predict_proba(X)

        # LSTM produces fewer predictions due to sequence windowing
        # Align by taking only the last len(p_lstm) predictions from tree models
        n = len(p_lstm)
        if n < len(p_rf):
            p_rf = p_rf[-n:]
            p_xgb = p_xgb[-n:]
            p_lgbm = p_lgbm[-n:]

        combined = w_rf * p_rf + w_xgb * p_xgb + w_lgbm * p_lgbm + w_lstm * p_lstm
        return combined

    def predict(self, X: np.ndarray) -> np.ndarray:
        probs = self.predict_proba(X)
        return (probs >= 0.5).astype(int)

    def feature_importances(self) -> dict[str, float]:
        """Average normalized feature importances from RF, XGBoost, and LightGBM."""
        rf_imp = self.rf.feature_importances_ / (self.rf.feature_importances_.sum() or 1)
        xgb_imp = self.xgb.feature_importances_ / (self.xgb.feature_importances_.sum() or 1)
        lgbm_imp = self.lgbm.feature_importances_ / (self.lgbm.feature_importances_.sum() or 1)
        avg_imp = (rf_imp + xgb_imp + lgbm_imp) / 3

        return {
            name: float(imp)
            for name, imp in sorted(
                zip(self._feature_names, avg_imp),
                key=lambda x: x[1],
                reverse=True,
            )
        }
