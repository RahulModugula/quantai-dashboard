from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/sip", tags=["sip"])


class SIPRequest(BaseModel):
    monthly_amount: float = 10000.0
    duration_years: int = 20
    expected_return: float = 0.12
    inflation_rate: float = 0.06
    tax_rate: float = 0.10  # LTCG rate for equity mutual funds (India)
    step_up_pct: float = 0.0  # Annual step-up in SIP amount (0 = no step-up)


@router.post("/calculate")
def calculate_sip(req: SIPRequest):
    """Calculate SIP returns with pre-tax, post-tax, and inflation-adjusted values."""
    from src.advisor.sip import calculate_sip
    result = calculate_sip(
        monthly_amount=req.monthly_amount,
        duration_years=req.duration_years,
        expected_return=req.expected_return,
        inflation_rate=req.inflation_rate,
        tax_rate=req.tax_rate,
        step_up_pct=req.step_up_pct,
    )
    return result
