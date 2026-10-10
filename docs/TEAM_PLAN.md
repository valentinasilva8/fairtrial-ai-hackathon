# Team plan — Shreya, Valentina, Ungu, Layla, Yuki

Deadline: **Saturday Oct 10, 3:30 pm ET** (submit repo link + description, then 10–15 min demo).
Mentor sessions: **Fri 1 pm, Fri 4 pm, Sat 11 am.**
Rule of thumb: Claude Code writes the code. **People find and verify facts, make judgment calls, talk to mentors, and present.**

---

## 1. Data: everyone verifies their cases (Fri 1:30–4 pm)

`data/cases_seed.csv` has 14 cases taken from the CFJ report in `references/` (page 39 onward: case studies A–F, then the Legal Analysis section). It was extracted quickly, so **every row must be checked by a person.** Plus we need ~3 **new cases filed after April 2025**.

| Person | Cases to verify | Extra |
|---|---|---|
| Shreya | fatia_haris, daniel_frits, karimunjawa_3, septia | (lighter: also building the stress test) |
| Valentina | tinus, madilis, marzuki, roy_suryo | |
| Ungu | dandhy, richard_lee, nugroho, edy_mulyadi | |
| Layla | meila, asrul | find 3 post-April-2025 ITE cases (SAFEnet, AJI, LBH Pers, Amnesty Indonesia, news: "UU ITE dilaporkan 2025") + police pledge date for Promise Clock |

### Checklist for each row
- [ ] `complainant` + `complainant_type` correct? (individual_victim / public_official / government_body / company / group / representative / police / unknown) — **this drives rules R1/R2**
- [ ] `article` correct? (27(3), 28(2), hoax…)
- [ ] `outcome` + `outcome_detail`: dates and sentences match the source
- [ ] `public_interest` (true/false) and `harm_shown` (true/false): see section 3, labelled independently
- [ ] `source`: add the **report page number**, and a **URL** to a second source (news, Front Line Defenders, TrialWatch) where possible
- [ ] Set `verified=true` only after this; otherwise leave `false`
- [ ] Add 4–8 rows per case to `data/events.csv` (date, lane, description, source, verified)
- [ ] Anything sensitive about the person (e.g. still in detention, at risk)? set `sensitive=true`

**Never invent anything.** Unknown = leave "unknown".

---

## 2. Build roles (after data, and in parallel where possible)

| Person | Owns | Claude Code prompts | Manual work |
|---|---|---|---|
| **Shreya** | Reform Stress Test: `src/stress_test.py`, `tests/`, `views/2_Stress_Test.py`, rules doc | 2, 3, 4 | Confirm rules with mentor at 1 pm; rule-sensitivity analysis; methodology slide |
| **Valentina** | App: `app.py`, `views/1_Cases.py`, Promise Clock, styling, deploy | 1 (done), 5, 6, 8, 9 | Deploy to Streamlit Cloud by Sat 11 am; API key as secret; screenshots |
| **Ungu** | Briefs + LLM: `pages/3_Briefs.py`, `src/llm.py` | 7 | Model letter on real UN communications; find a Bahasa speaker to check the post; brief evaluation (section 3) |
| **Layla** | Data lead + pitch: post-2025 cases, data QA, slides, submission text | one-liner "check CSVs for missing sources" | Slides + demo script; written description for submission; README final check |

(Swap roles if someone prefers; just update this file.)

---

## 3. Validation & testing (this is our Responsible AI score, 20%)

1. **Unit tests** for every stress-test rule (`pytest`). Shreya.
2. **Inter-rater agreement:** for `public_interest` and `harm_shown`, two people label each case *without looking at each other's answer*. Report % agreement (or Cohen's kappa) and resolve disagreements together. Shows the human labels are reliable. Everyone, Layla tallies.
3. **LLM extractor accuracy:** run the extractor (prompt 4) on each case's source passage and compare its fields to our verified labels. Report accuracy per field and show one failure honestly. Shreya.
4. **Rule sensitivity analysis:** re-run the headline with each rule switched off or changed (e.g. what if R1 doesn't exclude public officials?). Show how much the "X of Y barred" number moves, and which result is robust. *(Same idea as Shreya's DSPP threshold stress test.)* Shreya.
5. **Citation test:** automated check that every sentence in a generated brief has a `[case:…]` or `[promise:…]` citation, and that each cited ID exists. Ungu.
6. **Hallucination red-team:** give the brief generator a case with missing data and check it doesn't make things up. Ungu.
7. **Bahasa check:** a native speaker reviews 2–3 generated posts. Ungu.
8. **Data QA:** no row with `verified=true` lacks a source; no duplicate case IDs; dates parse. Layla (ask Claude Code to write `tests/test_data.py`).

---

## 4. Slides (Layla leads, everyone gives one slide) — 7 slides
1. **Hook:** "Indonesia reformed its speech law. Did it work?" + photo-free title, one real case line
2. **Problem:** ITE Law used against journalists & critics; reform 2024/2025; nobody measures follow-through
3. **What we built:** 4 features (tracker, Stress Test, Promise Clock, briefs) → switch to live demo
4. **Stress Test method + result:** 4 rules → "X of Y would now be barred" + sensitivity analysis
5. **Validation:** tests, inter-rater agreement, extractor accuracy, citation check
6. **Responsible AI + limits:** sources, "followed not caused", sensitive flag, lawyers decide; new Criminal Code displacement risk
7. **How TrialWatch uses it + next steps:** 73-case dataset, other countries, Criminal Code tracking

---

## 5. Timeline

