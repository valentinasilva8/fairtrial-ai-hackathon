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
        r"\bfined\b|\bfines\b|\ba fine\b|\bfine of\b|\d[\d,.]*\s+(?:\w+\s+)?fine\b|travel ban|\bpassport (?:was |were )?(?:confiscated|seized|revoked|withheld)"
        r"|\bassets? (?:were |was )?(?:frozen|seized|confiscated)|\bconfiscated\b|\b(?:seizure|confiscation) of\b"
        r"|\b(?:barred|banned|prohibited) from\b|\blicen[cs]e (?:was |were )?(?:revoked|suspended)\b"
        r"|\bstripped of\b|\bdisqualified\b|\bprobation\b|\bhouse arrest\b|\bcurfew\b"
    ),
    "prolonged_proceedings": (
        r"\bremained (?:a )?suspect\b|\bsuspect for\b|\bunder investigation for\b"
        r"|\b(?:prolonged|protracted|lengthy|undue) (?:proceedings?|investigation|trial|pre-?trial)\b"
        r"|\bdelays? (?:in|of) (?:the )?(?:trial|proceedings?|investigation|prosecution|case|hearings?|verdict|judgment|ruling)\b"
        r"|\bdelays? in bringing\b.{0,60}?\bto trial\b"
        r"|\b(?:trial|proceedings?|investigation|case|hearings?|verdict|judgment|ruling) (?:was |were |has been |have been )?(?:\w+ )?delayed\b"
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

# Sentences that are not statements of fact about the defendant: conditionals, hypotheticals
# and predictions ("If the conviction is upheld, he will be barred ..."), and the penalty a statute
# provides for, which is not the sentence imposed.
HEDGE = re.compile(r"(?i:\b(?:if|would|could|might|whether|unless)\b)|\b(?:may|will)\b")
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
    r"(?:(?:(?:HK|US|AU|NZ|S)\s?)?\$|Rp\.?|IDR|USD|EUR|GBP|RM|UGX|KHR|RUB)\s?\d[\d.,]*(?:\s?(?:million|billion|thousand))?"
    r"|\d[\d.,]*\s?(?:million|billion|thousand)?\s?(?:rupiah|dollars?|riels?|shillings?|ringgit|euros?|pounds?|rubles?|roubles?|dirhams?)\b",
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


# A number that comes before its category word must be right next to it ("9 months in pretrial detention"),
# so that "after a one-day trial ... was convicted" does not give the conviction a one-day length.
FOLLOWING_REACH = 25
CLAUSE_BREAK = re.compile(r"[;\u2014\u2013()]|\s-\s|[.!?]\s")


def _quantity_spans(sentence: str) -> list[tuple[int, int, str]]:
    return sorted((m.start(), m.end(), m.group(0).strip(" .,")) for m in [*DURATION.finditer(sentence), *AMOUNT.finditer(sentence)])


def quantities(sentence: str) -> list[str]:
    """Every duration and amount in the sentence, exactly as written ('five months', '2 years', '5 million rupiah')."""
    return [t for _, _, t in _quantity_spans(sentence)]


def assign_quantities(sentence: str, spans_by_category: dict[str, list[tuple[int, int]]], reach: int = 60) -> dict[str, list[str]]:
    """Give each number to one category, in the same clause.

    A number belongs to the category word it is part of ("two years' imprisonment"); otherwise to the nearest
    category word *before* it ("sentenced to 18 months", "fined 3,000,000 riels", "detained for two days");
    otherwise to the nearest one after it ("9 months in pretrial detention"). A dash or bracket ends the
    clause, so "sentenced to nine years - more than the seven to eight years recommended" keeps only the
    first. A number with no category within `reach` characters is left out; ties go to every tied category.
    """
    out: dict[str, list[str]] = {c: [] for c in spans_by_category}
    for qs, qe, text in _quantity_spans(sentence):
        best, owners = None, []
        for cat, spans in spans_by_category.items():
            for b, e in spans:
                if qs < e and qe > b:
                    rank, between = (0, 0), ""
                elif e <= qs:
                    rank, between = (1, qs - e), sentence[e:qs]
                else:
                    rank, between = (2, b - qe), sentence[qe:b]
                limit = reach if rank[0] < 2 else FOLLOWING_REACH
                if rank[1] > limit or CLAUSE_BREAK.search(HONORIFIC.sub(lambda m: m.group(1) + " ", between)):
                    continue
                if best is None or rank < best:
                    best, owners = rank, [cat]
                elif rank == best and cat not in owners:
                    owners.append(cat)
        for cat in owners:
            out[cat].append(text)
    return out


def usable(sentence: str) -> bool:
    """False for citation text, the grading annex, hypotheticals and predictions, and statutory penalty ranges."""
    return not (CITATION.search(sentence) or BOILERPLATE.search(sentence) or HEDGE.search(sentence)
                or STATUTE.search(sentence))


def category_hits(sentence: str, category: str) -> list[re.Match]:
    """Matches of the category's pattern that are not someone else's quoted words and not negated."""
    return [m for m in re.finditer(CATEGORIES[category], sentence, re.I)
            if not _in_quotes(sentence, m.start()) and not _negated(sentence, m.start())]


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
                if not usable(s) or not names_defendant(s, names):
                    continue
                hits_by_cat = {c: category_hits(s, c) for c in CATEGORIES}
                spans_by_cat = {c: [m.span() for m in h] for c, h in hits_by_cat.items() if h}
                numbers = assign_quantities(s, spans_by_cat)
                for cat in spans_by_cat:
                    if (cat, s) in seen or len(found[cat]) >= per_category:
                        continue
                    seen.add((cat, s))
                    found[cat].append({"sentence": s, "page": n, "quantities": numbers[cat]})
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


def impact_markdown(lines: list[dict]) -> list[str]:
    """Markdown bullets for the lines from impact_lines(): label, status, any number as written, the sentence, a page link."""
    out = []
    for ln in lines:
        status = "confirmed" if ln["confirmed"] else "unconfirmed"
        qty = f" ({', '.join(ln['quantities'])})" if ln["quantities"] else ""
        link = f" · [page {ln['page']}]({ln['url']})" if ln["url"] else f" · page {ln['page']}"
        out.append(f"- **{ln['label']}**{qty} · *{status}* — {ln['sentence']}{link}")
    return out

