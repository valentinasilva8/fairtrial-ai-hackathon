"""Argument Bank: similar past TrialWatch cases and the arguments made in them.

Combines data/trialwatch_case_features.csv (matching), data/trialwatch_outcomes.csv
(what happened, confirmed or not) and data/raw/trialwatch/arguments.jsonl (the
tagged paragraphs, local only because they are CFJ's text).
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

import pandas as pd

from src.reports import CATEGORIES
from src.similarity import match

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ARGUMENTS = DATA / "raw" / "trialwatch" / "arguments.jsonl"

GOOD_OUTCOMES = {
    "acquitted", "charges dropped", "conviction overturned",
    "released early / pardoned", "UN found detention arbitrary",
}
CATEGORY_LABELS = {
    "legality_vagueness": "Legality and vagueness",
    "legitimate_aim": "Legitimate aim",
    "necessity_proportionality": "Necessity and proportionality",
    "overbreadth": "Overbreadth",
    "pretrial_detention": "Pretrial detention",
    "fair_trial": "Fair trial",
}
# Paragraphs that apply the international standard are the useful ones for a new case.
# Template text that appears in every report (methodology, grading annex), not case arguments.
BOILERPLATE = re.compile(
    r"grading methodology|Grading Levels|Experts should assign|severity of the violation|"
    r"evaluate the trial.s fairness|arrive at a grade|provided the expert with a factual record|"
    r"monitors? (?:attended|did not)|TrialWatch Expert",
    re.I,
)
# A footnote that slipped into the body text: "87 Conversation with ... Available at https://..."
FOOTNOTE = re.compile(r"^\d{1,3}\s+\S|Available at\s+https?://", re.I)
AUTHORITY = re.compile(r"General Comment|Human Rights Committee|Special Rapporteur|Article 19|ICCPR|Working Group", re.I)


def _split(v: str) -> list[str]:
    return [x for x in str(v).split("; ") if x and x != "nan"]


def outcome_of(row: dict) -> tuple[str, bool]:
    """(label, confirmed). Confirmed only when a person has filled verified_by."""
    if str(row.get("verified_by", "")).strip() and str(row.get("outcome_label", "")).strip():
        return row["outcome_label"], True
    return row.get("suggested_label", "unknown") or "unknown", False


def is_good(label: str, confirmed: bool) -> bool:
    return (label in GOOD_OUTCOMES) if confirmed else label == "good"


@lru_cache(maxsize=1)
def past_cases() -> pd.DataFrame:
    feats = pd.read_csv(DATA / "trialwatch_case_features.csv", keep_default_na=False)
    outcomes = pd.read_csv(DATA / "trialwatch_outcomes.csv", keep_default_na=False)
    reports = pd.read_csv(DATA / "trialwatch_reports.csv", keep_default_na=False)[["url", "pdf_url", "hrc_decisions_cited"]]
    df = feats.merge(outcomes.drop(columns=["case", "grade"]), on="report_url", how="left")
    df = df.merge(reports, left_on="report_url", right_on="url", how="left").drop(columns=["url"])
    for col in ["charges", "speech", "roles"]:
        df[col] = df[col].apply(_split)
    labels = df.apply(lambda r: outcome_of(r.to_dict()), axis=1)
    df["outcome"] = [l for l, _ in labels]
    df["outcome_confirmed"] = [c for _, c in labels]
    df["good_outcome"] = [is_good(l, c) for l, c in labels]
    return df


def similar_cases(current: dict, top_n: int = 8, good_first: bool = True, min_score: int = 3) -> pd.DataFrame:
    """The top_n past cases most similar to `current` (features from src.similarity).

    A match needs at least min_score (by default, one shared charge type). Among
    those top matches, cases with a good outcome are listed first if good_first.
    """
    df = past_cases().copy()
    scored = df.apply(lambda r: match(current, r.to_dict()), axis=1)
    df["score"] = [s for s, _ in scored]
    df["why"] = [w for _, w in scored]
    df = df[df["score"] >= min_score].sort_values("score", ascending=False, kind="stable").head(top_n)
    if good_first:
        df = df.sort_values("good_outcome", ascending=False, kind="stable")
    return df.reset_index(drop=True)


def arguments_available() -> bool:
    return ARGUMENTS.exists()


@lru_cache(maxsize=1)
def _load_arguments() -> tuple[dict, dict]:
    paras, decisions = {}, {}
    if not ARGUMENTS.exists():
        return paras, decisions
    for line in open(ARGUMENTS):
        rec = json.loads(line)
        if "hrc_decisions" in rec:
            decisions[rec["url"]] = rec["hrc_decisions"]
        else:
            paras.setdefault(rec["url"], []).append(rec)
    return paras, decisions


def _strength(p: dict, cat: str) -> int:
    """How strongly a paragraph argues *this* category for this case.

    Favors paragraphs that use the category's own terms several times and cite a
    legal standard; penalizes the generic opening that lists every prong of the test.
    """
    text = p["text"]
    own = len(re.findall(CATEGORIES[cat], text, re.I))
    authority = min(len(AUTHORITY.findall(text)), 3)
    generic = max(len(p["categories"]) - 2, 0)
    size = 2 if 300 <= len(text) <= 1600 else 0
    return 3 * own + authority + size - 3 * generic


def best_arguments(report_url: str, per_category: int = 1) -> dict[str, list[dict]]:
    """For each category, the strongest paragraphs in this report (with page numbers)."""
    paras, _ = _load_arguments()
    out = {}
    for cat in CATEGORY_LABELS:
        cands = [p for p in paras.get(report_url, [])
                 if cat in p["categories"] and AUTHORITY.search(p["text"])
                 and not BOILERPLATE.search(p["text"]) and not FOOTNOTE.search(p["text"])]
        cands.sort(key=lambda p: _strength(p, cat), reverse=True)
        if cands:
            out[cat] = cands[:per_category]
    return out


def hrc_decisions(report_url: str) -> list[str]:
    return _load_arguments()[1].get(report_url, [])


def page_link(pdf_url: str, page: int) -> str:
    return f"{pdf_url}#page={page}" if pdf_url else ""
