# Precedent & Practice
*A human rights advocacy tracker built on TrialWatch's fairness reports*

**Live app: [https://fairtrial-ai-hackathongit-cyvqxeqekcqd4hjsqr7b5w.streamlit.app/](https://fairtrial-ai-hackathongit-cyvqxeqekcqd4hjsqr7b5w.streamlit.app/)**

[![Tests](https://github.com/valentinasilva8/fairtrial-ai-hackathon/actions/workflows/tests.yml/badge.svg)](https://github.com/valentinasilva8/fairtrial-ai-hackathon/actions/workflows/tests.yml)

> *TrialWatch has analysed dozens of trials of journalists and critics. We turn those reports into arguments, precedents and sourced UN submissions for the next person prosecuted for speech.*

Built for the TrialWatch Fair Trial & AI Hackathon (Columbia Law School Human Rights Institute), Track 3: Advocacy & Impact, by **Shreya, Valentina, Ungu, Layla and Yuki**.

An independent hackathon project. It is not endorsed by, or an official product of, the Clooney Foundation for Justice, TrialWatch® or Columbia Law School. **All outputs are drafts for lawyer review, not legal conclusions.**

## What it does
For a lawyer facing a new speech prosecution anywhere, Precedent & Practice:

1. **finds the most similar trials TrialWatch has graded** (47 graded freedom-of-expression fairness reports, 2,075 PDF pages, covering trials in 23 countries) and **what followed** in each, with good outcomes first;
2. **shows the arguments their reports made**, grouped under the five labels the TrialWatch mentor asked for (**legality, vagueness, broadness, necessity, proportionality**), each with its author, the exact report page and the UN Human Rights Committee decisions cited, counting a paragraph reused across reports once;
3. **drafts a submission to the UN Special Rapporteur** in which every sentence cites its source and a lawyer approves before use.

Where a country has just reformed its speech law, a **reform stress test** adds whether the reform should already bar the case. Our worked example is Indonesia's ITE Law (revised 2024, narrowed by Constitutional Court Decision 105/PUU-XXII/2024): 5 of 13 past cases would likely be barred, 3 to 8 across contested legal readings.

See [docs/SUBMISSION.md](docs/SUBMISSION.md) for the full description.

## What's in the app
| Page | What it does |
|---|---|
| **Home** | Headline numbers, how it works, cases by outcome, and the **Promise Clock**: days since each official pledge and the evidence that it was kept |
| **Argument Bank** | Pick a current case or describe a new one. **By argument:** the arguments from the most similar TrialWatch trials, grouped by legality, vagueness, broadness, necessity and proportionality (then legitimate aim, pretrial detention, fair trial), each with case, report author, page link and outcome; identical paragraphs reused across reports shown once. **By case:** each similar trial with why it matched, its confirmed outcome, the impact on the defendant and the UN decisions cited |
| **Stress Test** | Runs each Indonesian case through rules R1–R4 from the reformed law and the 2025 ruling: *likely barred / at risk / still prosecutable*, with the rule and reason, and a ten-scenario sensitivity analysis. Paste a news story to have Gemini suggest the rule inputs, each with a verbatim quote |
| **UN Letter** | A draft submission to the UN Special Rapporteur on freedom of expression, for a seeded Indonesian case or **a new case in any country** you describe, built from the case, the Argument Bank, and (for Indonesia) the stress test and the pledges. Drafts with an uncited sentence, an unknown source or an invented quotation are rejected; a second check flags sentences the sources don't fully support; a named reviewer approves before saving |

## Related work
[Advocacy Trace](https://github.com/valentinasilva8/human-rights-advocacy-tracker) is an earlier prototype by the same
team (Valentina): a review-first explorer where a person approves each argument record before it is shown. Its review of
this repository shaped several choices here: the five argument labels, naming each report's author instead of "TrialWatch
argued", counting a paragraph reused across reports once, dated outcomes with "followed, not caused", the independence
disclaimer, and keeping full CFJ reports out of git. Its approval workflow uses SQLite; this app does not need a database.

## Team
| | Role |
|---|---|
| **Shreya** | Reform stress test, sensitivity analysis, Argument Bank, UN letter |
| **Valentina** | Repository, case tracker, case verification, Advocacy Trace review rules |
| **Ungu** | Indonesian case research and verification, impact categories |
| **Layla** | Data lead: Meila and Asrul cases, sensitive-case review, pitch |
| **Yuki** | Confirmed all 47 TrialWatch outcomes with sources |

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

### Load the TrialWatch reports (optional, ~1 hour)
The app works without this step: it shows the published excerpts in `data/trialwatch_argument_excerpts.jsonl`.
Run the scripts to rebuild the datasets from cfj.org or to work on the pipeline. The full report PDFs and
text are CFJ's copyrighted work and stay on your machine (`data/raw/`, git-ignored). The scripts wait 10
seconds between requests, as cfj.org's robots.txt asks.

```bash
python scripts/fetch_trialwatch_reports.py   # 94 report PDFs
python scripts/fetch_trialwatch_news.py      # 226 CFJ news posts, for later case outcomes
python scripts/build_report_index.py         # grades, argument paragraphs, UN decisions cited
python scripts/build_outcomes.py             # outcome evidence for people to confirm
python scripts/build_case_features.py        # features used to match similar cases
python scripts/export_argument_excerpts.py   # the excerpts the app displays
```

## Run
```bash
streamlit run app.py
```
Opens at http://localhost:8501.

## Screenshots
<!-- Add before submission: docs/screenshots/*.png -->
| Home | Stress Test | Argument Bank | UN Letter |
|---|---|---|---|
| *screenshot to add* | *screenshot to add* | *screenshot to add* | *screenshot to add* |

## Pitch deck
`pitch/Precedent_and_Practice.pptx` is generated from the hackathon template with numbers read live from the data.
After any data or feature change, rebuild it so the slides stay true:
```bash
pip install python-pptx
python scripts/build_slides.py
```

## Deploy (Streamlit Community Cloud)
1. Push to `main` on GitHub (the app is `app.py`; dependencies are in `requirements.txt`).
2. Go to https://share.streamlit.io, sign in with GitHub, and click **Create app** → **Deploy a public app from GitHub**.
3. Repository `valentinasilva8/fairtrial-ai-hackathon`, branch `main`, main file path `app.py`.
4. Under **Advanced settings**, choose Python 3.11 or later and paste this into **Secrets**:
   ```toml
   GEMINI_API_KEY = "your-key-here"
   ```
5. Click **Deploy**. The app reads the key from Streamlit secrets, falling back to `.env` locally.

The deployed app is public: sensitive cases stay hidden, and the AI features use the team's free-tier
Gemini quota, so the UN Letter page also offers a plain draft that needs no AI.

## Test
```bash
pytest
```
Tests run on every pull request and push to `main` (GitHub Actions). They use made-up text and a fake Gemini client, so they need no key and no CFJ files.

## Project structure
```
app.py                       # entry point: page navigation (Monitoring / Evaluation / Advocacy)
pages/0_Home.py              # overview, cases by outcome, Promise Clock
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
- **TrialWatch reports** (`data/trialwatch_reports.csv`, [docs/TRIALWATCH_REPORTS.md](docs/TRIALWATCH_REPORTS.md)): all 96 report listings on cfj.org (90 distinct reports, 94 PDFs). 63 reports grade a trial A–F, each stored with the text it was read from; 47 graded reports analyse freedom of expression and form the Argument Bank. They cite 154 distinct UN Human Rights Committee decisions.
- **Outcomes** (`data/trialwatch_outcomes.csv`): suggested from the reports and 226 CFJ news posts, with every sentence and link in `trialwatch_outcome_evidence.csv`. Suggestions are often wrong; an outcome counts only once a person fills `verified_by` ([docs/VERIFY_OUTCOMES.md](docs/VERIFY_OUTCOMES.md)).

## Responsible AI
- **Every claim has a source.** Rows without one show as unverified; every letter sentence cites numbered sources, and quotations are checked word for word against them.
- **No AI where rules will do.** The stress test, report parsing, grade extraction, outcome evidence and case matching are deterministic code. Gemini only suggests rule inputs from text (each with a verified quote) and drafts letters (checked twice, then approved by a person).
- **Transparent matching.** Similar cases are matched on named features, and each match lists the features it shares.
- **No outcome prediction.** We show what *followed* in similar past cases, never that an argument *caused* an outcome, and never a prediction for a live trial.
- **Sensitive cases** are hidden from public views and can't be sent to Gemini. On Gemini's free tier, Google may use prompts to improve its products.
- **Copyright.** The repository publishes only the 201 report paragraphs the app displays, each linked to its source page, under CFJ's copyright notice ([data/NOTICE.md](data/NOTICE.md)); full reports stay on cfj.org.

## Limitations
- Argument tags come from keyword matching and over-tag; outcomes are unconfirmed until checked by a person.
- The arguments are TrialWatch experts' analysis in their fairness reports, not necessarily what was argued in court.
- Only 2 Indonesian cases so far date from after the 2025 ruling, so "is the reform stopping new cases?" is a monitoring framework, not yet a finding.
- The new Criminal Code may let prosecutions move off the ITE Law (e.g. Laras Faizati, convicted under the Penal Code), so a falling ITE case count is not proof of success.

## License
Code: [MIT](LICENSE). TrialWatch report excerpts and derived data: © Clooney Foundation for Justice, all
rights reserved, not covered by the MIT license; see [data/NOTICE.md](data/NOTICE.md).
