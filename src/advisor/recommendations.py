"""
Portfolio rebalancing recommendations.

Compares current allocation vs target allocation and suggests moves.
"""

from src.advisor.allocation import get_allocation
from src.advisor.risk_profile import RiskProfile


def generate_recommendations(
    risk_profile: RiskProfile,
    current_allocation: dict[str, float],
) -> list[dict]:
    """
    Generate rebalancing recommendations.

    Args:
        risk_profile: The user's risk profile
        current_allocation: Dict of asset_class -> percentage (must sum to ~100)

    Returns:
        List of recommendation dicts with action, asset, current, target, delta
    """
    target = get_allocation(risk_profile.category)
    recommendations = []

    all_asset_classes = set(target.allocations.keys()) | set(current_allocation.keys())

    for asset in sorted(all_asset_classes):
        current_pct = current_allocation.get(asset, 0)
        target_pct = target.allocations.get(asset, 0)
        delta = target_pct - current_pct

        if abs(delta) < 2:  # < 2% deviation is fine
            action = "hold"
        elif delta > 0:
            action = "increase"
        else:
            action = "reduce"

        recommendations.append(
            {
                "asset_class": asset,
                "current_pct": round(current_pct, 1),
                "target_pct": round(target_pct, 1),
                "delta_pct": round(delta, 1),
                "action": action,
                "priority": "high" if abs(delta) >= 10 else "medium" if abs(delta) >= 5 else "low",
            }
        )

    # Sort by priority (high first) then abs delta
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda x: (priority_order[x["priority"]], -abs(x["delta_pct"])))

    return recommendations
