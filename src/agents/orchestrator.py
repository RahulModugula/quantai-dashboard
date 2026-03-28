"""PortfolioManagerAgent — orchestrates all agents and issues the final decision."""

import asyncio
import logging
from datetime import date, datetime
from uuid import uuid4

from src.agents.base_agent import BaseAgent
from src.agents.news_agent import NewsAgent
from src.agents.quant_agent import QuantAgent
from src.agents.risk_agent import RiskAgent

logger = logging.getLogger(__name__)

# Mapping of tickers to approximate company names for SEC search
_TICKER_TO_COMPANY = {
    "AAPL": "Apple Inc",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc",
    "AMZN": "Amazon.com",
    "META": "Meta Platforms",
    "NVDA": "NVIDIA Corporation",
    "TSLA": "Tesla Inc",
    "SPY": "SPDR S&P 500",
    "QQQ": "Invesco QQQ",
    "BRK.B": "Berkshire Hathaway",
}


class PortfolioManagerAgent(BaseAgent):
    name = "PortfolioManagerAgent"
    system_prompt = (
        "You are the Portfolio Manager at a multi-strategy hedge fund. "
        "You have received analysis from three specialists: a quant analyst, a research analyst, "
        "and a risk manager. Weigh their arguments carefully, consider the current portfolio "
        "position, and issue a final trading decision. Explain your reasoning transparently. "
        "Your decision will be logged and evaluated against actual market outcomes."
    )
    tool_schemas = []

    def _build_user_message(self, context: dict) -> str:
        ticker = context.get("ticker", "UNKNOWN").upper()
        quant_brief = context.get("quant_brief", "Not available")
        news_brief = context.get("news_brief", "Not available")
        risk_brief = context.get("risk_brief", "Not available")
        position = context.get("current_position", "No existing position")

        return (
            f"Make a final trading decision for {ticker}. Today: {context.get('date', str(date.today()))}\n\n"
            "--- QUANT ANALYST BRIEF ---\n"
            f"{quant_brief}\n\n"
            "--- RESEARCH ANALYST BRIEF ---\n"
            f"{news_brief}\n\n"
            "--- RISK MANAGER BRIEF ---\n"
            f"{risk_brief}\n\n"
            f"Current portfolio position: {position}\n\n"
            "Write your Portfolio Manager Decision using EXACTLY this format:\n\n"
            "DECISION: [BUY / SELL / HOLD]\n"
            "CONFIDENCE: [0-100]%\n"
            "REASONING:\n"
            "- [point 1 — why you weighted quant/news/risk the way you did]\n"
            "- [point 2]\n"
            "- [point 3]\n"
            "KEY RISK: [single most important risk to monitor going forward]\n"
            "SUMMARY: [2-3 sentence final narrative suitable for an investor memo]"
        )

    async def _dispatch_tool(self, tool_name: str, args: dict) -> dict:
        return {"error": f"PortfolioManagerAgent has no tools: {tool_name}"}


