"""Stress testing and scenario analysis for portfolios."""

import logging
import numpy as np

logger = logging.getLogger(__name__)


class StressTestScenario:
    """Define and run stress test scenarios."""

    def __init__(self, name: str, market_shock_pct: float):
        self.name = name
        self.market_shock_pct = market_shock_pct
        self.results = None

    def apply_shock_to_portfolio(self, portfolio_values: dict) -> dict:
        """Apply market shock to portfolio holdings."""
        shocked = {}
        for ticker, value in portfolio_values.items():
            # Apply shock (negative for drawdown, positive for rally)
            shocked[ticker] = value * (1 + self.market_shock_pct)
        return shocked

    def estimate_max_loss(self, portfolio_value: float) -> float:
        """Estimate maximum portfolio loss under shock."""
        loss_pct = abs(self.market_shock_pct) if self.market_shock_pct < 0 else 0
        return portfolio_value * loss_pct


class StressTestRunner:
    """Run multiple stress test scenarios."""

    # Common stress scenarios
    SCENARIOS = {
        "market_crash_10": StressTestScenario("10% Market Crash", -0.10),
        "market_crash_20": StressTestScenario("20% Market Crash", -0.20),
        "market_crash_30": StressTestScenario("30% Market Crash", -0.30),
        "market_rally_10": StressTestScenario("10% Market Rally", 0.10),
        "volatility_spike": StressTestScenario("Volatility Spike", -0.15),
        "sector_rotation": StressTestScenario("Sector Rotation", -0.10),
    }

    @classmethod
    def run_scenario(cls, scenario_name: str, portfolio_value: float) -> dict:
        """Run a single stress test scenario."""
        if scenario_name not in cls.SCENARIOS:
            return {"error": f"Unknown scenario: {scenario_name}"}

        scenario = cls.SCENARIOS[scenario_name]
        max_loss = scenario.estimate_max_loss(portfolio_value)

        return {
            "scenario": scenario.name,
            "shock_pct": scenario.market_shock_pct * 100,
            "current_value": portfolio_value,
            "estimated_value": portfolio_value * (1 + scenario.market_shock_pct),
            "max_loss": max_loss,
            "max_loss_pct": abs(scenario.market_shock_pct) * 100,
        }

    @classmethod
    def run_all_scenarios(cls, portfolio_value: float) -> list[dict]:
        """Run all stress test scenarios."""
        results = []
        for scenario_name in cls.SCENARIOS.keys():
            result = cls.run_scenario(scenario_name, portfolio_value)
            results.append(result)
        return results

    @classmethod
    def monte_carlo_simulation(
        cls,
        portfolio_value: float,
        daily_volatility: float,
        days: int = 252,
        simulations: int = 1000,
    ) -> dict:
        """Run Monte Carlo simulation of portfolio outcomes."""
        results = []

        for _ in range(simulations):
            value = portfolio_value
            for _ in range(days):
                daily_return = np.random.normal(0, daily_volatility)
                value *= 1 + daily_return
            results.append(value)

        results = np.array(results)

        return {
            "simulations": simulations,
            "days": days,
            "initial_value": portfolio_value,
            "mean_final_value": float(np.mean(results)),
            "median_final_value": float(np.median(results)),
            "std_dev": float(np.std(results)),
            "worst_case": float(np.min(results)),
            "best_case": float(np.max(results)),
            "value_at_risk_95": float(np.percentile(results, 5)),  # 95% VaR
            "value_at_risk_99": float(np.percentile(results, 1)),  # 99% VaR
        }
