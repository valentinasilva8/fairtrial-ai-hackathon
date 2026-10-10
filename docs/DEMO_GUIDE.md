# Demo guide — Precedent & Practice, for the mentor meeting and the judges

Live app: https://fairtrial-ai-hackathongit-cyvqxeqekcqd4hjsqr7b5w.streamlit.app/

Start the app from its **Home** link (not a page link). Free Streamlit apps sleep when unused: open the link a few minutes before presenting. Total: about 10 minutes.

## 1. Home (1 min)
- **Say:** "TrialWatch has graded dozens of trials of journalists and critics. Precedent & Practice turns those reports into arguments, precedents and sourced UN submissions for the next person prosecuted for speech."
- **Show:** the four numbers (47 fairness reports searchable by argument · 23 countries · 21 of 47 good outcomes that followed · 5 of 13 Indonesian cases likely barred) and "How it works": Evaluation → Advocacy → Accountability.
- **Scroll to the Promise Clock:** days since each official pledge; the police pledge's date is marked "to verify". We don't overstate.

## 2. Argument Bank (3 min): the core
- **Pick Fatia Maulidiyanti & Haris Azhar** (or "A new case" and describe one: charge, speech, defendant, region).
- **By argument tab:** open Legality, then Vagueness and Broadness. Each argument shows the case, **report by [author]**, a page link (click it: the PDF opens on that page) and the outcome badge. Point at "Same paragraph in N reports, counted once" where it appears.
- **By case tab:** the first match is the Thai defamation trial of Wuth Boonlert and Samak Donnapee, **acquitted, confirmed** with its source. Show "Why it matched", the impact on the defendant and the UN decisions cited.
- **Say:** "47 TrialWatch fairness reports, searchable by the five labels you asked for. Good outcomes come first; we say they *followed*, never that an argument *caused* them, and each analysis is credited to its author."

## 3. UN Letter (2 min)
- **Same case, "Draft with Gemini".** If the free tier is slow, "Build plain draft (no AI)" uses the same sources.
- **Show:** "Citation check passed", the numbered citations, the source list naming each report's author, and "Check each sentence against its sources", which flags the sentences a lawyer must look at.
- **Edit the letter:** change a sentence or delete a citation number and show the warning that appears; put it back and it re-checks clean.
- **Review, approve and download:** enter a reviewer name, tick the box, then **Download Word (.docx)**. The file says who approved it and whether any warnings were left. Sensitive cases can't be used.

## 4. Stress Test (1–2 min): where a law has just been reformed
- **Show:** "5 of 13 past cases would likely be barred under the 2025 ruling", then open "How robust is this number?": 3 to 8 of 13 across ten legal readings.
- **Click Fatia & Haris:** reported by a minister; R1 says a public official can no longer be a defamation victim.

## 5. Validation (1 min)
- Report authors extracted for 47 / 47 reports, each with its source sentence.
- Page citations: 2,381 / 2,381 argument paragraphs and 288 / 288 impact sentences found on the page they cite.
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
| Argument paragraphs | Page-checked by code (2,381 / 2,381); earlier labels spot-checked (about 75–80%); authors found for 47 / 47 reports |
| Grades | Each stored with the sentence it was read from |

## Questions for the mentor
1. Do our argument categories match how TrialWatch structures its analysis?
2. Do public officials count as excluded defamation victims under Decision 105? (This moves our headline between 3 and 5 of 13.)
3. Is showing short report excerpts with attribution OK for a public demo?
4. Which UN mechanism would TrialWatch use first: the Special Rapporteur or the Working Group on Arbitrary Detention?
5. Would TrialWatch use this tool, and where in its workflow?
