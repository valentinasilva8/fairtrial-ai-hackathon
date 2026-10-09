"""Reform Stress Test rule engine.

Implements docs/stress_test_rules.md as pure, deterministic functions.
No LLM calls here. Output is for lawyer review, not a legal conclusion.
"""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

LIKELY_BARRED = "LIKELY BARRED"
AT_RISK = "AT RISK"
STILL_PROSECUTABLE = "STILL PROSECUTABLE"
VERDICTS = [LIKELY_BARRED, AT_RISK, STILL_PROSECUTABLE]

RULE_SOURCE = (
    "CFJ report 'Protecting Online Speech in Indonesia', summarizing Law No. 1/2024 "
    "and Constitutional Court Decisions 105/PUU-XXII/2024 and 115/PUU-XXII/2024"
)

RULES = {
    "R1": {
        "name": "Victim must be an individual",
        "basis": "Court held 'victim' applies only to individuals, excluding corporations, "
                 "government agencies, public officials and groups.",
    },
    "R2": {
        "name": "Complaint must come from the victim personally",
        "basis": "Defamation complaints must be filed by the victim, not a representative "
                 "(e.g. Dr. Richard Lee: suspect status invalidated).",
    },
    "R3": {
        "name": "Hate speech requires real, imminent harm",
        "basis": "State intervention is legitimate only if the expression poses "
                 "'a real and imminent danger'.",
    },
    "R4": {
        "name": "Public-interest defense",
        "basis": "Article 45(7)(a) of the amended law provides a defense for speech in the public interest.",
    },
}

DEFAMATION_TOKENS = ("27(3)", "27A")
HATE_SPEECH_TOKEN = "28(2)"
R1_COMPLAINANTS = {"public_official", "government_body", "company", "group"}
KNOWN_COMPLAINANTS = R1_COMPLAINANTS | {"individual_victim", "representative", "police"}
# New Criminal Code articles that can still punish criticism (rules doc "watch-out").
DISPLACEMENT_ARTICLES = ("433", "240", "218", "219")

_TRUE = {"true", "1", "yes", "y"}


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in _TRUE


def _articles(value) -> list[str]:
    return [a.strip() for a in str(value).split(";") if a.strip()]


def is_defamation(article) -> bool:
    return any(tok in a for a in _articles(article) for tok in DEFAMATION_TOKENS)


def is_hate_speech(article) -> bool:
    return any(HATE_SPEECH_TOKEN in a for a in _articles(article))


def is_displacement_watch(article) -> bool:
    return any(a.startswith(DISPLACEMENT_ARTICLES) for a in _articles(article))


def evaluate_case(case: Mapping) -> dict:
    """Run one case (a row of data/cases_seed.csv) through rules R1–R4."""
    article = case.get("article", "")
    complainant_type = str(case.get("complainant_type", "unknown")).strip() or "unknown"
    public_interest = _as_bool(case.get("public_interest", False))
    harm_shown = _as_bool(case.get("harm_shown", False))
    defamation = is_defamation(article)

    rules_fired: list[str] = []
    reasons: list[str] = []

    if defamation and complainant_type not in KNOWN_COMPLAINANTS:
        reasons.append("Complainant unknown — needs data (R1/R2 not evaluated).")
    elif defamation and complainant_type in R1_COMPLAINANTS:
        rules_fired.append("R1")
        reasons.append(
            f"R1: defamation complaint by a {complainant_type.replace('_', ' ')}, "
            "which can no longer be a defamation victim."
        )
    elif defamation and complainant_type == "representative":
        rules_fired.append("R2")
        reasons.append("R2: defamation complaint filed by a representative, not the victim personally.")

    if is_hate_speech(article) and not harm_shown:
        rules_fired.append("R3")
        reasons.append("R3: hate-speech charge with no real, imminent harm shown in the record.")

    if public_interest:
        rules_fired.append("R4")
        reasons.append("R4: speech on a matter of public interest — defense available.")

    if "R1" in rules_fired or "R2" in rules_fired:
        verdict = LIKELY_BARRED
    elif "R3" in rules_fired or "R4" in rules_fired:
        verdict = AT_RISK
    else:
        verdict = STILL_PROSECUTABLE
        reasons.append("No reform rule applies to the recorded facts.")

    if not defamation and not is_hate_speech(article):
        reasons.append("Charge is outside the defamation / hate-speech rules (R1–R3); only R4 checked.")

    return {
        "case_id": case.get("case_id", ""),
        "verdict": verdict,
        "rules_fired": rules_fired,
        "reasons": reasons,
        "rule_basis": {r: RULES[r]["basis"] for r in rules_fired},
        "rule_source": RULE_SOURCE,
        "source": case.get("source", ""),
        "displacement_watch": is_displacement_watch(article),
    }


def evaluate_all(cases: pd.DataFrame) -> pd.DataFrame:
    """Evaluate every case; returns one row per case."""
    return pd.DataFrame([evaluate_case(row) for row in cases.to_dict("records")])


def summarize(results: pd.DataFrame) -> dict:
    """Headline: 'X of Y past cases would likely be barred.'"""
    counts = results["verdict"].value_counts()
    return {
        "total": len(results),
        **{v: int(counts.get(v, 0)) for v in VERDICTS},
    }
