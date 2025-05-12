from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/advisor", tags=["advisor"])


class RiskProfileRequest(BaseModel):
    age: int = 30
    income_stability: int = 3  # 1-5 (1=unstable, 5=very stable)
    investment_horizon_years: int = 10
    loss_tolerance: int = 3  # 1-5 (1=cannot tolerate any loss, 5=can handle 50%+ loss)
    existing_savings_months: int = 6  # Emergency fund in months
    debt_to_income_pct: float = 0.2  # 0.0-1.0


@router.post("/risk-profile")
def get_risk_profile(req: RiskProfileRequest):
    """Score risk profile and return recommended asset allocation."""
    from src.advisor.risk_profile import score_risk_profile
    from src.advisor.allocation import get_allocation

    profile = score_risk_profile(
        age=req.age,
        income_stability=req.income_stability,
        investment_horizon_years=req.investment_horizon_years,
        loss_tolerance=req.loss_tolerance,
        existing_savings_months=req.existing_savings_months,
        debt_to_income_pct=req.debt_to_income_pct,
    )
    allocation = get_allocation(profile.category)

    return {
        "risk_profile": profile.dict(),
        "allocation": allocation.dict(),
        "disclaimer": "Educational purposes only. Consult a SEBI-registered financial advisor.",
    }


@router.get("/allocation/{risk_category}")
def get_allocation_by_category(risk_category: str):
    """Get asset allocation for a specific risk category."""
    from src.advisor.allocation import get_allocation
    allocation = get_allocation(risk_category)
    return allocation.dict()
