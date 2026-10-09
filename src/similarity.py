"""Find past TrialWatch cases similar to a current case, and say why.

Transparent by design: each case is described by a few named features
(charge types, kind of speech, defendant role, country/region), counted from
the report text with regular expressions, and a match is a weighted overlap
of those features. Every match lists the features it shares. No LLM.
"""

from __future__ import annotations

import re

CHARGES = {
    "defamation or insult": r"defam|\binsult|slander|\blibel|lese[- ]majeste|lèse[- ]majesté",
    "incitement or public order": r"incit|social order|public order|hatred|hate speech",
    "false information": r"false (?:news|information)|fake news|disinformation|\bhoax",
    "extremism or terrorism": r"extremis|terroris",
    "sedition or national security": r"sedition|national security|treason|espionage|state secret",
    "religion or blasphemy": r"blasphem|insult(?:ing)? (?:a |the )?religio|religious hatred",
}
SPEECH = {
    "online post": r"facebook|twitter|tweet|youtube|tiktok|instagram|social media|online post|\bposts?\b",
    "journalism": r"\bjournalis|news(?:paper)? article|\breporting\b|broadcast",
    "protest or assembly": r"protest|demonstrat|peaceful assembly",
    "art or satire": r"satir|\bsong|perform(?:ance|ing)|\bpoem|cartoon",
}
ROLES = {
    "journalist": r"\bjournalist",
    "human rights defender or activist": r"human rights defender|\bactivist",
    "opposition politician": r"opposition (?:leader|politician|party|figure)",
    "human rights lawyer": r"human rights lawyer",
    "academic": r"\bacademic|professor",
}
COUNTRIES = [
    "Algeria", "Azerbaijan", "Bangladesh", "Belarus", "Cambodia", "El Salvador", "Hong Kong",
    "Indonesia", "Kazakhstan", "Kyrgyzstan", "Malaysia", "Mexico", "Morocco", "Myanmar", "Nigeria",
    "Pakistan", "Poland", "Russia", "Rwanda", "Thailand", "Tunisia", "Turkey", "Uganda",
    "Venezuela", "Vietnam",
]
REGION = {
    "Southeast Asia": {"Cambodia", "Indonesia", "Malaysia", "Myanmar", "Thailand", "Vietnam"},
    "South Asia": {"Bangladesh", "Pakistan"},
    "East Asia": {"Hong Kong"},
    "Central Asia": {"Kazakhstan", "Kyrgyzstan"},
    "Europe and Caucasus": {"Azerbaijan", "Belarus", "Poland", "Russia", "Turkey"},
    "Middle East and North Africa": {"Algeria", "Morocco", "Tunisia"},
    "Sub-Saharan Africa": {"Nigeria", "Rwanda", "Uganda"},
    "Latin America": {"El Salvador", "Mexico", "Venezuela"},
}
WEIGHTS = {"charges": 3, "speech": 1, "roles": 1, "country": 2, "region": 1}


def region_of(country: str) -> str:
    return next((r for r, cs in REGION.items() if country in cs), "")


def _present(text: str, patterns: dict[str, str], min_share: float = 0.25, min_count: int = 3) -> tuple[list[str], dict]:
    """Features mentioned at least min_count times and at least min_share of the top feature's count."""
    counts = {k: len(re.findall(p, text, re.I)) for k, p in patterns.items()}
    top = max(counts.values()) if counts else 0
    keep = [k for k, n in counts.items() if n >= min_count and n >= min_share * top]
    return keep, counts


def features_from_report(title: str, text: str) -> dict:
    """Features of a past TrialWatch case, from its report title and text."""
    country_counts = {c: len(re.findall(r"\b" + re.escape(c) + r"\b", title + " " + text)) for c in COUNTRIES}
    country = max(country_counts, key=country_counts.get) if any(country_counts.values()) else ""
    charges, charge_counts = _present(text, CHARGES)
    speech, speech_counts = _present(text, SPEECH)
    roles, role_counts = _present(text, ROLES)
    return {
        "country": country, "region": region_of(country),
        "charges": charges, "speech": speech, "roles": roles,
        "counts": {**charge_counts, **speech_counts, **role_counts},
    }


ARTICLE_TO_CHARGE = {
    "27(3)": "defamation or insult", "27A": "defamation or insult",
    "28(2)": "incitement or public order", "hoax": "false information",
}


def features_from_case(case: dict, country: str = "Indonesia") -> dict:
    """Features of a current case from a row of data/cases_seed.csv (ITE Law cases are online speech)."""
    articles = [a.strip() for a in str(case.get("article", "")).split(";")]
    charges = sorted({ARTICLE_TO_CHARGE[a] for a in articles if a in ARTICLE_TO_CHARGE})
    role_text = str(case.get("role", ""))
    roles = [r for r, p in ROLES.items() if re.search(p, role_text, re.I)]
    if re.search(r"\bHRD\b|defender", role_text):
        roles.append("human rights defender or activist")
    speech = ["online post"]
    if "journalist" in roles:
        speech.append("journalism")
    return {"country": country, "region": region_of(country), "charges": charges,
            "speech": speech, "roles": sorted(set(roles))}


def match(current: dict, past: dict) -> tuple[int, list[str]]:
    """Similarity score and the reasons, e.g. ['same charge: defamation or insult', 'same region: Southeast Asia']."""
    score, reasons = 0, []
    for key, label in [("charges", "charge"), ("speech", "kind of speech"), ("roles", "defendant")]:
        shared = sorted(set(current[key]) & set(past[key]))
        if shared:
            score += WEIGHTS[key] * len(shared)
            reasons.append(f"same {label}: {', '.join(shared)}")
    if current["country"] and current["country"] == past["country"]:
        score += WEIGHTS["country"]
        reasons.append(f"same country: {past['country']}")
    elif current["region"] and current["region"] == past["region"]:
        score += WEIGHTS["region"]
        reasons.append(f"same region: {past['region']}")
    return score, reasons
