import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from src.data.schemas import OptimizerRequest

router = APIRouter(prefix="/optimizer", tags=["optimizer"])
logger = logging.getLogger(__name__)


class TuneRequest(BaseModel):
    ticker: str = "AAPL"
    n_trials: int = 30

    @field_validator("n_trials")
    @classmethod
    def validate_trials(cls, v: int) -> int:
        if v <= 0 or v > 500:
            raise ValueError("n_trials must be between 1 and 500")
        return v


@router.post("/portfolio")
def optimize_portfolio(req: OptimizerRequest) -> dict:
    """Optimize portfolio weights using mean-variance or HRP."""
    try:
        from src.advisor.optimizer import optimize_hrp, optimize_max_sharpe, optimize_min_volatility

        method = req.expected_return_type  # Use this field for method selection
        if method == "min_volatility":
            weights = optimize_min_volatility(req.tickers, req.lookback_days)
        elif method == "hrp":
            weights = optimize_hrp(req.tickers, req.lookback_days)
        else:
            weights = optimize_max_sharpe(req.tickers, req.lookback_days)

        return {"method": method, "weights": weights}
    except Exception as e:
        logger.error(f"Error optimizing portfolio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Portfolio optimization failed: {str(e)}")


@router.post("/frontier")
def efficient_frontier(req: OptimizerRequest) -> dict:
    """Compute efficient frontier for a set of tickers."""
    try:
        from src.advisor.optimizer import compute_efficient_frontier

        return compute_efficient_frontier(req.tickers, req.lookback_days)
    except Exception as e:
        logger.error(f"Error computing efficient frontier: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Frontier computation failed: {str(e)}")


@router.post("/tune")
def tune_thresholds(req: TuneRequest) -> dict:
    """Optimize buy/sell thresholds using Optuna."""
    try:
        from src.models.tuning import optimize_thresholds

        return optimize_thresholds(req.ticker, n_trials=req.n_trials)
    except Exception as e:
        logger.error(f"Error tuning thresholds: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Threshold tuning failed: {str(e)}")
