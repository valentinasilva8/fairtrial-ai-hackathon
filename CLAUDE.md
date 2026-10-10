# Precedent & Practice (formerly Paper vs. Practice) — project context for Claude Code

## What this is
Hackathon project for the TrialWatch Fair Trial & AI Hackathon (Columbia Law School Human Rights Institute), Oct 9–10, 2026. Track 3: Advocacy & Impact.
Final deliverables due **Saturday Oct 10, 3:30 pm ET**: GitHub repo (code + README + open-source license), working demo, short written description of the tool and how TrialWatch would use it. 10–15 min demo to judges.

**One line:** Indonesia reformed its speech law (ITE / EIT Law). We stress-test the reform: how many past prosecutions would it have stopped, and is it stopping new ones?

TrialWatch monitors criminal prosecutions of journalists and other public-interest voices. The ITE Law has been used against journalists, activists and critics. It was revised in 2024 (Law No. 1/2024) and narrowed by the Constitutional Court in Decision No. 105/PUU-XXII/2024 (2025). Nobody can easily see whether this changed outcomes.

## Features (priority order)
1. **Case tracker** — each case on one source-linked timeline (post → complaint → detention → trial → advocacy → verdict → appeal).
2. **Reform Stress Test** (core feature, owned by Shreya) — run each case through the reform rules in `docs/stress_test_rules.md` and output: likely barred / at risk / still prosecutable, with the reason and rule cited. Headline: "X of Y past cases would now be barred."
3. **Promise Clock** — days since an official pledge (e.g. police pledge to follow the ruling) and evidence of implementation. Data in `data/promises_seed.csv`.
4. **Argument Bank** (added after judge feedback, owned by Shreya) — for a current case, the most similar past TrialWatch cases (good outcomes first), what happened in them, and the arguments TrialWatch's experts made (legality/vagueness, legitimate aim, necessity/proportionality, overbreadth, pretrial detention, fair trial) with page links and the UN Human Rights Committee decisions cited. Built from all TrialWatch reports on cfj.org; see `docs/ARGUMENT_BANK.md`.
5. **UN Special Rapporteur letter** — LLM drafts a submission from the case, stress test, pledges and Argument Bank. Every sentence cites numbered sources; code rejects uncited sentences, unknown sources and invented quotations; a second check flags unsupported sentences; a named reviewer approves before saving. (English press release and Bahasa post: not built yet.)

## Stack
- Python 3.11+, Streamlit (`app.py` + `pages/`), pandas
- LLM via Google Gemini API, free tier (key in `.env` as `GEMINI_API_KEY`, never committed; model `gemini-flash-latest` with fallbacks). Free tier: Google may use prompts, so never send sensitive cases.
- PDF text via poppler's `pdftotext`; CFJ report PDFs/text live in git-ignored `data/raw/`
- Data as CSV in `data/`. No database.
- Run: `streamlit run app.py`; deploy on Streamlit Community Cloud (steps in README)

## Structure
```
app.py                    # entry point: st.navigation grouped Monitoring / Evaluation / Advocacy (page config set here only)
pages/0_Home.py           # overview metrics, cases by outcome, Promise Clock
pages/1_Cases.py          # case list + timeline view (Valentina, PR #5)
pages/2_Stress_Test.py    # stress test results + "add a case from text"
pages/3_Argument_Bank.py  # similar TrialWatch cases, outcomes, arguments
pages/4_UN_Letter.py      # sourced UN Special Rapporteur letter with approve / mark-sensitive
src/stress_test.py        # rule engine (pure functions, unit tested, no LLM)
src/reports.py            # parse TrialWatch PDFs: grades, argument tags, UN decisions
src/outcomes.py           # outcome evidence from reports + CFJ news posts
src/similarity.py         # transparent case matching (no LLM)
src/argument_bank.py      # similar cases + strongest arguments
src/letter.py             # letter sources, citation validation, support check
src/llm.py                # Gemini helpers (extraction, JSON generation)
src/promise_clock.py      # days since each pledge
src/data.py               # load + validate CSVs
scripts/                  # download/build TrialWatch datasets (10 s between requests)
data/                     # cases_seed, events, promises_seed, verification_log, trialwatch_*.csv
data/raw/                 # git-ignored: CFJ PDFs, news posts, extracted argument text
docs/                     # proposal, rules, team plan, ARGUMENT_BANK, VERIFY_OUTCOMES, TRIALWATCH_REPORTS
references/               # source PDFs (CFJ EIT report) — not required to run
```

