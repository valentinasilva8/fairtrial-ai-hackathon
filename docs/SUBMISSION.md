# Paper vs. Practice — an advocacy tracker for TrialWatch
*TrialWatch Fair Trial & AI Hackathon · Track 3: Advocacy & Impact*
*Team: Shreya, Valentina, Ungu, Layla, Yuki*
*Repository: https://github.com/valentinasilva8/fairtrial-ai-hackathon (MIT; report excerpts © Clooney Foundation for Justice)*

## In one sentence
Paper vs. Practice checks whether a speech-law reform would have stopped real prosecutions, finds how TrialWatch argued similar trials in 23 countries and what followed, and turns that into a UN Special Rapporteur submission where every sentence is sourced and a lawyer approves before use.

## The problem
Indonesia's ITE (EIT) Law has been used against journalists, human rights defenders and critics, often on complaints by ministers, officials and companies. It was revised in 2024 (Law No. 1/2024) and narrowed by the Constitutional Court in 2025 (Decision 105/PUU-XXII/2024), and the police pledged to comply. Nobody can see whether this protects people in practice.

At the same time, TrialWatch has published 90 reports, including 63 graded trials. When a new case arrives, a lawyer cannot quickly find how TrialWatch's experts argued a similar trial, which UN decisions they relied on, or what happened to the defendant afterwards. Advocacy letters are written from scratch each time.

## What the tool does
The app follows TrialWatch's own process: **Monitoring → Evaluation → Advocacy**.

1. **Reform Stress Test (Evaluation).** Four rules from the reformed law and the 2025 ruling, written as transparent code: only individuals can be defamation victims (R1); the victim must complain personally (R2); hate speech needs real, imminent harm (R3); public-interest speech has a defense (R4). Each Indonesian case gets *likely barred / at risk / still prosecutable*, with the rule and reason. **Result: 5 of 13 past cases would likely be barred.** A sensitivity analysis reruns this under ten readings of the law: it ranges from 3 to 8 of 13 and rests mainly on R1, which tells a lawyer exactly what to confirm.
2. **Argument Bank (Evaluation).** Built from every report on cfj.org: 47 graded freedom-of-expression trials in 23 countries and territories. For a current case it finds the most similar past trials (by charge, kind of speech, defendant and region, with the reasons shown), puts those with a **good outcome first**, and shows the strongest argument TrialWatch's experts made on legality and vagueness, legitimate aim, necessity and proportionality, overbreadth, pretrial detention and fair trial, each with a link to the exact report page and the UN Human Rights Committee decisions cited. It also shows the **impact on each defendant** (conviction and sentence, detention, mistreatment, reputational harm, other restrictions, prolonged proceedings), each backed by the report sentence that states it.
3. **UN Special Rapporteur letter (Advocacy).** A draft submission built only from numbered sources: the case record, the stress test, official pledges, and the Argument Bank. Code rejects any sentence without a source and any quotation not found word for word in its source; a second check flags sentences the sources don't fully support; a named reviewer approves before the letter is saved. A plain version can be built without AI.
4. **Promise Clock (accountability).** Days since each official pledge, with the evidence that it was kept.
5. **Add a case from text.** Paste a news story about a new prosecution; Gemini suggests the rule inputs, each with a quote that code checks against the text, and a person edits every field before the stress test runs.

## Why lawyers can use it
- **Easy:** a web app; pick a case and click. No installation, no AI knowledge, no database.
- **Fast:** from a new case to similar TrialWatch trials, the arguments used, what followed, and a sourced draft letter in minutes instead of a day of reading.
- **Checkable:** every argument links to the exact report page; every letter sentence lists its sources; nothing is hidden behind an AI answer.
- **Honest about uncertainty:** verdicts are marked "for lawyer review"; the sensitivity analysis shows which legal reading the result depends on; unconfirmed data is labelled.

## Why it is specific to TrialWatch
- It is built from **TrialWatch's own work**: all 96 report pages on cfj.org, the A–F fairness grades, the three-part test its experts apply, and its grading annex's definition of harm (which we use for the impact categories).
- It follows **TrialWatch's process** (monitoring, evaluation, advocacy) and produces what TrialWatch already sends: submissions to UN mechanisms.
- It makes TrialWatch's **47 fairness reports searchable by argument for the first time**, and links them to the 154 UN Human Rights Committee decisions they cite.
- It measures **what followed TrialWatch's work**: 21 of the 47 trials had a good outcome (acquittal, charges dropped, conviction overturned, early release or pardon, or a UN finding of arbitrary detention), each confirmed by a teammate with a source.
- It runs on **TrialWatch's existing infrastructure**: CSV files, a small Streamlit app and a free AI tier. The reform rules live in one file, so the next country's reform reuses everything.

## Human rights impact
Behind each row is a person. Septia Dwi Pertiwi, a whistleblower, was detained for more than five months before a court found her posts true. Fatia Maulidiyanti and Haris Azhar spent about three years under prosecution for discussing a human rights report. Our stress test shows both complaints would likely be barred under the 2025 ruling. The tool lets TrialWatch spot such a case the day a complaint is filed and put the strongest, best-sourced argument in front of police, prosecutors and the UN before months of detention or years of suspicion add up. It also shows publicly whether officials kept the promises they made.

## Responsible AI
- **No AI where rules will do:** the stress test, report parsing, grades, outcome and impact evidence, and case matching are deterministic code. AI only suggests rule inputs (each with a verified quote) and drafts letters (checked twice, then approved by a person).
- **Every claim sourced**, unverified data labelled, and every number on our slides recomputed from the data.
- **No predictions:** we show what *followed* in similar cases, never that an argument *caused* an outcome, and never a forecast for a live trial.
- **People confirm the data:** cases, outcomes and impacts each carry a named checker.
- **Sensitive cases** (people still at risk) are hidden from public views and never sent to the AI; on Gemini's free tier, Google may use prompts.
- **Copyright:** only the 168 report paragraphs the app displays are published, each linked to its page, under CFJ's copyright notice.

## Validation
| Check | Result |
|---|---|
| Argument paragraphs found on the PDF page they cite | 2,304 / 2,304 |
| Impact sentences found on the PDF page they cite | 288 / 288 |
| Argument category tags (hand-read sample of 40) | about 75–80% right |
| Impact categories (hand-read sample of 10) | 8 / 10, both misses since fixed |
| TrialWatch outcomes confirmed by a teammate with a source | 47 / 47 |
| Stress-test headline across ten legal readings | 3 to 8 of 13 (baseline 5) |
| Automated tests, run on every change | 149 passing |

## Limits
- Argument categories come from keyword matching and need human review; the page says so and always links the exact text.
- The arguments are TrialWatch experts' analysis, not necessarily what was argued in court.
- Only two post-ruling Indonesian cases so far; the new Criminal Code may let prosecutions move off the ITE Law (Laras Faizati was convicted under the Penal Code).
- We are data science students, not lawyers: legal readings come from cited sources and need a lawyer's review.

## How TrialWatch would use it, step by step
1. A monitor reads about a new ITE prosecution and pastes the story into the app.
2. The stress test shows whether the 2025 ruling should have barred it, and why.
3. The Argument Bank shows the closest past TrialWatch trials, what followed, and the arguments and UN decisions to rely on.
4. The UN Letter page drafts a submission; a TrialWatch lawyer reviews the flagged sentences, edits, approves and sends.
5. Over time, the Promise Clock and outcome data show whether the reform, and TrialWatch's advocacy, changed what happens to people.
