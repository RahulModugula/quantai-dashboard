import logging
from fastapi import APIRouter, HTTPException

from src.data.schemas import RiskProfileRequest

router = APIRouter(prefix="/advisor", tags=["advisor"])
logger = logging.getLogger(__name__)


@router.post("/risk-profile")
def get_risk_profile(req: RiskProfileRequest) -> dict:
    """Score risk profile and return recommended asset allocation."""
    try:
        from src.advisor.risk_profile import score_risk_profile
        from src.advisor.allocation import get_allocation

        profile = score_risk_profile(
            age=req.age,
            investment_horizon_years=req.investment_horizon_years,
            annual_income=req.annual_income,
            monthly_savings=req.monthly_savings,
            has_emergency_fund=req.has_emergency_fund,
            debt_ratio=req.debt_ratio,
        )
        allocation = get_allocation(profile.category)

        return {
            "risk_profile": profile.model_dump(),
            "allocation": allocation.model_dump(),
            "disclaimer": "Educational purposes only. Consult a SEBI-registered financial advisor.",
        }
    except Exception as e:
        logger.error(f"Error scoring risk profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Risk profile calculation failed: {str(e)}")


@router.get("/allocation/{risk_category}")
def get_allocation_by_category(risk_category: str) -> dict:
    """Get asset allocation for a specific risk category."""
    try:
        from src.advisor.allocation import get_allocation
        allocation = get_allocation(risk_category)
        return allocation.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid risk category: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting allocation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Allocation lookup failed: {str(e)}")
