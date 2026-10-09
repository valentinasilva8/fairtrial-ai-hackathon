"""Find what happened to the defendants in TrialWatch cases, with the sentence that says so.

Deterministic: regular expressions over report text and CFJ news posts. The
output is *evidence for a person to check*, never a final label: every
suggested outcome is marked as a suggestion until someone fills verified_by.
"""

from __future__ import annotations

import re
import unicodedata

GOOD = {
    "acquitted": r"\bacquitt(?:ed|al)\b",
    "charges dropped": r"charges? (?:\w+ ){0,3}(?:dropped|withdrawn|dismissed)|(?:dropped|withdrew|dismiss(?:ed|al of)) (?:the |all )?(?:case|charges)",
    "conviction overturned": r"overturn(?:ed|s)?|quash(?:ed)?|vacat(?:ed|e) (?:the |his |her |their )?(?:conviction|sentence)",
    "released": r"\b(?:was|were|been|is) (?:later |subsequently |finally |now )?(?:released|freed)\b(?![^.]{0,40}\b(?:bail|bond)\b)",
    "pardoned": r"\bpardon(?:ed)?\b|amnest(?:y|ied)",
    "UN found detention arbitrary": r"Working Group on Arbitrary Detention.{0,200}arbitrary",
}
NOT_GOOD = {
    "convicted": r"\bconvicted\b|found (?:him|her|them) guilty|\bguilty\b",
    "sentenced": r"\bsentenced to\b",
    "conviction upheld": r"\bupheld\b",
    "still detained": r"remains? (?:in )?(?:detention|detained|in prison|behind bars)|still (?:in )?(?:detention|detained|in prison)",
}

# Words in report titles that are not part of a defendant's name.
TITLE_NOISE = re.compile(
    r"^(?:(?:CFJ |Final Report: |Fairness Report(?: II)?: |Trial Monitoring of (?:Proceedings against |People v\. )?|Monitoring of the Trial of ))+",
)
# Titles that don't name a person; the name to search for, taken from the title itself.
TITLE_NAMES = {
    "The Trial of the Peacock Generation Troupe: Myanmar": ["Peacock Generation"],
    "Thailand v. Does 1-5 of the Organization for Thai Federation": ["Organization for Thai Federation"],
    "15 Post-Election Trials: A Window into Courts in Belarus": [],
}
SPLIT_PARTY = re.compile(r"\s+vs?\.\s+|\bCase (?:of|Against)\s+|\bagainst\s+", re.I)
# Other spellings used on cfj.org for the same person.
ALIASES = {"Aleksey Navalny": ["alexei navalny"], "Pham Thi Doan Trang": ["pham doan trang"]}
NAME_STOP = {"others", "al", "et", "the", "of", "and", "media", "troupe", "trial", "september", "ii"}


def _ascii(s: str) -> str:
    s = s.replace("ı", "i").replace("İ", "I")
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def defendants(title: str) -> list[str]:
    """Defendant names from a report title, e.g. 'Turkey v. Veysel Ok' -> ['Veysel Ok']."""
    if title in TITLE_NAMES:
        return TITLE_NAMES[title]
    t = TITLE_NOISE.sub("", title.strip())
    parts = SPLIT_PARTY.split(t)
    side = parts[-1] if len(parts) > 1 else t
    side = re.sub(r"\(.*?\)|\bet al\.?|\bII\b|:.*$", "", side)
    names = [n.strip(" .,'\"“”").replace('"', "") for n in re.split(r",\s*(?:and\s+)?|\s+and\s+|\s*&\s*", side)]
    return [n for n in names if n and len(n) > 2]


def full_name_keys(names: list[str]) -> list[str]:
    """Keys for deciding whether a news post is about this case: full names only.

    (Surnames alone collide: Kenia Hernandez and Evelyn Hernandez are different cases.)
    """
    keys = set()
    for n in names:
        toks = _ascii(n).split()
        keys.add(" ".join(toks))
        if len(toks) > 2:  # "Ahmet Tuna Altinel" also as "Ahmet Altinel"; drop a trailing nickname
            keys.add(f"{toks[0]} {toks[-1]}")
            keys.add(" ".join(toks[:-1]))
        keys.update(ALIASES.get(n, []))
    return sorted(keys, key=len, reverse=True)


def name_tokens(names: list[str]) -> list[str]:
    """Keys for picking sentences inside a document already known to be about this case."""
    toks = {t for n in names for t in re.findall(r"[a-z][a-z'-]{3,}", _ascii(n)) if t not in NAME_STOP}
    return sorted(toks, key=len, reverse=True)


def mentions(text: str, keys: list[str]) -> bool:
    a = _ascii(text)
    return any(re.search(r"\b" + re.escape(k) + r"\b", a) for k in keys)


def sentences(text: str) -> list[str]:
    flat = re.sub(r"\s+", " ", text)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z“\"])", flat) if 20 <= len(s.strip()) <= 400]


def signals(sentence: str) -> tuple[list[str], list[str]]:
    good = [k for k, p in GOOD.items() if re.search(p, sentence, re.I)]
    bad = [k for k, p in NOT_GOOD.items() if re.search(p, sentence, re.I)]
    return good, bad


# Footnote and citation text, which mentions outcomes of other proceedings.
CITATION = re.compile(r"\b(?:p|pp|para|paras)\. ?\d|\bNo\. ?\d|U\.N\. Doc|\bId\.|Available at", re.I)


def outcome_evidence(text: str, keys: list[str], require_name: bool = True) -> list[dict]:
    """Sentences that state an outcome; with require_name, only those naming a defendant."""
    out = []
    for s in sentences(text):
        if CITATION.search(s):
            continue
        good, bad = signals(s)
        if not (good or bad):
            continue
        if require_name and not mentions(s, keys):
            continue
        out.append({"sentence": s, "good": good, "not_good": bad})
    return out


def suggest_label(evidence_by_date: list[dict]) -> str:
    """A suggestion only: the latest piece of evidence decides; 'mixed' if it says both."""
    if not evidence_by_date:
        return "unknown"
    last = evidence_by_date[-1]
    if last["good"] and not last["not_good"]:
        return "good"
    if last["not_good"] and not last["good"]:
        return "not good"
    return "mixed"
