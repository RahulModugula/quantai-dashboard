"""RiskAgent — devil's advocate that challenges every trade idea."""

from src.agents.base_agent import BaseAgent


class RiskAgent(BaseAgent):
    name = "RiskAgent"
    system_prompt = (
        "You are the Chief Risk Officer at a hedge fund. Your job is to stress-test trade ideas. "
        "You have received a quant brief and a research brief from two analysts recommending a trade. "
        "Your role is adversarial: find the flaws, identify tail risks, and raise scenarios "
        "where both analysts could be wrong. Do not simply agree — always push back. "
        "Be specific about what could go wrong and how likely each risk is."
    )
    tool_schemas = []  # No external tools — reads context only

    def _build_user_message(self, context: dict) -> str:
        ticker = context.get("ticker", "UNKNOWN").upper()
        quant_brief = context.get("quant_brief", "Not available")
        news_brief = context.get("news_brief", "Not available")

        return (
            f"Challenge the following trade proposal for {ticker}.\n\n"
            "--- QUANT BRIEF ---\n"
            f"{quant_brief}\n\n"
            "--- RESEARCH BRIEF ---\n"
            f"{news_brief}\n\n"
            "Write your Risk Assessment using EXACTLY this format:\n\n"
            "RISK RATING: [1=minimal / 2=low / 3=moderate / 4=high / 5=extreme]\n"
            "VERDICT: [AGREE / CAUTION / DISAGREE]\n"
            "CHALLENGES:\n"
            "- [challenge to quant or news analysis]\n"
            "- [another challenge]\n"
            "TAIL RISKS:\n"
            "- [low-probability, high-impact scenario]\n"
            "- [another tail risk]\n"
            "MISSING FACTORS: [what both analysts failed to consider]\n"
            "SUMMARY: [2-3 sentence risk narrative]"
        )

    async def _dispatch_tool(self, tool_name: str, args: dict) -> dict:
        return {"error": f"RiskAgent has no tools: {tool_name}"}
