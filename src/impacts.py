"""Find the impact of a prosecution on the defendant in a TrialWatch report, with the sentence that says so.

Deterministic: regular expressions over report text, no LLM. Every hit keeps
the exact sentence and its PDF page, and any duration or amount in the
sentence is kept exactly as written. Nothing is computed or inferred.

Categories 1-4 are the harms TrialWatch's own grading annex asks experts to
weigh ("whether the defendant was unjustly convicted and, if so, the sentence
imposed; ... unjustified pretrial detention; ... mistreated; ... reputation
was harmed"). Categories 5 and 6 are ours and are not in the annex.

A hit is evidence for a person to check. The patterns find sentences that
*state* a conviction, a detention and so on for the defendant; they cannot
tell whether it was unjust. Unconfirmed until verified_by is filled.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from src.outcomes import CITATION, full_name_keys, mentions
from src.reports import body_paragraphs

ROOT = Path(__file__).resolve().parent.parent
IMPACTS_CSV = ROOT / "data" / "trialwatch_impacts.csv"
HUMAN_FIELDS = ["verified_by", "notes"]

CATEGORIES = {
    "conviction_sentence": (
        r"\bsentenced\b|\bconvicted\b|\bfound (?!not\b)(?:\w+ )?guilty\b|\bprison (?:term|sentence)\b"
        r"|\b(?:years?|months?|days?)[’']? imprisonment\b|\bterm of imprisonment\b"
    ),
    "pretrial_detention": (
        r"pre-?trial detention|\bdetained\b|\bin detention\b|\bremanded\b|\bheld in (?:custody|detention)\b"
        r"|\bin custody\b|\btaken into custody\b|\bjailed\b|\bimprisoned\b|\bbehind bars\b"
    ),
    "mistreatment": (
        r"\btortur\w*|\bill-?treat\w*|\bmistreat\w*|\bbeaten\b|\bassault(?:ed)?\b|solitary confinement"
        r"|(?:denied|deprived of|refused|without) (?:\w+ ){0,2}medical (?:care|attention|treatment)"
        r"|\binhuman\w*|\bdegrading\b"
    ),
    "reputational_harm": (
        r"\breputation(?:al)?\b|\bsmear\w*|\bstigmati[sz]\w*|\bdiscredit\w*|\bhumiliat\w*"
    ),
    "other_restrictions": (
        r"\bfined\b|\bfines\b|\ba fine\b|\bfine of\b|travel ban|\bpassport (?:was |were )?(?:confiscated|seized|revoked|withheld)"
        r"|\bassets? (?:were |was )?(?:frozen|seized|confiscated)|\bconfiscated\b|\b(?:seizure|confiscation) of\b"
        r"|\b(?:barred|banned|prohibited) from\b|\blicen[cs]e (?:was |were )?(?:revoked|suspended)\b"
        r"|\bstripped of\b|\bdisqualified\b|\bprobation\b|\bhouse arrest\b|\bcurfew\b"
    ),
    "prolonged_proceedings": (
        r"\bremained (?:a )?suspect\b|\bsuspect for\b|\bunder investigation for\b"
        r"|\b(?:prolonged|protracted|lengthy|undue) (?:delay|proceedings?|investigation|trial)\b"
        r"|\bdelays?\b|\bdelayed\b"
    ),
}

LABELS = {
    "conviction_sentence": "Conviction and sentence",
    "pretrial_detention": "Detention",
    "mistreatment": "Mistreatment",
    "reputational_harm": "Reputational harm",
    "other_restrictions": "Other restrictions",
    "prolonged_proceedings": "Prolonged proceedings",
}
# The categories that come from TrialWatch's grading annex; the rest are ours.
FROM_ANNEX = ("conviction_sentence", "pretrial_detention", "mistreatment", "reputational_harm")

# The grading methodology annex appears in every report and lists these harms in general terms.
BOILERPLATE = re.compile(
    r"grading methodology|Grading Levels|Experts should assign|severity of the violation|"
    r"extent of the harm related to the charges|arrive at a grade|TrialWatch Expert",
    re.I,
)

# Sentences that are not statements of fact about the defendant: conditionals and
# hypotheticals ("if she had been detained ... would be"), and the penalty a statute
# provides for, which is not the sentence imposed.
HEDGE = re.compile(r"\b(?:if|would|could|might|may|whether|unless)\b")
STATUTE = re.compile(r"\bprovides? for\b|\bprescrib\w+|\bpunishable\b|\bpunishment\b|\branging from\b|\bcarries a\b|\bstatutory\b", re.I)
HONORIFIC = re.compile(r"\b(Mr|Ms|Mrs|Dr|Prof|No|Art|St)\.\s")
# A footnote number stuck to the end of a sentence ("station.44 The officers ..."), which
# otherwise glues two sentences together. Only after a letter or closing mark, so "1.5 million" is safe.
FOOTNOTE_MARK = re.compile(r"(?<=[A-Za-z)\u201d\"\u2019][.!?])\d{1,3}(?=\s+[A-Z\u201c\"]|$)")


_SENTENCE_END = re.compile(r"(?:(?<=[.!?])|(?<=[.!?][\u201d\"\u2019]))\s+(?=[A-Z\u201c\"])")


def _split(text: str) -> list[str]:
    """Sentences of 20-400 characters, without breaking after 'Mr.' or 'Ms.' and splitting after a closing quote."""
    flat = re.sub(r"\s+", " ", HONORIFIC.sub(lambda m: m.group(1) + ".\x00", FOOTNOTE_MARK.sub("", text))).strip()
    parts = [p.replace("\x00", " ").strip() for p in _SENTENCE_END.split(flat)]
    return [p for p in parts if 20 <= len(p) <= 400]


def _in_quotes(sentence: str, pos: int) -> bool:
    """True if position pos falls inside a quotation, i.e. someone else's words."""
    before = sentence[:pos]
    return (before.count("\u201c") > before.count("\u201d")) or (before.count('"') % 2 == 1)


