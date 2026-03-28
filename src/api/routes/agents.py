"""QuantAI Intel — Multi-Agent LLM intelligence endpoints."""

import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException

from src.data.storage import (
    load_agent_accuracy,
    load_agent_decision,
    load_agent_decisions,
)

router = APIRouter(prefix="/agents", tags=["intel"])
logger = logging.getLogger(__name__)

# In-memory registry of running background analysis tasks
_running: dict[str, str] = {}  # ticker -> analysis_id


@router.post("/analyze/{ticker}")
async def trigger_analysis(ticker: str, background_tasks: BackgroundTasks) -> dict:
    """Trigger a multi-agent analysis for a ticker.

    Returns immediately with the analysis_id. Poll
    ``GET /api/agents/status/{analysis_id}`` to check progress.
    """
    ticker = ticker.upper()

    from src.agents.orchestrator import run_full_analysis
    from uuid import uuid4

    analysis_id = str(uuid4())
    _running[ticker] = analysis_id

    async def _run():
        try:
            await run_full_analysis(ticker, analysis_id=analysis_id)
        except Exception as exc:
            logger.error(f"Background analysis failed for {ticker}: {exc}", exc_info=True)
        finally:
            if _running.get(ticker) == analysis_id:
                _running.pop(ticker, None)

    background_tasks.add_task(_run)

    return {
        "analysis_id": analysis_id,
        "ticker": ticker,
        "status": "running",
        "message": f"Analysis started. Poll /api/agents/status/{analysis_id} for progress.",
    }


@router.get("/status/{analysis_id}")
def get_status(analysis_id: str) -> dict:
    """Poll the status of an in-progress or completed analysis."""
    record = load_agent_decision(analysis_id)
    if record is None:
        # Could still be very early in execution
        return {"analysis_id": analysis_id, "status": "pending"}
    return {
        "analysis_id": analysis_id,
        "ticker": record.get("ticker"),
        "status": record.get("status"),
        "decision": record.get("decision"),
        "confidence": record.get("confidence"),
        "reasoning_summary": record.get("reasoning_summary"),
        "triggered_at": str(record.get("triggered_at", "")),
        "completed_at": str(record.get("completed_at", "") or ""),
        "error": record.get("error_message"),
    }


@router.get("/decision/{ticker}")
def get_latest_decision(ticker: str) -> dict:
    """Get the most recent completed analysis decision for a ticker."""
    ticker = ticker.upper()
    decisions = load_agent_decisions(ticker, limit=10)
    completed = [d for d in decisions if d.get("status") == "complete"]
    if not completed:
        raise HTTPException(
            status_code=404,
            detail=f"No completed analysis found for {ticker}. "
            f"POST /api/agents/analyze/{ticker} to start one.",
        )
    latest = completed[0]
    return {
        "ticker": ticker,
        "analysis_id": latest.get("analysis_id"),
        "decision": latest.get("decision"),
        "confidence": latest.get("confidence"),
        "reasoning_summary": latest.get("reasoning_summary"),
        "model_used": latest.get("model_used"),
        "analyzed_at": str(latest.get("triggered_at", "")),
        "total_tokens": latest.get("total_tokens"),
    }


@router.get("/debate/{ticker}")
def get_debate(ticker: str) -> dict:
    """Get the full multi-agent debate transcript for the latest analysis."""
    ticker = ticker.upper()
    decisions = load_agent_decisions(ticker, limit=10)
    completed = [d for d in decisions if d.get("status") == "complete"]
    if not completed:
        raise HTTPException(
            status_code=404,
            detail=f"No completed analysis found for {ticker}.",
        )
    latest = completed[0]
    return {
        "ticker": ticker,
        "analysis_id": latest.get("analysis_id"),
        "decision": latest.get("decision"),
        "confidence": latest.get("confidence"),
        "analyzed_at": str(latest.get("triggered_at", "")),
        "agents": {
            "quant": latest.get("quant_brief"),
            "news": latest.get("news_brief"),
            "risk": latest.get("risk_brief"),
            "portfolio_manager": latest.get("pm_brief"),
        },
    }


@router.get("/history/{ticker}")
def get_history(ticker: str, limit: int = 20) -> dict:
    """Get recent analysis history for a ticker."""
    ticker = ticker.upper()
    decisions = load_agent_decisions(ticker, limit=min(limit, 100))
    return {
        "ticker": ticker,
        "count": len(decisions),
        "decisions": [
            {
                "analysis_id": d.get("analysis_id"),
                "decision": d.get("decision"),
                "confidence": d.get("confidence"),
                "status": d.get("status"),
                "analyzed_at": str(d.get("triggered_at", "")),
                "correct_24h": d.get("decision_correct_24h"),
                "correct_7d": d.get("decision_correct_7d"),
            }
            for d in decisions
        ],
    }


@router.get("/accuracy")
def get_accuracy() -> dict:
    """Get aggregate accuracy metrics across all tickers and decisions."""
    return load_agent_accuracy()
