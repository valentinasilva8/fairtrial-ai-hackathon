from datetime import date

from src.promise_clock import days_since, evidence_text, parse_pledge_date, status_label

TODAY = date(2026, 10, 9)


def test_full_date():
    assert days_since("2025-04-17", TODAY) == (540, "540 days since 17 April 2025")


def test_month_only_date_is_approximate():
    days, label = days_since("2025-04", TODAY)
    assert days == (TODAY - date(2025, 4, 1)).days
    assert label.startswith("about ") and "April 2025" in label


def test_unverified_date():
    assert days_since("TO VERIFY", TODAY) == (None, "date to verify")
    assert parse_pledge_date("") == (None, "")


def test_placeholder_evidence_hidden():
    assert evidence_text("TO FILL: any guidance issued?") == "No evidence collected yet."
    assert evidence_text("TO FILL") == "No evidence collected yet."
    assert evidence_text("Police circular 3/2025 issued") == "Police circular 3/2025 issued"


def test_status_labels():
    assert status_label("no_evidence_yet") == "No evidence yet"
    assert status_label("kept") == "Kept"
    assert status_label("partly_kept") == "Partly kept"
    assert status_label("weird") == "Unknown"
