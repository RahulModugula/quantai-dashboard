"""Tests for the deterministic cap-structure snapshot, validation, and the
CLI decision parser."""

from __future__ import annotations

from examples.distressed.models import Situation
from examples.distressed.run import _parse_decision
from examples.distressed.snapshot import compute_snapshot, validate_situation


def _situation(**over):
    base = dict(
        company="Test Co",
        ticker="TST",
        sector="Test",
        situation_type="Chapter 11",
        thesis_one_liner="A thesis.",
        timeline=[{"date": "DECISION_POINT", "event": "meeting"}],
        capital_structure=[
            {"name": "1L", "face_mm": 300, "seniority": 1, "maturity": "2027"},
            {"name": "2L", "face_mm": 200, "seniority": 2, "maturity": "2028"},
        ],
        operating_metrics={"x": "y"},
        key_risks=["r"],
        ltm_ebitda_mm=100.0,
        cash_interest_mm=40.0,
    )
    base.update(over)
    return Situation.from_dict(base)


def test_snapshot_with_financials():
    snap = compute_snapshot(_situation())
    assert snap.total_debt_mm == 500.0
    assert snap.leverage_x == 5.0  # 500 / 100
    assert snap.coverage_x == 2.5  # 100 / 40
    assert snap.num_tranches == 2
    # attach/detach in turns of EBITDA
    a = {x.tranche_name: x for x in snap.attachments}
    assert a["1L"].detach_x == 3.0  # 300/100
    assert a["2L"].attach_x == 3.0
    assert a["2L"].detach_x == 5.0
    assert not snap.warnings  # complete situation


def test_snapshot_without_ebitda_degrades():
    snap = compute_snapshot(_situation(ltm_ebitda_mm=None, cash_interest_mm=None))
    assert snap.leverage_x is None
    assert snap.coverage_x is None
    assert all(x.attach_x is None for x in snap.attachments)
    assert snap.total_debt_mm == 500.0  # dollar amounts still computed
    assert any("ltm_ebitda_mm" in w for w in snap.warnings)


def test_snapshot_to_dict_is_json_safe():
    snap = compute_snapshot(_situation())
    import json

    d = snap.to_dict()
    json.dumps(d)  # must not raise
    assert d["leverage_x"] == 5.0
    assert d["maturity_wall_mm"]["2027"] == 300.0


def test_situation_round_trip_includes_financials():
    s = _situation()
    rebuilt = Situation.from_dict(s.to_dict())
    assert rebuilt.ltm_ebitda_mm == 100.0
    assert rebuilt.cash_interest_mm == 40.0
    assert rebuilt.total_debt_mm == 500.0


def test_validate_flags_missing_pieces():
    s = Situation.from_dict({"company": "Bare Co"})
    warnings = validate_situation(s)
    text = " ".join(warnings)
    assert "No capital structure" in text
    assert "thesis" in text
    assert "timeline" in text.lower()


def test_validate_flags_pari_passu_and_dupes():
    s = Situation.from_dict(
        {
            "company": "Dup Co",
            "thesis_one_liner": "t",
            "timeline": [{"date": "DECISION_POINT", "event": "m"}],
            "ltm_ebitda_mm": 50,
            "operating_metrics": {"a": 1},
            "capital_structure": [
                {"name": "TL", "face_mm": 100, "seniority": 1, "maturity": "2027"},
                {"name": "TL", "face_mm": 100, "seniority": 1, "maturity": "2027"},
            ],
        }
    )
    text = " ".join(validate_situation(s))
    assert "Duplicate tranche names" in text
    assert "pari-passu" in text


def test_validate_flags_missing_decision_point():
    s = Situation.from_dict(
        {
            "company": "X",
            "thesis_one_liner": "t",
            "timeline": [{"date": "2024", "event": "something"}],
            "ltm_ebitda_mm": 50,
            "operating_metrics": {"a": 1},
            "capital_structure": [
                {"name": "A", "face_mm": 100, "seniority": 1, "maturity": "2027"},
                {"name": "B", "face_mm": 50, "seniority": 2, "maturity": "2028"},
            ],
        }
    )
    assert any("DECISION_POINT" in w for w in validate_situation(s))


def test_parse_decision_extracts_fields():
    memo = (
        "RECOMMENDATION: BUY\n"
        "INSTRUMENT: 2L PIK Convertible\n"
        "SIZING: 1.0-1.5% AUM\n"
        "TARGET PRICE: 140-180c\n"
        "CATALYST: EBITDA recovery\n\n"
        "## Vote\n"
        "**APPROVE WITH CONDITIONS**\n"
    )
    d = _parse_decision(memo)
    assert d["recommendation"] == "BUY"
    assert d["instrument"] == "2L PIK Convertible"
    assert d["sizing"] == "1.0-1.5% AUM"
    assert d["target_price"] == "140-180c"
    assert d["catalyst"] == "EBITDA recovery"
    assert d["vote"] == "APPROVE WITH CONDITIONS"


def test_parse_decision_handles_missing():
    assert _parse_decision("no structured fields here") == {}


def test_bundled_examples_snapshot_cleanly():
    from examples.distressed.run import SITUATIONS_DIR

    for p in SITUATIONS_DIR.glob("*.y*ml"):
        if p.name == "TEMPLATE.yaml":
            continue
        snap = compute_snapshot(Situation.from_file(p))
        snap.to_dict()  # must not raise
        snap.render_markdown()  # must not raise
