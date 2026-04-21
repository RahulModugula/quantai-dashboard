"""Credit-focused agent subclasses for distressed / special-situations analysis.

These re-use the same BaseAgent tool-call loop as the equity agents — the only
differences are the system prompts, the user-message templates, and the output
format. Tools are now integrated for quantitative credit analysis.

Orchestration mirrors ``src/agents/orchestrator.py`` but writes an IC-style
memo instead of a BUY / SELL / HOLD decision.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from src.agents.base_agent import AgentBrief, BaseAgent

from examples.distressed.credit_tools import (
    CREDIT_TOOLS_SCHEMA,
    analyze_recovery_scenarios,
    calculate_coverage,
    calculate_leverage,
    check_covenant_headroom,
    format_covenant_status,
    format_recovery_analysis,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Situation data model
# ---------------------------------------------------------------------------


@dataclass
class CapitalStructureTranche:
    """One layer of the pre-restructuring capital stack."""

    name: str  # e.g. "Senior Secured Term Loan B (2028)"
    face_amount_mm: float  # outstanding principal in $MM
    coupon: str  # e.g. "SOFR + 750"
    maturity: str  # ISO date or "N/A"
    seniority: int  # 1 = most senior
    current_price: float | None = None  # trade price, as % of par, or None
    holder: str | None = None  # known holder if public


@dataclass
class Situation:
    """Everything the committee needs to know before reading the briefs."""

    company: str
    ticker: str | None
    sector: str
    situation_type: str  # "Chapter 11", "Out-of-court exchange", "Take-private", ...
    thesis_one_liner: str  # 1-sentence summary of the opportunity
    timeline: list[dict[str, str]] = field(default_factory=list)  # [{date, event}]
    capital_structure: list[CapitalStructureTranche] = field(default_factory=list)
    operating_metrics: dict[str, Any] = field(default_factory=dict)  # revenue, EBITDA, etc.
    current_position: str = "No existing position"
    key_risks: list[str] = field(default_factory=list)

    def as_context(self) -> dict[str, Any]:
        """Flatten into the context dict the agents consume."""
        return {
            "ticker": self.ticker or self.company,
            "company_name": self.company,
            "sector": self.sector,
            "situation_type": self.situation_type,
            "thesis_one_liner": self.thesis_one_liner,
            "timeline": self.timeline,
            "capital_structure": [_tranche_as_row(t) for t in self.capital_structure],
            "operating_metrics": self.operating_metrics,
            "current_position": self.current_position,
            "key_risks": self.key_risks,
        }


def _tranche_as_row(t: CapitalStructureTranche) -> dict[str, Any]:
    return {
        "name": t.name,
        "face_mm": t.face_amount_mm,
        "coupon": t.coupon,
        "maturity": t.maturity,
        "seniority": t.seniority,
        "price_pct_par": t.current_price,
        "holder": t.holder,
    }


def _format_cap_structure(rows: list[dict]) -> str:
    if not rows:
        return "(no capital structure provided)"
    lines = [
        "| # | Tranche | Face $MM | Coupon | Maturity | Price %par | Known Holder |",
        "|---|---------|----------|--------|----------|------------|--------------|",
    ]
    for r in sorted(rows, key=lambda x: x.get("seniority", 99)):
        price = f"{r['price_pct_par']:.1f}" if r.get("price_pct_par") is not None else "—"
        lines.append(
            f"| {r.get('seniority', '?')} | {r['name']} | {r['face_mm']:.0f} | "
            f"{r['coupon']} | {r['maturity']} | {price} | {r.get('holder') or '—'} |"
        )
    return "\n".join(lines)


def _format_timeline(events: list[dict]) -> str:
    if not events:
        return "(no timeline provided)"
    return "\n".join(f"- {e.get('date', '?')} — {e.get('event', '')}" for e in events)


def _format_metrics(metrics: dict) -> str:
    if not metrics:
        return "(no operating metrics provided)"
    return "\n".join(f"- {k}: {v}" for k, v in metrics.items())


# ---------------------------------------------------------------------------
# Agent subclasses
# ---------------------------------------------------------------------------


class CapStructureAgent(BaseAgent):
    """Reads the cap stack, computes leverage and coverage, estimates recovery per tranche.

    Enhanced with domain-specific tools for quantitative credit analysis.
    """

    name = "CapStructureAgent"
    system_prompt = (
        "You are a distressed-debt analyst on a credit investment team. "
        "Given a company's pre-restructuring capital structure and operating metrics, "
        "you analyze the stack from the top down: what each tranche's leverage multiple is, "
        "what the coverage and asset coverage look like, and where the fulcrum security sits. "
        "You estimate recovery per tranche under base / bear / bull EBITDA scenarios. "
        "Be numerical and specific. If a number can be computed from the inputs, compute it. "
        "If a value must be assumed, state the assumption explicitly. "
        "Use the available tools to calculate leverage, coverage, and recovery scenarios with precision."
    )
    tool_schemas: list[dict] = CREDIT_TOOLS_SCHEMA

    def _build_user_message(self, context: dict) -> str:
        # Stash the context so _dispatch_tool can reach the capital structure
        # (LiteLLM tool calls don't carry the original context).
        self._context: dict = context
        company = context.get("company_name", "UNKNOWN")
        cap_table = _format_cap_structure(context.get("capital_structure", []))
        metrics = _format_metrics(context.get("operating_metrics", {}))
        return (
            f"Analyze the capital structure of {company}.\n\n"
            "--- CAPITAL STRUCTURE ---\n"
            f"{cap_table}\n\n"
            "--- OPERATING METRICS ---\n"
            f"{metrics}\n\n"
            "Write your Capital Structure Brief using EXACTLY this format:\n\n"
            "LEVERAGE: [total debt / LTM EBITDA, computed]\n"
            "COVERAGE: [LTM EBITDA / cash interest, computed]\n"
            "FULCRUM: [which tranche is likely the fulcrum security and why]\n"
            "RECOVERY ANALYSIS:\n"
            "- Base case ([assumed EBITDA]): recovery per tranche, in % of par\n"
            "- Bear case ([assumed EBITDA]): recovery per tranche, in % of par\n"
            "- Bull case ([assumed EBITDA]): recovery per tranche, in % of par\n"
            "ASSET COVERAGE: [how much of the senior debt is covered by tangible assets / real estate / going-concern value]\n"
            "BEST RISK/REWARD TRANCHE: [which tranche offers the best risk-adjusted return, and why]\n"
            "SUMMARY: [2-3 sentence narrative of the cap stack thesis]"
        )

    def _capital_structure_from_context(self) -> list[CapitalStructureTranche]:
        """Reconstruct tranche dataclasses from the stashed context rows."""
        rows = getattr(self, "_context", {}).get("capital_structure", []) or []
        return [
            CapitalStructureTranche(
                name=r.get("name", "Unknown"),
                face_amount_mm=float(r.get("face_mm", 0) or 0),
                coupon=r.get("coupon", ""),
                maturity=r.get("maturity", ""),
                seniority=int(r.get("seniority", 99) or 99),
                current_price=r.get("price_pct_par"),
                holder=r.get("holder"),
            )
            for r in rows
        ]

    async def _dispatch_tool(self, tool_name: str, args: dict) -> dict:
        """Dispatch credit analysis tools."""
        try:
            if tool_name == "calculate_leverage":
                return {
                    "leverage_x": calculate_leverage(
                        total_debt_mm=args.get("total_debt_mm", 0),
                        ebitda_mm=args.get("ebitda_mm", 0),
                        include_lease_obligations=args.get("include_lease_obligations", 0.0),
                    )
                }
            elif tool_name == "calculate_coverage":
                return {
                    "coverage_x": calculate_coverage(
                        ebitda_mm=args.get("ebitda_mm", 0),
                        cash_interest_mm=args.get("cash_interest_mm", 0),
                        preferred_dividends_mm=args.get("preferred_dividends_mm", 0.0),
                    )
                }
            elif tool_name == "analyze_recovery_scenarios":
                cap_structure = self._capital_structure_from_context()
                if not cap_structure:
                    return {
                        "error": "No capital structure available in context",
                        "scenarios_table": "(no data)",
                    }
                scenarios = analyze_recovery_scenarios(
                    capital_structure=cap_structure,
                    base_ebitda_mm=args.get("base_ebitda_mm", 0),
                    bear_ebitda_mm=args.get("bear_ebitda_mm", 0),
                    bull_ebitda_mm=args.get("bull_ebitda_mm", 0),
                    base_multiple=args.get("base_multiple", 7.0),
                    bear_multiple=args.get("bear_multiple", 5.0),
                    bull_multiple=args.get("bull_multiple", 11.0),
                )
                return {
                    "scenarios_table": format_recovery_analysis(scenarios),
                    "fulcrum_tranche": scenarios[0].fulcrum_tranche if scenarios else None,
                }
            elif tool_name == "check_covenant_headroom":
                covenants = check_covenant_headroom(
                    ebitda_mm=args.get("ebitda_mm", 0),
                    total_debt_mm=args.get("total_debt_mm", 0),
                    max_leverage_x=args.get("max_leverage_x", 5.0),
                    min_coverage_x=args.get("min_coverage_x", 2.0),
                    cash_interest_mm=args.get("cash_interest_mm"),
                )
                return {
                    "covenants_table": format_covenant_status(covenants),
                    "breached_count": sum(1 for c in covenants if c.is_breached),
                }
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Error in {tool_name}: {e}")
            return {"error": str(e)}


class SituationAgent(BaseAgent):
    """Reads the docket / timeline / news flow and identifies material catalysts."""

    name = "SituationAgent"
    system_prompt = (
        "You are a special-situations research analyst. "
        "You are given a chronological timeline of events — bankruptcy filings, 8-K disclosures, "
        "management changes, litigation, M&A activity, macro shocks. "
        "Your job is to identify what has actually happened, what is about to happen (upcoming catalysts), "
        "and which events are structural (change the investment thesis) versus noise. "
        "Quote dates. Do not speculate about events that are not in the timeline."
    )
    tool_schemas: list[dict] = []

    def _build_user_message(self, context: dict) -> str:
        company = context.get("company_name", "UNKNOWN")
        timeline = _format_timeline(context.get("timeline", []))
        return (
            f"Research the situation at {company}.\n\n"
            "--- TIMELINE ---\n"
            f"{timeline}\n\n"
            "Write your Situation Brief using EXACTLY this format:\n\n"
            "KEY STRUCTURAL EVENTS:\n"
            "- [event 1 with date and why it changed the thesis]\n"
            "- [event 2 with date and why it changed the thesis]\n"
            "UPCOMING CATALYSTS:\n"
            "- [catalyst 1, expected date, expected impact]\n"
            "- [catalyst 2, expected date, expected impact]\n"
            "NOISE: [events that look material but aren't — or 'None']\n"
            "INFORMATION GAPS: [things we'd want to know before underwriting — data we don't have]\n"
            "SUMMARY: [2-3 sentence narrative of where the situation stands]"
        )

    async def _dispatch_tool(self, tool_name: str, args: dict) -> dict:
        return {"error": f"SituationAgent has no tools: {tool_name}"}


class CreditRiskAgent(BaseAgent):
    """Devil's-advocate credit risk officer — stress-tests the thesis.

    Enhanced with covenant checking tools for quantitative risk assessment.
    """

    name = "CreditRiskAgent"
    system_prompt = (
        "You are the Chief Risk Officer on a distressed credit investment committee. "
        "The cap-structure analyst and the situation analyst have just presented a trade. "
        "Your role is adversarial: find the flaws, stress-test the recovery assumptions, "
        "and enumerate scenarios where the fund loses money. "
        "Think about liquidity, legal / cramdown risk, adequate-protection litigation, "
        "fraudulent-conveyance claims on prior refinancings, sector tail risk, and exit-liquidity risk. "
        "Do not agree politely. Push back with specifics. "
        "Use the available tools to check covenant headroom and validate assumptions."
    )
    tool_schemas: list[dict] = CREDIT_TOOLS_SCHEMA

    def _build_user_message(self, context: dict) -> str:
        company = context.get("company_name", "UNKNOWN")
        cap_brief = context.get("cap_structure_brief", "Not available")
        situation_brief = context.get("situation_brief", "Not available")
        known_risks = (
            "\n".join(f"- {r}" for r in context.get("key_risks", [])) or "- (none flagged)"
        )
        return (
            f"Stress-test the trade proposal for {company}.\n\n"
            "--- CAP STRUCTURE BRIEF ---\n"
            f"{cap_brief}\n\n"
            "--- SITUATION BRIEF ---\n"
            f"{situation_brief}\n\n"
            "--- PRE-FLAGGED RISKS ---\n"
            f"{known_risks}\n\n"
            "Write your Credit Risk Assessment using EXACTLY this format:\n\n"
            "VERDICT: [AGREE / PROCEED WITH CAUTION / DISAGREE]\n"
            "RISK RATING: [1=minimal / 2=low / 3=moderate / 4=high / 5=extreme]\n"
            "CHALLENGES TO RECOVERY MATH:\n"
            "- [specific pushback on the cap-structure analyst's recovery numbers]\n"
            "- [another pushback]\n"
            "TAIL RISKS:\n"
            "- [low-probability, high-loss scenario]\n"
            "- [another tail risk]\n"
            "LEGAL / PROCESS RISKS: [cramdown, adequate protection, 363 sale risk, plan approval risk]\n"
            "EXIT LIQUIDITY: [how we get out — secondary market, M&A, IPO, dividend recap — and what could block it]\n"
            "SUMMARY: [2-3 sentence devil's-advocate narrative]"
        )

    async def _dispatch_tool(self, tool_name: str, args: dict) -> dict:
        """Dispatch credit risk tools."""
        try:
            if tool_name == "check_covenant_headroom":
                covenants = check_covenant_headroom(
                    ebitda_mm=args.get("ebitda_mm", 0),
                    total_debt_mm=args.get("total_debt_mm", 0),
                    max_leverage_x=args.get("max_leverage_x", 5.0),
                    min_coverage_x=args.get("min_coverage_x", 2.0),
                    cash_interest_mm=args.get("cash_interest_mm"),
                )
                return {
                    "covenants_table": format_covenant_status(covenants),
                    "breached_count": sum(1 for c in covenants if c.is_breached),
                }
            elif tool_name == "calculate_leverage":
                return {
                    "leverage_x": calculate_leverage(
                        total_debt_mm=args.get("total_debt_mm", 0),
                        ebitda_mm=args.get("ebitda_mm", 0),
                        include_lease_obligations=args.get("include_lease_obligations", 0.0),
                    )
                }
            elif tool_name == "calculate_coverage":
                return {
                    "coverage_x": calculate_coverage(
                        ebitda_mm=args.get("ebitda_mm", 0),
                        cash_interest_mm=args.get("cash_interest_mm", 0),
                        preferred_dividends_mm=args.get("preferred_dividends_mm", 0.0),
                    )
                }
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Error in {tool_name}: {e}")
            return {"error": str(e)}


class CreditCommitteeAgent(BaseAgent):
    """Writes the final IC memo — what we're doing, how big, why, what could go wrong."""

    name = "CreditCommitteeAgent"
    system_prompt = (
        "You are the Portfolio Manager chairing an investment committee at a distressed credit fund. "
        "You've heard three briefs: the cap-structure analyst, the situation analyst, and the risk officer. "
        "Write the final IC memo. Be decisive — RECOMMEND a specific trade in a specific instrument "
        "at a specific sizing band. Reflect the firm's capital-preservation philosophy: if our thesis "
        "is wrong, we should not lose meaningful money. Your memo will be read by investors — "
        "it must be clear, quantitative, and free of jargon that isn't load-bearing."
    )
    tool_schemas: list[dict] = []

    def _build_user_message(self, context: dict) -> str:
        company = context.get("company_name", "UNKNOWN")
        situation_type = context.get("situation_type", "")
        thesis = context.get("thesis_one_liner", "")
        cap_brief = context.get("cap_structure_brief", "Not available")
        situation_brief = context.get("situation_brief", "Not available")
        risk_brief = context.get("credit_risk_brief", "Not available")
        position = context.get("current_position", "No existing position")

        return (
            f"Write the investment committee memo for {company} ({situation_type}).\n"
            f"Working thesis: {thesis}\n"
            f"Current position: {position}\n\n"
            "--- CAP STRUCTURE BRIEF ---\n"
            f"{cap_brief}\n\n"
            "--- SITUATION BRIEF ---\n"
            f"{situation_brief}\n\n"
            "--- CREDIT RISK BRIEF ---\n"
            f"{risk_brief}\n\n"
            "Write the memo using EXACTLY this format (this is the document the IC votes on):\n\n"
            "RECOMMENDATION: [BUY / BUILD / HOLD / REDUCE / EXIT]\n"
            "INSTRUMENT: [exact tranche or instrument, e.g. '2028 Term Loan at 72c' or 'post-reorg equity']\n"
            "SIZING: [target position in % of AUM or $MM, with a range]\n"
            "TARGET PRICE: [where we think this clears — par, post-reorg equity implied value, or $/share]\n"
            "CATALYST: [what gets us paid, with expected date]\n\n"
            "## Executive Summary\n"
            "[3-4 sentences: situation, trade, why it works, asymmetric downside]\n\n"
            "## Thesis\n"
            "- [point 1 — why the trade works]\n"
            "- [point 2]\n"
            "- [point 3]\n\n"
            "## Downside\n"
            "[What's our loss if we're wrong? Quote a specific % of capital at risk and reference the risk officer's concerns.]\n\n"
            "## Sizing Rationale\n"
            "[Why this size? What's the scaling plan if price moves against us?]\n\n"
            "## Vote\n"
            "[one line: APPROVE / APPROVE WITH CONDITIONS (list conditions) / REJECT]"
        )

    async def _dispatch_tool(self, tool_name: str, args: dict) -> dict:
        return {"error": f"CreditCommitteeAgent has no tools: {tool_name}"}


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


