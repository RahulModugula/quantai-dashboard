"""Tests for the QuantAI Intel multi-agent system."""

from __future__ import annotations

import asyncio
import json
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _make_litellm_response(content: str, tool_calls: Optional[List] = None):
    """Build a minimal mock litellm completion response."""
    msg = MagicMock()
    msg.content = content if not tool_calls else None
    msg.tool_calls = tool_calls or []

    usage = MagicMock()
    usage.total_tokens = 50

    choice = MagicMock()
    choice.message = msg

    response = MagicMock()
    response.choices = [choice]
    response.usage = usage
    return response


def _make_tool_call(tc_id: str, name: str, args: dict):
    tc = MagicMock()
    tc.id = tc_id
    tc.function.name = name
    tc.function.arguments = json.dumps(args)
    return tc


# ---------------------------------------------------------------------------
# BaseAgent loop
# ---------------------------------------------------------------------------


class TestBaseAgentLoop:
    """Test the agentic tool-call loop in BaseAgent."""

    def _make_agent(self):
        from src.agents.base_agent import BaseAgent

        class _ConcreteAgent(BaseAgent):
            name = "TestAgent"
            system_prompt = "You are a test agent."
            tool_schemas = []

            def _build_user_message(self, context: dict) -> str:
                return f"Analyze {context.get('ticker', 'AAPL')}"

        return _ConcreteAgent()

    @pytest.mark.asyncio
    async def test_returns_brief_on_plain_response(self):
        agent = self._make_agent()
        response = _make_litellm_response("SIGNAL: BUY\nCONFIDENCE: 80%\nSUMMARY: Looks good.")

        with patch("litellm.acompletion", new_callable=AsyncMock, return_value=response):
            brief = await agent.run({"ticker": "AAPL"})

        assert brief.agent_name == "TestAgent"
        assert brief.ticker == "AAPL"
        assert "BUY" in brief.content
        assert brief.error is None
        assert brief.tokens_used == 50

    @pytest.mark.asyncio
    async def test_handles_timeout_and_retries(self):
        agent = self._make_agent()

        call_count = 0

        async def _side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            raise asyncio.TimeoutError()

        with patch("litellm.acompletion", new_callable=AsyncMock, side_effect=_side_effect):
            brief = await agent.run({"ticker": "AAPL"})

        assert brief.error is not None
        assert call_count == agent._max_retries + 1  # initial + retries

    @pytest.mark.asyncio
    async def test_executes_tool_call_loop(self):
        """Agent should call the tool and continue until final text response."""

        class _ToolAgent(self._make_agent().__class__):
            tool_schemas = [
                {"type": "function", "function": {"name": "dummy_tool", "parameters": {}}}
            ]

            async def _dispatch_tool(self, tool_name, args):
                return {"result": "tool_output"}

        agent = _ToolAgent()

        tc = _make_tool_call("tc1", "dummy_tool", {})
        first_response = _make_litellm_response("", tool_calls=[tc])
        second_response = _make_litellm_response("Final answer after tool call.")

        responses = [first_response, second_response]
        idx = 0

        async def _side_effect(**kwargs):
            nonlocal idx
            r = responses[idx]
            idx += 1
            return r

        with patch("litellm.acompletion", new_callable=AsyncMock, side_effect=_side_effect):
            brief = await agent.run({"ticker": "AAPL"})

        assert "Final answer" in brief.content
        assert "dummy_tool" in brief.tool_calls_made


# ---------------------------------------------------------------------------
# Quant tools
# ---------------------------------------------------------------------------


class TestQuantTools:
    def test_dispatch_unknown_tool(self):
        from src.agents.tools.quant_tools import dispatch

        result = dispatch("nonexistent_tool", {})
        assert "error" in result

    def test_ml_prediction_no_model(self):
        from src.agents.tools.quant_tools import get_ml_prediction

        with patch("src.api.dependencies.get_model_bundle", return_value=(None, {})):
            result = get_ml_prediction("AAPL")
        assert "error" in result

    def test_get_technical_signals_no_data(self):
        import pandas as pd
        from src.agents.tools.quant_tools import get_technical_signals

        with patch("src.data.storage.load_features", return_value=pd.DataFrame()):
            result = get_technical_signals("AAPL")
        assert "error" in result


