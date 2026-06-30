"""Regression tests for distressed-credit correctness fixes.

Each test here pins a specific correctness property that was previously wrong or
untested:

- the fulcrum is found at an *exact* claim boundary (not silently missed);
- the waterfall, breakeven, and attach/detach agree about the same tranche
  (one canonical face-value claim, PIK accrual opt-in and applied consistently);
- preferred / equity is not counted as funded debt;
- asset-coverage recovery is available for silo / collateral-pool cases;
- the bundled Serta (uptier) and Hertz (asset-coverage) situations compute a
  sensible snapshot and raise the right structural warnings.
"""

from __future__ import annotations

from pathlib import Path

from examples.distressed.credit_tools import (
    asset_coverage_ratio,
    calculate_attachment_detachment,
    calculate_breakeven_ev,
    calculate_fulcrum_security,
    calculate_recovery_waterfall,
    collateral_recovery_pct,
)
from examples.distressed.models import CapitalStructureTranche, Situation
from examples.distressed.snapshot import compute_snapshot

SITUATIONS_DIR = Path(__file__).resolve().parent.parent / "examples" / "distressed" / "situations"


def _stack() -> list[CapitalStructureTranche]:
    return [
        CapitalStructureTranche("1L", 100.0, "5%", "2028", seniority=1),
        CapitalStructureTranche("2L", 100.0, "8%", "2029", seniority=2),
    ]


# ---------------------------------------------------------------------------
# Fulcrum at an exact claim boundary
# ---------------------------------------------------------------------------


class TestFulcrumBoundary:
    def test_fulcrum_at_exact_senior_boundary(self):
        # EV lands exactly on the 1L's claim: 1L is whole, 2L is impaired at 0%.
        # The impaired 2L is the fulcrum — the old (0 < r < 100) rule missed it.
        name, recovery = calculate_fulcrum_security(_stack(), 100.0)
        assert name == "2L"
        assert recovery == 0.0

    def test_fulcrum_just_below_boundary(self):
        name, recovery = calculate_fulcrum_security(_stack(), 99.9)
        assert name == "1L"
        assert 0 < recovery < 100

    def test_fulcrum_just_above_boundary(self):
        name, recovery = calculate_fulcrum_security(_stack(), 100.1)
        assert name == "2L"
        assert 0 < recovery < 100

    def test_over_collateralized_has_no_fulcrum(self):
        name, recovery = calculate_fulcrum_security(_stack(), 500.0)
        assert name is None and recovery is None

    def test_zero_ev_has_no_fulcrum(self):
        name, recovery = calculate_fulcrum_security(_stack(), 0.0)
        assert name is None and recovery is None


# ---------------------------------------------------------------------------
# The three "audited" tools agree about the same tranche
# ---------------------------------------------------------------------------


class TestToolConsistency:
    def test_waterfall_ties_out_with_breakeven_at_face(self):
        # A PIK tranche. By default (face value, no accrual) the waterfall and
        # the breakeven tool must agree: at EV = full face, the junior tranche
        # is exactly whole.
        stack = [
            CapitalStructureTranche("1L", 100.0, "5%", "2028", seniority=1),
            CapitalStructureTranche("2L PIK", 100.0, "10% PIK", "2029", seniority=2),
        ]
        rec = calculate_recovery_waterfall(stack, 200.0)  # PIK accrual OFF by default
        assert rec["2L PIK"] == 100.0
        begins, whole = calculate_breakeven_ev(stack, "2L PIK")
        assert begins == 100.0 and whole == 200.0
        # And the waterfall agrees exactly at the breakeven point.
        assert calculate_recovery_waterfall(stack, whole)["2L PIK"] == 100.0

    def test_pik_accrual_is_opt_in_and_consistent(self):
        stack = [CapitalStructureTranche("2L PIK", 100.0, "10% PIK", "2029", seniority=1)]
        face_rec = calculate_recovery_waterfall(stack, 100.0)["2L PIK"]
        accreted_rec = calculate_recovery_waterfall(
            stack, 100.0, include_pik_accrual=True, pik_years=2.0
        )["2L PIK"]
        assert face_rec == 100.0  # whole at face by default
        assert accreted_rec < 100.0  # accreted claim (100 * 1.1**2 = 121) is impaired at 100 EV

    def test_attachment_uses_face(self):
        stack = _stack()
        att = {a.tranche_name: a for a in calculate_attachment_detachment(stack, ebitda_mm=50.0)}
        # 2L sits above 100 of senior debt, through 200 — on face, matching breakeven.
        assert att["2L"].debt_above_mm == 100.0
        assert att["2L"].debt_through_mm == 200.0


