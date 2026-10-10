"""Tests for src/sensitivity.py with a tiny made-up case table."""

import pandas as pd

from src.sensitivity import Scenario, barred_ids, robustness, run
from src.stress_test import evaluate_case

CASES = pd.DataFrame([
    {"case_id": "a", "name": "A", "complainant_type": "public_official", "article": "27(3)", "year_reported": 2021,
     "public_interest": True, "harm_shown": False, "verified": True},
    {"case_id": "b", "name": "B", "complainant_type": "group", "article": "28(2)", "year_reported": 2022,
     "public_interest": True, "harm_shown": False, "verified": True},
    {"case_id": "c", "name": "C", "complainant_type": "company", "article": "27(3)", "year_reported": 2025,
     "public_interest": False, "harm_shown": False, "verified": True},  # post-ruling: not counted
    {"case_id": "d", "name": "D", "complainant_type": "representative", "article": "27(3)", "year_reported": None,
     "public_interest": False, "harm_shown": False, "verified": False},
])
CASES["year_reported"] = CASES["year_reported"].astype("Int64")


def test_defaults_unchanged():
    assert evaluate_case(CASES.iloc[0].to_dict())["rules_fired"] == ["R1", "R4"]


def test_baseline_counts_only_past_cases():
    ids, total = barred_ids(CASES, Scenario("Baseline", ""))
    assert ids == {"a", "d"} and total == 3


def test_disabling_a_rule():
    ids, _ = barred_ids(CASES, Scenario("x", "", options={"disabled": frozenset({"R1"})}))
    assert ids == {"d"}


def test_r1_for_hate_speech_and_narrower_r1():
    wide, _ = barred_ids(CASES, Scenario("x", "", options={"r1_covers_hate_speech": True}))
    assert "b" in wide
    narrow, _ = barred_ids(CASES, Scenario("x", "", options={"r1_complainants": frozenset({"company", "group"})}))
    assert "a" not in narrow


def test_edit_and_verified_filter():
    ids, _ = barred_ids(CASES, Scenario("x", "", edit={"a": {"complainant_type": "individual_victim"}}))
    assert "a" not in ids
    ids, total = barred_ids(CASES, Scenario("x", "", only_verified="source"))
    assert total == 2 and ids == {"a"}


def test_run_and_robustness_tables():
    scenarios = [Scenario("Baseline", ""), Scenario("No R1", "", options={"disabled": frozenset({"R1"})})]
    table = run(CASES, scenarios)
    assert list(table["headline"]) == ["2 of 3", "1 of 3"]
    assert table.loc[1, "no_longer_barred"] == "A"
    rob = robustness(CASES, scenarios).set_index("case")
    assert rob.loc["D", "stays_barred"] == 2 and rob.loc["A", "stays_barred"] == 1
