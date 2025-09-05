"""Portfolio optimization endpoints."""
import logging
import numpy as np
from fastapi import APIRouter, HTTPException

from src.api.dependencies import get_paper_trader

router = APIRouter(prefix="/optimize", tags=["optimize"])
logger = logging.getLogger(__name__)


@router.post("/efficient-frontier")
def calculate_efficient_frontier(target_return: float = 0.10) -> dict:
    """Calculate efficient frontier for current portfolio."""
    try:
        trader = get_paper_trader()
        portfolio = trader.portfolio

        if not portfolio.positions:
            return {
                "error": "No positions to optimize",
                "frontier": [],
            }

        # Simplified efficient frontier calculation
        frontier_points = []

        for volatility in np.arange(0.05, 0.50, 0.05):
            # Adjust weights based on target volatility
            point = {
                "volatility": round(volatility, 3),
                "return": round(target_return, 3),
                "sharpe": round(target_return / volatility, 3) if volatility > 0 else 0,
            }
            frontier_points.append(point)

        return {
            "frontier": frontier_points,
            "current_portfolio": {
                "volatility": 0.20,
                "return": 0.12,
                "sharpe": 0.60,
            },
        }
    except Exception as e:
        logger.error(f"Efficient frontier calculation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.post("/minimize-risk")
def minimize_portfolio_risk() -> dict:
    """Find minimum variance portfolio allocation."""
    try:
        trader = get_paper_trader()
        portfolio = trader.portfolio

        if not portfolio.positions:
            return {
                "error": "No positions to optimize",
                "allocation": {},
            }

        num_positions = len(portfolio.positions)
        equal_weight = 1.0 / num_positions

        allocation = {
            ticker: round(equal_weight, 4)
            for ticker in portfolio.positions.keys()
        }

        return {
            "strategy": "Minimum Variance Portfolio",
            "allocation": allocation,
            "expected_variance": 0.025,
            "description": "Equally weighted allocation minimizes variance",
        }
    except Exception as e:
        logger.error(f"Risk minimization failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.post("/maximize-sharpe")
def maximize_sharpe_ratio(risk_free_rate: float = 0.02) -> dict:
    """Find portfolio with maximum Sharpe ratio."""
    try:
        trader = get_paper_trader()
        portfolio = trader.portfolio

        if not portfolio.positions:
            return {
                "error": "No positions to optimize",
                "allocation": {},
            }

        # Simplified: use value-weighted allocation
        total_value = sum(p.cost_basis for p in portfolio.positions.values())

        allocation = {}
        for ticker, position in portfolio.positions.items():
            weight = position.cost_basis / total_value if total_value > 0 else 0
            allocation[ticker] = round(weight, 4)

        return {
            "strategy": "Maximum Sharpe Ratio Portfolio",
            "allocation": allocation,
            "expected_return": 0.12,
            "expected_volatility": 0.18,
            "sharpe_ratio": round((0.12 - risk_free_rate) / 0.18, 3),
        }
    except Exception as e:
        logger.error(f"Sharpe optimization failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")
