"""Domain-specific tools for distressed credit analysis.

These tools provide quantitative calculations that credit committee agents
can use to support their analysis, including:
- Leverage and coverage calculations
- Recovery waterfall analysis
- Covenant headroom checking
- DIP financing tracking
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Type-only import to avoid circular dependency with agents.py.
    from examples.distressed.agents import CapitalStructureTranche

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


def calculate_leverage(
    total_debt_mm: float,
    ebitda_mm: float,
    include_lease_obligations: float = 0.0,
) -> float:
    """Calculate leverage ratio (Total Debt / EBITDA).

    Args:
        total_debt_mm: Total debt in millions
        ebitda_mm: EBITDA in millions
        include_lease_obligations: Additional lease obligations in millions

    Returns:
        Leverage multiple (e.g., 5.2x)
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
    """Calculate interest coverage ratio (EBITDA / Cash Interest).

    Args:
        ebitda_mm: EBITDA in millions
        cash_interest_mm: Cash interest expense in millions
        preferred_dividends_mm: Preferred dividends in millions

    Returns:
        Coverage ratio (e.g., 2.5x)
    """
    total_fixed_charges = cash_interest_mm + preferred_dividends_mm

    if total_fixed_charges <= 0:
        logger.warning("Fixed charges are zero or negative, coverage is undefined")
        return float("inf")

    return ebitda_mm / total_fixed_charges


def calculate_recovery_waterfall(
    capital_structure: list[CapitalStructureTranche],
    enterprise_value_mm: float,
    include_piK_accrual: bool = True,
) -> dict[str, float]:
    """Calculate recovery per tranche under a waterfall analysis.

    Args:
        capital_structure: List of capital structure tranches
        enterprise_value_mm: Enterprise value at exit in millions
        include_piK_accrual: Whether to include PIK accrual in face amounts

    Returns:
        Dictionary mapping tranche names to recovery % of par
    """
    # Sort by seniority (lower number = more senior)
    sorted_tranches = sorted(capital_structure, key=lambda t: t.seniority)

    recovery_by_tranche = {}
    remaining_value = enterprise_value_mm

    for tranche in sorted_tranches:
        face_amount = tranche.face_amount_mm

        # Add PIK accrual if applicable (simplified: 8% annual accrual)
        if include_piK_accrual and "PIK" in tranche.coupon:
            # Assume 2 years of PIK accrual for simplicity
            face_amount *= 1.16

        if remaining_value <= 0:
            recovery_by_tranche[tranche.name] = 0.0
            continue

        recovery = min(remaining_value, face_amount)
        recovery_pct = (recovery / face_amount) * 100.0

        recovery_by_tranche[tranche.name] = recovery_pct
        remaining_value -= recovery

    return recovery_by_tranche


def analyze_recovery_scenarios(
    capital_structure: list[CapitalStructureTranche],
    base_ebitda_mm: float,
    bear_ebitda_mm: float,
    bull_ebitda_mm: float,
    base_multiple: float = 7.0,
    bear_multiple: float = 5.0,
    bull_multiple: float = 11.0,
) -> list[RecoveryScenario]:
    """Generate recovery analysis across base/bear/bull EBITDA scenarios.

    Args:
        capital_structure: List of capital-structure tranches
        base_ebitda_mm: Base case EBITDA in millions
        bear_ebitda_mm: Bear case EBITDA in millions
        bull_ebitda_mm: Bull case EBITDA in millions
        base_multiple: EV/EBITDA multiple for base case
        bear_multiple: EV/EBITDA multiple for bear case
        bull_multiple: EV/EBITDA multiple for bull case

    Returns:
        List of RecoveryScenario objects
    """
    scenarios = [
        ("Base Case", base_ebitda_mm, base_multiple),
        ("Bear Case", bear_ebitda_mm, bear_multiple),
        ("Bull Case", bull_ebitda_mm, bull_multiple),
    ]

    results = []
    for scenario_name, ebitda, multiple in scenarios:
        ev_mm = ebitda * multiple
        recovery_by_tranche = calculate_recovery_waterfall(capital_structure, ev_mm)

        # Identify fulcrum (first tranche with recovery < 100% but > 0%)
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


def check_covenant_headroom(
    ebitda_mm: float,
    total_debt_mm: float,
    max_leverage_x: float = 5.0,
    min_coverage_x: float = 2.0,
    cash_interest_mm: float | None = None,
) -> list[CovenantStatus]:
    """Check covenant headroom for leverage and coverage.

    Args:
        ebitda_mm: Current EBITDA in millions
        total_debt_mm: Total debt in millions
        max_leverage_x: Maximum allowed leverage multiple
        min_coverage_x: Minimum required coverage ratio
        cash_interest_mm: Cash interest expense (for coverage check)

    Returns:
        List of CovenantStatus objects
    """
    covenants = []

    # Leverage covenant
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

    # Coverage covenant (if interest provided)
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


def calculate_fulcrum_security(
    capital_structure: list[CapitalStructureTranche],
    enterprise_value_mm: float,
) -> tuple[str | None, float | None]:
    """Identify fulcrum security in capital structure.

    The fulcrum is first tranche (by seniority) that receives
    partial recovery (0% < recovery < 100%).

    Args:
        capital_structure: List of capital structure tranches
        enterprise_value_mm: Enterprise value at exit in millions

    Returns:
        Tuple of (fulcrum_tranche_name, recovery_percentage)
    """
    recovery_by_tranche = calculate_recovery_waterfall(capital_structure, enterprise_value_mm)

    for tranche in sorted(capital_structure, key=lambda t: t.seniority):
        recovery = recovery_by_tranche.get(tranche.name, 0.0)
        if 0 < recovery < 100:
            return tranche.name, recovery

    return None, None


def format_recovery_analysis(
    scenarios: list[RecoveryScenario],
) -> str:
    """Format recovery scenarios into a markdown table.

    Args:
        scenarios: List of RecoveryScenario objects

    Returns:
        Markdown-formatted table string
    """
    lines = [
        "| Scenario | EBITDA ($MM) | EV ($MM) | EV/EBITDA | Fulcrum | Key Recoveries % par |",
        "|----------|----------------|------------|-------------|----------|---------------------|",
    ]

    for scenario in scenarios:
        # Format key recoveries (first 3 tranches)
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
    """Format covenant status into a markdown table.

    Args:
        covenants: List of CovenantStatus objects

    Returns:
        Markdown-formatted table string
    """
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


# ---------------------------------------------------------------------------
# Tool schema for agent use
# ---------------------------------------------------------------------------


CREDIT_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "calculate_leverage",
            "description": (
                "Calculate leverage ratio (Total Debt / EBITDA). Returns leverage multiple."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "total_debt_mm": {
                        "type": "number",
                        "description": "Total debt in millions",
                    },
                    "ebitda_mm": {
                        "type": "number",
                        "description": "EBITDA in millions",
                    },
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
            "description": (
                "Calculate interest coverage ratio (EBITDA / Cash Interest). "
                "Returns coverage multiple."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ebitda_mm": {
                        "type": "number",
                        "description": "EBITDA in millions",
                    },
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
                "Returns recovery % per tranche for each scenario."
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
            "name": "check_covenant_headroom",
            "description": (
                "Check covenant headroom for leverage and coverage ratios. "
                "Returns current values, thresholds, and breach status."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ebitda_mm": {
                        "type": "number",
                        "description": "Current EBITDA in millions",
                    },
                    "total_debt_mm": {
                        "type": "number",
                        "description": "Total debt in millions",
                    },
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
