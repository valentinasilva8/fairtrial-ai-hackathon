# Confirming case outcomes

`data/trialwatch_outcomes.csv` has one row per core TrialWatch case (47 graded fairness reports with
freedom-of-expression analysis). The `suggested_label` column is a **machine suggestion** from
keyword matching and is often wrong: for example, it can't tell a defendant's acquittal from a
co-defendant's, or a release on bail from a final release. Nothing is treated as an outcome until
a person fills `verified_by`.

## How to confirm one case
1. Open `data/trialwatch_outcome_evidence.csv` and filter `case` to the case. Each row is a
   sentence from the TrialWatch report or a CFJ news post, with its link and date.
2. Open the latest source link and read what happened to **this defendant**.
3. In `data/trialwatch_outcomes.csv` fill:
   - `outcome_label`: one of
     - `acquitted` · `charges dropped` · `conviction overturned` · `released early / pardoned` ·
       `UN found detention arbitrary` (these count as good outcomes)
     - `convicted` · `still detained` · `pending` · `unknown`
   - `outcome_summary`: one plain sentence, e.g. "Acquitted on appeal in May 2024."
   - `outcome_source_url`: the page that says so (a cfj.org report or news post, or another reliable source)
   - `verified_by`: your name
4. If no source settles it, use `unknown` and say why in `notes`. Never guess.

Re-running `python scripts/build_outcomes.py` keeps everything people have filled in.

## Later changes
If a case's outcome changes after you confirmed it (e.g. a conviction overturned on appeal), don't edit
`trialwatch_outcomes.csv`: add a row to `trialwatch_outcome_updates.csv` instead ([OUTCOME_UPDATES.md](OUTCOME_UPDATES.md)).

## Wording
A good outcome **followed** TrialWatch's work and the arguments in its report; we never say the
arguments **caused** it.
