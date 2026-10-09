# Prompts to paste into Claude Code (in order)

Run each one, check the result, commit, then the next.

## 1. Scaffold
```
Read CLAUDE.md, docs/PROPOSAL.md, docs/stress_test_rules.md and the CSVs in data/. Scaffold the repo exactly per the structure in CLAUDE.md: requirements.txt (streamlit, pandas, anthropic, python-dotenv, pytest), .gitignore (include .env), MIT LICENSE, README.md with setup and run instructions, src/data.py that loads and validates the CSVs, and an app.py home page that shows the project name, the one-line hook, and counts of cases by outcome. Make it run with `streamlit run app.py`. Don't build the other pages yet.
```

## 2. Stress test engine (Shreya)
```
Build src/stress_test.py implementing docs/stress_test_rules.md as pure, deterministic functions. Input: one row of data/cases_seed.csv. Output: a dict with verdict (LIKELY BARRED / AT RISK / STILL PROSECUTABLE), rules_fired (list), reasons (one line per rule), and the source. Treat articles containing "27(3)" or "27A" as defamation. Unknown complainant_type → no R1/R2 verdict, add reason "complainant unknown — needs data". Write tests/test_stress_test.py covering each rule, using fatia_haris (R1 → barred), richard_lee (R2 → barred), roy_suryo (R3 → at risk), marzuki (R4 → at risk). Run pytest until green.
```

## 3. Stress test page
```
Create pages/2_Stress_Test.py: run the engine over every case, show a headline "X of Y past cases would likely be barred under the 2025 ruling", a bar chart of verdict counts, and a table (name, role, complainant, article, verdict as a colored badge, rules fired, reason, source link). Add a banner: "For lawyer review — not legal advice." Add a filter by verdict and by article. Click a case to see its reasoning.
```

## 4. LLM fact extraction for rule inputs
```
Create src/llm.py with a function that takes a news article or report passage and returns JSON for the stress-test inputs (complainant, complainant_type, article, public_interest, harm_shown) plus a verbatim quote supporting each field. If a field can't be supported by a quote, return "unknown" and verified=false. Use the Anthropic API via ANTHROPIC_API_KEY from .env. Add a Streamlit expander on the Stress Test page: "Add a case from text" — paste text, see extracted fields, edit them, then run the stress test on it. Nothing is saved without a click.
```

## 5. Cases + timeline page
```
Create pages/1_Cases.py: a case list with a search box and filters (role, outcome, article). Selecting a case shows its details and a vertical timeline from data/events.csv (create that file with columns case_id,date,lane,description,source,verified; seed it from the outcome_detail text in cases_seed.csv). Show unverified items with a dashed "unverified" tag. Hide cases where sensitive=true unless a sidebar toggle "Show sensitive (internal)" is on.
```

## 6. Promise Clock
```
On app.py add a Promise Clock section from data/promises_seed.csv: for each promise show the text, who made it, date, days since (computed from today), status badge (kept / broken / no evidence yet) and evidence. If the date is "TO VERIFY", show "date to verify" instead of a count.
```

## 7. Brief generator
```
Create pages/3_Briefs.py: pick a case and an audience (UN Special Rapporteur letter / English press release / Bahasa Indonesia social post). Generate a draft with the LLM using only that case's rows, the stress-test result and the promises. Every sentence must end with a citation like [case:fatia_haris] or [promise:p2]; reject and regenerate any draft with an uncited sentence. Show Approve and Mark sensitive buttons; approved drafts are saved to outputs/briefs/ with a timestamp. Sensitive cases can't be used.
```

## 8. Polish for demo
```
Review the whole app for the demo: consistent styling, clear headings, no errors with missing data, README updated with screenshots placeholders, setup steps, data sources, limitations, and the Responsible AI section from docs/PROPOSAL.md. Run tests.
```
