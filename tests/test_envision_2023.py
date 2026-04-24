"""Tests for Envision Healthcare May 2023 distressed credit analysis.

⚠️ DATA VERIFICATION NOTICE
----------------------------
These tests use Envision Healthcare May 2023 Chapter 11 bankruptcy numbers as
ground truth, but THE DATA HAS NOT BEEN VERIFIED against actual SEC filings
(10-K, 10-Q, 8-K, bankruptcy docket).

For production use, all data points should be verified against:
- Envision Healthcare 10-K FY2022
- Envision Healthcare 10-Q Q1 2023
- Envision Healthcare 8-K filings (May 2023 bankruptcy)
- Bankruptcy docket (Delaware)
- DIP financing motions
- Plan of reorganization documents
- Emergence announcement (April 2024)

The ATI Physical Therapy tests ([`test_distressed_credit.py`](test_distressed_credit.py))
use fully verified data and should be used as the primary example for production.

Uses Envision Healthcare May 2023 Chapter 11 bankruptcy numbers as ground truth.
"""

from __future__ import annotations

import pytest

from examples.distressed.credit_tools import (
    analyze_recovery_scenarios,
    calculate_coverage,
    calculate_fulcrum_security,
    calculate_leverage,
    calculate_recovery_waterfall,
    check_covenant_headroom,
    format_covenant_status,
    format_recovery_analysis,
)
from examples.distressed.models import CapitalStructureTranche


# ---------------------------------------------------------------------------
# Fixtures — Envision Healthcare May 2023 capital structure
# ---------------------------------------------------------------------------


@pytest.fixture
def envision_capital_structure() -> list[CapitalStructureTranche]:
    """Envision Healthcare pre-bankruptcy capital structure (May 2023)."""
    return [
        CapitalStructureTranche(
            name="Super-priority DIP Term Loan (New Money)",
            face_amount_mm=2600.0,
            coupon="SOFR + 450",
            maturity="2027-05",
            seniority=1,
            holder="KKR-led lender group",
        ),
        CapitalStructureTranche(
            name="First-Lien Secured Term Loan",
            face_amount_mm=2800.0,
            coupon="LIBOR + 325",
            maturity="2025-03",
            seniority=2,
            holder="Various institutional investors",
        ),
        CapitalStructureTranche(
            name="Second-Lien Secured Notes",
            face_amount_mm=1800.0,
            coupon="8.875%",
            maturity="2026-06",
            seniority=3,
            holder="Various institutional investors",
        ),
        CapitalStructureTranche(
            name="Senior Unsecured Notes",
            face_amount_mm=1200.0,
            coupon="6.875%",
            maturity="2025-03",
            seniority=4,
            holder="Various institutional investors",
        ),
        CapitalStructureTranche(
            name="Senior Subordinated Notes",
            face_amount_mm=1000.0,
            coupon="7.500%",
            maturity="2027-06",
            seniority=5,
            holder="Various institutional investors",
        ),
    ]


# ---------------------------------------------------------------------------
# calculate_leverage
# ---------------------------------------------------------------------------


class TestCalculateLeverageEnvision:
    def test_envision_pre_bankruptcy(self):
        # Envision FY2022: $7.4B gross debt / $485M EBITDA = 15.2x
        result = calculate_leverage(total_debt_mm=7400.0, ebitda_mm=485.0)
        assert abs(result - 15.26) < 0.1

    def test_envision_post_emergence(self):
        # Post-emergence: $5.6B debt / $485M EBITDA = 11.5x
        result = calculate_leverage(total_debt_mm=5600.0, ebitda_mm=485.0)
        assert abs(result - 11.55) < 0.1

    def test_envision_dip_only(self):
        # DIP only: $2.6B / $485M EBITDA = 5.4x
        result = calculate_leverage(total_debt_mm=2600.0, ebitda_mm=485.0)
        assert abs(result - 5.36) < 0.1


# ---------------------------------------------------------------------------
# calculate_coverage
# ---------------------------------------------------------------------------


