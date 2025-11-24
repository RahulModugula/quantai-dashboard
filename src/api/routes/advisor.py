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


@router.post("/rebalance/equal-weight")
def suggest_equal_weight_rebalance() -> dict:
    """Suggest rebalancing portfolio to equal weight across holdings."""
    try:
        from src.api.dependencies import get_paper_trader
        from src.advisor.rebalancing import PortfolioRebalancer

        trader = get_paper_trader()
        portfolio = trader.portfolio

        if not portfolio.positions:
            return {
                "actions": [],
                "message": "No open positions to rebalance",
                "total_trades": 0,
            }

        actions = PortfolioRebalancer.suggest_equal_weight(
            positions=portfolio.positions,
            portfolio_value=portfolio.get_value({}),
        )

        return {
            "actions": [
                {
                    "ticker": a.ticker,
                    "action": a.action,
                    "current_pct": round(a.current_pct, 2),
                    "target_pct": round(a.target_pct, 2),
                    "shares_to_trade": a.shares_to_trade,
                    "estimated_value": round(a.estimated_value, 2),
                    "reason": a.reason,
                }
                for a in actions
            ],
            "total_trades": len(actions),
            "disclaimer": "Educational purposes. Not financial advice.",
        }
    except Exception as e:
        logger.error(f"Error generating rebalance suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Rebalancing failed: {str(e)}")


@router.post("/rebalance/reduce-risk")
def suggest_risk_reduction_rebalance(max_position_pct: float = 0.30) -> dict:
    """Suggest selling oversized positions to reduce concentration risk."""
    try:
        from src.api.dependencies import get_paper_trader
        from src.advisor.rebalancing import PortfolioRebalancer

        trader = get_paper_trader()
        portfolio = trader.portfolio

        actions = PortfolioRebalancer.suggest_risk_reduction(
            positions=portfolio.positions,
            portfolio_value=portfolio.get_value({}),
            max_position_pct=max_position_pct,
        )

        if not actions:
            return {
                "actions": [],
                "message": f"No positions exceed {max_position_pct * 100:.0f}% threshold",
                "total_trades": 0,
            }

        tax_impact = PortfolioRebalancer.estimate_tax_impact(actions)

        return {
            "actions": [
                {
                    "ticker": a.ticker,
                    "action": a.action,
                    "current_pct": round(a.current_pct, 2),
                    "target_pct": round(a.target_pct, 2),
                    "shares_to_trade": a.shares_to_trade,
                    "estimated_value": round(a.estimated_value, 2),
                    "reason": a.reason,
                }
                for a in actions
            ],
            "tax_impact": tax_impact,
            "total_trades": len(actions),
            "disclaimer": "Tax estimates are rough. Consult a tax professional.",
        }
    except Exception as e:
        logger.error(f"Error generating risk reduction suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Risk reduction analysis failed: {str(e)}")
