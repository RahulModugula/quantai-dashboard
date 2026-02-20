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

    def _block_bootstrap(self, returns: np.ndarray, rng: np.random.Generator) -> np.ndarray:
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
                representative_paths.append([round(float(v), 2) for v in equity])

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
            "expected_return": round(float(terminal_values.mean() / initial_value - 1), 6),
            "var_95": round(var_95, 6),
            "cvar_95": round(cvar_95, 6),
            "max_drawdown_median": round(float(np.median(max_drawdowns)), 6),
            "paths": representative_paths,
        }


SCENARIOS = {
    "covid_crash_2020": ("2020-02-19", "2020-03-23"),
    "rate_hike_2022": ("2022-01-01", "2022-10-15"),
    "dotcom_bust": ("2000-03-10", "2002-10-09"),
    "gfc_2008": ("2008-09-01", "2009-03-09"),
    "flash_crash_2010": ("2010-05-06", "2010-05-07"),
}


class HistoricalScenarioTest:
    """Replay specific historical crisis periods against a price DataFrame.

    Each scenario returns the period total return, max drawdown, and duration.
    When price history doesn't cover the scenario window, available=False is returned
    instead of raising an error, allowing callers to handle gaps gracefully.
    """

    def _compute_max_drawdown(self, price_slice: pd.Series) -> float:
        if price_slice.empty or len(price_slice) < 2:
            return 0.0
        running_max = price_slice.cummax()
        dd = (price_slice - running_max) / running_max
        return float(dd.min())

    def replay(self, prices: pd.DataFrame, scenario_name: str) -> dict:
        """Compute what the portfolio would have returned during a historical period.

        Args:
            prices: DataFrame with DatetimeIndex and at least one numeric (close) column.
            scenario_name: One of the keys in SCENARIOS.

        Returns:
            Dict with scenario, period, return, max_drawdown, duration_days, available.
        """
        if scenario_name not in SCENARIOS:
            raise ValueError(f"Unknown scenario '{scenario_name}'. Valid: {list(SCENARIOS.keys())}")

        start_str, end_str = SCENARIOS[scenario_name]
        start_ts = pd.Timestamp(start_str)
        end_ts = pd.Timestamp(end_str)

        if not isinstance(prices.index, pd.DatetimeIndex):
            if "date" in prices.columns:
                prices = prices.set_index(pd.to_datetime(prices["date"]))
            else:
                prices.index = pd.to_datetime(prices.index)

        available = (prices.index.min() <= start_ts) and (prices.index.max() >= end_ts)
        duration_days = (end_ts - start_ts).days

        if not available:
            return {
                "scenario": scenario_name,
                "period": {"start": start_str, "end": end_str},
                "return": None,
                "max_drawdown": None,
                "duration_days": duration_days,
                "available": False,
            }

        mask = (prices.index >= start_ts) & (prices.index <= end_ts)
        slice_df = prices.loc[mask]

        if slice_df.empty:
            return {
                "scenario": scenario_name,
                "period": {"start": start_str, "end": end_str},
                "return": None,
                "max_drawdown": None,
                "duration_days": duration_days,
                "available": False,
            }

        numeric_cols = slice_df.select_dtypes(include=[np.number]).columns.tolist()
        asset_returns = slice_df[numeric_cols].iloc[-1] / slice_df[numeric_cols].iloc[0] - 1.0
        portfolio_return = float(asset_returns.mean())
        equal_weight_index = slice_df[numeric_cols].mean(axis=1)
        mdd = self._compute_max_drawdown(equal_weight_index)

        return {
            "scenario": scenario_name,
            "period": {"start": start_str, "end": end_str},
            "return": round(portfolio_return, 6),
            "max_drawdown": round(mdd, 6),
            "duration_days": duration_days,
            "available": True,
        }

    def run_all(self, prices: pd.DataFrame) -> list[dict]:
        """Run all scenarios, sorted by worst return. Unavailable scenarios appended last."""
        results = [self.replay(prices, name) for name in SCENARIOS]
        available = sorted([r for r in results if r["available"]], key=lambda r: r["return"])
        unavailable = [r for r in results if not r["available"]]
        return available + unavailable
