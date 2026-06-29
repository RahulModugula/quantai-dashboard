"""Domain-specific tools for distressed credit analysis.

Deterministic, unit-tested calculations the credit-committee agents call to
support their analysis. The LLM decides *which* tool to call and interprets the
output; the math here never varies by temperature, prompt phrasing, or model
version. That separation — judgment from the model, arithmetic from audited
functions — is the point.

Tools:
- Leverage and coverage ratios
- Recovery waterfall (pari-passu pro-rata, admin claims, PIK accrual)
- Bear / base / bull recovery scenarios
- Fulcrum security detection
- Attachment / detachment points (leverage in turns of EBITDA per tranche)
- Breakeven enterprise value per tranche
- Covenant headroom
- Current yield / approximate yield-to-maturity on traded tranches
- Maturity-wall summary
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass

from examples.distressed.models import CapitalStructureTranche

logger = logging.getLogger(__name__)


@dataclass
class RecoveryScenario:
    """Recovery analysis for a specific EBITDA scenario."""

    scenario_name: str
    ebitda_mm: float
    enterprise_value_mm: float
    recovery_by_tranche: dict[str, float]  # tranche_name -> recovery_pct_of_par
    fulcrum_tranche: str | None = None


@dataclass
class CovenantStatus:
    """Status of key covenants."""

    covenant_name: str
    current_value: float
    threshold: float
    headroom_pct: float
    is_breached: bool
    description: str


@dataclass
class TrancheAttachment:
    """Attachment / detachment of a tranche, in turns of EBITDA.

    ``attach_x`` is the leverage multiple at which the tranche begins to take
    loss (all strictly-senior debt / EBITDA). ``detach_x`` is the multiple at
    which it is made whole (senior debt + this tranche's pari-passu group /
    EBITDA). Pari-passu tranches share the same attach/detach band.
    """

    tranche_name: str
    seniority: int
    debt_above_mm: float
    debt_through_mm: float
    attach_x: float | None
    detach_x: float | None


# ---------------------------------------------------------------------------
# Ratios
# ---------------------------------------------------------------------------


def calculate_leverage(
    total_debt_mm: float,
    ebitda_mm: float,
    include_lease_obligations: float = 0.0,
) -> float:
    """Calculate leverage ratio (Total Debt / EBITDA).

    Returns the leverage multiple (e.g. 5.2), or ``inf`` if EBITDA <= 0.
    """
    if ebitda_mm <= 0:
        logger.warning("EBITDA is zero or negative, leverage is undefined")
        return float("inf")

    total_obligations = total_debt_mm + include_lease_obligations
    return total_obligations / ebitda_mm


def calculate_coverage(
    ebitda_mm: float,
    cash_interest_mm: float,
    preferred_dividends_mm: float = 0.0,
) -> float:
    """Calculate interest coverage ratio (EBITDA / fixed charges).

    Returns the coverage multiple (e.g. 2.5), or ``inf`` if fixed charges <= 0.
    """
    total_fixed_charges = cash_interest_mm + preferred_dividends_mm

    if total_fixed_charges <= 0:
        logger.warning("Fixed charges are zero or negative, coverage is undefined")
        return float("inf")

    return ebitda_mm / total_fixed_charges


# ---------------------------------------------------------------------------
# Recovery waterfall
# ---------------------------------------------------------------------------


def _infer_rate(coupon: str, default: float = 0.08) -> float:
    """Pull a leading percentage out of a coupon string (e.g. '8% PIK' -> 0.08).

    Falls back to ``default`` when no percentage is present (e.g. floating-rate
    coupons quoted as a spread like 'SOFR + 725').
    """
    if not coupon:
        return default
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", coupon)
    return float(m.group(1)) / 100.0 if m else default


def _accreted_face(tranche: CapitalStructureTranche, include_pik: bool, pik_years: float) -> float:
    """Face amount, grown for PIK accrual when the coupon is PIK."""
    face = tranche.face_amount_mm
    if include_pik and "PIK" in (tranche.coupon or "").upper():
        rate = _infer_rate(tranche.coupon, default=0.08)
        face = face * (1.0 + rate) ** pik_years
    return face


def calculate_recovery_waterfall(
    capital_structure: list[CapitalStructureTranche],
    enterprise_value_mm: float,
    include_piK_accrual: bool = True,
    pik_years: float = 2.0,
    admin_claims_mm: float = 0.0,
) -> dict[str, float]:
    """Recovery per tranche (% of par) under an absolute-priority waterfall.

    Tranches are paid strictly in order of seniority. Tranches that share a
    seniority rank are treated as **pari passu** and split the value available
    to their rank **pro rata by claim**. ``admin_claims_mm`` (DIP / admin /
    priority claims) are paid off the top before any tranche.

    Args:
        capital_structure: the tranches (seniority 1 = most senior).
        enterprise_value_mm: distributable enterprise value.
        include_piK_accrual: grow PIK tranche claims by accrued interest.
        pik_years: years of PIK accrual to assume.
        admin_claims_mm: super-priority admin/DIP claims paid first.

    Returns:
        ``{tranche_name: recovery_pct_of_par}``.
    """
    remaining = max(0.0, enterprise_value_mm - max(0.0, admin_claims_mm))

    groups: dict[int, list[CapitalStructureTranche]] = defaultdict(list)
    for t in capital_structure:
        groups[t.seniority].append(t)

    recovery: dict[str, float] = {}
    for seniority in sorted(groups):
        tranches = groups[seniority]
        claims = {t.name: _accreted_face(t, include_piK_accrual, pik_years) for t in tranches}
        total_claim = sum(claims.values())

        if total_claim <= 0:
            for t in tranches:
                recovery[t.name] = 0.0
            continue

        payable = min(remaining, total_claim)
        for name, claim in claims.items():
            # pro-rata share of the value reaching this rank
            got = payable * (claim / total_claim) if total_claim > 0 else 0.0
            recovery[name] = (got / claim * 100.0) if claim > 0 else 0.0
        remaining -= payable

    return recovery


def analyze_recovery_scenarios(
    capital_structure: list[CapitalStructureTranche],
    base_ebitda_mm: float,
    bear_ebitda_mm: float,
    bull_ebitda_mm: float,
    base_multiple: float = 7.0,
    bear_multiple: float = 5.0,
    bull_multiple: float = 11.0,
) -> list[RecoveryScenario]:
    """Recovery analysis across bear / base / bull EBITDA scenarios."""
    scenarios = [
        ("Base Case", base_ebitda_mm, base_multiple),
        ("Bear Case", bear_ebitda_mm, bear_multiple),
        ("Bull Case", bull_ebitda_mm, bull_multiple),
    ]

    results = []
    for scenario_name, ebitda, multiple in scenarios:
        ev_mm = ebitda * multiple
        recovery_by_tranche = calculate_recovery_waterfall(capital_structure, ev_mm)

        # Fulcrum: most senior tranche with partial recovery (0% < r < 100%)
        fulcrum = None
        for tranche in sorted(capital_structure, key=lambda t: t.seniority):
            recovery = recovery_by_tranche.get(tranche.name, 0.0)
            if 0 < recovery < 100:
                fulcrum = tranche.name
                break

        results.append(
            RecoveryScenario(
                scenario_name=scenario_name,
                ebitda_mm=ebitda,
                enterprise_value_mm=ev_mm,
                recovery_by_tranche=recovery_by_tranche,
                fulcrum_tranche=fulcrum,
            )
        )

    return results


def calculate_fulcrum_security(
    capital_structure: list[CapitalStructureTranche],
    enterprise_value_mm: float,
) -> tuple[str | None, float | None]:
    """Identify the fulcrum security at a given enterprise value.

    The fulcrum is the most senior tranche receiving partial recovery
    (0% < recovery < 100%) — the security that converts to the reorganized
    equity in a restructuring.
    """
    recovery_by_tranche = calculate_recovery_waterfall(capital_structure, enterprise_value_mm)

    for tranche in sorted(capital_structure, key=lambda t: t.seniority):
        recovery = recovery_by_tranche.get(tranche.name, 0.0)
        if 0 < recovery < 100:
            return tranche.name, recovery

    return None, None


# ---------------------------------------------------------------------------
# Attachment / detachment and breakeven
# ---------------------------------------------------------------------------


def calculate_attachment_detachment(
    capital_structure: list[CapitalStructureTranche],
    ebitda_mm: float,
) -> list[TrancheAttachment]:
    """Attachment and detachment points per tranche, in turns of EBITDA.

    For each tranche: ``attach_x`` = (debt strictly senior) / EBITDA — the
    leverage at which the tranche starts taking loss; ``detach_x`` = (senior
    debt + this tranche's pari-passu group) / EBITDA — the leverage at which it
    is made whole. This is the standard "where do I sit in the stack" view.
    """
    groups: dict[int, list[CapitalStructureTranche]] = defaultdict(list)
    for t in capital_structure:
        groups[t.seniority].append(t)

    out: list[TrancheAttachment] = []
    debt_above = 0.0
    for seniority in sorted(groups):
        group = groups[seniority]
        group_face = sum(t.face_amount_mm for t in group)
        debt_through = debt_above + group_face
        for t in group:
            out.append(
                TrancheAttachment(
                    tranche_name=t.name,
                    seniority=seniority,
                    debt_above_mm=debt_above,
                    debt_through_mm=debt_through,
                    attach_x=(debt_above / ebitda_mm) if ebitda_mm > 0 else None,
                    detach_x=(debt_through / ebitda_mm) if ebitda_mm > 0 else None,
                )
            )
        debt_above = debt_through

    return out


def calculate_breakeven_ev(
    capital_structure: list[CapitalStructureTranche],
    tranche_name: str,
) -> tuple[float | None, float | None]:
    """Enterprise value at which a tranche (a) starts to recover and (b) is whole.

    Returns ``(ev_recovery_begins, ev_full_recovery)`` in $MM, using face value
    (no PIK accrual) for transparency. ``ev_recovery_begins`` = face of all
    strictly-senior debt; ``ev_full_recovery`` = that plus the tranche's
    pari-passu group. Returns ``(None, None)`` if the tranche is not found.
    """
    target = next((t for t in capital_structure if t.name == tranche_name), None)
    if target is None:
        return None, None

    debt_above = sum(t.face_amount_mm for t in capital_structure if t.seniority < target.seniority)
    group_face = sum(t.face_amount_mm for t in capital_structure if t.seniority == target.seniority)
    return debt_above, debt_above + group_face


# ---------------------------------------------------------------------------
# Yield on traded tranches
# ---------------------------------------------------------------------------


def current_yield(coupon_pct: float, price_pct_par: float) -> float:
    """Current yield (%) = annual coupon / price. Price is % of par."""
    if price_pct_par <= 0:
        return float("inf")
    return coupon_pct / price_pct_par * 100.0


def approx_ytm(coupon_pct: float, price_pct_par: float, years_to_maturity: float) -> float:
    """Approximate yield-to-maturity (%) via the standard bond approximation.

    ytm ≈ (coupon + (100 - price)/years) / ((100 + price)/2)
    """
    if years_to_maturity <= 0 or price_pct_par <= 0:
        return float("inf")
    return (
        (coupon_pct + (100.0 - price_pct_par) / years_to_maturity)
        / ((100.0 + price_pct_par) / 2.0)
        * 100.0
    )


# ---------------------------------------------------------------------------
# Covenants and maturity wall
# ---------------------------------------------------------------------------


def check_covenant_headroom(
    ebitda_mm: float,
    total_debt_mm: float,
    max_leverage_x: float = 5.0,
    min_coverage_x: float = 2.0,
    cash_interest_mm: float | None = None,
) -> list[CovenantStatus]:
    """Check leverage and (optionally) coverage covenant headroom."""
    covenants = []

    current_leverage = calculate_leverage(total_debt_mm, ebitda_mm)
    leverage_headroom = (
        (max_leverage_x - current_leverage) / max_leverage_x * 100
        if current_leverage < max_leverage_x
        else 0.0
    )
    covenants.append(
        CovenantStatus(
            covenant_name="Leverage Covenant",
            current_value=current_leverage,
            threshold=max_leverage_x,
            headroom_pct=leverage_headroom,
            is_breached=current_leverage > max_leverage_x,
            description=f"Total Debt / EBITDA = {current_leverage:.1f}x vs {max_leverage_x:.1f}x limit",
        )
    )

    if cash_interest_mm is not None:
        current_coverage = calculate_coverage(ebitda_mm, cash_interest_mm)
        coverage_headroom = (
            (current_coverage - min_coverage_x) / min_coverage_x * 100
            if current_coverage >= min_coverage_x
            else 0.0
        )
        covenants.append(
            CovenantStatus(
                covenant_name="Interest Coverage Covenant",
                current_value=current_coverage,
                threshold=min_coverage_x,
                headroom_pct=coverage_headroom,
                is_breached=current_coverage < min_coverage_x,
                description=f"EBITDA / Cash Interest = {current_coverage:.2f}x vs {min_coverage_x:.1f}x minimum",
            )
        )

    return covenants


def summarize_maturity_wall(
    capital_structure: list[CapitalStructureTranche],
) -> dict[str, float]:
    """Aggregate face amount by maturity year (the 'maturity wall').

    Parses a 4-digit year out of each tranche's ``maturity`` string. Tranches
    with no parseable year (e.g. 'Perpetual', 'N/A') bucket under 'No maturity'.
    Returns an ordered ``{year: total_face_mm}`` dict.
    """
    wall: dict[str, float] = defaultdict(float)
    for t in capital_structure:
        m = re.search(r"(19|20)\d{2}", t.maturity or "")
        key = m.group(0) if m else "No maturity"
        wall[key] += t.face_amount_mm

    # Sort numeric years ascending, push 'No maturity' to the end.
    def _sort_key(k: str) -> tuple[int, str]:
        return (0, k) if k.isdigit() else (1, k)

    return {k: wall[k] for k in sorted(wall, key=_sort_key)}


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


def format_recovery_analysis(scenarios: list[RecoveryScenario]) -> str:
    """Format recovery scenarios into a markdown table."""
    lines = [
        "| Scenario | EBITDA ($MM) | EV ($MM) | EV/EBITDA | Fulcrum | Key Recoveries % par |",
        "|----------|----------------|------------|-------------|----------|---------------------|",
    ]
    for scenario in scenarios:
        key_recoveries = []
        for tranche_name, recovery_pct in list(scenario.recovery_by_tranche.items())[:3]:
            key_recoveries.append(f"{tranche_name}: {recovery_pct:.0f}%")
        lines.append(
            f"| {scenario.scenario_name} | ${scenario.ebitda_mm:.1f} | "
            f"${scenario.enterprise_value_mm:.1f} | "
            f"{scenario.enterprise_value_mm / scenario.ebitda_mm:.1f}x | "
            f"{scenario.fulcrum_tranche or 'N/A'} | "
            f"{', '.join(key_recoveries)} |"
        )
    return "\n".join(lines)


def format_covenant_status(covenants: list[CovenantStatus]) -> str:
    """Format covenant status into a markdown table."""
    lines = [
        "| Covenant | Current | Threshold | Headroom | Status |",
        "|----------|----------|------------|---------|--------|",
    ]
    for covenant in covenants:
        status_icon = "❌ BREACHED" if covenant.is_breached else "✅ OK"
        lines.append(
            f"| {covenant.covenant_name} | {covenant.current_value:.2f} | "
            f"{covenant.threshold:.2f} | {covenant.headroom_pct:+.1f}% | {status_icon} |"
        )
    return "\n".join(lines)


def format_attachment_detachment(attachments: list[TrancheAttachment]) -> str:
    """Format attachment/detachment points into a markdown table."""
    lines = [
        "| Tranche | Debt Above ($MM) | Debt Through ($MM) | Attach (x) | Detach (x) |",
        "|---------|------------------|--------------------|-----------|-----------|",
    ]
    for a in attachments:
        attach = f"{a.attach_x:.1f}x" if a.attach_x is not None else "—"
        detach = f"{a.detach_x:.1f}x" if a.detach_x is not None else "—"
        lines.append(
            f"| {a.tranche_name} | {a.debt_above_mm:.0f} | {a.debt_through_mm:.0f} | "
            f"{attach} | {detach} |"
        )
    return "\n".join(lines)


def format_maturity_wall(wall: dict[str, float]) -> str:
    """Format a maturity-wall summary into a markdown table."""
    lines = ["| Maturity | Face ($MM) |", "|----------|------------|"]
    for year, face in wall.items():
        lines.append(f"| {year} | {face:.0f} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool schema for agent use
# ---------------------------------------------------------------------------


CREDIT_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "calculate_leverage",
            "description": "Calculate leverage ratio (Total Debt / EBITDA). Returns leverage multiple.",
            "parameters": {
                "type": "object",
                "properties": {
                    "total_debt_mm": {"type": "number", "description": "Total debt in millions"},
                    "ebitda_mm": {"type": "number", "description": "EBITDA in millions"},
                    "include_lease_obligations": {
                        "type": "number",
                        "description": "Additional lease obligations in millions (optional)",
                        "default": 0.0,
                    },
                },
                "required": ["total_debt_mm", "ebitda_mm"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_coverage",
            "description": "Calculate interest coverage ratio (EBITDA / Cash Interest). Returns coverage multiple.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ebitda_mm": {"type": "number", "description": "EBITDA in millions"},
                    "cash_interest_mm": {
                        "type": "number",
                        "description": "Cash interest expense in millions",
                    },
                    "preferred_dividends_mm": {
                        "type": "number",
                        "description": "Preferred dividends in millions (optional)",
                        "default": 0.0,
                    },
                },
                "required": ["ebitda_mm", "cash_interest_mm"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_recovery_scenarios",
            "description": (
                "Generate recovery analysis across base/bear/bull EBITDA scenarios. "
                "Returns recovery % per tranche for each scenario, with the fulcrum security."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "base_ebitda_mm": {
                        "type": "number",
                        "description": "Base case EBITDA in millions",
                    },
                    "bear_ebitda_mm": {
                        "type": "number",
                        "description": "Bear case EBITDA in millions",
                    },
                    "bull_ebitda_mm": {
                        "type": "number",
                        "description": "Bull case EBITDA in millions",
                    },
                    "base_multiple": {
                        "type": "number",
                        "description": "EV/EBITDA multiple for base case (default 7.0)",
                        "default": 7.0,
                    },
                    "bear_multiple": {
                        "type": "number",
                        "description": "EV/EBITDA multiple for bear case (default 5.0)",
                        "default": 5.0,
                    },
                    "bull_multiple": {
                        "type": "number",
                        "description": "EV/EBITDA multiple for bull case (default 11.0)",
                        "default": 11.0,
                    },
                },
                "required": ["base_ebitda_mm", "bear_ebitda_mm", "bull_ebitda_mm"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_attachment_detachment",
            "description": (
                "Attachment and detachment points per tranche, in turns of EBITDA. "
                "Shows where each tranche sits in the capital structure: attach_x is the "
                "leverage where it starts taking loss, detach_x where it is made whole."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ebitda_mm": {"type": "number", "description": "EBITDA in millions"},
                },
                "required": ["ebitda_mm"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_breakeven_ev",
            "description": (
                "Enterprise value ($MM) at which a named tranche starts to recover and at "
                "which it is fully covered. Tells you the asset-value cushion below a tranche."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tranche_name": {
                        "type": "string",
                        "description": "Exact name of the tranche to analyze",
                    },
                },
                "required": ["tranche_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_maturity_wall",
            "description": (
                "Aggregate face amount by maturity year (the maturity wall). Returns "
                "{year: total_face_mm}. Use to spot near-term refinancing pressure."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_covenant_headroom",
            "description": (
                "Check covenant headroom for leverage and coverage ratios. "
                "Returns current values, thresholds, and breach status."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ebitda_mm": {"type": "number", "description": "Current EBITDA in millions"},
                    "total_debt_mm": {"type": "number", "description": "Total debt in millions"},
                    "max_leverage_x": {
                        "type": "number",
                        "description": "Maximum allowed leverage multiple (default 5.0)",
                        "default": 5.0,
                    },
                    "min_coverage_x": {
                        "type": "number",
                        "description": "Minimum required coverage ratio (default 2.0)",
                        "default": 2.0,
                    },
                    "cash_interest_mm": {
                        "type": "number",
                        "description": "Cash interest expense in millions (optional)",
                    },
                },
                "required": ["ebitda_mm", "total_debt_mm"],
            },
        },
    },
]