@dataclass
class CreditCommitteeResult:
    situation: Situation
    cap_structure_brief: AgentBrief
    situation_brief: AgentBrief
    credit_risk_brief: AgentBrief
    committee_memo: AgentBrief
    total_tokens: int

    def rendered_memo(self) -> str:
        """Return a single-file markdown memo combining all briefs."""
        s = self.situation
        cap_table = _format_cap_structure([_tranche_as_row(t) for t in s.capital_structure])
        timeline = _format_timeline(s.timeline)
        metrics = _format_metrics(s.operating_metrics)

        return "\n".join(
            [
                f"# IC Memo — {s.company} ({s.situation_type})",
                "",
                f"> {s.thesis_one_liner}",
                "",
                "## Situation",
                f"- **Sector:** {s.sector}",
                f"- **Situation type:** {s.situation_type}",
                f"- **Current position:** {s.current_position}",
                "",
                "### Operating metrics",
                metrics,
                "",
                "### Capital structure (pre-restructuring)",
                cap_table,
                "",
                "### Timeline",
                timeline,
                "",
                "---",
                "## CapStructureAgent brief",
                self.cap_structure_brief.content.strip() or "(no output)",
                "",
                "## SituationAgent brief",
                self.situation_brief.content.strip() or "(no output)",
                "",
                "## CreditRiskAgent brief",
                self.credit_risk_brief.content.strip() or "(no output)",
                "",
                "---",
                "## Committee memo",
                self.committee_memo.content.strip() or "(no output)",
                "",
                "---",
                f"_Total LLM tokens used: {self.total_tokens:,}_",
            ]
        )