class TestCalculateCoverageEnvision:
    def test_envision_pre_bankruptcy(self):
        # Envision FY2022: $485M EBITDA / $620M cash interest = 0.78x
        result = calculate_coverage(ebitda_mm=485.0, cash_interest_mm=620.0)
        assert abs(result - 0.78) < 0.01

    def test_envision_post_emergence(self):
        # Post-emergence: $485M EBITDA / $350M cash interest = 1.39x
        result = calculate_coverage(ebitda_mm=485.0, cash_interest_mm=350.0)
        assert abs(result - 1.39) < 0.01

    def test_envision_dip_only(self):
        # DIP only: $485M EBITDA / $150M cash interest = 3.23x
        result = calculate_coverage(ebitda_mm=485.0, cash_interest_mm=150.0)
        assert abs(result - 3.23) < 0.01


# ---------------------------------------------------------------------------
# calculate_recovery_waterfall
# ---------------------------------------------------------------------------


class TestCalculateRecoveryWaterfallEnvision:
    def test_envision_base_case_recovery(self, envision_capital_structure):
        # Base case: $3.6B enterprise value at emergence ($485M EBITDA × 7.5x)
        # Note: post-emergence capital structure is $5.4B debt, but test uses pre-bankruptcy structure
        # This illustrates waterfall waterfall with realistic enterprise value for distressed asset
        ev_mm = 3600.0
        recovery = calculate_recovery_waterfall(envision_capital_structure, ev_mm)

        # DIP and 1L combined face value is $5.4B; EV of $3.6B means partial recovery
        dip_recovery = recovery["Super-priority DIP Term Loan (New Money)"]
        l1_recovery = recovery["First-Lien Secured Term Loan"]

        # DIP is super-priority so should recover first
        assert dip_recovery > 0
        # Recovery cascade: DIP > 1L > 2L > Unsecured > Subordinated
        assert dip_recovery >= l1_recovery

    def test_envision_bear_case_recovery(self, envision_capital_structure):
        # Bear case: $2.4B enterprise value (lower EBITDA scenario)
        ev_mm = 2400.0
        recovery = calculate_recovery_waterfall(envision_capital_structure, ev_mm)

        # Verify seniority-based recovery (each tranche gets less than more senior)
        dip_recovery = recovery["Super-priority DIP Term Loan (New Money)"]
        l1_recovery = recovery["First-Lien Secured Term Loan"]
        l2_recovery = recovery["Second-Lien Secured Notes"]
        unsecured_recovery = recovery["Senior Unsecured Notes"]

        assert dip_recovery >= l1_recovery >= l2_recovery >= unsecured_recovery

    def test_envision_bull_case_recovery(self, envision_capital_structure):
        # Bull case: $5.0B enterprise value (operational improvement scenario)
        ev_mm = 5000.0
        recovery = calculate_recovery_waterfall(envision_capital_structure, ev_mm)

        # With more enterprise value, more tranches achieve full recovery
        dip_recovery = recovery["Super-priority DIP Term Loan (New Money)"]
        l1_recovery = recovery["First-Lien Secured Term Loan"]
        l2_recovery = recovery["Second-Lien Secured Notes"]

        # DIP should recover at or near par in bull case
        assert dip_recovery > 90.0
        # Recovery cascade maintained
        assert dip_recovery >= l1_recovery >= l2_recovery


# ---------------------------------------------------------------------------
# analyze_recovery_scenarios
# ---------------------------------------------------------------------------


