"""Build the impact sheet for the core TrialWatch cases, for people to confirm.

Needs the downloads from fetch_trialwatch_reports.py (and poppler's pdftotext).

Writes:
- data/trialwatch_impacts.csv: one row per core case. For each impact category a yes/no
  column and, for each yes, the evidence sentence, its PDF page, any duration or amount
  exactly as written, and a link to that page. People fill verified_by and notes.
  Re-running keeps anything people have already filled in.
- data/trialwatch_impact_evidence.csv: every evidence sentence found, one per row.

Nothing is an impact until a person fills verified_by. Say "followed", never "caused".

Run: python scripts/build_impacts.py
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.impacts import CATEGORIES, HUMAN_FIELDS, case_row, evidence_rows, impact_evidence  # noqa: E402
from src.outcomes import defendants  # noqa: E402
from src.reports import pdf_pages  # noqa: E402

RAW = ROOT / "data" / "raw" / "trialwatch"
IMPACTS = ROOT / "data" / "trialwatch_impacts.csv"
EVIDENCE = ROOT / "data" / "trialwatch_impact_evidence.csv"


def core_reports():
    rows = csv.DictReader(open(ROOT / "data" / "trialwatch_reports.csv", encoding="utf-8"))
    return [r for r in rows if r["grade"] and r["freedom_of_expression"] == "True"]


def write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main(pages_fn=pdf_pages, raw=RAW, impacts=IMPACTS, evidence=EVIDENCE):
    pages_csv = raw / "pages.csv"
    if not pages_csv.exists():
        sys.exit("No downloads found. Run: python scripts/fetch_trialwatch_reports.py")
    pdf_for = {r["url"]: r["pdf_file"] for r in csv.DictReader(open(pages_csv, encoding="utf-8"))}
    previous = {r["report_url"]: r for r in csv.DictReader(open(impacts, encoding="utf-8"))} if impacts.exists() else {}

    case_rows, evidence_out, skipped = [], [], []
    for rep in core_reports():
        pdf = raw / pdf_for[rep["url"]] if rep["url"] in pdf_for else None
        if not pdf or not pdf.exists():
            skipped.append(rep["title"])
            if rep["url"] in previous:  # a partial run must not wipe what people already filled in
                case_rows.append(previous[rep["url"]])
            continue
        names = defendants(rep["title"])
        found = impact_evidence(pages_fn(pdf), names) if names else {c: [] for c in CATEGORIES}
        case_rows.append(case_row(rep, names, found, previous.get(rep["url"])))
        evidence_out.extend(evidence_rows(rep, found))

    if not case_rows:
        sys.exit("No core report PDFs found in " + str(raw))
    write(impacts, case_rows)
    if evidence_out:
        write(evidence, evidence_out)

    print(f"{len(case_rows)} cases, {len(evidence_out)} evidence sentences")
    for cat in CATEGORIES:
        print(f"  {cat}: {sum(1 for r in case_rows if r.get(cat) == 'yes')} cases")
    if skipped:
        print(f"{len(skipped)} core reports have no downloaded PDF and were skipped (rows kept if already present)")
    kept = sum(1 for r in case_rows if any(r.get(f) for f in HUMAN_FIELDS))
    print(f"rows with something filled in by a person: {kept}")


if __name__ == "__main__":
    main()
