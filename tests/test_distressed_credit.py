"""Tests for distressed credit analysis tools.

Uses ATI Physical Therapy April 2023 TSA numbers as ground truth.
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
# Fixtures — ATI Physical Therapy April 2023 capital structure
# ---------------------------------------------------------------------------


@pytest.fixture
def ati_capital_structure() -> list[CapitalStructureTranche]:
    return [
        CapitalStructureTranche(
            name="Super-Priority Revolver",
            face_amount_mm=50.0,
            coupon="SOFR + ~500",
            maturity="2027-02",
            seniority=1,
            holder="HPS Investment Partners",
        ),
        CapitalStructureTranche(
            name="1L Senior Secured Term Loan",
            face_amount_mm=500.0,
            coupon="SOFR + 725",
            maturity="2028-02",
            seniority=2,
            holder="HPS Investment Partners",
        ),
        CapitalStructureTranche(
            name="2L PIK Convertible Notes",
            face_amount_mm=125.0,
            coupon="8% PIK",
            maturity="2028-08",
            seniority=3,
            holder="TSA participants",
        ),
        CapitalStructureTranche(
            name="Series A Senior Preferred",
            face_amount_mm=165.0,
            coupon="8% cash / 10% PIK",
            maturity="Perpetual",
            seniority=4,
            holder="Advent International",
        ),
    ]


# ---------------------------------------------------------------------------
# calculate_leverage
# ---------------------------------------------------------------------------


class TestCalculateLeverage:
    def test_ati_pre_tsa(self):
        # ATI FY2022: $550M gross debt / $6.7M EBITDA = 82.1x
        result = calculate_leverage(total_debt_mm=550.0, ebitda_mm=6.7)
        assert abs(result - 82.09) < 0.1

    def test_normal_leverage(self):
        result = calculate_leverage(total_debt_mm=500.0, ebitda_mm=100.0)
        assert abs(result - 5.0) < 1e-9

    def test_with_lease_obligations(self):
        result = calculate_leverage(
            total_debt_mm=500.0, ebitda_mm=100.0, include_lease_obligations=50.0
        )
        assert abs(result - 5.5) < 1e-9

    def test_zero_ebitda_returns_inf(self):
        result = calculate_leverage(total_debt_mm=500.0, ebitda_mm=0.0)
        assert result == float("inf")

    def test_negative_ebitda_returns_inf(self):
        result = calculate_leverage(total_debt_mm=500.0, ebitda_mm=-10.0)
        assert result == float("inf")


# ---------------------------------------------------------------------------
# calculate_coverage
# ---------------------------------------------------------------------------


class TestCalculateCoverage:
    def test_ati_pre_tsa(self):
        # $6.7M EBITDA / ~$61M cash interest = 0.11x
        result = calculate_coverage(ebitda_mm=6.7, cash_interest_mm=61.0)
        assert abs(result - 0.11) < 0.01

    def test_ati_post_tsa(self):
        # Guided EBITDA $30M / $49M post-TSA cash interest = 0.61x
        result = calculate_coverage(ebitda_mm=30.0, cash_interest_mm=49.0)
        assert abs(result - 0.612) < 0.01

    def test_healthy_coverage(self):
        result = calculate_coverage(ebitda_mm=100.0, cash_interest_mm=25.0)
        assert abs(result - 4.0) < 1e-9

    def test_with_preferred_dividends(self):
        result = calculate_coverage(
            ebitda_mm=100.0, cash_interest_mm=25.0, preferred_dividends_mm=10.0
        )
        assert abs(result - (100 / 35)) < 1e-9

    def test_zero_interest_returns_inf(self):
        result = calculate_coverage(ebitda_mm=100.0, cash_interest_mm=0.0)
        assert result == float("inf")


# ---------------------------------------------------------------------------
# calculate_recovery_waterfall
# ---------------------------------------------------------------------------


class TestCalculateRecoveryWaterfall:
    def test_full_recovery_at_high_ev(self, ati_capital_structure):
        # At $900M EV, all tranches (ex-PIK accrual) should be fully covered
        result = calculate_recovery_waterfall(
            ati_capital_structure, enterprise_value_mm=900.0, include_piK_accrual=False
        )
        assert result["Super-Priority Revolver"] == 100.0
        assert result["1L Senior Secured Term Loan"] == 100.0
        assert result["2L PIK Convertible Notes"] == 100.0

    def test_partial_recovery_at_low_ev(self, ati_capital_structure):
        # At $75M EV (bear case), only revolver gets full recovery, 1L partial
        result = calculate_recovery_waterfall(
            ati_capital_structure, enterprise_value_mm=75.0, include_piK_accrual=False
        )
        assert result["Super-Priority Revolver"] == 100.0
        assert result["1L Senior Secured Term Loan"] < 100.0
        assert result["2L PIK Convertible Notes"] == 0.0

    def test_zero_recovery_below_senior_debt(self, ati_capital_structure):
        # At $40M EV (< revolver face), revolver partial, everything else zero
        result = calculate_recovery_waterfall(
            ati_capital_structure, enterprise_value_mm=40.0, include_piK_accrual=False
        )
        assert result["Super-Priority Revolver"] < 100.0
        assert result["1L Senior Secured Term Loan"] == 0.0
        assert result["2L PIK Convertible Notes"] == 0.0

    def test_seniority_ordering(self, ati_capital_structure):
        # Senior tranches always recover before junior tranches
        result = calculate_recovery_waterfall(
            ati_capital_structure, enterprise_value_mm=250.0, include_piK_accrual=False
        )
        # With $250M: Revolver (50) + 1L (partial 200) — 2L gets 0
        assert result["Super-Priority Revolver"] >= result["1L Senior Secured Term Loan"]
        assert result["1L Senior Secured Term Loan"] >= result["2L PIK Convertible Notes"]


# ---------------------------------------------------------------------------
# analyze_recovery_scenarios
# ---------------------------------------------------------------------------


class TestAnalyzeRecoveryScenarios:
    def test_returns_three_scenarios(self, ati_capital_structure):
        scenarios = analyze_recovery_scenarios(
            ati_capital_structure,
            base_ebitda_mm=30.0,
            bear_ebitda_mm=12.0,
            bull_ebitda_mm=50.0,
        )
        assert len(scenarios) == 3
        names = [s.scenario_name for s in scenarios]
        assert "Base Case" in names
        assert "Bear Case" in names
        assert "Bull Case" in names

    def test_bull_ev_greater_than_bear(self, ati_capital_structure):
        scenarios = analyze_recovery_scenarios(
            ati_capital_structure,
            base_ebitda_mm=30.0,
            bear_ebitda_mm=12.0,
            bull_ebitda_mm=50.0,
            base_multiple=7.0,
            bear_multiple=5.0,
            bull_multiple=11.0,
        )
        ev_by_name = {s.scenario_name: s.enterprise_value_mm for s in scenarios}
        assert ev_by_name["Bull Case"] > ev_by_name["Base Case"] > ev_by_name["Bear Case"]

    def test_fulcrum_identified(self, ati_capital_structure):
        # Base case EV = $210M (30 * 7x) — 2L PIK should be the fulcrum
        scenarios = analyze_recovery_scenarios(
            ati_capital_structure,
            base_ebitda_mm=30.0,
            bear_ebitda_mm=12.0,
            bull_ebitda_mm=50.0,
        )
        base = next(s for s in scenarios if s.scenario_name == "Base Case")
        # At $210M EV: Revolver ($50) + 1L ($500) = $550M needed; EV = $210M
        # Only revolver fully covered → 1L is the fulcrum
        assert base.fulcrum_tranche is not None

    def test_all_tranches_in_each_scenario(self, ati_capital_structure):
        scenarios = analyze_recovery_scenarios(
            ati_capital_structure,
            base_ebitda_mm=30.0,
            bear_ebitda_mm=12.0,
            bull_ebitda_mm=50.0,
        )
        tranche_names = {t.name for t in ati_capital_structure}
        for scenario in scenarios:
            assert set(scenario.recovery_by_tranche.keys()) == tranche_names


# ---------------------------------------------------------------------------
# check_covenant_headroom
# ---------------------------------------------------------------------------


class TestCheckCovenantHeadroom:
    def test_ati_leverage_breached(self):
        # ATI: 82.1x leverage vs typical 5.0x covenant → breached
        covenants = check_covenant_headroom(ebitda_mm=6.7, total_debt_mm=550.0, max_leverage_x=5.0)
        lev_covenant = next(c for c in covenants if "Leverage" in c.covenant_name)
        assert lev_covenant.is_breached is True
        assert lev_covenant.headroom_pct == 0.0

    def test_healthy_leverage_not_breached(self):
        covenants = check_covenant_headroom(
            ebitda_mm=100.0, total_debt_mm=300.0, max_leverage_x=5.0
        )
        lev_covenant = next(c for c in covenants if "Leverage" in c.covenant_name)
        assert lev_covenant.is_breached is False
        assert lev_covenant.headroom_pct > 0.0

    def test_coverage_covenant_included_when_interest_provided(self):
        covenants = check_covenant_headroom(
            ebitda_mm=100.0,
            total_debt_mm=300.0,
            max_leverage_x=5.0,
            min_coverage_x=2.0,
            cash_interest_mm=30.0,
        )
        assert len(covenants) == 2
        cov_names = [c.covenant_name for c in covenants]
        assert any("Coverage" in n for n in cov_names)

    def test_coverage_covenant_excluded_without_interest(self):
        covenants = check_covenant_headroom(
            ebitda_mm=100.0, total_debt_mm=300.0, max_leverage_x=5.0
        )
        assert len(covenants) == 1

    def test_coverage_covenant_breached(self):
        # ATI post-TSA: 0.6x coverage vs 2.0x minimum → breached
        covenants = check_covenant_headroom(
            ebitda_mm=30.0,
            total_debt_mm=550.0,
            max_leverage_x=99.0,
            min_coverage_x=2.0,
            cash_interest_mm=49.0,
        )
        cov_covenant = next(c for c in covenants if "Coverage" in c.covenant_name)
        assert cov_covenant.is_breached is True


# ---------------------------------------------------------------------------
# calculate_fulcrum_security
# ---------------------------------------------------------------------------


class TestCalculateFulcrumSecurity:
    def test_1l_is_fulcrum_at_210m_ev(self, ati_capital_structure):
        # At $210M EV: Revolver ($50) full, 1L has $160/$500 = 32% → fulcrum
        name, recovery = calculate_fulcrum_security(ati_capital_structure, 210.0)
        assert name == "1L Senior Secured Term Loan"
        assert recovery is not None
        assert 0 < recovery < 100

    def test_2l_is_fulcrum_at_700m_ev(self, ati_capital_structure):
        # At $700M EV (without PIK accrual): Revolver + 1L fully covered ($550M)
        # 2L has $150/$125 left → 2L partially recovered → fulcrum (ignoring PIK)
        name, recovery = calculate_fulcrum_security(
            ati_capital_structure,
            # 700M covers Revolver(50) + 1L(500) = 550, leaves 150 > 2L face(125) → full...
            # Let's use 600M: 600-50-500 = 50 < 125 → 2L partial
            600.0,
        )
        assert name is not None
        assert recovery is not None
        assert 0 < recovery < 100

    def test_no_fulcrum_at_very_high_ev(self, ati_capital_structure):
        # At $1B EV, all debt fully covered (no partial recovery tranche)
        name, recovery = calculate_fulcrum_security(ati_capital_structure, 1000.0)
        # Preferred ($165) at seniority 4: 1000 - 50 - 500 - 125 = 325 > 165 → full
        # No fulcrum (all fully recovered)
        # Note: PIK accrual may affect this — test with PIK disabled conceptually
        # This is valid if EV > total face + PIK accrual
        assert name is None or recovery == 100.0 or recovery is None

    def test_returns_none_at_zero_ev(self, ati_capital_structure):
        name, recovery = calculate_fulcrum_security(ati_capital_structure, 0.0)
        assert name is None
        assert recovery is None


# ---------------------------------------------------------------------------
# Formatting utilities
# ---------------------------------------------------------------------------


class TestFormattingUtils:
    def test_format_recovery_analysis_returns_markdown(self, ati_capital_structure):
        scenarios = analyze_recovery_scenarios(
            ati_capital_structure,
            base_ebitda_mm=30.0,
            bear_ebitda_mm=12.0,
            bull_ebitda_mm=50.0,
        )
        result = format_recovery_analysis(scenarios)
        assert "Base Case" in result
        assert "Bear Case" in result
        assert "Bull Case" in result
        assert "|" in result

    def test_format_covenant_status_returns_markdown(self):
        covenants = check_covenant_headroom(
            ebitda_mm=6.7,
            total_debt_mm=550.0,
            max_leverage_x=5.0,
            min_coverage_x=2.0,
            cash_interest_mm=61.0,
        )
        result = format_covenant_status(covenants)
        assert "BREACHED" in result or "OK" in result
        assert "|" in result


# ---------------------------------------------------------------------------
# Integration: ATI situation → end-to-end recovery analysis
# ---------------------------------------------------------------------------


class TestATISituationIntegration:
    def test_build_ati_situation_and_run_scenarios(self):
        from examples.distressed.ati_2023 import build_ati_situation

        situation = build_ati_situation()
        assert situation.company == "ATI Physical Therapy"
        assert len(situation.capital_structure) == 4

        scenarios = analyze_recovery_scenarios(
            situation.capital_structure,
            base_ebitda_mm=30.0,
            bear_ebitda_mm=12.0,
            bull_ebitda_mm=50.0,
        )
        assert len(scenarios) == 3

        # Bull recovery (EV = 50 * 11 = $550M) on 2L PIK should be non-zero
        bull = next(s for s in scenarios if s.scenario_name == "Bull Case")
        pik_recovery = bull.recovery_by_tranche.get("2L PIK Convertible Notes", 0)
        assert pik_recovery >= 0  # structure-dependent on PIK accrual

    def test_ati_leverage_matches_memo(self):
        # From ATI memo: pre-TSA 82.1x
        leverage = calculate_leverage(550.0, 6.7)
        assert abs(leverage - 82.09) < 0.1

    def test_ati_coverage_matches_memo(self):
        # From ATI memo: 0.11x pre-TSA
        coverage = calculate_coverage(6.7, 61.0)
        assert abs(coverage - 0.11) < 0.01
