"""Automated hyperparameter optimization for models."""
import logging

logger = logging.getLogger(__name__)


class BayesianOptimizer:
    """Bayesian optimization for hyperparameter tuning."""

    def __init__(self, model, param_space: dict):
        self.model = model
        self.param_space = param_space
        self.history = []
        self.best_params = None
        self.best_score = float('-inf')

    def optimize(self, X_train, y_train, X_val, y_val, n_iterations: int = 10):
        """Run Bayesian optimization.

        Args:
            X_train, y_train: Training data
            X_val, y_val: Validation data
            n_iterations: Number of iterations
        """
        import random

        for iteration in range(n_iterations):
            # Random sampling from param space
            params = {
                key: random.choice(values)
                for key, values in self.param_space.items()
            }

            try:
                # Train and evaluate
                self.model.set_params(**params)
                self.model.fit(X_train, y_train)
                score = self.model.score(X_val, y_val)

                # Track
                self.history.append({
                    "iteration": iteration,
                    "params": params,
                    "score": score,
                })

                if score > self.best_score:
                    self.best_score = score
                    self.best_params = params

                logger.info(f"Iteration {iteration}: score={score:.4f}")

            except Exception as e:
                logger.warning(f"Iteration {iteration} failed: {e}")
                continue

        return self.best_params

    def get_history(self) -> list:
        """Get optimization history."""
        return self.history


class GridSearchOptimizer:
    """Exhaustive grid search over parameter space."""

    def __init__(self, model, param_grid: dict):
        self.model = model
        self.param_grid = param_grid
        self.results = []

    def optimize(self, X_train, y_train, X_val, y_val) -> dict:
        """Run grid search.

        Args:
            X_train, y_train: Training data
            X_val, y_val: Validation data

        Returns:
            Best parameters found
        """
        from itertools import product

        keys = self.param_grid.keys()
        values = self.param_grid.values()

        best_score = float('-inf')
        best_params = None

        for param_values in product(*values):
            params = dict(zip(keys, param_values))

            try:
                self.model.set_params(**params)
                self.model.fit(X_train, y_train)
                score = self.model.score(X_val, y_val)

                self.results.append({
                    "params": params,
                    "score": score,
                })

                if score > best_score:
                    best_score = score
                    best_params = params

            except Exception as e:
                logger.warning(f"Grid point {params} failed: {e}")
                continue

        return best_params

    def get_top_params(self, n: int = 5) -> list:
        """Get top N parameter combinations."""
        sorted_results = sorted(self.results, key=lambda x: x["score"], reverse=True)
        return [r["params"] for r in sorted_results[:n]]