class TestAnalyzeRecoveryScenariosEnvision:
    def test_envision_recovery_scenarios(self, envision_capital_structure):
        scenarios = analyze_recovery_scenarios(
            capital_structure=envision_capital_structure,
            base_ebitda_mm=485.0,
            bear_ebitda_mm=400.0,
            bull_ebitda_mm=550.0,
            base_multiple=7.5,
            bear_multiple=6.0,
            bull_multiple=9.0,
        )

        assert len(scenarios) == 3

        # Base case
        base_scenario = scenarios[0]
        assert base_scenario.scenario_name == "Base Case"
        assert base_scenario.ebitda_mm == 485.0
        assert abs(base_scenario.enterprise_value_mm - 3637.5) < 0.1  # 485 * 7.5

        # Bear case
        bear_scenario = scenarios[1]
        assert bear_scenario.scenario_name == "Bear Case"
        assert bear_scenario.ebitda_mm == 400.0
        assert abs(bear_scenario.enterprise_value_mm - 2400.0) < 0.1  # 400 * 6.0

        # Bull case
        bull_scenario = scenarios[2]
        assert bull_scenario.scenario_name == "Bull Case"
        assert bull_scenario.ebitda_mm == 550.0
        assert abs(bull_scenario.enterprise_value_mm - 4950.0) < 0.1  # 550 * 9.0

    def test_envision_fulcrum_identification(self, envision_capital_structure):
        scenarios = analyze_recovery_scenarios(
            capital_structure=envision_capital_structure,
            base_ebitda_mm=485.0,
            bear_ebitda_mm=400.0,
            bull_ebitda_mm=550.0,
            base_multiple=7.5,
            bear_multiple=5.0,
            bull_multiple=9.0,
        )

        # Fulcrum will be the first tranche with partial recovery (0% < recovery < 100%)
        # With high debt levels relative to EV, fulcrum may vary by scenario
        for scenario in scenarios:
            if scenario.fulcrum_tranche:
                # Verify fulcrum has partial recovery
                fulcrum_recovery = scenario.recovery_by_tranche[scenario.fulcrum_tranche]
                assert 0 < fulcrum_recovery < 100


# ---------------------------------------------------------------------------
# calculate_fulcrum_security
# ---------------------------------------------------------------------------


class TestCalculateFulcrumSecurityEnvision:
    def test_envision_fulcrum_security(self, envision_capital_structure):
        # Base case: $3.6B enterprise value (7.5x EBITDA)
        fulcrum_name, fulcrum_recovery = calculate_fulcrum_security(
            envision_capital_structure, enterprise_value_mm=3600.0
        )

        # With $9.4B debt and $3.6B EV, identify which tranche has partial recovery
        # (not 100%, not 0%)
        assert fulcrum_name is not None
        assert fulcrum_recovery is not None
        assert 0 < fulcrum_recovery < 100  # Fulcrum by definition has partial recovery

    def test_envision_fulcrum_rationale(self, envision_capital_structure):
        # The fulcrum is the tranche that receives a mix of new debt and equity
        # in the reorganized company, sitting between super-priority DIP and junior debt
        fulcrum_name, _ = calculate_fulcrum_security(
            envision_capital_structure, enterprise_value_mm=3600.0
        )

        # Verify the fulcrum position in the stack
        dip_tranche = [t for t in envision_capital_structure if "DIP" in t.name][0]
        fulcrum_tranche = [t for t in envision_capital_structure if t.name == fulcrum_name][0]

        # Fulcrum should be senior to junior debt but junior to DIP
        assert fulcrum_tranche.seniority > dip_tranche.seniority
        assert fulcrum_tranche.seniority < 3  # Senior to 2L, unsecured, subordinated


# ---------------------------------------------------------------------------
# check_covenant_headroom
# ---------------------------------------------------------------------------


