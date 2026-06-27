"""Tests for the situation loader and CLI scaffolding.

These cover the layer that turns a user-authored YAML/JSON file into a
``Situation`` the credit committee can run on — the thing that makes the
credit committee a reusable tool rather than a single hardcoded example.
"""

from __future__ import annotations

import json

import pytest

from examples.distressed.models import CapitalStructureTranche, Situation
from examples.distressed.run import SITUATIONS_DIR, TEMPLATE_PATH


# ---------------------------------------------------------------------------
# CapitalStructureTranche.from_dict
# ---------------------------------------------------------------------------


def test_tranche_from_dict_canonical_fields():
    t = CapitalStructureTranche.from_dict(
        {"name": "1L TL", "face_amount_mm": 500, "seniority": 1, "current_price": 72}
    )
    assert t.name == "1L TL"
    assert t.face_amount_mm == 500.0
    assert t.seniority == 1
    assert t.current_price == 72.0


def test_tranche_from_dict_friendly_aliases():
    # The YAML templates use face_mm / price_pct_par.
    t = CapitalStructureTranche.from_dict(
        {"name": "Notes", "face_mm": 400, "seniority": 3, "price_pct_par": 38}
    )
    assert t.face_amount_mm == 400.0
    assert t.current_price == 38.0


def test_tranche_missing_required_fields_raise():
    with pytest.raises(ValueError, match="name"):
        CapitalStructureTranche.from_dict({"face_mm": 100, "seniority": 1})
    with pytest.raises(ValueError, match="face"):
        CapitalStructureTranche.from_dict({"name": "X", "seniority": 1})
    with pytest.raises(ValueError, match="seniority"):
        CapitalStructureTranche.from_dict({"name": "X", "face_mm": 100})


def test_tranche_optional_price_defaults_none():
    t = CapitalStructureTranche.from_dict({"name": "Rev", "face_mm": 50, "seniority": 1})
    assert t.current_price is None
    assert t.holder is None


# ---------------------------------------------------------------------------
# Situation.from_dict
# ---------------------------------------------------------------------------


def test_situation_requires_company():
    with pytest.raises(ValueError, match="company"):
        Situation.from_dict({"sector": "Retail"})


def test_situation_minimal_dict():
    s = Situation.from_dict({"company": "ACME"})
    assert s.company == "ACME"
    assert s.capital_structure == []
    assert s.current_position == "No existing position"


def test_situation_company_name_alias():
    s = Situation.from_dict({"company_name": "Legacy Key Co"})
    assert s.company == "Legacy Key Co"


def test_timeline_normalization_variants():
    s = Situation.from_dict(
        {
            "company": "X",
            "timeline": [
                {"date": "2024-01", "event": "filed"},  # canonical
                {"2025-02": "amended"},  # single-key shorthand
                "bare string event",  # bare string
            ],
        }
    )
    assert s.timeline[0] == {"date": "2024-01", "event": "filed"}
    assert s.timeline[1] == {"date": "2025-02", "event": "amended"}
    assert s.timeline[2] == {"date": "", "event": "bare string event"}


def test_bad_capital_structure_type_raises():
    with pytest.raises(ValueError, match="capital_structure"):
        Situation.from_dict({"company": "X", "capital_structure": {"not": "a list"}})


# ---------------------------------------------------------------------------
# Round-trip + file loading
# ---------------------------------------------------------------------------


def test_round_trip_dict():
    original = Situation.from_dict(
        {
            "company": "RoundTrip Inc",
            "ticker": "RT",
            "capital_structure": [
                {"name": "1L", "face_mm": 300, "seniority": 1, "price_pct_par": 90},
                {"name": "2L", "face_mm": 150, "seniority": 2},
            ],
            "operating_metrics": {"EBITDA": "$40M"},
            "key_risks": ["risk one"],
        }
    )
    rebuilt = Situation.from_dict(original.to_dict())
    assert rebuilt.company == original.company
    assert rebuilt.ticker == original.ticker
    assert len(rebuilt.capital_structure) == 2
    assert rebuilt.capital_structure[0].current_price == 90.0
    assert rebuilt.capital_structure[1].current_price is None
    assert rebuilt.operating_metrics == original.operating_metrics
    assert rebuilt.key_risks == original.key_risks


def test_load_json_file(tmp_path):
    payload = {
        "company": "JSON Co",
        "capital_structure": [{"name": "TL", "face_mm": 100, "seniority": 1}],
    }
    p = tmp_path / "deal.json"
    p.write_text(json.dumps(payload))
    s = Situation.from_file(p)
    assert s.company == "JSON Co"
    assert len(s.capital_structure) == 1


def test_unsupported_file_type_raises(tmp_path):
    p = tmp_path / "deal.txt"
    p.write_text("company: X")
    with pytest.raises(ValueError, match="unsupported"):
        Situation.from_file(p)


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        Situation.from_file("does/not/exist.yaml")


# ---------------------------------------------------------------------------
# Bundled situation files (the shipped examples must always be valid)
# ---------------------------------------------------------------------------


def test_template_file_is_valid():
    s = Situation.from_file(TEMPLATE_PATH)
    assert s.company  # template has a placeholder company
    assert len(s.capital_structure) >= 1


def test_ati_yaml_loads_and_is_faithful():
    s = Situation.from_file(SITUATIONS_DIR / "ati_2023.yaml")
    assert s.company == "ATI Physical Therapy"
    assert s.ticker == "ATIP"
    assert len(s.capital_structure) == 4
    # The four tranches, by face amount (sourced from FY2022 filings).
    faces = {t.name: t.face_amount_mm for t in s.capital_structure}
    assert any("1L Senior Secured" in n for n in faces)
    assert 500.0 in faces.values()  # 1L term loan
    assert 125.0 in faces.values()  # new 2L PIK convertible
    # Decision-point marker must survive normalization (agents key off it).
    assert any(e["date"] == "DECISION_POINT" for e in s.timeline)


def test_build_ati_situation_matches_yaml():
    # build_ati_situation now loads the YAML — guard against the loader and the
    # bundled file drifting apart.
    from examples.distressed.ati_2023 import build_ati_situation

    s = build_ati_situation()
    assert s.company == "ATI Physical Therapy"
    assert len(s.capital_structure) == 4
    assert len(s.key_risks) == 7


def _bundled_situation_files():
    return sorted(p for p in SITUATIONS_DIR.glob("*.y*ml") if p.name != "TEMPLATE.yaml")


def test_there_are_multiple_bundled_situations():
    # Breadth matters: the tool should ship more than one worked example.
    names = {p.name for p in _bundled_situation_files()}
    assert {"ati_2023.yaml", "serta_2020.yaml", "hertz_2020.yaml"} <= names


@pytest.mark.parametrize("path", _bundled_situation_files(), ids=lambda p: p.name)
def test_every_bundled_situation_is_valid(path):
    # Every shipped situation must load, have a cap structure, and mark the
    # committee meeting with DECISION_POINT (the agents key off it). This also
    # guards future contributed situations.
    s = Situation.from_file(path)
    assert s.company
    assert len(s.capital_structure) >= 1
    for t in s.capital_structure:
        assert t.face_amount_mm > 0
        assert t.seniority >= 1
    assert any(e["date"] == "DECISION_POINT" for e in s.timeline), (
        f"{path.name} must mark the committee meeting with a DECISION_POINT event"
    )
