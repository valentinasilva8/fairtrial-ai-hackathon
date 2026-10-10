# Paper vs. Practice — Proposal
*TrialWatch Fair Trial & AI Hackathon · Track 3: Advocacy & Impact*

## Pitch
Indonesia's ITE Law has been used to criminally prosecute journalists, activists and ordinary critics — often on complaints filed by ministers, companies and officials. After years of advocacy, the law was revised in 2024, the Constitutional Court narrowed it in 2025, and the police pledged to comply. But nobody can see whether the reform actually protects people.

**Paper vs. Practice stress-tests the reform.** We run real prosecutions through the new legal rules and ask: *would this case still be allowed today?* Then we track whether officials kept their promises, find how TrialWatch argued similar cases elsewhere, and turn every finding into a cited UN submission TrialWatch can send the same day.

> *"Indonesia reformed its speech law. We stress-tested the reform: how many past prosecutions would it have stopped — and is it stopping new ones?"*

## Problem
- TrialWatch documents unfair prosecutions and pushes for legal reform, but has no systematic way to measure whether a reform changed outcomes.
- TrialWatch has published 90 reports, including 63 graded trials in more than 20 countries, but there is no way to search the arguments its experts made in them: a lawyer facing a new case can't quickly find how TrialWatch argued a similar one.
- Case information is scattered across court records, NGO reports and news, in English and Bahasa Indonesia.
- Advocacy letters are written by hand for each case.

## Solution
TrialWatch's own process is Monitoring → Evaluation → Advocacy. The tool follows it:

1. **Monitoring — case tracker.** Each Indonesian case on one source-linked timeline: post → complaint → detention → trial → advocacy → verdict → appeal.
2. **Evaluation — Reform Stress Test.** A transparent rule engine applies four rules from the reformed law and the 2025 Constitutional Court ruling:
   - R1 only an individual can be a defamation victim (not companies, government bodies, officials or groups)
   - R2 the victim must file the complaint personally
   - R3 hate speech requires real, imminent harm
   - R4 public-interest speech has a defense
   Each case gets **Likely barred / At risk / Still prosecutable**, with the rule and source shown, labeled "for lawyer review". Current result: **5 of 13 past cases would likely be barred.** A sensitivity analysis reruns this under ten scenarios: it ranges from **3 of 13** (if public officials can still be defamation victims) to **8 of 13** (if the "only individuals" rule also covers hate-speech complaints by groups), and falls to 1 of 13 without R1. The headline rests mainly on R1, and the key open legal question is whether public officials are excluded.
3. **Evaluation — Argument Bank** (added after judge feedback on day 1). For a current case, find the most similar past TrialWatch cases, show what happened in them, and show the arguments TrialWatch's experts made, by category:
   - legality and vagueness
   - legitimate aim
   - necessity and proportionality
   - overbreadth
   - pretrial detention and fair trial
   Each argument comes with the page in the report and the UN Human Rights Committee decisions it cites. Cases with a good outcome (acquittal, charges dropped, release) are listed first.
4. **Promise Clock.** Days since each official pledge, and the evidence (or absence of it) that it was carried out.
5. **Advocacy — UN Special Rapporteur letter.** A draft submission to the Special Rapporteur on freedom of expression, built from the case, the stress test, the pledges and the Argument Bank. Every sentence cites numbered sources; code rejects any uncited sentence or invented quotation, a second check flags sentences the sources don't fully support, and a named reviewer approves before it is saved.

