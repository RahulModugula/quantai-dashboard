"""QuantAI Intel — Multi-Agent LLM Intelligence Layer.

Four specialized agents deliberate on each trade decision:
  QuantAgent         — reads ML predictions, SHAP, and technical signals
  NewsAgent          — reads recent news and SEC EDGAR filings via tool use
  RiskAgent          — devil's advocate: challenges every trade idea
  PortfolioManagerAgent — orchestrates the debate, issues final Buy/Sell/Hold

Usage::

    from src.agents import run_full_analysis

    result = await run_full_analysis("AAPL")
"""

from src.agents.orchestrator import run_full_analysis

__all__ = ["run_full_analysis"]
