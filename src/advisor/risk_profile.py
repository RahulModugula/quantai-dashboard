"""
Risk profiling questionnaire and scorer.

Produces a risk category used for asset allocation suggestions.
Categories: Conservative, Moderate, Aggressive, Very Aggressive
"""

from dataclasses import dataclass


@dataclass
class RiskProfile:
    score: int
    category: str
    description: str

    def dict(self) -> dict:
        return {
            "score": self.score,
            "category": self.category,
            "description": self.description,
        }


def score_risk_profile(
    age: int,
    income_stability: int,  # 1-5
    investment_horizon_years: int,
    loss_tolerance: int,  # 1-5
    existing_savings_months: int,  # Emergency fund coverage
    debt_to_income_pct: float,  # 0.0 to 1.0
) -> RiskProfile:
    """
    Score a user's risk profile based on key financial parameters.

    Scoring rubric (100 points total):
        Age factor (25 pts): Younger = higher score
        Horizon (20 pts): Longer = higher score
        Income stability (15 pts)
        Loss tolerance (20 pts)
        Emergency fund (10 pts)
        Debt ratio (10 pts): Lower debt = higher score
    """
    score = 0

    # Age factor (25 points) — classic rule: 100 - age = equity allocation
    age_score = max(0, min(25, int((100 - age) / 3)))
    score += age_score

    # Investment horizon (20 points)
    if investment_horizon_years >= 15:
        score += 20
    elif investment_horizon_years >= 10:
        score += 16
    elif investment_horizon_years >= 7:
        score += 12
    elif investment_horizon_years >= 5:
        score += 8
    elif investment_horizon_years >= 3:
        score += 4
    else:
        score += 0

    # Income stability (15 points)
    score += max(0, min(15, (income_stability - 1) * 4))

    # Loss tolerance (20 points)
    score += max(0, min(20, (loss_tolerance - 1) * 5))

    # Emergency fund (10 points)
    if existing_savings_months >= 12:
        score += 10
    elif existing_savings_months >= 6:
        score += 7
    elif existing_savings_months >= 3:
        score += 4
    else:
        score += 0

    # Debt ratio (10 points) — lower debt = better
    if debt_to_income_pct <= 0.1:
        score += 10
    elif debt_to_income_pct <= 0.2:
        score += 7
    elif debt_to_income_pct <= 0.35:
        score += 4
    elif debt_to_income_pct <= 0.5:
        score += 2
    else:
        score += 0

    score = min(100, max(0, score))

    if score >= 75:
        category = "Very Aggressive"
        description = (
            "You have a high risk capacity and can tolerate significant market volatility. "
            "Suitable for high-equity, growth-oriented portfolios."
        )
    elif score >= 55:
        category = "Aggressive"
        description = (
            "You can handle market volatility and have a long investment horizon. "
            "A growth-oriented portfolio with moderate debt allocation is suitable."
        )
    elif score >= 35:
        category = "Moderate"
        description = (
            "You prefer a balance between growth and stability. "
            "A balanced portfolio with equity and debt in roughly equal measure suits you."
        )
    else:
        category = "Conservative"
        description = (
            "You prefer capital preservation over high returns. "
            "A debt-heavy portfolio with limited equity exposure is suitable."
        )

    return RiskProfile(score=score, category=category, description=description)
