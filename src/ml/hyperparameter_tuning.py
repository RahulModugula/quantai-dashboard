"""Hyperparameter tuning utilities for model optimization."""


class GridSearch:
    """Simple grid search for hyperparameters."""

    def __init__(self, param_grid: dict):
        self.param_grid = param_grid
        self.results = []

    def generate_combinations(self) -> list[dict]:
        """Generate all parameter combinations."""
        from itertools import product

        keys = self.param_grid.keys()
        values = self.param_grid.values()
        combinations = [dict(zip(keys, combo)) for combo in product(*values)]
        return combinations

    def best_params(self) -> dict:
        """Get best parameters from results."""
        if not self.results:
            return {}
        best = max(self.results, key=lambda x: x.get("score", 0))
        return best.get("params", {})


class RandomSearch:
    """Random search for hyperparameters (faster than grid search)."""

    def __init__(self, param_distributions: dict, n_iter: int = 10):
        self.param_distributions = param_distributions
        self.n_iter = n_iter
        self.results = []

    def sample_params(self) -> list[dict]:
        """Randomly sample parameters."""
        import random

        samples = []
        for _ in range(self.n_iter):
            params = {}
            for key, values in self.param_distributions.items():
                params[key] = random.choice(values)
            samples.append(params)
        return samples
