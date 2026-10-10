# Precedent & Practice
*A human rights advocacy tracker built on TrialWatch's fairness reports*

*TrialWatch Fair Trial & AI Hackathon · Track 3: Advocacy & Impact*
*Team: Shreya, Valentina, Ungu, Layla, Yuki*
*Live app: https://fairtrial-ai-hackathongit-cyvqxeqekcqd4hjsqr7b5w.streamlit.app/*
*Repository: https://github.com/valentinasilva8/fairtrial-ai-hackathon (code MIT; report excerpts © Clooney Foundation for Justice)*
*An independent hackathon project, not endorsed by the Clooney Foundation for Justice, TrialWatch® or Columbia Law School.*

## In one sentence
When a journalist or activist is prosecuted for speech, Precedent & Practice finds the trials TrialWatch has already graded that most resemble the case, shows the arguments those reports made on legality, vagueness, broadness, necessity and proportionality and what followed for each defendant, and drafts a UN Special Rapporteur submission in which every sentence is sourced and a lawyer approves before use.

## The problem
TrialWatch has monitored and graded dozens of trials of journalists, human rights defenders and critics. Each fairness report applies international human rights law to the case: whether the law was clear enough (legality, vagueness), whether it swept in protected speech (broadness), and whether prosecution was necessary and proportionate. These reports are some of the best-sourced human-rights legal analysis available, but they sit as separate PDFs. When a new case arrives, a lawyer cannot quickly find how a similar trial was argued, which UN decisions the report relied on, or what happened to the defendant afterwards. Advocacy letters start from a blank page.

Reforms make this harder to judge. Indonesia revised its speech law in 2024, its Constitutional Court narrowed it in 2025 and the police pledged to comply, but nobody can see whether this protects people in practice.

## What the tool does
The app follows TrialWatch's own process: **Monitoring → Evaluation → Advocacy**.

1. **Argument Bank (the core).** Built from all 96 report listings on cfj.org: 47 graded freedom-of-expression fairness reports (2,075 PDF pages) on trials in 23 countries and territories. Some reports cover several trials or defendants (the Belarus report alone covers 15 trials). For a current case, or a new one a lawyer describes, it:
   - finds the most similar trials by charge, kind of speech, defendant and region, and says why each matched;
   - lists trials with a good outcome first (21 of the 47 reported cases: acquittal, charges dropped, conviction overturned, early release or pardon, or a UN finding of arbitrary detention), each confirmed by a teammate with a source;
   - **By argument:** groups the arguments from those trials under the five labels the mentor asked for (legality, vagueness, broadness, necessity, proportionality), then legitimate aim, pretrial detention and fair trial. Each argument names the report's author, links the exact PDF page and lists the UN Human Rights Committee decisions cited. A paragraph reused word for word across reports, such as in three Cambodia cases, is shown once;
   - **By case:** shows each similar trial's outcome, the impact on the defendant (conviction and sentence, detention, mistreatment, reputational harm, other restrictions, prolonged proceedings), and its arguments.
2. **UN Special Rapporteur letter (advocacy).** For a seeded case or a new case in any country, a draft built only from numbered sources: the case record, the Argument Bank, the stress test and official pledges. Code rejects any sentence without a source and any quotation not found word for word; a second check flags sentences the sources don't fully support; a named reviewer approves before it is saved. A plain version can be built without AI.
3. **Reform stress test (where a law has just changed).** For Indonesia, four rules from the reformed law and the 2025 ruling, written as transparent code, show that **5 of 13 past cases would likely be barred today**. A sensitivity analysis shows the range across ten legal readings (3 to 8 of 13), which tells a lawyer exactly what to confirm.
4. **Outcome Updates (accountability).** TrialWatch's impact often shows after the report. A log of verified, dated changes (e.g. a conviction overturned on appeal) makes the latest one each case's current outcome everywhere, shows the history ("convicted → conviction overturned"), and counts the cases that changed for the better. A person checks every entry against a source; automated tests check the log on every change.
5. **Promise Clock (accountability).** Days since each official pledge, with sourced evidence of whether it was kept: three of Indonesia's four pledges are partly kept (e.g. SAFEnet still counted 34 online-expression cases in Jan–Mar 2025, most under the defamation article, and 29 more in Apr–Jun), one has no evidence yet.

