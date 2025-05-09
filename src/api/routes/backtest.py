from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from src.backtest.engine import WalkForwardBacktester
from src.backtest.report import generate_report
from src.config import settings
from src.data.storage import load_ohlcv, save_backtest_result
from src.models.training import walk_forward_train

router = APIRouter(prefix="/backtest", tags=["backtest"])

_backtest_cache: dict[str, dict] = {}


class BacktestRequest(BaseModel):
    ticker: str = "AAPL"
    initial_capital: float = 100_000.0
    buy_threshold: float = 0.6
    sell_threshold: float = 0.4


@router.post("/run")
async def run_backtest(req: BacktestRequest, background_tasks: BackgroundTasks):
    """Trigger a backtest run (runs in background for large datasets)."""
    key = f"{req.ticker}_{req.initial_capital}"
    _backtest_cache[key] = {"status": "running", "ticker": req.ticker}

    background_tasks.add_task(_run_backtest_task, req, key)
    return {"status": "started", "key": key, "ticker": req.ticker}


async def _run_backtest_task(req: BacktestRequest, cache_key: str):
    try:
        train_result = walk_forward_train(req.ticker)
        prices = load_ohlcv(req.ticker)

        backtester = WalkForwardBacktester(
            initial_capital=req.initial_capital,
            commission_pct=settings.commission_pct,
            buy_threshold=req.buy_threshold,
            sell_threshold=req.sell_threshold,
        )
        run = backtester.run(train_result.oos_predictions, prices)
        report = generate_report(run)

        save_backtest_result({
            "ticker": req.ticker,
            "start_date": report["equity_curve"][0]["date"] if report["equity_curve"] else None,
            "end_date": report["equity_curve"][-1]["date"] if report["equity_curve"] else None,
            "initial_capital": req.initial_capital,
            "final_value": run.final_value,
            **report["metrics"],
        })

        _backtest_cache[cache_key] = {"status": "complete", "result": report}
    except Exception as e:
        _backtest_cache[cache_key] = {"status": "error", "error": str(e)}


@router.get("/result/{key}")
def get_backtest_result(key: str):
    """Get a backtest result by cache key."""
    if key not in _backtest_cache:
        raise HTTPException(status_code=404, detail="Backtest result not found")
    return _backtest_cache[key]


@router.get("/results")
def list_backtest_results():
    """List all cached backtest results."""
    return {k: {"status": v["status"], "ticker": v.get("ticker")} for k, v in _backtest_cache.items()}
