# Pitch script: Precedent & Practice (slide by slide)

For `pitch/fairtrial_advocacy_tracker.pptx` (14 slides). About 4 minutes of talking plus the live demo.
Numbers are the ones on the slides; if the data changes, rerun `scripts/build_slides.py` and check them.
Wording rule: outcomes "followed" TrialWatch's work, never "were caused by" it.

---

**1 · Title (10 s)**
"We're Team 12, Track 3, Advocacy and Impact. Our project is Precedent & Practice: a human rights advocacy tracker built on TrialWatch's own fairness reports."

**2 · Contents (5 s)**
"Quick route: the problem, our solution, why now, how it works, a live demo, then the roadmap and the team."

**3 · Problem (40 s)**
"TrialWatch's analysis is some of the best in the field, but a lawyer facing a new speech case can't use it quickly. There are 90 reports, 63 of them graded trials, and they sit in PDFs. You can't search for how a similar case was argued, which UN decisions applied, or what happened afterwards.
Second, every UN submission is written from scratch, from court records, NGO reports and news in several languages.
Third, reforms go unmeasured. Indonesia revised its speech law in 2024 and 2025, and police pledged to comply. Nobody tracks whether the prosecutions actually stop."

**4 · Solution (35 s)**
"So we built two things. First, an Argument Bank over 47 TrialWatch freedom-of-expression trials in 23 countries. For any case it finds the closest trials, good outcomes first, with their arguments on legality, vagueness, broadness, necessity and proportionality, each with its author and page.
Second, a draft submission to the UN Special Rapporteur in which every sentence cites its source, quotes are checked word for word, and a lawyer approves.
And where a law has just changed, a stress test: 5 of 13 past Indonesian cases would likely be barred today, and 3 to 9 across different legal readings."

**5 · Why now: the human impact (30 s)**
"Behind each row is a person. Laras Faizati Khairunnisa shared an Instagram Story about a police headquarters during the August 2025 unrest and was convicted in January 2026. She received six months of supervision rather than prison. Fatia and Haris spent about three years under prosecution for discussing a human rights report. Those are the cases the tool is for."

**6 · How it works (35 s)**
"Three steps. One: pick a case or describe a new one, and the matches say why they match. Arguments come grouped by the five labels, with author and page, and good outcomes first, each confirmed with a source.
Two: the stress test. Rules R1 to R4 run as transparent code, with no AI, plus a sensitivity analysis over ten legal readings.
Three: the letter. AI suggests case facts from a news story and drafts the letter, but the letter is built only from numbered sources. Code rejects uncited sentences and invented quotes, a second check flags weak sentences, and a named lawyer approves."

**7 · Demo (about 90 s, live)**
Open the live app (link on the handover slide).
1. *Start here:* point at the four numbers (47 reports, 23 countries, 21 of 47 good outcomes, 5 of 13 likely barred).
2. *Argument Bank:* pick a seeded case or describe a new one. Show the matching trials, the "why it matches" line, and one argument with its author and a page link.
3. *Stress Test:* show the five likely-barred cases and the rule behind one of them (for example Septia: R1, a company cannot be a defamation victim).
4. *UN Letter:* "Draft a UN letter for this case". Show the numbered sources, the check, and the approval step.
Say: "Everything here is a draft for lawyer review."
Fallback if the app is slow: the plain no-AI draft still works, and the Argument Bank needs no key.

**8 · Service pipeline (30 s)**
"Here is the pipeline. TrialWatch's 96 listings give 94 PDFs. We parse them with no AI: 63 grades, 47 authors, 2,381 argument paragraphs and 154 UN decisions cited. People confirm the outcomes, 47 of 47, and 288 impact sentences. We match the current case, run the stress test, and produce a sourced UN letter. AI is used in only two places, suggesting case facts and drafting the letter, and both are checked by code against the sources and then approved by a person."

**9 · Why TrialWatch lawyers use it (25 s)**
"Our user, illustrative, is a TrialWatch legal monitor, reviewing new speech prosecutions and drafting UN submissions under time pressure. The pain: 90 reports, sources in several languages, letters from scratch. We give them minutes, not a day: the closest cases, arguments with page links, and a sourced draft to approve. It is specific, built from TrialWatch's own reports. It is checkable, since every claim links to its page. And it is easy: a web app with no install."

**10 · Responsible AI (30 s)**
"No AI where rules will do: the stress test, parsing, grades and matching are plain, tested code. Every claim has a source: quotes are checked word for word, uncited sentences are rejected, each argument is credited to its report's author, and a person approves. And we are honest and safe: no predictions, outcomes 'followed' and are never 'caused'. Two at-risk people are hidden and never sent to AI, and we publish only cited excerpts, credited to the Clooney Foundation for Justice."

**11 · Validation (30 s)**
"We checked our own work. All 2,381 arguments are on the page they cite, and all 288 impact sentences too. Every one of the 47 reports has an author with a source sentence, and all 47 outcomes are confirmed with a source. 14 of 16 Indonesian cases are signed off by a teammate.
And we know our limits: the headline is 5 of 13, and 3 to 9 across legal readings. Argument categories are about 75 to 80 percent right in a hand-read sample, so a person always checks them. There are 168 automated tests on every change."

**12 · Next steps (20 s)**
"Today it is ready to hand over: a live app, an open-source repo and a written guide. With TrialWatch, we'd confirm rules R1 to R4 and the argument categories with TrialWatch lawyers and add the 73-case Indonesia dataset. Next, swap the rules file for the next country's reform, and add a live news intake that feeds a review queue."

**13 · Team (15 s)**
"Shreya built the rule engine, sensitivity analysis, Argument Bank and UN letter. Valentina built the repository, case tracker and case verification. Ungu did the Indonesian case verification and impact categories. Layla was data lead and handled sensitive-case review and the pitch. Yuki confirmed all 47 TrialWatch outcomes, each with a source."

**14 · Close (5 s)**
"Thank you. Precedent & Practice puts TrialWatch's findings in the hands of the next lawyer on the day a complaint is filed. Happy to take questions."

---

## Likely questions

- **Why 13, not 14?** The stress test counts cases reported before the 2025 ruling. That leaves out Laras (2025) and the two hidden cases.
- **Why 3 to 9?** Each of nine alternative readings changes one rule or one contested fact. The low is "officials can still be victims" (3). The high is "the ruling also covers hate-speech complaints by groups" (9). Dropping R1 altogether would give 1, shown separately.
- **Does it replace a lawyer?** No. Every output is a draft; a named lawyer approves the letter.
- **Where does the AI sit?** Two places only, both checked by code against the sources.
- **Is this TrialWatch's product?** No. It is an independent hackathon project built on their published reports, with attribution and permission to reuse report language.
