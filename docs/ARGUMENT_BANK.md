# TrialWatch Argument Bank — data pipeline

Builds a dataset of TrialWatch fairness reports from cfj.org: each report's grade, the argument
categories it uses, the UN Human Rights Committee decisions it cites, and tagged argument
paragraphs with page numbers. Extraction is deterministic (pdftotext + regex); no LLM.

## Run
Requires poppler (`brew install poppler` on macOS) for `pdftotext`.

```bash
python scripts/fetch_trialwatch_reports.py   # ~30 min: waits 10 s per request (cfj.org robots.txt Crawl-delay)
python scripts/fetch_trialwatch_news.py      # ~40+ min: 226 CFJ news posts, for outcomes after a report
python scripts/build_report_index.py         # a few seconds
python scripts/build_outcomes.py             # outcome evidence + suggested labels
python scripts/build_case_features.py        # features for similar-case matching
```

## Outputs
| file | committed? | contents |
|---|---|---|
| `data/trialwatch_reports.csv` | yes | one row per report: title, URL, grade **with the text it was read from**, argument-category counts, number of UN HRC decisions cited, `verified_by` |
| `data/raw/trialwatch/*.pdf` | no | CFJ's reports (copyright CFJ; not republished) |
| `data/raw/trialwatch/arguments.jsonl` | no | tagged paragraphs: report URL, page, categories, verbatim text; plus the HRC decision symbols each report cites |
| `data/raw/trialwatch/news/*.json` | no | CFJ news posts (title, date, text) |
| `data/trialwatch_outcome_evidence.csv` | yes | every sentence that states an outcome for a core case's defendant, from the report or a news post, with link and date |
| `data/trialwatch_outcomes.csv` | yes | one row per core case: suggested label, plus `outcome_label`, `outcome_source_url`, `verified_by` filled by people ([VERIFY_OUTCOMES.md](VERIFY_OUTCOMES.md)) |
| `data/trialwatch_case_features.csv` | yes | country, region, charge types, kind of speech, defendant role, with the keyword counts behind each |

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

## Similar cases (src/similarity.py, src/argument_bank.py)
A current case and each past case are described by named features: charge type (defamation or insult,
incitement or public order, false information, extremism or terrorism, sedition or national security,
religion or blasphemy), kind of speech, defendant role, and country/region. A past case's features are
keyword counts from its report (a feature needs at least 3 mentions and a quarter of the top count).
The match score is a weighted overlap (shared charge 3, same country 2, same region 1, shared speech or
role 1 each); a match needs at least one shared charge. Each match lists the features it shares.
Among the top matches, cases with a good outcome are listed first. For each, the page shows the strongest
paragraph per argument category (template text such as the grading annex is excluded).

## UN letter (src/letter.py)
The letter may only use a numbered list of sources built in code: the case record and timeline, the
stress-test result, the official pledges and the Argument Bank paragraphs (with page links). Every
sentence must cite source ids; code rejects uncited sentences, unknown ids and quotations whose words
aren't in the cited source (ignoring punctuation), and sends the problems back to Gemini up to twice. A
second Gemini pass rates each sentence as supported, partly supported or not supported, and its quoted
evidence is itself checked against the source. A named reviewer approves before the letter is saved
to `outputs/briefs/` (git-ignored). A plain draft can be built without AI.