# ---------------------------------------------------------------------------
# Preferred / equity is not debt
# ---------------------------------------------------------------------------


class TestDebtVsPreferred:
    def test_preferred_excluded_from_debt(self):
        s = Situation(
            company="Test",
            ticker=None,
            sector="",
            situation_type="",
            thesis_one_liner="",
            capital_structure=[
                CapitalStructureTranche("1L TL", 400.0, "5%", "2028", seniority=1),
                CapitalStructureTranche(
                    "Series A Preferred",
                    165.0,
                    "8%",
                    "Perpetual",
                    seniority=2,
                    instrument_class="preferred",
                ),
            ],
            ltm_ebitda_mm=100.0,
        )
        assert s.total_debt_mm == 400.0
        assert s.preferred_equity_mm == 165.0
        assert s.total_claims_mm == 565.0

    def test_instrument_class_inferred_from_name(self):
        t = CapitalStructureTranche.from_dict(
            {"name": "Series A Preferred Stock", "face_mm": 100.0, "seniority": 3}
        )
        assert t.instrument_class == "preferred"
        assert not t.is_debt


# ---------------------------------------------------------------------------
# Asset coverage (silo / collateral-pool recovery)
# ---------------------------------------------------------------------------


class TestAssetCoverage:
    def test_full_coverage(self):
        assert collateral_recovery_pct(collateral_value_mm=120.0, secured_claim_mm=100.0) == 100.0
        assert asset_coverage_ratio(120.0, 100.0) == 1.2

    def test_partial_coverage(self):
        assert collateral_recovery_pct(collateral_value_mm=60.0, secured_claim_mm=100.0) == 60.0
        assert asset_coverage_ratio(60.0, 100.0) == 0.6

    def test_zero_claim_is_infinite_coverage(self):
        assert asset_coverage_ratio(50.0, 0.0) == float("inf")


# ---------------------------------------------------------------------------
# Bundled hard cases compute a sensible snapshot + raise structural warnings
# ---------------------------------------------------------------------------


class TestBundledHardCases:
    def test_serta_uptier_computes_and_warns(self):
        s = Situation.from_file(SITUATIONS_DIR / "serta_2020.yaml")
        snap = compute_snapshot(s)
        # No double-count: pro-forma debt is ~$2.76B, not the ~$3.6B that would
        # result from carrying the rolled-up 1L/2L at full face.
        assert 2700 <= snap.total_debt_mm <= 2800
        assert snap.leverage_x is not None and 10.0 <= snap.leverage_x <= 11.0
        assert any("uptier" in w.lower() or "priming" in w.lower() for w in snap.warnings)

    def test_hertz_asset_coverage_warns(self):
        s = Situation.from_file(SITUATIONS_DIR / "hertz_2020.yaml")
        snap = compute_snapshot(s)
        assert any(
            "asset-backed" in w.lower() or "collateral" in w.lower() or "silo" in w.lower()
            for w in snap.warnings
        )

    def test_ati_snapshot_is_internally_consistent(self):
        s = Situation.from_file(SITUATIONS_DIR / "ati_2023.yaml")
        snap = compute_snapshot(s)
        # $575M debt / $6.7M EBITDA = 85.8x; preferred shown but not in debt.
        assert snap.total_debt_mm == 575.0
        assert snap.preferred_equity_mm == 165.0
        assert abs(snap.leverage_x - 85.8) < 0.2
