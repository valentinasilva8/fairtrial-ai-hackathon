# Paper vs. Practice — project context for Claude Code

## What this is
Hackathon project for the TrialWatch Fair Trial & AI Hackathon (Columbia Law School Human Rights Institute), Oct 9–10, 2026. Track 3: Advocacy & Impact.
Final deliverables due **Saturday Oct 10, 3:30 pm ET**: GitHub repo (code + README + open-source license), working demo, short written description of the tool and how TrialWatch would use it. 10–15 min demo to judges.

**One line:** Indonesia reformed its speech law (ITE / EIT Law). We stress-test the reform: how many past prosecutions would it have stopped, and is it stopping new ones?

TrialWatch monitors criminal prosecutions of journalists and other public-interest voices. The ITE Law has been used against journalists, activists and critics. It was revised in 2024 (Law No. 1/2024) and narrowed by the Constitutional Court in Decision No. 105/PUU-XXII/2024 (2025). Nobody can easily see whether this changed outcomes.

## Features (priority order)
1. **Case tracker** — each case on one source-linked timeline (post → complaint → detention → trial → advocacy → verdict → appeal).
2. **Reform Stress Test** (core feature, owned by Shreya) — run each case through the reform rules in `docs/stress_test_rules.md` and output: likely barred / at risk / still prosecutable, with the reason and rule cited. Headline: "X of Y past cases would now be barred."
3. **Promise Clock** — days since an official pledge (e.g. police pledge to follow the ruling) and evidence of implementation. Data in `data/promises_seed.csv`.
4. **One-click advocacy briefs** — LLM drafts a UN Special Rapporteur letter, English press release, or Bahasa Indonesia social post from a case's data. Every sentence cites a source row. Human approves before use.

## Stack
- Python 3.11+, Streamlit (`app.py` + `pages/`), pandas
- LLM via Anthropic API (key in `.env` as `ANTHROPIC_API_KEY`, never committed)
- Data as CSV in `data/`. No database.
- Run: `streamlit run app.py`

## Suggested structure
```
app.py                  # Streamlit home: headline stats + Promise Clock
pages/1_Cases.py        # case list + timeline view
pages/2_Stress_Test.py  # stress test results table + summary chart
pages/3_Briefs.py       # brief generator with approve / mark-sensitive
src/stress_test.py      # rule engine (pure functions, unit tested)
src/llm.py              # LLM helpers (extraction, rule check, briefs)
src/data.py             # load + validate CSVs
tests/test_stress_test.py
data/cases_seed.csv
data/events.csv
data/promises_seed.csv
docs/
references/             # source PDFs (CFJ EIT report) — not required to run
```

## Rules for all code and content (Responsible AI — 20% of judging)
- **Every factual claim must link to a source** (`source` column). Rows without one show as "unverified" in the UI.
- Stress-test output is **"for lawyer review"**, never a legal conclusion. Show which rule triggered and why.
- Say **"followed", never "caused"** when relating advocacy to outcomes.
- Every case has a `sensitive` flag; sensitive cases are hidden from public views and briefs.
- No personal data beyond what is already in the public record. No scraping that violates site terms.
- LLM outputs must quote the source text they rely on; if they can't, mark unverified.
- Keep the rule engine deterministic (rules in code); use the LLM only to help fill rule inputs from text, and show its reasoning.

## Judging criteria (optimize for these)
Innovation 25 · Feasibility within TrialWatch's infrastructure 25 · Human Rights Impact 30 · Ethical Rigor & Responsible AI 20.

## Team
4 data science students, no law students. Legal claims come from cited sources (CFJ/TrialWatch report, HRW, court decisions), not our own judgment.
- Data: build `data/cases_seed.csv` / `events.csv` from the CFJ report + news
- Stress Test: Shreya
- App: Streamlit pages
- Briefs + pitch

## Key sources
- `references/` — CFJ report "Protecting Online Speech in Indonesia: Lessons from the EIT Law and the Road Ahead" (based on a 73-case dataset; 6 deep-dive case studies)
- https://cfj.org/trialwatch/trials/ — TrialWatch case pages
- https://www.hrw.org/news/2025/05/08/indonesian-court-restricts-criminal-defamation-lawsuits
- https://inp.polri.go.id/artikel/inp-to-obey-constitutional-courts-ruling-on-ite-law