## Rules for all code and content (Responsible AI — 20% of judging)
- **Every factual claim must link to a source** (`source` column). Rows without one show as "unverified" in the UI.
- Stress-test output is **"for lawyer review"**, never a legal conclusion. Show which rule triggered and why.
- Say **"followed", never "caused"** when relating advocacy to outcomes.
- Every case has a `sensitive` flag; sensitive cases are hidden from public views and briefs.
- No personal data beyond what is already in the public record. No scraping that violates site terms.
- LLM outputs must quote the source text they rely on; if they can't, mark unverified. Quotations are checked in code.
- Keep the rule engine, report parsing and case matching deterministic; use the LLM only to fill rule inputs from text and to draft letters, and show its reasoning.
- Never predict the outcome of a live trial; show what followed in similar past cases.
- TrialWatch outcomes count only once a person fills `verified_by` in `data/trialwatch_outcomes.csv`.
- Later outcome changes go in `data/trialwatch_outcome_updates.csv` (append-only, one verified dated row per change; rules in `docs/OUTCOME_UPDATES.md`). Never edit an old row; add a new one.
- Don't commit full CFJ report text or PDFs. Only the paragraphs the app displays are published
  (`data/trialwatch_argument_excerpts.jsonl`, regenerate with `scripts/export_argument_excerpts.py`)
  under CFJ's copyright notice in `data/NOTICE.md`.
- New pages: add them to the navigation in `app.py`; don't call `st.set_page_config` in pages.
- The Gemini key comes from Streamlit secrets when deployed, else `.env` (`src/llm.py: api_key()`).

## Judging criteria (optimize for these)
Innovation 25 · Feasibility within TrialWatch's infrastructure 25 · Human Rights Impact 30 · Ethical Rigor & Responsible AI 20.

## Working rules for Claude Code
- **Never invent case facts, dates, names, quotes or sources.** If data is missing, leave it blank or "unknown" and set `verified=false`.
- Keep `src/stress_test.py` free of LLM calls; it must be deterministic and unit tested.
- Never read or print `.env`; never commit secrets. Use `st.secrets` / `.env` only.
- Small changes per commit; run `pytest` before saying a task is done.
- Each teammate works on their own branch; avoid editing files another role owns (see `docs/TEAM_PLAN.md`).

## Team
See `docs/TEAM_PLAN.md` for each person's tasks and the timeline.
5 data science students (Shreya, Valentina, Ungu, Layla, Yuki), no law students. Legal claims come from cited sources (CFJ/TrialWatch report, HRW, court decisions), not our own judgment.
- Data: build `data/cases_seed.csv` / `events.csv` from the CFJ report + news
- Stress Test + Argument Bank + UN letter: Shreya
- App: Streamlit pages
- Briefs + pitch
- Outcome confirmation + argument accuracy check: Yuki

## Key sources
- `references/` — CFJ report "Protecting Online Speech in Indonesia: Lessons from the EIT Law and the Road Ahead" (based on a 73-case dataset; 6 deep-dive case studies)
- https://cfj.org/trialwatch/trials/ — TrialWatch case pages
- https://cfj.org/reports/ — all TrialWatch/CFJ reports (96 entries; listed in `docs/TRIALWATCH_REPORTS.md`)
- https://www.hrw.org/news/2025/05/08/indonesian-court-restricts-criminal-defamation-lawsuits
- https://inp.polri.go.id/artikel/inp-to-obey-constitutional-courts-ruling-on-ite-law
