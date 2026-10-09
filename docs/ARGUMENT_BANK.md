# TrialWatch Argument Bank — data pipeline

Builds a dataset of TrialWatch fairness reports from cfj.org: each report's grade, the argument
categories it uses, the UN Human Rights Committee decisions it cites, and tagged argument
paragraphs with page numbers. Extraction is deterministic (pdftotext + regex); no LLM.

## Run
Requires poppler (`brew install poppler` on macOS) for `pdftotext`.

```bash
python scripts/fetch_trialwatch_reports.py   # ~30 min: waits 10 s per request (cfj.org robots.txt Crawl-delay)
python scripts/build_report_index.py         # a few seconds
```

## Outputs
| file | committed? | contents |
|---|---|---|
| `data/trialwatch_reports.csv` | yes | one row per report: title, URL, grade **with the text it was read from**, argument-category counts, number of UN HRC decisions cited, `verified_by` |
| `data/raw/trialwatch/*.pdf` | no | CFJ's reports (copyright CFJ; not republished) |
| `data/raw/trialwatch/arguments.jsonl` | no | tagged paragraphs: report URL, page, categories, verbatim text; plus the HRC decision symbols each report cites |

## Coverage (run of 9 Oct 2026)
- 96 report pages in the cfj.org sitemap; 94 have a PDF; all 94 have extractable text.
- 63 reports carry an A–F trial grade (D 43, F 11, C 9); every grade is stored with its source text, and no report mentions two different grades.
- 47 graded reports analyse freedom of expression (ICCPR Article 19). This is the core set.
- The 47 cite 154 distinct UN Human Rights Committee decisions (median 9 per report).

## Argument categories
The first four follow the UN Human Rights Committee's three-part test for restrictions on expression
(General Comment No. 34), which TrialWatch reports apply: `legality_vagueness`, `legitimate_aim`,
`necessity_proportionality`, `overbreadth`. Plus `pretrial_detention` and `fair_trial`.

## Limits
- Tags come from keyword matching and over-tag (a paragraph mentioning "law" in passing may be tagged).
  Each argument shown in the app must be confirmed by a person, who fills `verified_by`.
- Arguments are TrialWatch experts' analysis of the trial, not necessarily what the defence argued in court.
- The grade is TrialWatch's assessment of fairness, not the court's verdict. Outcomes after a report
  (appeal, release) are not in the PDF.
- The year in a PDF's upload path is when it was uploaded to cfj.org (many in a 2023 migration), not the publication date.