_NUMBER = (
    r"(?:\d[\d,.]*|(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen"
    r"|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred)"
    r"(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?)"
)
DURATION = re.compile(
    rf"\b{_NUMBER}(?:[- ]and[- ]a[- ]half)?[- ](?:years?|months?|weeks?|days?)\b(?!-old|\s+anniversary)",
    re.I,
)
AMOUNT = re.compile(
    r"(?:(?:Rp\.?|IDR|USD|US\$|\$|€|£|RM|UGX|KHR)\s?\d[\d.,]*(?:\s?(?:million|billion|thousand))?"
    r"|\d[\d.,]*\s?(?:million|billion|thousand)?\s?(?:rupiah|dollars|riel|shillings|ringgit|euros|pounds))",
    re.I,
)


NEGATIONS = {"not", "never", "no", "without", "neither", "nor"}


def _negated(sentence: str, pos: int) -> bool:
    """True if a negation sits in the few words just before position pos ('was not convicted', 'At no time ... detained')."""
    before = HONORIFIC.sub(lambda m: m.group(1) + " ", sentence[:pos])
    before = re.split(r"[.!?][\u201d\"\u2019]?\s", before)[-1]
    return any(w.lower().strip(",;:()\u201c\u201d\"") in NEGATIONS for w in before.split()[-8:])


def names_defendant(sentence: str, names: list[str]) -> bool:
    """The sentence names the defendant: their full name, or Mr./Ms./Dr. plus part of the name.

    A bare name part is not enough: 'Kong' alone also names Kong Mas, a different person.
    """
    if mentions(sentence, full_name_keys(names)):
        return True
    parts = {t for n in names for t in re.findall(r"[A-Za-z\u00c0-\u024f'-]{4,}", n)}
    return any(re.search(rf"\b(?:Mr|Ms|Mrs|Dr|Prof)\.? (?:\w+ )?{re.escape(t)}\b", sentence, re.I) for t in parts)


def quantities(sentence: str, near: list[tuple[int, int]] | None = None, reach: int = 40) -> list[str]:
    """Durations and amounts exactly as written in the sentence ('five months', '2 years', '5 million rupiah').

    With near (character spans of a category's match), only quantities within
    `reach` characters of one of them are kept, so the 'two years' of a
    suspended sentence is not also reported as the length of a detention.
    """
    found = []
    for m in [*DURATION.finditer(sentence), *AMOUNT.finditer(sentence)]:
        if near is None or any(m.start() <= e + reach and m.end() >= b - reach for b, e in near):
            found.append(m.group(0).strip(" .,"))
    return found


