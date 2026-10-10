# Demo guide — for the mentor meeting and the judges

Start the app from its **Home** link (not a page link). Total: about 10 minutes.

## 1. Home (1 min)
- **Say:** "Indonesia reformed its speech law. We stress-tested the reform, and turned TrialWatch's own past reports into an Argument Bank for the next case."
- **Show:** the three numbers at the top (5 of 13 past cases likely barred · 47 Argument Bank trials · 23 countries), then the "How it works" steps: Monitoring → Evaluation → Advocacy, TrialWatch's own process.
- **Scroll to the Promise Clock:** days since each official pledge, with "no evidence yet" and the police pledge's date marked "to verify". The point: we don't overstate.

## 2. Stress Test (2 min)
- **Show:** the headline "5 of 13 past cases would likely be barred under the 2025 ruling" and the banner "For lawyer review — not legal advice".
- **Open "How robust is this number?":** 3 to 8 of 13 across ten legal readings; 1 of 13 without R1. "Our number depends mainly on one rule, and on whether public officials still count as victims. That's the question we'd put to a lawyer."
- **Click Fatia Maulidiyanti & Haris Azhar in the table:** reported by a minister over a YouTube discussion of a human rights report; about three years under prosecution before a final acquittal. Verdict: likely barred under R1, with the rule's legal basis.
- *(Optional)* **"Add a case from text":** paste a short news paragraph and extract; every field shows the quote it came from.

## 3. Argument Bank (2–3 min)
- **Pick Fatia Maulidiyanti & Haris Azhar.** Show "How we describe this case for matching" (charge, speech, defendant, region), which a lawyer can edit.
- **First match:** the Thai defamation trial of Wuth Boonlert and Samak Donnapee. **Acquitted, confirmed** (green badge, with the source link). Show "Why it matched".
- **Inside it:** the legality and overbreadth arguments with **page links** (click one: the PDF opens on that page), the UN Human Rights Committee decisions cited, and **Impact on the defendant**.
- **Say:** "47 TrialWatch fairness reports are now searchable by argument. Good outcomes are listed first, but we say an outcome *followed*, never that an argument *caused* it."

## 4. UN Letter (2 min)
- **Pick the same case and click "Draft with Gemini".** If Gemini's free tier is slow, click "Build plain draft (no AI)"; it uses the same sources.
- **Show:** "Citation check passed", the numbered citations [1] [2] in the text, and the source list with links.
- **Click "Check each sentence against its sources":** it flags the sentences a lawyer must look at, often the model's own legal conclusions.
- **Show the Review box:** a reviewer must enter a name and confirm they read everything before saving. Sensitive cases can't be used at all.

## 5. Validation (1 min)
- Page citations: 2,304 / 2,304 argument paragraphs and 288 / 288 impact sentences found on the page they cite.
- 47 / 47 TrialWatch outcomes confirmed by a teammate with a source; 21 good outcomes.
- Sensitivity analysis: 3 to 8 of 13.
- Argument categories about 75–80% right in a hand-read sample; impacts 8 / 10, both misses fixed.
- 149 automated tests on every change.

## 6. Limits and how TrialWatch uses it (1–2 min)
- **Limits:** keyword categories need review; arguments are TrialWatch's analysis, not necessarily what was argued in court; only two post-ruling cases; prosecutions may move to the new Criminal Code; we're not lawyers.
- **Use:** intake of a new case → stress test → closest past trials and arguments → sourced UN draft → lawyer approves. Reusable for the next country's reform.

## What is verified, and by whom
| Data | Status |
|---|---|
| 16 Indonesian cases | Sourced; 14 signed off in `data/verification_log.csv` (Valentina 4, Ungu 10 including Shreya's 4); Meila and Asrul sourced by Layla, sign-off pending; Meila and Khariq Anhar marked sensitive (hidden) |
| 47 TrialWatch outcomes | All confirmed with a source by Yuki (`data/trialwatch_outcomes.csv`) |
| 288 impact sentences | Page-checked by code; categories spot-checked; confirmation by a person pending (Ungu) |
| Argument paragraphs | Page-checked by code (2,304 / 2,304); categories spot-checked (about 75–80%) |
| Grades | Each stored with the sentence it was read from |

## Questions for the mentor
1. Do our argument categories match how TrialWatch structures its analysis?
2. Do public officials count as excluded defamation victims under Decision 105? (This moves our headline between 3 and 5 of 13.)
3. Is showing short report excerpts with attribution OK for a public demo?
4. Which UN mechanism would TrialWatch use first: the Special Rapporteur or the Working Group on Arbitrary Detention?
5. Would TrialWatch use this tool, and where in its workflow?
