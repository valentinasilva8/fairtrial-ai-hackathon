"""Describe each core TrialWatch case by matchable features (see src/similarity.py).

Writes data/trialwatch_case_features.csv: country, region, charge types, kind of
speech and defendant role, with the keyword counts behind each, so a person can
check why a case was tagged the way it was.

Run: python scripts/build_case_features.py
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.reports import pdf_pages  # noqa: E402
from src.similarity import features_from_report  # noqa: E402

RAW = ROOT / "data" / "raw" / "trialwatch"


def main():
    pdf_for = {r["url"]: r["pdf_file"] for r in csv.DictReader(open(RAW / "pages.csv"))}
    reports = [r for r in csv.DictReader(open(ROOT / "data" / "trialwatch_reports.csv"))
               if r["grade"] and r["freedom_of_expression"] == "True"]
    rows = []
    for r in reports:
        f = features_from_report(r["title"], "\n".join(pdf_pages(RAW / pdf_for[r["url"]])))
        rows.append({
            "report_url": r["url"], "case": r["title"], "grade": r["grade"],
            "country": f["country"], "region": f["region"],
            "charges": "; ".join(f["charges"]), "speech": "; ".join(f["speech"]), "roles": "; ".join(f["roles"]),
            "keyword_counts": json.dumps(f["counts"]),
        })
    out = ROOT / "data" / "trialwatch_case_features.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} cases -> {out}")


if __name__ == "__main__":
    main()
