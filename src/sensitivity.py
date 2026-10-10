"""Rule sensitivity analysis: how much does "X of Y past cases would likely be barred" move?

Each scenario changes one rule or one contested fact and reruns the deterministic
engine. The point is to show judges which part of the headline is robust and which
depends on a reading a lawyer should confirm.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from src.stress_test import LIKELY_BARRED, R1_COMPLAINANTS, evaluate_all

RULING_YEAR = 2025
VERIFICATION_LOG = Path(__file__).resolve().parent.parent / "data" / "verification_log.csv"


@dataclass
class Scenario:
    name: str
    question: str
    options: dict = field(default_factory=dict)
    edit: dict = field(default_factory=dict)  # {case_id: {column: value}}: a contested fact read differently
    only_verified: str = ""  # "" | "source" | "person"


SCENARIOS = [
    Scenario("Baseline", "The rules as written in docs/stress_test_rules.md."),
    Scenario("Without R1", "What if the 'only individuals can be victims' ruling didn't exist?",
             options={"disabled": frozenset({"R1"})}),
    Scenario("Without R2", "What if complaints by a representative were still allowed?",
             options={"disabled": frozenset({"R2"})}),
    Scenario("Without R3", "What if hate speech didn't need real, imminent harm?",
             options={"disabled": frozenset({"R3"})}),
    Scenario("Without R4", "What if there were no public-interest defense?",
             options={"disabled": frozenset({"R4"})}),
    Scenario("Officials can still be victims",
             "What if R1 excludes companies, government bodies and groups, but not individual officials? "
             "(The rules doc takes 'officials' from the CFJ report; a lawyer should confirm.)",
             options={"r1_complainants": frozenset(R1_COMPLAINANTS - {"public_official"})}),
    Scenario("R1 also covers hate-speech complaints",
             "What if 'only individuals can be victims' also applies to hate-speech complaints by groups?",
             options={"r1_covers_hate_speech": True}),
    Scenario("Septia: owner complained personally",
             "What if the complaint against Septia counts as the owner's own (individual), not the company's?",
             edit={"septia": {"complainant_type": "individual_victim"}}),
    Scenario("Only source-verified cases", "Count only cases marked verified=true in the data.",
             only_verified="source"),
    Scenario("Only cases checked by a teammate", "Count only cases a named teammate has signed off.",
             only_verified="person"),
]


def past_cases(cases: pd.DataFrame) -> pd.DataFrame:
    """Cases reported before the 2025 ruling, or with an unknown year."""
    return cases[cases["year_reported"].isna() | (cases["year_reported"] < RULING_YEAR)]


def _person_checked() -> set[str]:
    if not VERIFICATION_LOG.exists():
        return set()
    log = pd.read_csv(VERIFICATION_LOG, dtype=str, keep_default_na=False)
    return set(log.loc[log["verified_by"].str.strip() != "", "case_id"])


def barred_ids(cases: pd.DataFrame, scenario: Scenario) -> tuple[set[str], int]:
    """Ids of past cases likely barred under the scenario, and how many past cases were counted."""
    df = past_cases(cases).copy()
    for cid, changes in scenario.edit.items():
        for col, value in changes.items():
            df.loc[df["case_id"] == cid, col] = value
    if scenario.only_verified == "source":
        df = df[df["verified"]]
    elif scenario.only_verified == "person":
        df = df[df["case_id"].isin(_person_checked())]
    if df.empty:
        return set(), 0
    res = evaluate_all(df.reset_index(drop=True), **scenario.options)
    return set(res.loc[res["verdict"] == LIKELY_BARRED, "case_id"]), len(df)


def run(cases: pd.DataFrame, scenarios: list[Scenario] = SCENARIOS) -> pd.DataFrame:
    """One row per scenario: the headline under it and which cases flip versus the baseline."""
    base, _ = barred_ids(cases, scenarios[0])
    names = dict(zip(cases["case_id"], cases["name"]))
    rows = []
    for s in scenarios:
        ids, total = barred_ids(cases, s)
        rows.append({
            "scenario": s.name,
            "question": s.question,
            "barred": len(ids),
            "counted": total,
            "headline": f"{len(ids)} of {total}",
            "newly_barred": ", ".join(sorted(names[i] for i in ids - base)),
            "no_longer_barred": ", ".join(sorted(names[i] for i in base - ids)),
        })
    return pd.DataFrame(rows)


def robustness(cases: pd.DataFrame, scenarios: list[Scenario] = SCENARIOS) -> pd.DataFrame:
    """For each case barred at baseline: in how many scenarios it stays barred (counting only those that include it)."""
    base, _ = barred_ids(cases, scenarios[0])
    names = dict(zip(cases["case_id"], cases["name"]))
    stays = {i: 0 for i in base}
    counted = {i: 0 for i in base}
    for s in scenarios:
        ids, _ = barred_ids(cases, s)
        included = set(past_cases(cases)["case_id"])
        if s.only_verified == "source":
            included = set(cases.loc[cases["verified"], "case_id"])
        elif s.only_verified == "person":
            included = _person_checked()
        for i in base:
            if i in included:
                counted[i] += 1
                stays[i] += i in ids
    return pd.DataFrame([
        {"case": names[i], "stays_barred": stays[i], "scenarios": counted[i]} for i in sorted(base)
    ]).sort_values("stays_barred", ascending=False, kind="stable").reset_index(drop=True)
