"""Performance attribution and analysis tools."""

import logging

logger = logging.getLogger(__name__)


class PerformanceAttribution:
    """Analyze sources of portfolio returns."""

    @staticmethod
    def attribution_by_position(
        portfolio_returns: dict[str, float],
        position_values: dict[str, float],
    ) -> dict[str, float]:
        """Calculate return contribution by position.

        Args:
            portfolio_returns: {ticker: return} as fraction
            position_values: {ticker: value} in dollars

        Returns:
            {ticker: contribution} as fraction of total return
        """
        if not position_values or not portfolio_returns:
            return {}

        total_value = sum(position_values.values())
        if total_value == 0:
            return {}

        attribution = {}
        for ticker, ret in portfolio_returns.items():
            weight = position_values.get(ticker, 0) / total_value
            contribution = weight * ret
            attribution[ticker] = contribution

        return attribution

    @staticmethod
    def return_decomposition(
        total_return: float,
        risk_free_rate: float,
    ) -> dict:
        """Decompose return into alpha and beta components.

        Args:
            total_return: Total portfolio return
            risk_free_rate: Risk-free return rate

        Returns:
            Dict with excess return and components
        """
        excess_return = total_return - risk_free_rate

        return {
            "total_return": total_return,
            "risk_free_rate": risk_free_rate,
            "excess_return": excess_return,
        }

    @staticmethod
    def compare_to_benchmark(
        portfolio_return: float,
        benchmark_return: float,
    ) -> dict:
        """Calculate outperformance vs benchmark.

        Args:
            portfolio_return: Portfolio return
            benchmark_return: Benchmark return

        Returns:
            Outperformance analysis
        """
        outperformance = portfolio_return - benchmark_return

        return {
            "portfolio_return": portfolio_return,
            "benchmark_return": benchmark_return,
            "outperformance": outperformance,
            "outperformance_pct": (outperformance / abs(benchmark_return * 100))
            if benchmark_return != 0
            else 0,
        }
