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

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import only for type checkers
    from src.agents.orchestrator import run_full_analysis

__all__ = ["run_full_analysis"]


def __getattr__(name: str):
    """Lazily expose the equity orchestrator.

    The orchestrator pulls in the full ML/data stack (pandas, torch, yfinance,
    shap, ...). Importing it eagerly here would force every consumer of the
    lightweight `BaseAgent` — notably the distressed-credit committee, which
    only needs litellm + stdlib — to install all of it. PEP 562 lets us keep
    `from src.agents import run_full_analysis` working while deferring that
    heavy import until it's actually used.
    """
    if name == "run_full_analysis":
        from src.agents.orchestrator import run_full_analysis

        return run_full_analysis
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
