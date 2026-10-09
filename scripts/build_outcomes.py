"""Build the outcome sheets for the core TrialWatch cases, for people to confirm.

Needs the downloads from fetch_trialwatch_reports.py and fetch_trialwatch_news.py.

Writes:
- data/trialwatch_outcome_evidence.csv: every sentence that states an outcome for a
  core case's defendant, from the report or a CFJ news post, with its link.
- data/trialwatch_outcomes.csv: one row per core case with a *suggested* label.
  People fill outcome_label, outcome_summary, outcome_source_url and verified_by.
  Re-running keeps anything people have already filled in.

Run: python scripts/build_outcomes.py
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.outcomes import (  # noqa: E402
    defendants,
    full_name_keys,
    mentions,
    name_tokens,
    outcome_evidence,
    suggest_label,
)
from src.reports import pdf_pages  # noqa: E402

RAW = ROOT / "data" / "raw" / "trialwatch"
EVIDENCE = ROOT / "data" / "trialwatch_outcome_evidence.csv"
OUTCOMES = ROOT / "data" / "trialwatch_outcomes.csv"
PER_SOURCE = 4  # keep the sheet reviewable
HUMAN_FIELDS = ["outcome_label", "outcome_summary", "outcome_source_url", "verified_by", "notes"]


def core_reports():
    rows = csv.DictReader(open(ROOT / "data" / "trialwatch_reports.csv"))
    return [r for r in rows if r["grade"] and r["freedom_of_expression"] == "True"]


def main():
    pdf_for = {r["url"]: r["pdf_file"] for r in csv.DictReader(open(RAW / "pages.csv"))}
    news = [json.loads(p.read_text()) for p in sorted((RAW / "news").glob("*.json"))]
    previous = {r["report_url"]: r for r in csv.DictReader(open(OUTCOMES))} if OUTCOMES.exists() else {}

    evidence_rows, outcome_rows = [], []
    for rep in core_reports():
        names = defendants(rep["title"])
        tokens = name_tokens(names)
        found = []  # in date order: report first (it predates later news), then posts by date

        if names:
            text = "\n".join(pdf_pages(RAW / pdf_for[rep["url"]]))
            for e in outcome_evidence(text, tokens)[:PER_SOURCE]:
                found.append({**e, "source_type": "report", "source_url": rep["url"], "source_title": rep["title"], "date": ""})

            posts = [p for p in news if mentions(p["title"] + " " + p["text"], full_name_keys(names))]
            for p in sorted(posts, key=lambda p: p["date"]):
                for e in outcome_evidence(p["text"], tokens)[:PER_SOURCE]:
                    found.append({**e, "source_type": "news", "source_url": p["url"], "source_title": p["title"], "date": p["date"]})
        else:
            posts = []

        for e in found:
            evidence_rows.append({
                "report_url": rep["url"], "case": rep["title"], "source_type": e["source_type"],
                "date": e["date"], "source_title": e["source_title"], "source_url": e["source_url"],
                "good_signals": "; ".join(e["good"]), "not_good_signals": "; ".join(e["not_good"]),
                "sentence": e["sentence"],
            })

        prev = previous.get(rep["url"], {})
        outcome_rows.append({
            "report_url": rep["url"], "case": rep["title"], "grade": rep["grade"],
            "defendants": "; ".join(names), "news_posts_matched": len(posts),
            "evidence_sentences": len(found),
            "suggested_label": suggest_label(found),
            "suggested_from": found[-1]["source_url"] if found else "",
            **{f: prev.get(f, "") for f in HUMAN_FIELDS},
        })

    for path, rows in [(EVIDENCE, evidence_rows), (OUTCOMES, outcome_rows)]:
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

    labels = {}
    for r in outcome_rows:
        labels[r["suggested_label"]] = labels.get(r["suggested_label"], 0) + 1
    print(f"{len(outcome_rows)} cases, {len(evidence_rows)} evidence sentences; suggested labels: {labels}")
    print(f"cases with at least one matching news post: {sum(1 for r in outcome_rows if r['news_posts_matched'])}")


if __name__ == "__main__":
    main()