## Why lawyers can use it
- **Easy:** a web app. Pick a case or describe a new one; no installation, no AI knowledge.
- **Fast:** from a new case to the closest TrialWatch trials, their arguments by label, what followed, and a sourced draft letter in minutes instead of a day of reading PDFs.
- **Checkable:** every argument links to the exact report page and names its author; every letter sentence lists its sources.
- **Honest about uncertainty:** outputs are marked "for lawyer review"; labels come from keyword matching and say so; unconfirmed data is labelled.

## Why it is specific to TrialWatch
- It is built from **TrialWatch's own work**: its fairness reports, its A–F grades, the three-part test its experts apply, the authors on its Experts Panel, and its grading annex's definition of harm (used for the impact categories).
- It follows **TrialWatch's process** and produces what TrialWatch already sends: submissions to UN mechanisms.
- It makes TrialWatch's **47 fairness reports searchable by argument for the first time**, linked to the 154 UN Human Rights Committee decisions they cite.
- It shows **what followed TrialWatch's work**: 21 of the 47 reported cases ended in a good outcome. We say these outcomes *followed*; we never claim an argument *caused* them.
- It runs on **TrialWatch's existing infrastructure**: CSV files, a small Streamlit app and a free AI tier. Adding a country's reform means writing its rules into one file.

## Human rights impact
The tool's value lies in what it does for human rights work, beyond any single case. It turns TrialWatch's analysis of international human rights law (ICCPR Article 19 and the UN Human Rights Committee's test for restricting speech) into reusable advocacy for the next person prosecuted for what they said. A lawyer defending a journalist in one country can rely on the strongest, best-sourced arguments TrialWatch made for a defendant in another, see that similar cases ended in acquittal or release, and send a sourced submission to a UN mechanism the same day. That speed matters because the harm in these cases is pretrial detention and years under prosecution: in our Indonesian data, Septia Dwi Pertiwi was detained more than five months before a court found her posts true, and Fatia Maulidiyanti and Haris Azhar spent about three years under prosecution for discussing a human rights report.

## Responsible AI
- **No AI where rules will do:** report parsing, grades, authors, argument labels, outcome and impact evidence, case matching and the stress test are deterministic, tested code. AI only suggests case facts from a news story (each with a verified quote) and drafts letters (checked twice, then approved by a person).
- **Every claim sourced:** arguments link to their page; letter quotations are checked word for word; unverified data is labelled.
- **Correct attribution:** each argument names the report's author; the analysis is theirs and not necessarily the Clooney Foundation for Justice's. Shared drafting is counted once, not as independent support.
- **No predictions:** we show what followed in similar cases, never a forecast for a live trial.
- **People confirm the data:** Indonesian cases, the 47 outcomes and the impacts each carry a named checker.
- **Sensitive cases** (people still at risk) are hidden from public views and never sent to the AI.
- **Copyright:** only the 201 report paragraphs the app displays are published, each linked to its page, under CFJ's copyright notice; the full reports stay on cfj.org.

## Validation
| Check | Result |
|---|---|
| Argument paragraphs found on the PDF page they cite | 2,381 / 2,381 |
| Impact sentences found on the PDF page they cite | 288 / 288 |
| Report authors extracted, each with the sentence it came from | 47 / 47 |
| TrialWatch outcomes confirmed by a teammate with a source | 47 / 47 |
| Argument labels (hand-read sample of 40, earlier label set) | about 75–80% right |
| Impact categories (hand-read sample of 10) | 8 / 10, both misses since fixed |
| Stress-test headline across ten legal readings | 3 to 8 of 13 (baseline 5) |
| Automated tests, run on every change | all passing |

## Limits
- Argument labels come from keyword matching and need human review; the app says so and always links the exact text.
- The arguments are the report authors' analysis, not necessarily what was argued in court.
- Similar-case matching uses a few named features (charge, speech, defendant, region); a lawyer can edit them.
- Only two post-ruling Indonesian cases so far; prosecutions may move to the new Criminal Code.
- We are data science students, not lawyers: legal readings come from cited sources and need a lawyer's review.

## How TrialWatch would use it
1. A monitor or lawyer hears of a new speech prosecution and opens the Argument Bank, picking a similar case or describing the new one.
2. **By argument** shows how TrialWatch's reports argued legality, vagueness, broadness, necessity and proportionality in the closest trials, by whom, on which page, and what followed.
3. Where the country has just reformed its law, the stress test shows whether the reform should already bar the case.
4. The UN Letter page drafts a submission from those sources; a TrialWatch lawyer reviews the flagged sentences, edits, approves and sends.
5. Over time, the outcome data and the Promise Clock show what followed TrialWatch's work and whether reforms are being kept.