def impact_evidence(pages: list[str], names: list[str], per_category: int = 6) -> dict[str, list[dict]]:
    """For each category, sentences that state it for the defendant.

    pages: text of each PDF page (page numbers are PDF pages, starting at 1).
    names: the defendants, from src.outcomes.defendants(title). A sentence
    counts only if it names the defendant (see names_defendant), so sentences
    about other people, and sentences with only a pronoun, are left out.
    """
    found: dict[str, list[dict]] = {c: [] for c in CATEGORIES}
    seen: set[tuple[str, str]] = set()
    for n, page in enumerate(pages, 1):
        for para in body_paragraphs(page, min_chars=20):
            for s in _split(para):
                if CITATION.search(s) or BOILERPLATE.search(s) or not names_defendant(s, names):
                    continue
                if HEDGE.search(s) or STATUTE.search(s):
                    continue
                for cat, pat in CATEGORIES.items():
                    if (cat, s) in seen or len(found[cat]) >= per_category:
                        continue
                    hits = [m for m in re.finditer(pat, s, re.I)
                            if not _in_quotes(s, m.start()) and not _negated(s, m.start())]
                    if not hits:
                        continue
                    seen.add((cat, s))
                    spans = [m.span() for m in hits]
                    found[cat].append({"sentence": s, "page": n, "quantities": quantities(s, spans)})
    return found


def has_impact(evidence: dict[str, list[dict]]) -> dict[str, bool]:
    return {c: bool(evidence.get(c)) for c in CATEGORIES}


def page_link(pdf_url: str, page) -> str:
    """Link to one page of a report's PDF (the page is a PDF page, not the printed number)."""
    return f"{pdf_url}#page={page}" if pdf_url and page != "" else ""


def case_row(rep: dict, names: list[str], evidence: dict[str, list[dict]], prev: dict | None = None) -> dict:
    """One row per case: yes/no for each category and, for each yes, the first sentence, its PDF page,
    any duration or amount exactly as written, and a link to that page.

    rep needs url, title, grade and pdf_url. People fill verified_by and notes; prev (the
    row from the last run) keeps what they filled in.
    """
    row = {"report_url": rep["url"], "case": rep["title"], "grade": rep.get("grade", ""),
           "defendants": "; ".join(names)}
    for cat in CATEGORIES:
        first = (evidence.get(cat) or [None])[0]
        row[cat] = "yes" if first else "no"
        row[f"{cat}_sentence"] = first["sentence"] if first else ""
        row[f"{cat}_page"] = first["page"] if first else ""
        row[f"{cat}_quantities"] = "; ".join(first["quantities"]) if first else ""
        row[f"{cat}_source_url"] = page_link(rep.get("pdf_url", ""), first["page"]) if first else ""
    prev = prev or {}
    row.update({f: prev.get(f, "") for f in HUMAN_FIELDS})
    return row


def evidence_rows(rep: dict, evidence: dict[str, list[dict]]) -> list[dict]:
    """Every evidence sentence for a case, one row each, for people checking the sheet."""
    return [
        {"report_url": rep["url"], "case": rep["title"], "category": cat, "pdf_page": it["page"],
         "quantities": "; ".join(it["quantities"]), "sentence": it["sentence"],
         "source_url": page_link(rep.get("pdf_url", ""), it["page"])}
        for cat, items in evidence.items() for it in items
    ]


def load_impacts(path: Path | None = None) -> dict[str, dict]:
    """The impacts sheet by report URL; empty if it hasn't been built."""
    path = path or IMPACTS_CSV
    if not path.exists():
        return {}
    with open(path, encoding="utf-8", newline="") as f:
        return {r["report_url"]: r for r in csv.DictReader(f)}


def is_confirmed(row: dict) -> bool:
    """Confirmed only when a person has filled verified_by."""
    return bool(str(row.get("verified_by", "")).strip())


def impact_lines(row: dict) -> list[dict]:
    """One entry per category found for a case: label, sentence, page, quantities and page link."""
    out = []
    for cat in CATEGORIES:
        if row.get(cat) != "yes":
            continue
        out.append({
            "category": cat, "label": LABELS[cat], "sentence": row.get(f"{cat}_sentence", ""),
            "page": row.get(f"{cat}_page", ""), "quantities": [q for q in row.get(f"{cat}_quantities", "").split("; ") if q],
            "url": row.get(f"{cat}_source_url", ""), "confirmed": is_confirmed(row),
        })
    return out


def impacts_for(report_url: str, impacts: dict[str, dict] | None = None) -> list[dict]:
    """impact_lines for one report, or [] if there is no sheet or no impact found."""
    impacts = load_impacts() if impacts is None else impacts
    row = impacts.get(report_url)
    return impact_lines(row) if row else []
