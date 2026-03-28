"""NewsAgent — reads recent news and SEC EDGAR filings via tool use."""

from datetime import date

from src.agents.base_agent import BaseAgent
from src.agents.tools import news_tools, sec_tools

# Combine tool schemas from both tools
_ALL_TOOL_SCHEMAS = news_tools.TOOL_SCHEMAS + sec_tools.TOOL_SCHEMAS


class NewsAgent(BaseAgent):
    name = "NewsAgent"
    system_prompt = (
        "You are a fundamental research analyst at a buy-side firm. "
        "You have tools to fetch recent news articles and SEC EDGAR regulatory filings. "
        "Use both tools before writing your brief. "
        "Focus on material events: earnings surprises, management changes, M&A activity, "
        "regulatory actions, and macro catalysts. Ignore noise and routine filings. "
        "Be specific — quote headlines and filing dates where relevant."
    )
    tool_schemas = _ALL_TOOL_SCHEMAS

    def _build_user_message(self, context: dict) -> str:
        ticker = context.get("ticker", "UNKNOWN").upper()
        company = context.get("company_name", ticker)
        today = context.get("date", str(date.today()))
        return (
            f"Research {ticker} ({company}) for fundamental developments. Today is {today}.\n\n"
            "Step 1: Call get_recent_news to fetch the latest news articles.\n"
            f"Step 2: Call get_sec_filings with company_name='{company}' to check recent regulatory filings.\n\n"
            "Then write your Research Brief using EXACTLY this format:\n\n"
            "SENTIMENT: [BULLISH / BEARISH / NEUTRAL]\n"
            "KEY EVENTS:\n"
            "- [event 1 with date]\n"
            "- [event 2 with date]\n"
            "- [event 3 with date, or 'None' if fewer events]\n"
            "RISKS: [key risks identified from news or filings]\n"
            "CATALYSTS: [upcoming catalysts in next 7-30 days, or 'None identified']\n"
            "SUMMARY: [2-3 sentence narrative of the fundamental picture]"
        )

    async def _dispatch_tool(self, tool_name: str, args: dict) -> dict:
        if tool_name in ("get_recent_news",):
            return news_tools.dispatch(tool_name, args)
        if tool_name in ("get_sec_filings",):
            return await sec_tools.dispatch_async(tool_name, args)
        return {"error": f"Unknown tool: {tool_name}"}
