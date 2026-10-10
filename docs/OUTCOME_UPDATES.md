# Recording later outcomes (outcome updates)

TrialWatch's impact often shows after the report: a conviction overturned on appeal, a release, a UN finding.
`data/trialwatch_outcome_updates.csv` records these changes so the app shows each case's **current** outcome
and its history (e.g. "convicted → conviction overturned (2023-06-05)").

## How the app uses it
- The log is **append-only**: one row per verified change. Never delete or rewrite a row; add a new one.
- A case's current outcome is its **latest verified update** (by `event_date`); with none, the confirmed outcome in
  `data/trialwatch_outcomes.csv` stands.
- The Argument Bank (good outcomes first, badges, "changed for the better"), the Start here page's impact count and the
  UN letter's sources all use the current outcome and history automatically.
- **Finding and adding a change is done by a person, on purpose.** Nothing is added to the log automatically:
  a court decision has to be read and matched to the right defendant, and the hosted app cannot write to
  GitHub. Once the line is merged, everything else updates by itself. A later step could re-run the CFJ news
  scan (`scripts/fetch_trialwatch_news.py`, `scripts/build_outcomes.py`) on a schedule to *suggest* changes to check.

## Columns
| column | rule |
|---|---|
| `report_url` | one of the 47 Argument Bank reports (as in `trialwatch_outcomes.csv`) |
| `case` | the report title |
| `event_date` | the decision's date: `YYYY`, `YYYY-MM` or `YYYY-MM-DD`; use the precision the source gives |
| `previous_outcome` | the outcome before this change (the form fills it) |
| `new_outcome` | one of: acquitted, acquittal upheld, charges dropped, conviction overturned, released early / pardoned, UN found detention arbitrary, convicted, conviction upheld, sentence reduced, still detained, pending, unknown |
| `summary` | one or two factual sentences |
| `source_url` | the source you checked (required) |
| `verified_by` | the person who checked it (required) |
| `entered_on`, `notes` | date entered; anything a reviewer should know |

Good outcomes: acquitted, acquittal upheld, charges dropped, conviction overturned, released early / pardoned,
UN found detention arbitrary.

## Verification rules (a person, every time)
1. **Prefer the primary source**: the judgment, court record or UN opinion. Otherwise a reliable report that
   names the defendant. Two articles copying one press release are one source.
2. **Match the defendant's full name.** A surname alone is not enough; another person's result is not this one's.
3. **A decision, not an interim step.** Release on bail is not an acquittal; an appeal *filed* is not an appeal *decided*.
4. **Use the decision's date**, not the article's.
5. **Wording:** the change *followed* TrialWatch's work. We never say TrialWatch's arguments *caused* it, unless a
   court's own reasoning says so, and then quote it.
6. **Sensitive people** (still at risk) are not recorded here without the team agreeing.

## How to add one
1. In the app, open **Outcome Updates**, fill the form and tick the confirmation. It checks the entry and gives
   you one CSV line.
2. Click **Open the log on GitHub**, paste the line as the last line, choose **Create a new branch and start a
   pull request**.
3. The automated tests check the log again (`tests/test_outcome_updates.py`); merge when green, then **Sync fork**
   so the live app updates.

The first two rows (Bao Choy Yuk-ling, Stella Nyanzi) come from Yuki's confirmed outcome sheet.
