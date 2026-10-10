"""Export only the argument paragraphs the app shows, for publishing with the app.

Reads the full local extraction (data/raw/trialwatch/arguments.jsonl, git-ignored) and
writes data/trialwatch_argument_excerpts.jsonl: for each of the 47 core cases, the strongest
paragraph per argument category (what the Argument Bank page and UN letter use), plus the
UN Human Rights Committee decisions each report cites. Every excerpt keeps its report URL
and page. The excerpts are © Clooney Foundation for Justice; see data/NOTICE.md.

Run after build_report_index.py: python scripts/export_argument_excerpts.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import argument_bank as ab  # noqa: E402


def main():
    if not ab.ARGUMENTS.exists():
        sys.exit("Run scripts/fetch_trialwatch_reports.py and scripts/build_report_index.py first.")
    n = 0
    with open(ab.EXCERPTS, "w") as out:
        for url in ab.past_cases()["report_url"]:
            seen = set()
            for cat, paras in ab.best_arguments(url).items():
                for p in paras:
                    key = (p["page"], p["text"])
                    if key in seen:
                        continue
                    seen.add(key)
                    out.write(json.dumps({"url": url, **p}, ensure_ascii=False) + "\n")
                    n += 1
            out.write(json.dumps({"url": url, "hrc_decisions": ab.hrc_decisions(url)}) + "\n")
    print(f"{n} excerpts -> {ab.EXCERPTS}")


if __name__ == "__main__":
    main()
