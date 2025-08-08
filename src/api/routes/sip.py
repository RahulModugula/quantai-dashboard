import logging
from fastapi import APIRouter, HTTPException

from src.data.schemas import SIPRequest, ReverseSIPRequest

router = APIRouter(prefix="/sip", tags=["sip"])
logger = logging.getLogger(__name__)


@router.post("/calculate")
def calculate_sip(req: SIPRequest) -> dict:
    """Calculate SIP returns with pre-tax, post-tax, and inflation-adjusted values."""
    try:
        from src.advisor.sip import calculate_sip as sip_calculate
        result = sip_calculate(
            monthly_amount=req.monthly_amount,
            duration_years=req.duration_years,
            expected_return=req.expected_annual_return,
            step_up_pct=req.annual_step_up,
        )
        return result.model_dump() if hasattr(result, "model_dump") else result
    except Exception as e:
        logger.error(f"Error calculating SIP: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"SIP calculation failed: {str(e)}")


@router.post("/reverse")
def reverse_sip_endpoint(req: ReverseSIPRequest) -> dict:
    """Goal-based SIP: calculate required monthly investment for a target corpus."""
    try:
        from src.advisor.sip import reverse_sip
        result = reverse_sip(
            target_corpus=req.target_corpus,
            duration_years=req.duration_years,
            expected_return=req.expected_annual_return,
            step_up_pct=req.annual_step_up,
        )
        return result.model_dump() if hasattr(result, "model_dump") else result
    except Exception as e:
        logger.error(f"Error calculating reverse SIP: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Reverse SIP calculation failed: {str(e)}")
