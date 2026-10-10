"""Tests for src/outcome_updates.py, plus a check of the real log that runs on every PR."""

import csv
import io

import pandas as pd

from src import outcome_updates as ou

URL = "https://cfj.org/reports/x-v-y/"


def log(rows):
    return pd.DataFrame([{**dict.fromkeys(ou.COLUMNS, ""), **r} for r in rows])


GOOD_ROW = {"report_url": URL, "case": "X v. Y", "event_date": "2024-05-21", "previous_outcome": "convicted",
            "new_outcome": "conviction overturned", "summary": "The appeal court overturned the conviction.",
            "source_url": "https://example.org/ruling", "verified_by": "Yuki", "entered_on": "2026-10-10"}


def test_valid_row_has_no_problems():
    assert ou.problems(log([GOOD_ROW]), {URL}) == []


def test_bad_rows_are_rejected():
    bad = log([{**GOOD_ROW, "new_outcome": "won", "event_date": "May 2024", "source_url": "",
                "verified_by": "", "report_url": "https://cfj.org/reports/unknown/"}])
    found = " ".join(ou.problems(bad, {URL}))
    for word in ["not an allowed label", "event_date", "source_url", "verified_by", "not one of the 47"]:
        assert word in found


def test_history_uses_only_verified_rows_in_date_order():
    rows = log([{**GOOD_ROW, "event_date": "2024-09", "new_outcome": "acquittal upheld", "previous_outcome": "conviction overturned"},
                GOOD_ROW,
                {**GOOD_ROW, "event_date": "2025", "new_outcome": "pending", "verified_by": ""}])
    hist = ou.history(rows, URL)
    assert [h["new_outcome"] for h in hist] == ["conviction overturned", "acquittal upheld"]
    assert ou.improved(hist[0]) and not ou.improved(hist[1])
    assert ou.describe(hist[0]) == "convicted → conviction overturned (2024-05-21)"


def test_update_row_is_one_quoted_csv_line():
    line = ou.update_row(URL, "X v. Y", "2024-05-21", "convicted", "conviction overturned",
                         "Overturned, and released the same day.", "https://e.org", "Yuki", "2026-10-10")
    assert next(csv.reader(io.StringIO(line)))[5] == "Overturned, and released the same day."


def test_committed_log_is_valid():
    """Fails the PR if someone adds an update with a wrong label, no source, no verifier or an unknown case."""
    known = set(pd.read_csv("data/trialwatch_outcomes.csv", dtype=str)["report_url"])
    assert ou.problems(ou.load(), known) == []
