"""Build data/trialwatch_reports.csv from the PDFs downloaded by fetch_trialwatch_reports.py.

Writes:
- data/trialwatch_reports.csv: one row per report (grade with its source text,
  argument-category counts, UN Human Rights Committee decisions cited). Committed.
- data/raw/trialwatch/arguments.jsonl: tagged argument paragraphs with page
  numbers and verbatim text. Git-ignored (contains CFJ report text).

Run: python scripts/build_report_index.py
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.reports import extract_arguments, hrc_decisions, pdf_pages, summarize_report  # noqa: E402

RAW = ROOT / "data" / "raw" / "trialwatch"


def main():
    pages_csv = RAW / "pages.csv"
    if not pages_csv.exists():
        sys.exit("Run scripts/fetch_trialwatch_reports.py first.")
    rows, n_args = [], 0
    with open(RAW / "arguments.jsonl", "w") as args_out:
        for page in csv.DictReader(open(pages_csv)):
            if page["status"] != "ok":
                continue
            pages = pdf_pages(RAW / page["pdf_file"])
            row = summarize_report(page["url"], page["title"], pages)
            row["pdf_url"] = page["pdf_url"]
            row["verified_by"] = ""  # filled in by the person who checks this row
            rows.append(row)
            for arg in extract_arguments(pages):
                args_out.write(json.dumps({"url": page["url"], **arg}, ensure_ascii=False) + "\n")
                n_args += 1
            decisions = hrc_decisions("\n".join(pages))
            args_out.write(json.dumps({"url": page["url"], "hrc_decisions": decisions}) + "\n")

    out = ROOT / "data" / "trialwatch_reports.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    graded = [r for r in rows if r["grade"]]
    core = [r for r in graded if r["freedom_of_expression"]]
    print(f"{len(rows)} reports indexed, {len(graded)} graded, {len(core)} graded with Article 19 analysis")
    print(f"{n_args} tagged argument paragraphs -> {RAW / 'arguments.jsonl'}")


if __name__ == "__main__":
    main()