## Example
Human rights defenders **Fatia Maulidiyanti and Haris Azhar** were reported by a government minister over a YouTube discussion of a human rights report. They went through a full criminal trial before being acquitted in 2024 (CFJ report, Case Study E).
- **Stress test:** under the 2025 ruling (R1: a public official can't be a defamation victim), the complaint would likely have been barred at the start.
- **Argument Bank:** the closest past TrialWatch case is the Thai defamation prosecution of Wuth Boonlert and Samak Donnapee — online criticism, a human rights defender, the same region — where TrialWatch's report argued that "imprisonment is never an appropriate penalty" for defamation, and the defendants were acquitted (to be confirmed by our team).
- **UN letter:** the draft cites the case record, the ruling, the police pledge and those TrialWatch pages, with every quotation checked against its source.

## Data (all public)
- **CFJ report** *Protecting Online Speech in Indonesia* (hackathon packet): 6 case studies plus further cases, based on a 73-case dataset (we will ask TrialWatch for access). Our Indonesian case table has 16 cases, each with sources; teammates sign off each one in a verification log, and 2 at-risk people are marked sensitive and hidden.
- **Every TrialWatch report on cfj.org:** 96 report pages = 90 distinct reports, 94 PDFs, downloaded at the rate cfj.org's robots.txt asks for.
  - 63 trials carry an A–F grade.
  - 47 graded trials analyse freedom of expression; these form the Argument Bank.
  - Those 47 cite 154 distinct UN Human Rights Committee decisions.
- **226 CFJ news posts**, for outcomes after each report (acquittals on appeal, releases).
- Human Rights Watch, Amnesty International, SAFEnet, AJI and news for Indonesian cases.

## How TrialWatch would use it
- **New case intake:** paste a news story about a new ITE prosecution; within minutes see whether the 2025 ruling should have barred it, and how TrialWatch argued the most similar past cases.
- **Faster, better-sourced advocacy:** a UN submission draft that cites TrialWatch's own findings and UN Committee decisions, ready for a lawyer to edit the same day.
- **Searching its own work:** the Argument Bank makes 47 fairness reports searchable by argument for the first time.
- **Measuring its own impact:** track whether outcomes followed TrialWatch's reports and whether reforms it campaigned for are being kept.
- **Other countries:** the stress-test rules live in one file and the Argument Bank already covers 23 countries and territories, so the same tool works for the next country's speech-law reform.
- **Fits existing infrastructure:** CSV files and a small Streamlit app, no database, free-tier AI.

## Responsible AI
- **Every claim is source-linked** or shown as unverified; quotations are checked word for word.
- **No AI where rules will do.** The stress test, report parsing, grades, outcome evidence and case matching are deterministic code; the AI only suggests rule inputs (each with a verified quote) and drafts letters (checked twice, then approved by a person).
- **Transparent matching:** each similar case lists the features it shares with the current one.
- **No outcome prediction.** We show what *followed* in similar cases, never that an argument *caused* an outcome, and never a prediction for a live trial.
- **Outcomes are unconfirmed until a person checks them** and records their name.
- **A sensitive flag** keeps at-risk defendants out of public views and out of the AI entirely (Gemini's free tier may use prompts to improve Google's products).
- **Copyright:** CFJ's report text stays on the user's machine; the public repository holds only metadata, grades and links.
- **Outputs are drafts for lawyers**, not legal conclusions.
- **Limitations we state openly:**
  - The new Criminal Code may let prosecutions move off the ITE Law, so a falling ITE case count isn't proof of success.
  - Only 2 post-ruling Indonesian cases so far.
  - Argument tags come from keyword matching and need human review.

## Validation
- Rule sensitivity analysis: the headline under ten scenarios (each rule switched off, narrower and broader readings of R1, a contested fact read the other way, only verified cases), shown on the Stress Test page.
- Automated tests run on every change: each stress-test rule, data validation, grade extraction, quote checks, citation rejection, and the Gemini calls (with a fake client).
- Every grade in the TrialWatch index is stored with the text it was read from.
- Team checks: case verification log, outcome confirmation, and a hand check of extracted arguments for an accuracy figure.

## Team & roles
- Data — case and promise datasets with sources; outcome confirmation
- **Reform Stress Test and Argument Bank — Shreya**
- App — Streamlit interface
- Briefs + pitch
- Outcome confirmation and argument accuracy check (Yuki)

## Stack
Python, Streamlit, pandas, Google Gemini API (free tier), poppler for PDF text. Open-source (MIT).
