"""Tests for the advanced credit tools: pari-passu waterfall, attachment/
detachment, breakeven EV, yields, and the maturity wall.

These guard the deterministic-math moat — the calculations the LLM agents rely
on but never perform themselves.
"""

from __future__ import annotations

import math

import pytest

from examples.distressed.credit_tools import (
    _infer_rate,
    approx_ytm,
    calculate_attachment_detachment,
    calculate_breakeven_ev,
    calculate_recovery_waterfall,
    current_yield,
    summarize_maturity_wall,
)
from examples.distressed.models import CapitalStructureTranche


def _tranche(name, face, seniority, coupon="", maturity="N/A"):
    return CapitalStructureTranche(
        name=name, face_amount_mm=face, coupon=coupon, maturity=maturity, seniority=seniority
    )


@pytest.fixture
def simple_stack():
    # 100 senior / 100 (two pari-passu of 50) / 100 junior
    return [
        _tranche("1L", 100, 1, maturity="2027"),
        _tranche("2L-A", 50, 2, maturity="2028"),
        _tranche("2L-B", 50, 2, maturity="2028"),
        _tranche("Unsecured", 100, 3, maturity="2029"),
    ]


# ---------------------------------------------------------------------------
# pari-passu waterfall
# ---------------------------------------------------------------------------


def test_pari_passu_shares_pro_rata(simple_stack):
    # EV 150: 1L fully covered (100), 50 left for the 100 of pari-passu 2L → 50%
    r = calculate_recovery_waterfall(simple_stack, 150.0, include_piK_accrual=False)
    assert r["1L"] == 100.0
    assert r["2L-A"] == pytest.approx(50.0)
    assert r["2L-B"] == pytest.approx(50.0)  # equal claims share equally
    assert r["Unsecured"] == 0.0


def test_pari_passu_unequal_claims_share_pro_rata():
    stack = [
        _tranche("A", 300, 1),  # senior, fully covered
        _tranche("B", 100, 2),
        _tranche("C", 300, 2),  # B and C pari-passu, 1:3 ratio
    ]
    # EV 500: A takes 300, 200 left for 400 of pari claims → 50% each
    r = calculate_recovery_waterfall(stack, 500.0, include_piK_accrual=False)
    assert r["A"] == 100.0
    assert r["B"] == pytest.approx(50.0)
    assert r["C"] == pytest.approx(50.0)


def test_admin_claims_paid_off_the_top(simple_stack):
    # EV 150 with 50 admin claims → only 100 distributable → 1L exactly whole
    r = calculate_recovery_waterfall(
        simple_stack, 150.0, include_piK_accrual=False, admin_claims_mm=50.0
    )
    assert r["1L"] == pytest.approx(100.0)
    assert r["2L-A"] == 0.0


def test_full_recovery_when_ev_exceeds_all(simple_stack):
    r = calculate_recovery_waterfall(simple_stack, 10_000.0, include_piK_accrual=False)
    assert all(v == 100.0 for v in r.values())


def test_pik_accrual_grows_claim():
    stack = [_tranche("PIK", 100, 1, coupon="10% PIK")]
    # With PIK accrual (10% for 2 years compounding → claim 121), EV 100 → ~82.6%
    r = calculate_recovery_waterfall(stack, 100.0, include_piK_accrual=True, pik_years=2.0)
    assert r["PIK"] == pytest.approx(100.0 / 121.0 * 100.0, rel=1e-3)
    # Without accrual, full recovery
    r2 = calculate_recovery_waterfall(stack, 100.0, include_piK_accrual=False)
    assert r2["PIK"] == 100.0


# ---------------------------------------------------------------------------
# attachment / detachment
# ---------------------------------------------------------------------------


