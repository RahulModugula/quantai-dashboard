"""Sector and industry analysis tools for portfolio insights."""
import logging
from typing import List

logger = logging.getLogger(__name__)

# Simple sector mapping for common tickers
TICKER_SECTORS = {
    "AAPL": "Technology",
    "MSFT": "Technology",
    "GOOGL": "Technology",
    "AMZN": "Consumer Cyclical",
    "TSLA": "Consumer Cyclical",
    "JNJ": "Healthcare",
    "PFE": "Healthcare",
    "XOM": "Energy",
    "CVX": "Energy",
    "JPM": "Financials",
    "BAC": "Financials",
    "GE": "Industrials",
    "CAT": "Industrials",
    "PG": "Consumer Defensive",
    "KO": "Consumer Defensive",
    "NFLX": "Communication",
    "DIS": "Communication",
}


class SectorAnalyzer:
    """Analyze portfolio sector composition and exposure."""

    @staticmethod
    def get_sector(ticker: str) -> str:
        """Get sector for a ticker."""
        ticker_upper = ticker.upper()
        return TICKER_SECTORS.get(ticker_upper, "Unknown")

    @staticmethod
    def analyze_portfolio(positions: dict, portfolio_value: float) -> dict:
        """Analyze sector composition of portfolio.

        Args:
            positions: {ticker: Position} dict
            portfolio_value: Total portfolio value

        Returns:
            Dict with sector breakdown, concentration, and diversification score
        """
        if not positions or portfolio_value == 0:
            return {
                "sectors": {},
                "sector_count": 0,
                "concentration_pct": 0.0,
                "diversification_score": 0.0,
                "message": "No positions to analyze",
            }

        sector_values = {}
        for ticker, position in positions.items():
            sector = SectorAnalyzer.get_sector(ticker)
            value = position.cost_basis
            sector_values[sector] = sector_values.get(sector, 0) + value

        # Calculate percentages and concentration
        sector_pcts = {
            sector: (value / portfolio_value * 100)
            for sector, value in sorted(sector_values.items(), key=lambda x: x[1], reverse=True)
        }

        # Herfindahl-Hirschman Index for concentration (0-10000 scale, higher = more concentrated)
        hhi = sum((pct ** 2) for pct in sector_pcts.values())
        concentration_pct = hhi / 100  # Convert to percentage

        # Simple diversification score (0-100, higher = more diversified)
        sector_count = len(sector_pcts)
        max_sectors = 10
        diversification_score = (sector_count / max_sectors) * 100 * (1 - concentration_pct / 100)

        return {
            "sectors": {sector: round(pct, 1) for sector, pct in sector_pcts.items()},
            "sector_count": sector_count,
            "concentration_pct": round(concentration_pct, 2),
            "diversification_score": round(max(0, min(100, diversification_score)), 2),
            "concentration_level": SectorAnalyzer._concentration_level(concentration_pct),
        }

    @staticmethod
    def _concentration_level(concentration_pct: float) -> str:
        """Get human-readable concentration level."""
        if concentration_pct < 25:
            return "Low (well-diversified)"
        elif concentration_pct < 50:
            return "Moderate"
        elif concentration_pct < 75:
            return "High"
        else:
            return "Very High (concentrated)"

    @staticmethod
    def find_sector_gaps(positions: dict, target_sectors: List[str]) -> dict:
        """Identify which target sectors are missing from portfolio.

        Args:
            positions: {ticker: Position} dict
            target_sectors: List of desired sectors (e.g., ["Technology", "Healthcare", "Financials"])

        Returns:
            Dict with missing sectors and allocation suggestions
        """
        if not positions:
            return {
                "missing_sectors": target_sectors,
                "suggestion": f"Add positions in all sectors: {', '.join(target_sectors)}",
            }

        held_sectors = {SectorAnalyzer.get_sector(t) for t in positions.keys()}
        missing = set(target_sectors) - held_sectors

        if not missing:
            return {
                "missing_sectors": [],
                "message": "Portfolio covers all target sectors",
            }

        suggested_weight = 100 / len(target_sectors) if target_sectors else 0
        return {
            "missing_sectors": list(missing),
            "missing_count": len(missing),
            "suggestion": f"Add {len(missing)} missing sectors: {', '.join(missing)}",
            "suggested_weight_pct": round(suggested_weight, 1),
        }

    @staticmethod
    def get_examples_per_sector(sector: str) -> List[str]:
        """Get example tickers in a given sector."""
        examples = []
        for ticker, s in TICKER_SECTORS.items():
            if s.lower() == sector.lower():
                examples.append(ticker)
        return examples[:5]  # Return up to 5 examples