# ---------------------------------------------------------------------------
# News tools
# ---------------------------------------------------------------------------


class TestNewsTools:
    def test_get_recent_news_formats_output(self):
        from src.agents.tools.news_tools import get_recent_news

        mock_news = [
            {
                "content": {
                    "title": "Apple Reports Record Revenue",
                    "summary": "Apple Inc reported record quarterly revenue.",
                    "provider": {"displayName": "Reuters"},
                    "pubDate": 1700000000,
                },
            }
        ]

        mock_ticker = MagicMock()
        mock_ticker.news = mock_news

        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = get_recent_news("AAPL", max_items=5)

        assert result["ticker"] == "AAPL"
        assert result["count"] == 1
        assert result["articles"][0]["title"] == "Apple Reports Record Revenue"

    def test_get_recent_news_handles_error(self):
        from src.agents.tools.news_tools import get_recent_news

        with patch("yfinance.Ticker", side_effect=Exception("network error")):
            result = get_recent_news("AAPL")
        assert "error" in result
        assert result["articles"] == []

    def test_dispatch_unknown_tool(self):
        from src.agents.tools.news_tools import dispatch

        result = dispatch("bad_tool", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# Agent-specific prompts
# ---------------------------------------------------------------------------


class TestAgentPrompts:
    def test_quant_agent_prompt_contains_ticker(self):
        from src.agents.quant_agent import QuantAgent

        agent = QuantAgent()
        msg = agent._build_user_message({"ticker": "MSFT", "date": "2026-04-10"})
        assert "MSFT" in msg
        assert "get_ml_prediction" in msg
        assert "get_shap_importance" in msg
        assert "get_technical_signals" in msg

    def test_risk_agent_includes_briefs_in_prompt(self):
        from src.agents.risk_agent import RiskAgent

        agent = RiskAgent()
        msg = agent._build_user_message(
            {
                "ticker": "AAPL",
                "quant_brief": "SIGNAL: BUY",
                "news_brief": "SENTIMENT: BULLISH",
            }
        )
        assert "SIGNAL: BUY" in msg
        assert "SENTIMENT: BULLISH" in msg
        assert "AAPL" in msg

    def test_pm_agent_includes_all_briefs(self):
        from src.agents.orchestrator import PortfolioManagerAgent

        agent = PortfolioManagerAgent()
        msg = agent._build_user_message(
            {
                "ticker": "GOOGL",
                "quant_brief": "Q brief",
                "news_brief": "N brief",
                "risk_brief": "R brief",
                "current_position": "No position",
            }
        )
        assert "Q brief" in msg
        assert "N brief" in msg
        assert "R brief" in msg


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------


class TestAgentStorage:
    def test_save_and_load_agent_decision(self, tmp_path):
        from src.data.storage import (
            init_db,
            load_agent_decision,
            save_agent_decision,
            update_agent_decision,
        )

        db = str(tmp_path / "test.db")
        init_db(db)

        analysis_id = save_agent_decision(
            {
                "ticker": "AAPL",
                "status": "pending",
            },
            db_path=db,
        )

        record = load_agent_decision(analysis_id, db_path=db)
        assert record is not None
        assert record["ticker"] == "AAPL"
        assert record["status"] == "pending"

        update_agent_decision(
            analysis_id,
            {"status": "complete", "decision": "BUY", "confidence": 0.75},
            db_path=db,
        )
        updated = load_agent_decision(analysis_id, db_path=db)
        assert updated["status"] == "complete"
        assert updated["decision"] == "BUY"
        assert updated["confidence"] == pytest.approx(0.75)

    def test_load_agent_decisions_ticker_filter(self, tmp_path):
        from src.data.storage import init_db, load_agent_decisions, save_agent_decision

        db = str(tmp_path / "test.db")
        init_db(db)

        for ticker in ("AAPL", "AAPL", "MSFT"):
            save_agent_decision({"ticker": ticker, "status": "complete"}, db_path=db)

        aapl = load_agent_decisions("AAPL", db_path=db)
        assert len(aapl) == 2

        msft = load_agent_decisions("MSFT", db_path=db)
        assert len(msft) == 1

    def test_load_agent_accuracy_empty(self, tmp_path):
        from src.data.storage import init_db, load_agent_accuracy

        db = str(tmp_path / "test.db")
        init_db(db)
        result = load_agent_accuracy(db_path=db)
        assert result.get("total_decisions", 0) == 0


# ---------------------------------------------------------------------------
# Orchestrator (integration-style with mocked LLM)
# ---------------------------------------------------------------------------


class TestOrchestrator:
    @pytest.mark.asyncio
    async def test_run_full_analysis_success(self, tmp_path):
        """Full orchestration should save a complete record to DB."""
        from src.data.storage import init_db, get_engine as real_get_engine

        db = str(tmp_path / "test.db")
        init_db(db)

        # Mock LiteLLM to return deterministic responses
        quant_resp = _make_litellm_response(
            "SIGNAL: BUY\nCONFIDENCE: 75%\nKEY DRIVERS:\n- RSI\n- MACD\nANOMALIES: None\n"
            "SUMMARY: Strong quant signal."
        )
        news_resp = _make_litellm_response(
            "SENTIMENT: BULLISH\nKEY EVENTS:\n- Q1 beat\nRISKS: None\n"
            "CATALYSTS: Earnings\nSUMMARY: Strong fundamentals."
        )
        risk_resp = _make_litellm_response(
            "RISK RATING: 2\nVERDICT: AGREE\nCHALLENGES:\n- Valuation high\n"
            "TAIL RISKS:\n- Rate hike\nMISSING FACTORS: None\nSUMMARY: Manageable risk."
        )
        pm_resp = _make_litellm_response(
            "DECISION: BUY\nCONFIDENCE: 80%\nREASONING:\n- Quant signal strong\n"
            "KEY RISK: Macro\nSUMMARY: Compelling entry point."
        )

        call_count = 0
        responses = [quant_resp, news_resp, risk_resp, pm_resp]

        async def _mock_completion(**kwargs):
            nonlocal call_count
            r = responses[call_count % len(responses)]
            call_count += 1
            return r

        # Capture real engine before patching
        _real_engine = real_get_engine(db)

        with (
            patch("litellm.acompletion", new_callable=AsyncMock, side_effect=_mock_completion),
            patch("src.data.storage.get_engine", return_value=_real_engine),
            patch("src.agents.orchestrator._get_current_position", return_value="No position"),
        ):
            from src.agents.orchestrator import run_full_analysis

            result = await run_full_analysis("AAPL")

        assert result["status"] == "complete"
        assert result["decision"] in ("BUY", "SELL", "HOLD")
        assert "agents" in result
        assert result["ticker"] == "AAPL"

    @pytest.mark.asyncio
    async def test_run_full_analysis_llm_error(self, tmp_path):
        """On LLM failure agents degrade gracefully and orchestrator still returns a result."""
        from src.data.storage import init_db, get_engine as real_get_engine

        db = str(tmp_path / "test.db")
        init_db(db)

        _real_engine = real_get_engine(db)

        async def _boom(**kwargs):
            raise Exception("LLM unavailable")

        with (
            patch("litellm.acompletion", new_callable=AsyncMock, side_effect=_boom),
            patch("src.data.storage.get_engine", return_value=_real_engine),
            patch("src.agents.orchestrator._get_current_position", return_value="No position"),
        ):
            from src.agents.orchestrator import run_full_analysis

            result = await run_full_analysis("AAPL")

        # System degrades gracefully — always returns a result dict
        assert "ticker" in result
        assert result["ticker"] == "AAPL"
        assert result.get("status") in ("complete", "error")
        # If complete, decision must be a valid value (defaults to HOLD)
        if result.get("status") == "complete":
            assert result.get("decision") in ("BUY", "SELL", "HOLD")
