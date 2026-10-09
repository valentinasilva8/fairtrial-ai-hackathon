# Paper vs. Practice

> *Indonesia reformed its speech law. We stress-tested the reform: how many past prosecutions would it have stopped — and is it stopping new ones?*

Built for the TrialWatch Fair Trial & AI Hackathon (Columbia Law School Human Rights Institute), Track 3: Advocacy & Impact.

Indonesia's ITE (EIT) Law has been used to prosecute journalists, activists and critics. It was revised in 2024 (Law No. 1/2024) and narrowed by Constitutional Court Decision No. 105/PUU-XXII/2024. Paper vs. Practice runs real cases through the reformed rules, tracks whether officials kept their promises, and drafts cited advocacy briefs. See [docs/PROPOSAL.md](docs/PROPOSAL.md).

**All outputs are drafts for lawyer review, not legal conclusions.**

## Setup

Requires Python 3.11+.

```bash
git clone https://github.com/valentinasilva8/fairtrial-ai-hackathon.git
cd fairtrial-ai-hackathon
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your ANTHROPIC_API_KEY (only needed for LLM features)
```

## Run

```bash
streamlit run app.py
```

Opens at http://localhost:8501.

## Test

```bash
pytest
```

## Project structure

```
app.py                  # Streamlit home: headline stats (+ Promise Clock, planned)
pages/                  # Cases, Stress Test, Briefs (planned)
src/data.py             # load + validate CSVs
src/stress_test.py      # rule engine (planned)
src/llm.py              # LLM helpers (planned)
tests/                  # pytest
data/                   # cases_seed.csv, events.csv, promises_seed.csv
docs/                   # proposal, stress-test rules, team plan
references/             # source PDFs — not required to run
```

## Data

All data comes from public sources, and every row carries a `source`. `src/data.py` validates the CSVs on load:

- Missing columns, duplicate ids or non-boolean flags stop the app with an error.
- Rows with no source, or with a `TO VERIFY` placeholder, are shown as **unverified**.
- Cases with `sensitive=true` are hidden from public views and briefs.

## Responsible AI

- Every factual claim links to a source; unsourced rows are marked unverified.
- The stress-test rule engine is deterministic; the LLM only helps fill rule inputs from text and must quote its source.
- We say "followed", never "caused", when relating advocacy to outcomes.
- Known limitation: the new Criminal Code may let prosecutions move off the ITE Law, so a falling ITE case count is not proof of success.

## License

[MIT](LICENSE)
