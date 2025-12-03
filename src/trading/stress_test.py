"""Portfolio stress testing: Monte Carlo simulation and historical scenario analysis.

Two approaches:
1. Monte Carlo: simulate N paths of portfolio returns using bootstrapped daily returns
2. Historical scenarios: replay specific crisis periods and compute portfolio drawdown
"""

import numpy as np
import pandas as pd


class MonteCarloStressTest:
    """Monte Carlo portfolio stress test using block bootstrap simulation.

    Block bootstrap with block_size=20 preserves the autocorrelation
    structure of daily returns (momentum, mean-reversion clustering).
    """

    def __init__(
        self,
        n_simulations: int = 1000,
        horizon_days: int = 252,
        seed: int = 42,
        block_size: int = 20,
    ):
        self.n_simulations = n_simulations
        self.horizon_days = horizon_days
        self.seed = seed
        self.block_size = block_size

    def _block_bootstrap(
        self, returns: np.ndarray, rng: np.random.Generator
    ) -> np.ndarray:
        """Draw a single bootstrapped path of length horizon_days using block bootstrap."""
        n = len(returns)
        path = []
        while len(path) < self.horizon_days:
            start = rng.integers(0, n - self.block_size + 1)
            block = returns[start : start + self.block_size]
            path.extend(block.tolist())
        return np.array(path[: self.horizon_days])

    def run(self, daily_returns: pd.Series, initial_value: float = 100_000.0) -> dict:
        """Simulate N portfolio paths over horizon_days.

        Args:
            daily_returns: Historical daily returns (used to fit bootstrap distribution)
            initial_value: Starting portfolio value

        Returns:
            {
                "percentiles": {5: float, 25: float, 50: float, 75: float, 95: float},
                "prob_loss": float,          # P(final_value < initial_value)
                "expected_return": float,    # mean final/initial - 1
                "var_95": float,             # 95% VaR (1-day, positive loss)
                "cvar_95": float,            # 95% CVaR / Expected Shortfall
                "max_drawdown_median": float,# median max drawdown across simulations
                "paths": list,               # list of 100 representative paths (every 10th sim)
            }
        """
        returns_arr = daily_returns.dropna().values
        rng = np.random.default_rng(self.seed)

        terminal_values = np.empty(self.n_simulations)
        max_drawdowns = np.empty(self.n_simulations)
        representative_paths = []

        for i in range(self.n_simulations):
            path_returns = self._block_bootstrap(returns_arr, rng)
            # Build equity path
            equity = initial_value * np.cumprod(1.0 + path_returns)
            terminal_values[i] = equity[-1]

            # Max drawdown for this path
            running_max = np.maximum.accumulate(np.concatenate([[initial_value], equity]))
            drawdowns = (equity - running_max[1:]) / running_max[1:]
            max_drawdowns[i] = float(drawdowns.min())

            # Keep every 10th simulation as a representative path
            if i % 10 == 0:
                representative_paths.append(
                    [round(float(v), 2) for v in equity]
                )

        # VaR and CVaR on 1-day returns from the historical series
        var_95 = float(-np.percentile(returns_arr, 5))
        cvar_mask = returns_arr <= -var_95
        cvar_95 = float(-returns_arr[cvar_mask].mean()) if cvar_mask.any() else var_95

        percentiles = {
            5: round(float(np.percentile(terminal_values, 5)), 2),
            25: round(float(np.percentile(terminal_values, 25)), 2),
            50: round(float(np.percentile(terminal_values, 50)), 2),
            75: round(float(np.percentile(terminal_values, 75)), 2),
            95: round(float(np.percentile(terminal_values, 95)), 2),
        }

        return {
            "percentiles": percentiles,
            "prob_loss": round(float((terminal_values < initial_value).mean()), 4),
            "expected_return": round(
                float(terminal_values.mean() / initial_value - 1), 6
            ),
            "var_95": round(var_95, 6),
            "cvar_95": round(cvar_95, 6),
            "max_drawdown_median": round(float(np.median(max_drawdowns)), 6),
            "paths": representative_paths,
        }