def test_attachment_detachment_turns(simple_stack):
    a = {x.tranche_name: x for x in calculate_attachment_detachment(simple_stack, ebitda_mm=50.0)}
    # 1L: nothing above (0x), through 100/50 = 2.0x
    assert a["1L"].attach_x == pytest.approx(0.0)
    assert a["1L"].detach_x == pytest.approx(2.0)
    # 2L pari group: above = 100 → 2.0x; through = 200 → 4.0x; same band for both
    assert a["2L-A"].attach_x == pytest.approx(2.0)
    assert a["2L-A"].detach_x == pytest.approx(4.0)
    assert a["2L-B"].attach_x == pytest.approx(2.0)
    assert a["2L-B"].detach_x == pytest.approx(4.0)
    # Unsecured: above = 200 → 4.0x, through = 300 → 6.0x
    assert a["Unsecured"].attach_x == pytest.approx(4.0)
    assert a["Unsecured"].detach_x == pytest.approx(6.0)


def test_attachment_handles_zero_ebitda(simple_stack):
    a = calculate_attachment_detachment(simple_stack, ebitda_mm=0.0)
    assert all(x.attach_x is None and x.detach_x is None for x in a)
    # dollar amounts still computed
    assert a[0].debt_through_mm == 100.0


# ---------------------------------------------------------------------------
# breakeven EV
# ---------------------------------------------------------------------------


def test_breakeven_ev(simple_stack):
    begins, full = calculate_breakeven_ev(simple_stack, "Unsecured")
    assert begins == 200.0  # all senior debt
    assert full == 300.0  # + its own 100
    # pari-passu tranche: full recovery EV includes the whole group
    begins2, full2 = calculate_breakeven_ev(simple_stack, "2L-A")
    assert begins2 == 100.0
    assert full2 == 200.0


def test_breakeven_ev_unknown_tranche(simple_stack):
    assert calculate_breakeven_ev(simple_stack, "nope") == (None, None)


# ---------------------------------------------------------------------------
# yields
# ---------------------------------------------------------------------------


def test_current_yield():
    assert current_yield(8.0, 50.0) == pytest.approx(16.0)
    assert current_yield(6.0, 100.0) == pytest.approx(6.0)
    assert current_yield(8.0, 0.0) == float("inf")


def test_approx_ytm_discount_bond():
    # 8% coupon, 80 price, 5y: (8 + 20/5) / (90) = 12/90 → ~13.33%
    assert approx_ytm(8.0, 80.0, 5.0) == pytest.approx(12.0 / 90.0 * 100.0, rel=1e-6)


def test_approx_ytm_par_bond_equals_coupon():
    # At par, approx YTM ≈ coupon
    assert approx_ytm(6.0, 100.0, 5.0) == pytest.approx(6.0)


def test_approx_ytm_guards():
    assert approx_ytm(8.0, 80.0, 0.0) == float("inf")
    assert math.isinf(approx_ytm(8.0, 0.0, 5.0))


# ---------------------------------------------------------------------------
# maturity wall + rate inference
# ---------------------------------------------------------------------------


def test_maturity_wall_aggregates_by_year():
    stack = [
        _tranche("A", 100, 1, maturity="Feb 2027"),
        _tranche("B", 200, 2, maturity="2027-08"),
        _tranche("C", 50, 3, maturity="Jan 2028"),
        _tranche("Pref", 165, 4, maturity="Perpetual"),
    ]
    wall = summarize_maturity_wall(stack)
    assert wall["2027"] == 300.0  # A + B
    assert wall["2028"] == 50.0
    assert wall["No maturity"] == 165.0
    # ordering: years ascending, "No maturity" last
    assert list(wall.keys()) == ["2027", "2028", "No maturity"]


def test_infer_rate():
    assert _infer_rate("8% PIK") == pytest.approx(0.08)
    assert _infer_rate("10% cash / 12% PIK") == pytest.approx(0.10)  # first match
    assert _infer_rate("SOFR + 725") == pytest.approx(0.08)  # no %, default
    assert _infer_rate("") == pytest.approx(0.08)
