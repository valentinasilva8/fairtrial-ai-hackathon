# FairTrial guide (floating assistant)

A robot in the lower-right corner of every page. Click it to open the chat panel.

- **Quick guides** answer common questions about the website.
- **Ask the legal guide** offers seven suggested questions on fair-trial and free-expression standards.
  Each has a prepared answer in `data/assistant_knowledge.json` with the exact passages it relies on.
  A typed question gets the answer to the closest suggested question (keyword match); anything else gets
  the list of suggested questions.
- No model is called, so the assistant never uses the team's Gemini quota. `ask()` in `src/assistant.py`
  is the Gemini version, kept for when a dedicated key is available; the UI doesn't call it.
- After a question, the robot bobs and a "Thinking…" bubble appears above its head; the answer then pops
  up in that speech bubble, with its sources. The panel keeps the conversation.

## Legal library
`data/assistant_knowledge.json` lists the website guides, the suggested questions and eight TrialWatch
report excerpts (by report URL and page) covering legality, vagueness, overbreadth, necessity,
proportionality, arbitrary detention and the presumption of innocence, including the Indonesia report on
Suzethe Margaret. The excerpt text is read from `data/trialwatch_argument_excerpts.jsonl` (CFJ copyright,
see `data/NOTICE.md`), so nothing is duplicated.

## Safeguards
- English only: the tests check every guide, question and answer for non-English characters.
- Every quote must appear in the cited source, and every `[source_id]` in an answer must have a checked
  quote; the tests run every prepared answer through this check (`validate_answer`).
- The assistant never reads case data and sends nothing to an outside service. Users are still told not
  to paste sensitive details.
- Answers are for lawyer review, not legal advice; outcomes "followed" advocacy, never "caused".
- `app.py` wraps the assistant in `try/except`, so if it ever breaks, the rest of the site still runs.

## Files
`src/assistant.py` (library, prompt, checks), `src/assistant_ui.py` (robot, panel, bubble; CSS scoped to
`pa_*` keys), `assets/assistant_robot.png`, `data/assistant_knowledge.json`, `tests/test_assistant.py`.
