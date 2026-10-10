"""Parse TrialWatch reports (CFJ PDFs) into grades, outcomes and tagged arguments.

Deterministic only: text from pdftotext, then regular expressions. No LLM.
Every value keeps the source text it came from, so it can be checked.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

# Argument categories. The first four follow the UN Human Rights Committee's
# three-part test for restrictions on expression (General Comment No. 34),
# which TrialWatch fairness reports apply.
CATEGORIES = {
    # The five argument labels the mentor asked for, from the UN Human Rights Committee's
    # test for restrictions on expression (General Comment No. 34), which TrialWatch reports apply.
    "legality": r"\blegality\b|prescribed by law|provided by law|legal certainty|nullum crimen",
    "vagueness": r"\bvague|insufficiently precise|sufficient precision|imprecis|unfettered discretion|unbounded discretion|ill-defined",
    "broadness": r"overbroad|overly broad|over-broad|broad swath|broadly (?:worded|defined|formulated)|sweeping",
    "necessity": r"\bnecessity\b|necessary in a democratic society|necessary to achieve|achieved in other ways",
    "proportionality": r"proportional|least intrusive|imprisonment is never|severity of the (?:penalty|sentence|sanction)",
    # Other recurring points, shown after the five.
    "legitimate_aim": r"legitimate (aim|objective|purpose)",
    "pretrial_detention": r"pre-?trial detention",
    "fair_trial": r"right to (counsel|a fair|be presumed|adequate time)|presumption of innocence|equality of arms|independent and impartial",
}

GRADE_PATTERNS = [
    re.compile(r"^\s*GRADE\s*:?\s*([ABCDF])\b", re.M),
    re.compile(r"assigned (?:this|the|these) (?:trials?|proceedings?)\s+a\s+[Gg]rade\s+of\s+[“\"]?([ABCDF])\b"),
    re.compile(r"\b[Gg]rade:\s*([ABCDF])\b"),
    re.compile(r"grade of [“\"]([ABCDF])[”\"]"),
]

# Who wrote the analysis: fairness reports name a TrialWatch expert, partner staff or a law firm.
GRADE_ASSIGN = re.compile(r"assigned (?:this|these|the) (?:trials?|proceedings?) a [Gg]rade")
AUTHOR_FALLBACKS = [
    (re.compile(r"Staff (?:at|of) the American Bar Association(?:[’']s)?(?: \(ABA\))? Center for Human Rights(?: \(Center\))? drafted this report"),
     "ABA Center for Human Rights staff"),
    (re.compile(r"This report was prepared by ([^.]{5,200}?)(?:\.|$)"), None),
    (re.compile(r"The TrialWatch initiative drafted this report"), "the TrialWatch initiative"),
    (re.compile(r"This report was authored by a member of the TrialWatch Experts? Panel"),
     "a member of the TrialWatch Experts Panel (not named)"),
]
NAME_STOP = re.compile(r",| who (?:is|are) | assigned |\s+(?:a|and)\s+member", re.I)


def find_author(text: str) -> tuple[str, str]:
    """(author, the sentence it was read from), or ("", "")."""
    flat = flatten(text)
    m = GRADE_ASSIGN.search(flat)
    if m:
        before = flat[max(0, m.start() - 400):m.start()]
        before = re.split(r"SUMMARY|(?<!\b[A-Z])\.\s", before)[-1].strip()  # keep "Hannah R. Garry"
        name = NAME_STOP.split(before, maxsplit=1)[0].strip(" :-")
        name = re.sub(r"^(?:\d+\s+|-\s*)+", "", name)
        name = re.sub(r"^TrialWatch Expert\s+", "", name)
        name = re.sub(r"\bStaff\b", "staff", name)
        if 3 <= len(name) <= 90 and name.lower() not in {"the authors", "the author"}:
            return name, flatten(before + " " + m.group(0))[:300]
    for pat, label in AUTHOR_FALLBACKS:
        m = pat.search(flat)
        if m:
            return (label or m.group(1).strip()), m.group(0)[:300]
    return "", ""


HRC_DECISION = re.compile(r"CCPR/C/\d+/D/\d+/\d{4}")
FOOTNOTE_START = re.compile(r"^\s*\d{1,3}\s+\S.{15,}")  # "203 U.N. General Assembly, ..."

TRIAL_URL = re.compile(r"-v-|-vs-|the-case-of")


def pdf_pages(pdf: Path) -> list[str]:
    """Text of each page (requires poppler's pdftotext)."""
    out = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True)
    return out.stdout.split("\f")


def flatten(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def find_grade(text: str) -> tuple[str, str]:
    """Return (grade, source snippet) or ("", "")."""
    flat = flatten(text)
    for pat in GRADE_PATTERNS:
        m = pat.search(text if pat.flags & re.M else flat)
        if m:
            return m.group(1), flatten(m.group(0))
    return "", ""


def hrc_decisions(text: str) -> list[str]:
    """UN Human Rights Committee decision symbols cited, e.g. CCPR/C/64/D/574/1994."""
    return sorted(set(HRC_DECISION.findall(flatten(text))))


def tag(text: str) -> list[str]:
    return [c for c, pat in CATEGORIES.items() if re.search(pat, text, re.I)]


def body_paragraphs(page: str, min_chars: int = 120) -> list[str]:
    """Body paragraphs of one page, with the footnote block at the bottom dropped."""
    lines = page.splitlines()
    cut = len(lines)
    for i, line in enumerate(lines):
        if i > len(lines) // 3 and FOOTNOTE_START.match(line):
            cut = i
            break
    paras = [flatten(p) for p in re.split(r"\n\s*\n", "\n".join(lines[:cut]))]
    return [p for p in paras if len(p) >= min_chars]


def extract_arguments(pages: list[str]) -> list[dict]:
    """Tagged paragraphs with their page number and verbatim text."""
    out = []
    for n, page in enumerate(pages, 1):
        for para in body_paragraphs(page):
            cats = tag(para)
            if cats:
                out.append({"page": n, "categories": cats, "text": para})
    return out


def is_trial_report(url: str) -> bool:
    return bool(TRIAL_URL.search(url))


def summarize_report(url: str, title: str, pages: list[str]) -> dict:
    """One metadata row per report: grade (with source), category coverage, UN decisions cited."""
    text = "\n".join(pages)
    grade, grade_source = find_grade(text)
    author, author_source = find_author(text)
    row = {
        "url": url,
        "title": title,
        "kind": "trial" if grade or is_trial_report(url) else "thematic",
        "pages": len(pages),
        "grade": grade,
        "grade_source": grade_source,
        "author": author,
        "author_source": author_source,
        "freedom_of_expression": bool(re.search(r"Article 19", text)),
        "hrc_decisions_cited": len(hrc_decisions(text)),
    }
    for c, pat in CATEGORIES.items():
        row[c] = len(re.findall(pat, text, re.I))
    return row