class TestCheckCovenantHeadroomEnvision:
    def test_envision_pre_bankruptcy_covenant(self):
        # Envision pre-bankruptcy: leverage 15.2x vs typical 4.0x covenant
        covenants = check_covenant_headroom(
            ebitda_mm=485.0,
            total_debt_mm=7400.0,
            max_leverage_x=4.0,
        )

        # Check leverage covenant (first in list)
        leverage_covenant = covenants[0]
        assert leverage_covenant.covenant_name == "Leverage Covenant"
        assert leverage_covenant.is_breached
        assert leverage_covenant.current_value > 10.0  # Highly leveraged
        assert leverage_covenant.threshold == 4.0
        assert leverage_covenant.headroom_pct <= 0  # Negative or zero headroom

    def test_envision_post_emergence_covenant(self):
        # Envision post-emergence: still elevated leverage even after restructuring
        covenants = check_covenant_headroom(
            ebitda_mm=485.0,
            total_debt_mm=5600.0,
            max_leverage_x=4.0,
        )

        # Check leverage covenant (first in list)
        leverage_covenant = covenants[0]
        assert leverage_covenant.covenant_name == "Leverage Covenant"
        assert leverage_covenant.is_breached
        assert leverage_covenant.current_value > 8.0  # Still significantly leveraged
        assert leverage_covenant.threshold == 4.0
        assert leverage_covenant.headroom_pct <= 0  # Negative or zero headroom


# ---------------------------------------------------------------------------
# format_covenant_status
# ---------------------------------------------------------------------------


class TestFormatCovenantStatusEnvision:
    def test_envision_covenant_format(self):
        covenants = check_covenant_headroom(
            ebitda_mm=485.0,
            total_debt_mm=7400.0,
            max_leverage_x=4.0,
        )

        formatted = format_covenant_status(covenants)

        assert "Leverage Covenant" in formatted
        assert "15.26" in formatted
        assert "4.00" in formatted
        assert "BREACHED" in formatted


# ---------------------------------------------------------------------------
# format_recovery_analysis
# ---------------------------------------------------------------------------


class TestFormatRecoveryAnalysisEnvision:
    def test_envision_recovery_format(self, envision_capital_structure):
        scenarios = analyze_recovery_scenarios(
            capital_structure=envision_capital_structure,
            base_ebitda_mm=485.0,
            bear_ebitda_mm=400.0,
            bull_ebitda_mm=550.0,
            base_multiple=7.5,
            bear_multiple=6.0,
            bull_multiple=9.0,
        )

        formatted = format_recovery_analysis(scenarios)

        # Check that all scenarios are present
        assert "Base Case" in formatted
        assert "Bear Case" in formatted
        assert "Bull Case" in formatted

        # Check that EBITDA and EV values are present
        assert "485.0" in formatted
        assert "400.0" in formatted
        assert "550.0" in formatted

        # Check that recovery percentages are present
        assert "%" in formatted


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestEnvisionIntegration:
    def test_envision_full_analysis(self, envision_capital_structure):
        """Integration test simulating full Envision Healthcare analysis."""

        # Calculate leverage
        leverage = calculate_leverage(total_debt_mm=7400.0, ebitda_mm=485.0)
        assert abs(leverage - 15.26) < 0.1

        # Calculate coverage
        coverage = calculate_coverage(ebitda_mm=485.0, cash_interest_mm=620.0)
        assert abs(coverage - 0.78) < 0.01

        # Identify fulcrum
        fulcrum_name, fulcrum_recovery = calculate_fulcrum_security(
            envision_capital_structure, enterprise_value_mm=3600.0
        )
        assert fulcrum_name == "First-Lien Secured Term Loan"
        assert fulcrum_recovery is not None

        # Analyze recovery scenarios
        scenarios = analyze_recovery_scenarios(
            capital_structure=envision_capital_structure,
            base_ebitda_mm=485.0,
            bear_ebitda_mm=400.0,
            bull_ebitda_mm=550.0,
            base_multiple=7.5,
            bear_multiple=6.0,
            bull_multiple=9.0,
        )
        assert len(scenarios) == 3

        # Check covenant status
        covenants = check_covenant_headroom(
            ebitda_mm=485.0,
            total_debt_mm=7400.0,
            max_leverage_x=4.0,
        )
        assert covenants[0].is_breached  # Leverage covenant

        # Verify base case recovery for fulcrum
        if fulcrum_name:
            base_recovery = scenarios[0].recovery_by_tranche[fulcrum_name]
            assert 0 < base_recovery < 100  # Fulcrum has partial recovery
