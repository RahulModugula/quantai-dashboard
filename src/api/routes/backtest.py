import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException

from src.backtest.engine import WalkForwardBacktester
from src.backtest.report import generate_report
from src.config import settings
from src.data.schemas import BacktestRequestSchema
from src.data.storage import load_ohlcv, save_backtest_result
from src.models.training import walk_forward_train

router = APIRouter(prefix="/backtest", tags=["backtest"])
logger = logging.getLogger(__name__)

_backtest_cache: dict[str, dict] = {}


@router.post("/run")
async def run_backtest(req: BacktestRequestSchema, background_tasks: BackgroundTasks) -> dict:
    """Trigger a backtest run (runs in background for large datasets)."""
    key = f"{req.ticker}_{req.initial_capital}"
    _backtest_cache[key] = {"status": "running", "ticker": req.ticker}
    background_tasks.add_task(_run_backtest_task, req, key)
    return {"status": "started", "key": key, "ticker": req.ticker}


async def _run_backtest_task(req: BacktestRequestSchema, cache_key: str) -> None:
    """Background task to run backtest and cache results."""
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

        save_backtest_result(
            {
                "ticker": req.ticker,
                "start_date": report["equity_curve"][0]["date"] if report["equity_curve"] else None,
                "end_date": report["equity_curve"][-1]["date"] if report["equity_curve"] else None,
                "initial_capital": req.initial_capital,
                "final_value": run.final_value,
                **report["metrics"],
            }
        )

        _backtest_cache[cache_key] = {"status": "complete", "result": report}
        logger.info(f"Backtest completed for {req.ticker}")
    except Exception as e:
        logger.error(f"Backtest failed for {req.ticker}: {e}", exc_info=True)
        _backtest_cache[cache_key] = {"status": "error", "error": str(e)}


@router.get("/result/{key}")
def get_backtest_result(key: str) -> dict:
    """Get a backtest result by cache key."""
    if key not in _backtest_cache:
        raise HTTPException(status_code=404, detail="Backtest result not found")
    return _backtest_cache[key]


@router.get("/results")
def list_backtest_results() -> dict[str, dict]:
    """List all cached backtest results."""
    return {
        k: {"status": v["status"], "ticker": v.get("ticker")} for k, v in _backtest_cache.items()
    }


@router.get("/export/{key}/trades")
def export_trades_csv(key: str):
    """Export trades from backtest result as CSV."""
    if key not in _backtest_cache:
        raise HTTPException(status_code=404, detail="Backtest result not found")

    result = _backtest_cache[key]
    if result["status"] != "complete":
        raise HTTPException(status_code=400, detail="Backtest not complete")

    trades = result["result"]["trades"]
    if not trades:
        csv_data = "date,ticker,side,shares,price,commission,pnl\n"
    else:
        import csv
        import io

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=trades[0].keys())
        writer.writeheader()
        writer.writerows(trades)
        csv_data = output.getvalue()

    return {
        "csv": csv_data,
        "filename": f"{result.get('ticker')}_trades_{key}.csv",
    }


@router.get("/export/{key}/equity")
def export_equity_csv(key: str):
    """Export equity curve from backtest result as CSV."""
    if key not in _backtest_cache:
        raise HTTPException(status_code=404, detail="Backtest result not found")

    result = _backtest_cache[key]
    if result["status"] != "complete":
        raise HTTPException(status_code=400, detail="Backtest not complete")

    equity = result["result"]["equity_curve"]
    import csv
    import io

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["date", "value"])
    writer.writeheader()
    writer.writerows(equity)

    return {
        "csv": output.getvalue(),
        "filename": f"{result.get('ticker')}_equity_{key}.csv",
    }


@router.post("/compare")
def compare_backtests(key_a: str, key_b: str) -> dict:
    """Compare two backtest results to identify performance differences.

    Args:
        key_a: Cache key of first backtest result
        key_b: Cache key of second backtest result

    Returns:
        Comparison dict showing return, Sharpe, drawdown, and win rate differences
    """
    from src.backtest.comparison import compare_backtests as do_compare

    if key_a not in _backtest_cache:
        raise HTTPException(status_code=404, detail=f"Backtest {key_a} not found")
    if key_b not in _backtest_cache:
        raise HTTPException(status_code=404, detail=f"Backtest {key_b} not found")

    result_a = _backtest_cache[key_a]
    result_b = _backtest_cache[key_b]

    if result_a["status"] != "complete":
        raise HTTPException(status_code=400, detail=f"Backtest {key_a} is not complete")
    if result_b["status"] != "complete":
        raise HTTPException(status_code=400, detail=f"Backtest {key_b} is not complete")

    diff = do_compare(
        result_a["result"],
        result_b["result"],
        name_a=result_a.get("ticker", key_a),
        name_b=result_b.get("ticker", key_b),
    )

    return {
        "comparison": diff.to_dict(),
        "summary": diff.summary(),
    }
