"""Ensemble stacking for improved predictions."""
import logging
import numpy as np

logger = logging.getLogger(__name__)


class EnsembleStacking:
    """Stack multiple model predictions for meta-learner."""

    def __init__(self, base_models: list, meta_model):
        """Initialize stacking ensemble.

        Args:
            base_models: List of base model objects
            meta_model: Meta-learner model
        """
        self.base_models = base_models
        self.meta_model = meta_model
        self.is_fitted = False

    def fit(self, X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray):
        """Train base models and meta-learner.

        Args:
            X_train, y_train: Training data
            X_val, y_val: Validation data for meta-learner
        """
        # Train base models
        for model in self.base_models:
            logger.info(f"Training {model.__class__.__name__}")
            model.fit(X_train, y_train)

        # Generate meta features from validation set
        meta_features = self._generate_meta_features(X_val)

        # Train meta-learner
        logger.info("Training meta-learner")
        self.meta_model.fit(meta_features, y_val)

        self.is_fitted = True
        logger.info("Stacking ensemble training complete")

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions using stacking."""
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        meta_features = self._generate_meta_features(X)
        return self.meta_model.predict(meta_features)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get probability predictions."""
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        meta_features = self._generate_meta_features(X)

        if hasattr(self.meta_model, 'predict_proba'):
            return self.meta_model.predict_proba(meta_features)
        else:
            return self.meta_model.predict(meta_features)

    def _generate_meta_features(self, X: np.ndarray) -> np.ndarray:
        """Generate meta features from base model predictions."""
        meta_features_list = []

        for model in self.base_models:
            if hasattr(model, 'predict_proba'):
                predictions = model.predict_proba(X)
                # Take probability of positive class
                if predictions.ndim > 1:
                    predictions = predictions[:, 1]
            else:
                predictions = model.predict(X)

            meta_features_list.append(predictions)

        # Stack predictions column-wise
        return np.column_stack(meta_features_list)

    def get_base_model_weights(self) -> dict:
        """Get importance of each base model."""
        if not self.is_fitted:
            return {}

        # If meta_model has feature_importances_, use those as weights
        if hasattr(self.meta_model, 'feature_importances_'):
            importances = self.meta_model.feature_importances_
            weights = {
                model.__class__.__name__: float(imp)
                for model, imp in zip(self.base_models, importances)
            }
            return weights

        return {}
