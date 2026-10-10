# Paper vs. Practice

[![Tests](https://github.com/valentinasilva8/fairtrial-ai-hackathon/actions/workflows/tests.yml/badge.svg)](https://github.com/valentinasilva8/fairtrial-ai-hackathon/actions/workflows/tests.yml)

> *Indonesia reformed its speech law. We stress-tested the reform: how many past prosecutions would it have stopped — and is it stopping new ones?*

Built for the TrialWatch Fair Trial & AI Hackathon (Columbia Law School Human Rights Institute), Track 3: Advocacy & Impact.

Indonesia's ITE (EIT) Law has been used to prosecute journalists, activists and critics. It was revised in 2024 (Law No. 1/2024) and narrowed by Constitutional Court Decision No. 105/PUU-XXII/2024. Paper vs. Practice:

1. **stress-tests the reform** against real Indonesian cases,
2. **finds similar past TrialWatch cases** and the arguments TrialWatch's experts made in them (the **Argument Bank**, built from every report on cfj.org), and
3. **drafts a UN Special Rapporteur letter** in which every sentence cites its source.

See [docs/PROPOSAL.md](docs/PROPOSAL.md) for the full pitch.

**All outputs are drafts for lawyer review, not legal conclusions.**

## What's in the app
| Page | What it does |
|---|---|
| **Home** (`app.py`) | Cases by outcome, and the **Promise Clock**: days since each official pledge and the evidence that it was kept |
| **Stress Test** | Runs each case through rules R1–R4 from the reformed law and the 2025 ruling: *likely barred / at risk / still prosecutable*, with the rule and reason. Headline: "4 of 14 past cases would likely be barred". Paste a news story to have Gemini suggest the rule inputs, each with a verbatim quote |
| **Argument Bank** | For a current case, the most similar past TrialWatch cases (good outcomes first), why they match, what happened, and the strongest argument TrialWatch made on legality, legitimate aim, necessity and proportionality, overbreadth, pretrial detention and fair trial, with page links and the UN Human Rights Committee decisions cited |
| **UN Letter** | A draft submission to the UN Special Rapporteur on freedom of expression, built from the case, the stress test, the pledges and the Argument Bank. Drafts with an uncited sentence, an unknown source or an invented quotation are rejected; a second check flags sentences the sources don't fully support; a named reviewer approves before saving |

## Setup
Requires Python 3.11+ and, for the Argument Bank pipeline, poppler (`brew install poppler` on macOS).

```bash
git clone https://github.com/valentinasilva8/fairtrial-ai-hackathon.git
cd fairtrial-ai-hackathon
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add GEMINI_API_KEY (free at aistudio.google.com) for the AI features
```

Without a key, everything except the Gemini drafting and extraction works, including a plain (no-AI) letter draft.

### Load the TrialWatch reports (once, ~1 hour)
The report PDFs and their text are CFJ's copyrighted work, so they are not in this repository. Download them yourself; the scripts wait 10 seconds between requests, as cfj.org's robots.txt asks.

```bash
python scripts/fetch_trialwatch_reports.py   # 94 report PDFs
python scripts/fetch_trialwatch_news.py      # 226 CFJ news posts, for later case outcomes
python scripts/build_report_index.py         # grades, argument paragraphs, UN decisions cited
python scripts/build_outcomes.py             # outcome evidence for people to confirm
python scripts/build_case_features.py        # features used to match similar cases
```

The derived tables (`data/trialwatch_*.csv`) are committed, so matching and outcomes work without this step; the argument text needs it.

## Run
```bash
streamlit run app.py
```
Opens at http://localhost:8501.

## Test
```bash
pytest
```
Tests run on every pull request and push to `main` (GitHub Actions). They use made-up text and a fake Gemini client, so they need no key and no CFJ files.

## Project structure
```
app.py                       # home: cases by outcome + Promise Clock
pages/2_Stress_Test.py       # reform stress test + "add a case from text"
pages/3_Argument_Bank.py     # similar TrialWatch cases, outcomes, arguments
pages/4_UN_Letter.py         # sourced UN Special Rapporteur letter
src/stress_test.py           # rule engine R1–R4 (deterministic, no AI)
src/reports.py               # parse TrialWatch PDFs: grades, argument tags, UN decisions
src/outcomes.py              # outcome evidence from reports and CFJ news posts
src/similarity.py            # transparent case matching (charge, speech, role, region)
src/argument_bank.py         # similar cases + strongest arguments per category
src/letter.py                # letter sources, citation validation, support check
src/llm.py                   # Gemini calls (structured JSON, model fallback)
src/promise_clock.py         # days since each pledge
src/data.py                  # load + validate the case CSVs
scripts/                     # download and build the TrialWatch datasets
data/                        # case, event, promise, verification and TrialWatch tables
docs/                        # proposal, rules, team plan, data and verification guides
tests/                       # pytest
```

## Data
- **Indonesian cases** (`data/cases_seed.csv`, `events.csv`): from the CFJ report *Protecting Online Speech in Indonesia* and news, each row with a source. `data/verification_log.csv` records who checked each case.
- **TrialWatch reports** (`data/trialwatch_reports.csv`, [docs/TRIALWATCH_REPORTS.md](docs/TRIALWATCH_REPORTS.md)): all 96 report pages on cfj.org (90 distinct reports, 94 PDFs). 63 trials carry an A–F grade, each stored with the text it was read from; 47 graded trials analyse freedom of expression and form the Argument Bank. They cite 154 distinct UN Human Rights Committee decisions.
- **Outcomes** (`data/trialwatch_outcomes.csv`): suggested from the reports and 226 CFJ news posts, with every sentence and link in `trialwatch_outcome_evidence.csv`. Suggestions are often wrong; an outcome counts only once a person fills `verified_by` ([docs/VERIFY_OUTCOMES.md](docs/VERIFY_OUTCOMES.md)).

## Responsible AI
- **Every claim has a source.** Rows without one show as unverified; every letter sentence cites numbered sources, and quotations are checked word for word against them.
- **No AI where rules will do.** The stress test, report parsing, grade extraction, outcome evidence and case matching are deterministic code. Gemini only suggests rule inputs from text (each with a verified quote) and drafts letters (checked twice, then approved by a person).
- **Transparent matching.** Similar cases are matched on named features, and each match lists the features it shares.
- **No outcome prediction.** We show what *followed* in similar past cases, never that an argument *caused* an outcome, and never a prediction for a live trial.
- **Sensitive cases** are hidden from public views and can't be sent to Gemini. On Gemini's free tier, Google may use prompts to improve its products.
- **Copyright.** CFJ's report text stays on the user's machine; the repository holds only metadata, grades, short outcome sentences and links.

## Limitations
- Argument tags come from keyword matching and over-tag; outcomes are unconfirmed until checked by a person.
- The arguments are TrialWatch experts' analysis in their fairness reports, not necessarily what was argued in court.
- Only 2 Indonesian cases so far date from after the 2025 ruling, so "is the reform stopping new cases?" is a monitoring framework, not yet a finding.
- The new Criminal Code may let prosecutions move off the ITE Law (e.g. Laras Faizati, convicted under the Penal Code), so a falling ITE case count is not proof of success.

## License
[MIT](LICENSE)
