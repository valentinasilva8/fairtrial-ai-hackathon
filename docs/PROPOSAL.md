# Paper vs. Practice — Proposal
*TrialWatch Fair Trial & AI Hackathon · Track 3: Advocacy & Impact*

## 30-second pitch
Indonesia's ITE Law has been used to criminally prosecute journalists, activists and ordinary critics — often on complaints filed by ministers, companies and officials. After years of advocacy, the law was revised in 2024, the Constitutional Court narrowed it in 2025, and the police pledged to comply. But nobody can see whether the reform actually protects people.

**Paper vs. Practice stress-tests the reform.** We run real prosecutions through the new legal rules and ask: *would this case still be allowed today?* Then we track whether officials kept their promises, and turn every finding into a cited advocacy brief TrialWatch can send the same day.

> *"Indonesia reformed its speech law. We stress-tested the reform: how many past prosecutions would it have stopped — and is it stopping new ones?"*

## Problem
- TrialWatch documents unfair prosecutions and pushes for legal reform, but has no systematic way to measure whether a reform changed outcomes.
- Case information is scattered across court records, NGO reports and news, in English and Bahasa Indonesia.
- Advocacy materials are written by hand for each audience.

## Solution — four features
1. **Case tracker** — each case on one source-linked timeline: post → complaint → detention → trial → advocacy → verdict → appeal.
2. **Reform Stress Test** — a transparent rule engine applies four rules from the reformed law and the 2025 Constitutional Court ruling:
   - R1 only an individual can be a defamation victim (not companies, government bodies, officials or groups)
   - R2 the victim must file the complaint personally
   - R3 hate speech requires real, imminent harm
   - R4 public-interest speech has a defense
   Each case gets **Likely barred / At risk / Still prosecutable**, with the rule and source shown. Labeled "for lawyer review".
3. **Promise Clock** — days since each official pledge, and the evidence (or absence of it) that it was carried out.
4. **One-click advocacy briefs** — an LLM drafts a UN Special Rapporteur letter, an English press release, or a Bahasa Indonesia social post. Every sentence cites a source row; a person approves before use.

## Example (from the CFJ report)
Human rights defenders **Fatia Maulidiyanti and Haris Azhar** were reported by a government minister over a YouTube discussion of a human rights report. They went through a full criminal trial before being acquitted in 2024. Under the 2025 ruling (R1: a public official can't be a defamation victim), the complaint would likely have been barred at the start.

## Data (all public)
- CFJ report *Protecting Online Speech in Indonesia* (hackathon packet) — 6 case studies + further cases; based on a 73-case dataset (we will ask TrialWatch for access)
- TrialWatch case pages (e.g. journalist Muhammad Asrul)
- Human Rights Watch, Amnesty, SAFEnet, AJI (Indonesian journalists' alliance), news
- Indonesian court tracker (SIPP) for post-reform cases

## How TrialWatch would use it
- Before filing an amicus brief or UN submission: check whether a new case is one the reform should have barred.
- Measure the impact of its own advocacy on Indonesian law over time.
- Reuse the engine for other countries' speech-law reforms by swapping the rules file.

## Responsible AI
- Every claim is source-linked or shown as unverified.
- The rule engine is deterministic and explainable; the LLM only helps extract facts and must quote its source.
- We say "followed", never "caused".
- A sensitive flag keeps at-risk defendants out of public views and briefs.
- Outputs are drafts for lawyers, not legal conclusions.
- Limitation we state openly: the new Criminal Code may let prosecutions move off the ITE Law, so a falling ITE case count isn't proof of success.

## Team & roles
- Data — case and promise datasets with sources
- **Reform Stress Test — Shreya**
- App — Streamlit interface
- Briefs + pitch

## Stack
Python, Streamlit, pandas, Anthropic API. Open-source (MIT).
