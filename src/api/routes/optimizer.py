from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/optimizer", tags=["optimizer"])


class OptimizeRequest(BaseModel):
    tickers: list[str] = ["AAPL", "MSFT", "GOOGL", "AMZN", "SPY"]
    period: int = 252
    method: str = "max_sharpe"  # max_sharpe, min_volatility, hrp


@router.post("/portfolio")
def optimize_portfolio(req: OptimizeRequest):
    """Optimize portfolio weights using mean-variance or HRP."""
    from src.advisor.optimizer import optimize_hrp, optimize_max_sharpe, optimize_min_volatility

    if req.method == "min_volatility":
        weights = optimize_min_volatility(req.tickers, req.period)
    elif req.method == "hrp":
        weights = optimize_hrp(req.tickers, req.period)
    else:
        weights = optimize_max_sharpe(req.tickers, req.period)

    return {"method": req.method, "weights": weights}


@router.post("/frontier")
def efficient_frontier(req: OptimizeRequest):
    """Compute efficient frontier for a set of tickers."""
    from src.advisor.optimizer import compute_efficient_frontier
    return compute_efficient_frontier(req.tickers, req.period)


class TuneRequest(BaseModel):
    ticker: str = "AAPL"
    n_trials: int = 30


@router.post("/tune")
def tune_thresholds(req: TuneRequest):
    """Optimize buy/sell thresholds using Optuna."""
    from src.models.tuning import optimize_thresholds
    return optimize_thresholds(req.ticker, n_trials=req.n_trials)
