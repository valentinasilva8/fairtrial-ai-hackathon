"""Later changes to a TrialWatch case's outcome (e.g. a conviction overturned on appeal).

data/trialwatch_outcome_updates.csv is an append-only log: one row per verified, dated change.
Rows are never edited away, so each case keeps its history. A case's current outcome is its
latest verified update; with none, the confirmed outcome in data/trialwatch_outcomes.csv stands.
We say an outcome *followed* TrialWatch's work, never that the work caused it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

UPDATES = Path(__file__).resolve().parent.parent / "data" / "trialwatch_outcome_updates.csv"
COLUMNS = ["report_url", "case", "event_date", "previous_outcome", "new_outcome", "summary",
           "source_url", "verified_by", "entered_on", "notes"]

GOOD = {"acquitted", "acquittal upheld", "charges dropped", "conviction overturned",
        "released early / pardoned", "UN found detention arbitrary"}
LABELS = sorted(GOOD | {"convicted", "conviction upheld", "sentence reduced", "still detained",
                        "pending", "unknown"})
DATE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")  # 2023, 2023-06 or 2023-06-05


def load(path: Path | None = None) -> pd.DataFrame:
    path = path or UPDATES
    if not path.exists():
        return pd.DataFrame(columns=COLUMNS)
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def problems(updates: pd.DataFrame, known_urls: set[str]) -> list[str]:
    """Everything wrong with the log; an empty list means every row can be used."""
    out = []
    missing = [c for c in COLUMNS if c not in updates.columns]
    if missing:
        return [f"missing columns: {missing}"]
    for i, r in updates.iterrows():
        where = f"row {i + 2} ({r['case'] or r['report_url']})"
        if r["report_url"] not in known_urls:
            out.append(f"{where}: report_url is not one of the 47 Argument Bank reports")
        if r["new_outcome"] not in LABELS:
            out.append(f"{where}: new_outcome '{r['new_outcome']}' is not an allowed label")
        if r["previous_outcome"] and r["previous_outcome"] not in LABELS:
            out.append(f"{where}: previous_outcome '{r['previous_outcome']}' is not an allowed label")
        if not DATE.match(r["event_date"]):
            out.append(f"{where}: event_date must be YYYY, YYYY-MM or YYYY-MM-DD")
        if not r["source_url"].startswith("http"):
            out.append(f"{where}: a source_url is required")
        if not r["verified_by"].strip():
            out.append(f"{where}: verified_by is required (a person must check the source)")
        if not r["summary"].strip():
            out.append(f"{where}: summary is required")
    return out


def history(updates: pd.DataFrame, report_url: str) -> list[dict]:
    """Verified updates for one case, oldest first."""
    rows = updates[(updates["report_url"] == report_url) & (updates["verified_by"].str.strip() != "")]
    return rows.sort_values("event_date", kind="stable").to_dict("records")


def improved(row: dict) -> bool:
    """The update moved the case to a good outcome from one that was not."""
    return row["new_outcome"] in GOOD and row.get("previous_outcome", "") not in GOOD


def describe(row: dict) -> str:
    before = row.get("previous_outcome") or "earlier outcome"
    return f"{before} → {row['new_outcome']} ({row['event_date']})"


def update_row(report_url: str, case: str, event_date: str, previous: str, new: str, summary: str,
               source_url: str, verified_by: str, entered_on: str, notes: str = "") -> str:
    """One CSV line, quoted correctly, ready to append to the log."""
    import csv
    import io

    buf = io.StringIO()
    csv.writer(buf).writerow([report_url, case, event_date, previous, new, summary, source_url,
                              verified_by, entered_on, notes])
    return buf.getvalue().strip()
