"""
Asset allocation suggestions based on risk profile.

Asset classes:
  - Large Cap Equity: Blue-chip stocks / large-cap index funds
  - Mid Cap Equity: Mid-cap funds / ETFs
  - Small Cap Equity: Small-cap funds (high risk/reward)
  - International Equity: Global diversification
  - Debt / Bonds: Government/corporate bonds, liquid funds
  - Gold: Inflation hedge
"""

from dataclasses import dataclass


@dataclass
class AllocationSuggestion:
    risk_category: str
    allocations: dict
    rationale: str

    def dict(self) -> dict:
        return {
            "risk_category": self.risk_category,
            "allocations": self.allocations,
            "rationale": self.rationale,
        }


_ALLOCATION_MAP = {
    "Conservative": {
        "allocations": {
            "Large Cap Equity": 10,
            "Mid Cap Equity": 0,
            "Small Cap Equity": 0,
            "International Equity": 5,
            "Debt / Bonds": 70,
            "Gold": 15,
        },
        "rationale": (
            "Capital preservation is the primary goal. Heavy debt allocation provides stability, "
            "gold acts as an inflation hedge, and minimal equity limits volatility exposure."
        ),
    },
    "Moderate": {
        "allocations": {
            "Large Cap Equity": 30,
            "Mid Cap Equity": 10,
            "Small Cap Equity": 5,
            "International Equity": 5,
            "Debt / Bonds": 40,
            "Gold": 10,
        },
        "rationale": (
            "Balanced between growth and stability. Equity exposure skewed toward large-cap "
            "for quality, with meaningful debt buffer to reduce volatility."
        ),
    },
    "Aggressive": {
        "allocations": {
            "Large Cap Equity": 35,
            "Mid Cap Equity": 20,
            "Small Cap Equity": 15,
            "International Equity": 10,
            "Debt / Bonds": 15,
            "Gold": 5,
        },
        "rationale": (
            "Growth-oriented with diversified equity across market caps. "
            "Small international exposure for global diversification. "
            "Minimal debt allocation as a liquidity buffer."
        ),
    },
    "Very Aggressive": {
        "allocations": {
            "Large Cap Equity": 30,
            "Mid Cap Equity": 25,
            "Small Cap Equity": 25,
            "International Equity": 15,
            "Debt / Bonds": 5,
            "Gold": 0,
        },
        "rationale": (
            "Maximum growth focus with high allocation across all equity market caps. "
            "Strong international exposure for diversification. "
            "Near-zero debt — investor can withstand short-term losses for long-term gains."
        ),
    },
}


def get_allocation(risk_category: str) -> AllocationSuggestion:
    """Get the recommended asset allocation for a risk category."""
    key = risk_category.strip().title()

    # Normalize
    for k in _ALLOCATION_MAP:
        if k.lower() == key.lower():
            key = k
            break

    if key not in _ALLOCATION_MAP:
        key = "Moderate"

    data = _ALLOCATION_MAP[key]
    return AllocationSuggestion(
        risk_category=key,
        allocations=data["allocations"],
        rationale=data["rationale"],
    )
