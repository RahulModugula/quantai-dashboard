"""Shared data models for distressed credit analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
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

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CapitalStructureTranche:
        """Build a tranche from a plain dict (e.g. parsed YAML/JSON).

        Accepts either the canonical field names (``face_amount_mm``,
        ``current_price``) or the friendlier aliases used in the YAML
        templates (``face_mm``, ``price_pct_par``).
        """
        if "name" not in d:
            raise ValueError("each capital_structure tranche needs a 'name'")
        face = d.get("face_amount_mm", d.get("face_mm"))
        if face is None:
            raise ValueError(f"tranche '{d['name']}' is missing 'face_mm' / 'face_amount_mm'")
        if "seniority" not in d:
            raise ValueError(f"tranche '{d['name']}' is missing 'seniority' (1 = most senior)")
        return cls(
            name=str(d["name"]),
            face_amount_mm=float(face),
            coupon=str(d.get("coupon", "")),
            maturity=str(d.get("maturity", "N/A")),
            seniority=int(d["seniority"]),
            current_price=_opt_float(d.get("current_price", d.get("price_pct_par"))),
            holder=d.get("holder"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Inverse of :meth:`from_dict`, using the canonical field names."""
        return {
            "name": self.name,
            "face_amount_mm": self.face_amount_mm,
            "coupon": self.coupon,
            "maturity": self.maturity,
            "seniority": self.seniority,
            "current_price": self.current_price,
            "holder": self.holder,
        }


def _opt_float(v: Any) -> float | None:
    """Coerce to float, but pass None through (used for optional prices)."""
    return None if v is None else float(v)


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

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Situation:
        """Build a Situation from a plain dict (parsed YAML or JSON).

        This is the entry point that turns a user-authored ``situation.yaml``
        into something the credit committee can run on. Only ``company`` is
        strictly required; everything else degrades gracefully so an analyst
        can start with a sparse file and fill it in.
        """
        if not isinstance(d, dict):
            raise ValueError("situation file must contain a mapping at the top level")
        company = d.get("company") or d.get("company_name")
        if not company:
            raise ValueError("situation is missing the required 'company' field")

        raw_tranches = d.get("capital_structure") or []
        if not isinstance(raw_tranches, list):
            raise ValueError("'capital_structure' must be a list of tranches")
        cap_structure = [CapitalStructureTranche.from_dict(t) for t in raw_tranches]

        timeline = _normalize_timeline(d.get("timeline") or [])

        return cls(
            company=str(company),
            ticker=d.get("ticker"),
            sector=str(d.get("sector", "")),
            situation_type=str(d.get("situation_type", "")),
            thesis_one_liner=str(d.get("thesis_one_liner", "")),
            timeline=timeline,
            capital_structure=cap_structure,
            operating_metrics=dict(d.get("operating_metrics") or {}),
            current_position=str(d.get("current_position", "No existing position")),
            key_risks=list(d.get("key_risks") or []),
        )

    @classmethod
    def from_file(cls, path: str | Path) -> Situation:
        """Load a Situation from a ``.yaml``/``.yml`` or ``.json`` file."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"situation file not found: {p}")
        text = p.read_text()
        suffix = p.suffix.lower()
        if suffix in (".yaml", ".yml"):
            data = _load_yaml(text, source=str(p))
        elif suffix == ".json":
            import json

            data = json.loads(text)
        else:
            raise ValueError(
                f"unsupported situation file type '{suffix}' — use .yaml, .yml or .json"
            )
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """Serialize back to a plain dict (round-trips with :meth:`from_dict`)."""
        return {
            "company": self.company,
            "ticker": self.ticker,
            "sector": self.sector,
            "situation_type": self.situation_type,
            "thesis_one_liner": self.thesis_one_liner,
            "timeline": self.timeline,
            "capital_structure": [t.to_dict() for t in self.capital_structure],
            "operating_metrics": self.operating_metrics,
            "current_position": self.current_position,
            "key_risks": self.key_risks,
        }

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


def _normalize_timeline(events: list[Any]) -> list[dict[str, str]]:
    """Coerce timeline entries into the ``{date, event}`` shape agents expect.

    Accepts the canonical ``{date: ..., event: ...}`` mapping, or a shorthand
    single-key mapping ``{2023-04-11: "TSA signed"}`` that is natural to type
    in YAML.
    """
    out: list[dict[str, str]] = []
    for e in events:
        if isinstance(e, dict) and ("date" in e or "event" in e):
            out.append({"date": str(e.get("date", "")), "event": str(e.get("event", ""))})
        elif isinstance(e, dict) and len(e) == 1:
            ((date, event),) = e.items()
            out.append({"date": str(date), "event": str(event)})
        else:
            out.append({"date": "", "event": str(e)})
    return out


def _load_yaml(text: str, source: str = "<string>") -> dict[str, Any]:
    """Parse YAML, with a friendly error if PyYAML isn't installed."""
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError(
            "PyYAML is required to read .yaml situation files. "
            "Install it with `pip install pyyaml`, or use a .json file instead."
        ) from exc
    data = yaml.safe_load(text)
    if data is None:
        raise ValueError(f"situation file is empty: {source}")
    return data


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