async def run_credit_committee(situation: Situation) -> CreditCommitteeResult:
    """Run the full 4-agent credit-committee debate.

    Phase 1: CapStructureAgent + SituationAgent in parallel
    Phase 2: CreditRiskAgent (reads both briefs)
    Phase 3: CreditCommitteeAgent (reads all three)
    """
    base_context = situation.as_context()

    logger.info(f"[{situation.company}] Running CapStructureAgent + SituationAgent in parallel")
    cap_brief, sit_brief = await asyncio.gather(
        CapStructureAgent().run(base_context),
        SituationAgent().run(base_context),
        return_exceptions=False,
    )

    logger.info(f"[{situation.company}] Running CreditRiskAgent")
    risk_context = {
        **base_context,
        "cap_structure_brief": cap_brief.content,
        "situation_brief": sit_brief.content,
    }
    risk_brief = await CreditRiskAgent().run(risk_context)

    logger.info(f"[{situation.company}] Running CreditCommitteeAgent")
    committee_context = {
        **base_context,
        "cap_structure_brief": cap_brief.content,
        "situation_brief": sit_brief.content,
        "credit_risk_brief": risk_brief.content,
    }
    committee_brief = await CreditCommitteeAgent().run(committee_context)

    total_tokens = sum(
        [
            cap_brief.tokens_used,
            sit_brief.tokens_used,
            risk_brief.tokens_used,
            committee_brief.tokens_used,
        ]
    )

    return CreditCommitteeResult(
        situation=situation,
        cap_structure_brief=cap_brief,
        situation_brief=sit_brief,
        credit_risk_brief=risk_brief,
        committee_memo=committee_brief,
        total_tokens=total_tokens,
    )