async def run_full_analysis(ticker: str, analysis_id: str | None = None) -> dict:
    """Run the full 4-agent debate and persist results to the database.

    Returns a dict with analysis_id and all briefs + final decision.
    """
    from src.data.storage import save_agent_decision, update_agent_decision
    from src.config import settings

    ticker = ticker.upper()
    analysis_id = analysis_id or str(uuid4())
    today = str(date.today())
    company_name = _TICKER_TO_COMPANY.get(ticker, ticker)

    # Get current portfolio position for context
    current_position = _get_current_position(ticker)

    # Persist initial pending record
    save_agent_decision(
        {
            "ticker": ticker,
            "analysis_id": analysis_id,
            "triggered_at": datetime.utcnow(),
            "status": "running",
            "model_used": settings.agent_model,
        }
    )

    try:
        base_context = {
            "ticker": ticker,
            "company_name": company_name,
            "date": today,
        }

        # Phase 1: Run QuantAgent and NewsAgent in parallel
        logger.info(f"[{analysis_id}] Running QuantAgent + NewsAgent in parallel for {ticker}")
        quant_brief, news_brief = await asyncio.gather(
            QuantAgent().run(base_context),
            NewsAgent().run({**base_context}),
            return_exceptions=False,
        )

        # Phase 2: RiskAgent challenges both briefs
        logger.info(f"[{analysis_id}] Running RiskAgent for {ticker}")
        risk_context = {
            **base_context,
            "quant_brief": quant_brief.content,
            "news_brief": news_brief.content,
        }
        risk_brief = await RiskAgent().run(risk_context)

        # Phase 3: PortfolioManager makes final call
        logger.info(f"[{analysis_id}] Running PortfolioManagerAgent for {ticker}")
        pm_context = {
            **base_context,
            "quant_brief": quant_brief.content,
            "news_brief": news_brief.content,
            "risk_brief": risk_brief.content,
            "current_position": current_position,
        }
        pm_brief = await PortfolioManagerAgent().run(pm_context)

        # Extract decision from PM structured output
        decision = pm_brief.structured_data.get("decision", "HOLD").upper()
        if decision not in ("BUY", "SELL", "HOLD"):
            decision = "HOLD"

        conf_str = pm_brief.structured_data.get("confidence", "50")
        try:
            confidence = float(conf_str.replace("%", "")) / 100.0
        except (ValueError, AttributeError):
            confidence = 0.5

        total_tokens = sum(
            [
                quant_brief.tokens_used,
                news_brief.tokens_used,
                risk_brief.tokens_used,
                pm_brief.tokens_used,
            ]
        )

        # Persist completed result
        update_agent_decision(
            analysis_id,
            {
                "status": "complete",
                "completed_at": datetime.utcnow(),
                "decision": decision,
                "confidence": confidence,
                "reasoning_summary": _extract_summary(pm_brief.content),
                "quant_brief": {
                    "content": quant_brief.content,
                    "structured": quant_brief.structured_data,
                },
                "news_brief": {
                    "content": news_brief.content,
                    "structured": news_brief.structured_data,
                },
                "risk_brief": {
                    "content": risk_brief.content,
                    "structured": risk_brief.structured_data,
                },
                "pm_brief": {"content": pm_brief.content, "structured": pm_brief.structured_data},
                "total_tokens": total_tokens,
            },
        )

        result = {
            "analysis_id": analysis_id,
            "ticker": ticker,
            "status": "complete",
            "decision": decision,
            "confidence": confidence,
            "reasoning_summary": _extract_summary(pm_brief.content),
            "agents": {
                "quant": {
                    "content": quant_brief.content,
                    "structured": quant_brief.structured_data,
                },
                "news": {"content": news_brief.content, "structured": news_brief.structured_data},
                "risk": {"content": risk_brief.content, "structured": risk_brief.structured_data},
                "portfolio_manager": {
                    "content": pm_brief.content,
                    "structured": pm_brief.structured_data,
                },
            },
            "total_tokens": total_tokens,
            "model_used": settings.agent_model,
            "analyzed_at": today,
        }

        logger.info(
            f"[{analysis_id}] Analysis complete for {ticker}: "
            f"decision={decision}, confidence={confidence:.0%}, tokens={total_tokens}"
        )
        return result

    except Exception as exc:
        error_msg = str(exc)
        logger.error(f"[{analysis_id}] Analysis failed for {ticker}: {exc}", exc_info=True)
        update_agent_decision(
            analysis_id,
            {
                "status": "error",
                "completed_at": datetime.utcnow(),
                "error_message": error_msg,
            },
        )
        return {
            "analysis_id": analysis_id,
            "ticker": ticker,
            "status": "error",
            "error": error_msg,
        }


def _get_current_position(ticker: str) -> str:
    """Return a human-readable description of the current portfolio position."""
    try:
        from src.api.dependencies import get_paper_trader

        trader = get_paper_trader()
        positions = trader.portfolio.positions
        if ticker in positions:
            pos = positions[ticker]
            shares = getattr(pos, "shares", 0)
            avg_cost = getattr(pos, "avg_cost", 0)
            return f"{shares:.2f} shares at avg cost ${avg_cost:.2f}"
        return "No position"
    except Exception:
        return "Position data unavailable"


def _extract_summary(content: str) -> str:
    """Pull the SUMMARY line from the PM brief."""
    for line in content.splitlines():
        if line.upper().startswith("SUMMARY:"):
            return line.split(":", 1)[1].strip()
    # Fallback: last non-empty line
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    return lines[-1] if lines else ""
