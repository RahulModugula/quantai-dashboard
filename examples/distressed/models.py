"""Shared data models for distressed credit analysis."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
