# FairTrial guide (floating assistant)

A robot in the lower-right corner of every page. Click it to open the chat panel.

- **Quick guides** answer common questions about the website. They work without an API key.
- **Ask the legal guide** and free-text chat use Gemini through `src/llm.py`, the same key and models as
  the rest of the app (`GEMINI_API_KEY` in Streamlit secrets or `.env`). Without a key, chat is disabled.
- While Gemini works, the robot bobs and a "Thinking…" bubble appears above its head; the answer then
  pops up in that speech bubble, with its sources. The panel keeps the conversation.

## Legal library
`data/assistant_knowledge.json` lists the website guides, the suggested questions and eight TrialWatch
report excerpts (by report URL and page) covering legality, vagueness, overbreadth, necessity,
proportionality, arbitrary detention and the presumption of innocence, including the Indonesia report on
Suzethe Margaret. The excerpt text is read from `data/trialwatch_argument_excerpts.jsonl` (CFJ copyright,
see `data/NOTICE.md`), so nothing is duplicated.

## Safeguards
- English only: the prompt tells the model to always answer in English; the tests check the library text.
- Every quote the model gives must appear in the cited source, and every `[source_id]` in the answer must
  have a checked quote; otherwise the answer is rejected (`src/assistant.py`, `validate_answer`).
- The assistant never reads case data, so sensitive cases can't reach the model. Users are told not to
  paste sensitive details.
- Answers are for lawyer review, not legal advice; outcomes "followed" advocacy, never "caused".
- `app.py` wraps the assistant in `try/except`, so if it ever breaks, the rest of the site still runs.

## Files
`src/assistant.py` (library, prompt, checks), `src/assistant_ui.py` (robot, panel, bubble; CSS scoped to
`pa_*` keys), `assets/assistant_robot.png`, `data/assistant_knowledge.json`, `tests/test_assistant.py`.