| When | Milestone |
|---|---|
| **Fri 1:00** | Mentor 1: confirm Indonesia focus + stress-test rules; ask for the 73-case dataset |
| **Fri 1:30–4:00** | Everyone verifies their cases (section 1). Shreya: engine + tests. Valentina: cases page |
| **Fri 4:00** | Mentor 2: show stress test + headline number; ask "would TrialWatch use this?" |
| **Fri 4:30–night** | Stress-test page + extractor (Shreya) · Promise Clock (Valentina) · briefs (Ungu) · post-2025 cases + inter-rater tally (Layla) |
| **Fri night** | Everything runs end to end locally |
| **Sat 10–11** | Merge, deploy, data gaps |
| **Sat 11:00** | Mentor 3: full demo dry run |
| **Sat 11:30–2:00** | Fixes, validation numbers into slides, README |
| **Sat 2:00–3:00** | Two timed rehearsals |
| **Sat by 3:30** | Submit repo link, license, README, description |

---

## 6. Demo script (10 min)
1. Hook (1 min) → 2. Promise Clock (1) → 3. Stress Test: headline, filter, open Fatia & Haris (3) → 4. Post-2025 cases (1) → 5. Brief + citations + approve (2) → 6. Validation numbers (1) → 7. Limits + how TrialWatch uses it (1)

## Git habits
Pull before starting · own branch per person · small commits · PR to `main` · don't edit files another role owns.

---

## Status and plan to the deadline (updated Fri Oct 9, evening)
**Deadline: Sat Oct 10, 3:30 pm ET.** Mentor dry run Sat 11:00.

After judge feedback we added the **Argument Bank**: similar past TrialWatch cases, the arguments
TrialWatch fairness reports made in them, and a **UN Special Rapporteur letter** that cites them. It sits on top
of the stress test. The AI is now **Google Gemini (free tier)**: put `GEMINI_API_KEY` in `.env`.
Details: `docs/ARGUMENT_BANK.md`. The Argument Bank needs the TrialWatch reports on your laptop; run the
five scripts in the README once (~1 hour, unattended).

### Done
| | |
|---|---|
| Stress test engine + page | 5 of 13 past cases likely barred (was 4 before Karimunjawa 3's complainant was sourced); "add a case from text" with Gemini |
| Rule sensitivity analysis | 10 scenarios on the Stress Test page: 3–9 of 13 across legal readings; 1 of 13 without R1 |
| Promise Clock | Start here page |
| TrialWatch data | all 96 cfj.org report listings (90 distinct reports); 63 graded reports; 47 freedom-of-expression reports (2,075 PDF pages) = Argument Bank; 226 news posts; outcome evidence |
| Argument Bank page | similar cases, outcomes, arguments by category with page links |
| UN Letter page | every sentence cited; quotes checked; support check; reviewer approval |
| Case verification | Valentina's 4 and Ungu's 6 cases checked |
| Tests | 95 tests, run on every PR |

### Still to do — old plan
| Task | Who |
|---|---|
| Verify Shreya's 4 cases (fatia_haris, daniel_frits, karimunjawa_3, septia) and tick `data/verification_log.csv` | Shreya |
| Verify meila and asrul; fix PR #2 (deletes the `asrul` row, uses values outside the allowed lists, now conflicts) | Layla |
| Inter-rater labels for `public_interest` / `harm_shown` (two people each, blind), tally agreement | everyone; Layla tallies |
| Merge the case tracker (PR #5) | Valentina |
| Police pledge date (promise p4 is "TO VERIFY") | Layla |
| Polish (prompt 8) and deploy (prompt 9) | Valentina |
| Slides, demo script, written description for submission | Layla (+ one slide each) |

### Still to do — new (Argument Bank)
| Task | Who |
|---|---|
| **Confirm the 47 TrialWatch outcomes** (`docs/VERIFY_OUTCOMES.md`); start with the cases suggested good or mixed | **Yuki** (+ anyone free) |
| **Hand-check arguments in 10 reports**: for each paragraph shown on the Argument Bank page, is the category right? Record right/wrong → our accuracy figure | **Yuki** |
| Red-team the UN letter: run it on 5 cases, including one with missing data; note any claim not in the sources | Ungu |
| Bahasa / English press-release versions of the letter (optional, only if time) | Ungu |
| Ask the mentor: may we publish short report excerpts (needed to deploy the Argument Bank publicly)? Do the four argument categories match how TrialWatch thinks? | Shreya |
| Merge PR #13 | Valentina or Shreya |

### Yuki: getting started (no coding needed)
1. Clone the repo and follow the README setup (no key needed for your tasks).
2. Open `data/trialwatch_outcomes.csv` and `data/trialwatch_outcome_evidence.csv` in a spreadsheet; follow
   `docs/VERIFY_OUTCOMES.md` for each case. Use only what the linked source says; never guess.
3. For the argument check, run the app (after the report download) and open **Argument Bank**.

### Timeline
| When | Milestone |
|---|---|
| Fri night | Merge #13 and #5. Yuki starts outcomes. Shreya verifies her 4 cases. Everyone runs the report download |
| Sat 9:00–11:00 | Outcomes confirmed, argument accuracy figure, sensitivity analysis, letter red-team, slides draft |
| Sat 11:00 | Mentor dry run of the full demo |
| Sat 11:30–2:00 | Fixes, numbers into slides, README final check, deploy (or decide to demo locally) |
| Sat 2:00–3:00 | Two timed rehearsals |
| Sat by 3:30 | Submit repo link, license, README, written description |

### Demo flow (10 min)
Hook (1) → Promise Clock (1) → Stress Test: headline, open Fatia & Haris (2) → Argument Bank: closest
TrialWatch case and its arguments (2) → UN Letter: draft, citation check, support check, approve (2) →
Validation numbers (1) → Limits + how TrialWatch uses it (1)
