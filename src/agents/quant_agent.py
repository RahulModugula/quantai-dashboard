"""QuantAgent — reads ML predictions, SHAP importance, and technical signals."""

from datetime import date

from src.agents.base_agent import BaseAgent
from src.agents.tools import quant_tools


class QuantAgent(BaseAgent):
    name = "QuantAgent"
    system_prompt = (
        "You are a quantitative analyst at a systematic trading fund. "
        "You have access to tools that return live ML model predictions, "
        "SHAP feature importance, and technical indicator values for stocks. "
        "Use ALL three tools before writing your brief. "
        "Be concise, data-driven, and precise. Do not make up numbers — "
        "only report what the tools return."
    )
    tool_schemas = quant_tools.TOOL_SCHEMAS

    def _build_user_message(self, context: dict) -> str:
        ticker = context.get("ticker", "UNKNOWN").upper()
        today = context.get("date", str(date.today()))
        return (
            f"Analyze {ticker} for a potential next-day trade. Today is {today}.\n\n"
            "Step 1: Call get_ml_prediction to get the ensemble model's directional signal.\n"
            "Step 2: Call get_shap_importance to identify the top features driving the prediction.\n"
            "Step 3: Call get_technical_signals to get the current indicator values.\n\n"
            "Then write your Quant Brief using EXACTLY this format:\n\n"
            "SIGNAL: [BUY / SELL / HOLD]\n"
            "CONFIDENCE: [0-100]%\n"
            "KEY DRIVERS:\n"
            "- [feature 1 and why it matters]\n"
            "- [feature 2 and why it matters]\n"
            "- [feature 3 and why it matters]\n"
            "ANOMALIES: [any unusual model behavior or data issues, or 'None']\n"
            "SUMMARY: [2-3 sentence narrative of the quantitative picture]"
        )

    async def _dispatch_tool(self, tool_name: str, args: dict) -> dict:
        return quant_tools.dispatch(tool_name, args)
