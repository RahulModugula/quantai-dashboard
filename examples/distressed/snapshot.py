"""Deterministic cap-structure snapshot — computed with no LLM.

Given a ``Situation``, this produces the quantitative view a credit analyst
would build by hand before any committee meeting: total debt, leverage and
coverage (when EBITDA is provided), attachment/detachment in turns of EBITDA,
and the maturity wall. It also runs completeness checks so an analyst can catch
a thin situation file *before* paying for an LLM run.

Used by the ``validate`` command (free pre-flight) and embedded into the memo
and JSON output of ``run``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from examples.distressed.credit_tools import (
    TrancheAttachment,
    calculate_attachment_detachment,
    calculate_coverage,
    calculate_leverage,
    format_attachment_detachment,
    format_maturity_wall,
    summarize_maturity_wall,
)
from examples.distressed.models import Situation


def _fmt_x(value: float | None) -> str:
    if value is None:
        return "—"
    if value == float("inf"):
        return "n/m (EBITDA ≤ 0)"
    return f"{value:.1f}x"


@dataclass
class CapStructureSnapshot:
    """The deterministic, LLM-free quantitative view of a situation."""

    company: str
    num_tranches: int
    total_debt_mm: float
    ltm_ebitda_mm: float | None
    leverage_x: float | None
    cash_interest_mm: float | None
    coverage_x: float | None
    attachments: list[TrancheAttachment]
    maturity_wall: dict[str, float]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "company": self.company,
            "num_tranches": self.num_tranches,
            "total_debt_mm": self.total_debt_mm,
            "ltm_ebitda_mm": self.ltm_ebitda_mm,
            "leverage_x": None
            if self.leverage_x in (None, float("inf"))
            else round(self.leverage_x, 2),
            "cash_interest_mm": self.cash_interest_mm,
            "coverage_x": None
            if self.coverage_x in (None, float("inf"))
            else round(self.coverage_x, 2),
            "attachments": [
                {
                    "tranche": a.tranche_name,
                    "seniority": a.seniority,
                    "debt_above_mm": a.debt_above_mm,
                    "debt_through_mm": a.debt_through_mm,
                    "attach_x": None if a.attach_x is None else round(a.attach_x, 2),
                    "detach_x": None if a.detach_x is None else round(a.detach_x, 2),
                }
                for a in self.attachments
            ],
            "maturity_wall_mm": self.maturity_wall,
            "warnings": self.warnings,
        }

    def render_markdown(self) -> str:
        lines = [
            "## Cap-Structure Snapshot (computed, no LLM)",
            "",
            f"- **Tranches:** {self.num_tranches}",
            f"- **Total debt:** ${self.total_debt_mm:,.0f}MM",
        ]
        if self.ltm_ebitda_mm is not None:
            lines.append(f"- **LTM EBITDA:** ${self.ltm_ebitda_mm:,.1f}MM")
            lines.append(f"- **Leverage (gross):** {_fmt_x(self.leverage_x)}")
        if self.coverage_x is not None:
            lines.append(f"- **Interest coverage:** {_fmt_x(self.coverage_x)}")
        lines += ["", "### Attachment / detachment (turns of EBITDA)", ""]
        lines.append(format_attachment_detachment(self.attachments))
        lines += ["", "### Maturity wall", ""]
        lines.append(format_maturity_wall(self.maturity_wall))
        if self.warnings:
            lines += ["", "### Data-completeness notes", ""]
            lines += [f"- ⚠️ {w}" for w in self.warnings]
        return "\n".join(lines)


def validate_situation(situation: Situation) -> list[str]:
    """Return human-readable completeness/sanity warnings for a situation.

    Warnings are advisory, not errors — a situation can still run with them, but
    each one is something that would make the committee memo weaker.
    """
    w: list[str] = []
    s = situation

    if not s.capital_structure:
        w.append("No capital structure — the cap-stack analysis will be empty.")
    if len(s.capital_structure) == 1:
        w.append("Only one tranche — recovery waterfall and fulcrum analysis are trivial.")
    if not s.thesis_one_liner:
        w.append("No thesis_one_liner — the committee has no stated working thesis.")
    if not s.timeline:
        w.append("No timeline — the SituationAgent has no events to reason over.")
    elif not any(e.get("date") == "DECISION_POINT" for e in s.timeline):
        w.append("No DECISION_POINT event — mark when the committee is meeting.")
    if s.ltm_ebitda_mm is None:
        w.append(
            "No ltm_ebitda_mm — leverage and attach/detach in turns of EBITDA can't be computed."
        )
    if not s.operating_metrics:
        w.append("No operating_metrics — limited financial context for the agents.")

    # Tranche-level sanity
    names = [t.name for t in s.capital_structure]
    if len(names) != len(set(names)):
        w.append("Duplicate tranche names — recovery results will collide.")
    for t in s.capital_structure:
        if t.face_amount_mm <= 0:
            w.append(f"Tranche '{t.name}' has non-positive face amount.")
        if not t.maturity or t.maturity == "N/A":
            w.append(f"Tranche '{t.name}' has no maturity — excluded from the maturity wall.")

    # Informational: pari-passu groups (not a problem, but worth noting)
    seniorities = [t.seniority for t in s.capital_structure]
    if len(seniorities) != len(set(seniorities)):
        w.append(
            "Some tranches share a seniority rank (modeled pari-passu, pro-rata sharing). "
            "Confirm that is intended."
        )

    return w


def compute_snapshot(situation: Situation) -> CapStructureSnapshot:
    """Compute the deterministic snapshot for a situation."""
    cs = situation.capital_structure
    total_debt = situation.total_debt_mm
    ebitda = situation.ltm_ebitda_mm
    cash_int = situation.cash_interest_mm

    leverage = calculate_leverage(total_debt, ebitda) if ebitda is not None else None
    coverage = (
        calculate_coverage(ebitda, cash_int)
        if (ebitda is not None and cash_int is not None)
        else None
    )
    attachments = calculate_attachment_detachment(cs, ebitda if ebitda is not None else 0.0)
    wall = summarize_maturity_wall(cs)

    return CapStructureSnapshot(
        company=situation.company,
        num_tranches=len(cs),
        total_debt_mm=total_debt,
        ltm_ebitda_mm=ebitda,
        leverage_x=leverage,
        cash_interest_mm=cash_int,
        coverage_x=coverage,
        attachments=attachments,
        maturity_wall=wall,
        warnings=validate_situation(situation),
    )
