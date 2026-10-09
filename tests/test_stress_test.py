"""Tests for the rule engine.

Fixtures copy the rule inputs of four seed cases as of Oct 9 2026, so the tests
check the rules, not the data. Editing data/cases_seed.csv during verification
changes the app's verdicts but does not break these tests.
"""

import pytest

from src.data import load_all
from src.stress_test import (
    AT_RISK,
    LIKELY_BARRED,
    STILL_PROSECUTABLE,
    VERDICTS,
    evaluate_all,
    evaluate_case,
    summarize,
)

FATIA_HARIS = {  # Minister complains of defamation -> R1
    "case_id": "fatia_haris", "complainant_type": "public_official",
    "article": "27(3); hoax", "public_interest": True, "harm_shown": False,
    "source": "CFJ EIT report Case Study E",
}
RICHARD_LEE = {  # Lawyer files for the alleged victim -> R2
    "case_id": "richard_lee", "complainant_type": "representative",
    "article": "27(3)", "public_interest": True, "harm_shown": False,
    "source": "CFJ EIT report Legal Analysis (defamation)",
}
ROY_SURYO = {  # Hate speech, no harm shown, not public interest -> R3 only
    "case_id": "roy_suryo", "complainant_type": "individual_victim",
    "article": "28(2)", "public_interest": False, "harm_shown": False,
    "source": "CFJ EIT report Case Study A",
}
MARZUKI = {  # Individual victim, defamation, public interest -> R4 only
    "case_id": "marzuki", "complainant_type": "individual_victim",
    "article": "27(3)", "public_interest": True, "harm_shown": False,
    "source": "CFJ EIT report Case Study B",
}


def test_r1_fatia_haris_barred():
    r = evaluate_case(FATIA_HARIS)
    assert r["verdict"] == LIKELY_BARRED
    assert "R1" in r["rules_fired"]
    assert r["source"] == "CFJ EIT report Case Study E"


def test_r2_richard_lee_barred():
    r = evaluate_case(RICHARD_LEE)
    assert r["verdict"] == LIKELY_BARRED
    assert "R2" in r["rules_fired"]
    assert "R1" not in r["rules_fired"]


def test_r3_roy_suryo_at_risk():
    r = evaluate_case(ROY_SURYO)
    assert r["verdict"] == AT_RISK
    assert r["rules_fired"] == ["R3"]


def test_r4_marzuki_at_risk():
    r = evaluate_case(MARZUKI)
    assert r["verdict"] == AT_RISK
    assert r["rules_fired"] == ["R4"]


def test_one_reason_per_rule_fired():
    r = evaluate_case(FATIA_HARIS)
    for rule in r["rules_fired"]:
        assert any(reason.startswith(f"{rule}:") for reason in r["reasons"])
    assert set(r["rule_basis"]) == set(r["rules_fired"])


@pytest.mark.parametrize("complainant_type", ["public_official", "government_body", "company", "group"])
def test_r1_all_excluded_complainants(complainant_type):
    r = evaluate_case({**MARZUKI, "complainant_type": complainant_type})
    assert r["verdict"] == LIKELY_BARRED


def test_27a_counts_as_defamation():
    r = evaluate_case({**FATIA_HARIS, "article": "27A"})
    assert "R1" in r["rules_fired"]


def test_r1_does_not_apply_to_hate_speech():
    r = evaluate_case({**ROY_SURYO, "complainant_type": "group"})
    assert r["verdict"] == AT_RISK
    assert "R1" not in r["rules_fired"]


def test_r3_not_fired_when_harm_shown():
    r = evaluate_case({**ROY_SURYO, "harm_shown": True})
    assert r["verdict"] == STILL_PROSECUTABLE
    assert r["rules_fired"] == []


def test_unknown_complainant_needs_data():
    r = evaluate_case({**MARZUKI, "complainant_type": "unknown", "public_interest": False})
    assert r["verdict"] == STILL_PROSECUTABLE
    assert "R1" not in r["rules_fired"] and "R2" not in r["rules_fired"]
    assert any("Complainant unknown — needs data" in reason for reason in r["reasons"])


def test_unrecognised_complainant_treated_as_unknown():
    r = evaluate_case({**FATIA_HARIS, "complainant_type": "individual"})
    assert any("needs data" in reason for reason in r["reasons"])


def test_string_booleans_from_csv():
    r = evaluate_case({**MARZUKI, "public_interest": "true", "harm_shown": "false"})
    assert r["rules_fired"] == ["R4"]


def test_out_of_scope_article_noted():
    r = evaluate_case({**MARZUKI, "article": "other"})
    assert r["verdict"] == AT_RISK  # R4 still applies
    assert any("outside" in reason for reason in r["reasons"])


def test_displacement_watch_flag():
    assert evaluate_case({**MARZUKI, "article": "433"})["displacement_watch"]
    assert not evaluate_case(MARZUKI)["displacement_watch"]


def test_deterministic():
    assert evaluate_case(FATIA_HARIS) == evaluate_case(FATIA_HARIS)


def test_runs_on_seed_data():
    cases = load_all().cases
    results = evaluate_all(cases)
    assert len(results) == len(cases)
    assert results["verdict"].isin(VERDICTS).all()
    s = summarize(results)
    assert s["total"] == sum(s[v] for v in VERDICTS)
