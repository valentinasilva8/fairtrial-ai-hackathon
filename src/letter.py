"""Draft a submission to the UN Special Rapporteur on freedom of expression, with every sentence sourced.

1. build_sources() makes a numbered list of sources from the project's data:
   the case facts and timeline, the stress-test result, official pledges, and
   paragraphs from similar TrialWatch reports (with page links).
2. A draft is a list of sections, each a list of sentences, and every sentence
   names the source ids it relies on. Gemini writes it (generate_draft), or
   template_draft() builds a plain version from the same sources without an LLM.
3. validate() rejects any sentence with no source, an unknown source, or a
   quotation that isn't in the cited source. Nothing is used until a person approves.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.argument_bank import CATEGORY_LABELS, page_link
from src.llm import LLMError, generate_json

RECIPIENT = "Special Rapporteur on the promotion and protection of the right to freedom of opinion and expression"
SECTIONS = [
    "Summary",
    "The case",
    "The reform and how it applies",
    "International standards and TrialWatch's findings in similar cases",
    "Requested action",
]


class SensitiveCaseError(ValueError):
    """Sensitive cases are never used in briefs."""


@dataclass
class Source:
    id: str
    label: str
    text: str
    url: str = ""
    verified: bool = True


def _yes(v) -> bool:
    return str(v).strip().lower() in {"true", "1", "yes"}


def build_sources(case: dict, events: list[dict], stress: dict, promises: list[dict],
                  past: list[dict]) -> list[Source]:
    """past: [{"case", "report_url", "pdf_url", "outcome", "outcome_confirmed", "arguments": {cat: [para]}}]."""
    if _yes(case.get("sensitive")):
        raise SensitiveCaseError("This case is marked sensitive and can't be used in a brief.")
    cid = case["case_id"]
    src = [Source(
        f"case:{cid}", f"Case record: {case['name']}",
        f"{case['name']} ({case['role']}), prosecuted in Indonesia under the ITE (EIT) Law. Complainant: {case['complainant']} ({case['complainant_type']}). "
        f"Charged under: {case['article']}. Reported: {case['year_reported']}. "
        f"Outcome: {case['outcome']} — {case['outcome_detail']}",
        case.get("source", ""), _yes(case.get("verified")),
    )]
    for i, e in enumerate(events, 1):
        src.append(Source(f"event:{cid}:{i}", f"Timeline, {e['date']}", f"{e['date']}: {e['description']}",
                          e.get("source", ""), _yes(e.get("verified"))))
    src.append(Source(
        f"stress:{cid}", "Paper vs. Practice reform stress test (for lawyer review)",
        f"Verdict: {stress['verdict']}. " + " ".join(stress["reasons"]),
        "docs/stress_test_rules.md",
    ))
    for p in promises:
        src.append(Source(f"promise:{p['promise_id']}", f"Official pledge: {p['made_by']}",
                          f"{p['promise_text']} ({p['made_by']}, {p['date']}). Status: {p['status']}.",
                          p.get("source", ""), _yes(p.get("verified"))))
    for m in past:
        slug = m["report_url"].rstrip("/").rsplit("/", 1)[-1]
        outcome = f"{m['outcome']} ({'confirmed' if m['outcome_confirmed'] else 'unconfirmed'})"
        for cat, paras in m["arguments"].items():
            for para in paras:
                src.append(Source(
                    f"tw:{slug}:p{para['page']}",
                    f"TrialWatch report, {m['case']}, p. {para['page']} ({CATEGORY_LABELS[cat]}; outcome: {outcome})",
                    para["text"], page_link(m.get("pdf_url", ""), para["page"]) or m["report_url"],
                ))
    # de-duplicate ids (one paragraph can serve several categories)
    seen, out = set(), []
    for s in src:
        if s.id not in seen:
            seen.add(s.id)
            out.append(s)
    return out


QUOTE = re.compile(r"[“\"]([^”\"]{12,})[”\"]")


def _norm(s: str) -> str:
    """Words only, in order: ignores case, punctuation, brackets and spacing (e.g. "[T[he" -> "the")."""
    s = re.sub(r"[\[\]]", "", s.lower())
    return " ".join(re.findall(r"[a-z0-9]+", s))


def validate(draft: dict, sources: list[Source]) -> list[str]:
    """Problems with a draft; an empty list means every sentence is sourced."""
    by_id = {s.id: s for s in sources}
    errors = []
    sections = draft.get("sections", [])
    if not sections:
        return ["The draft has no sections."]
    for sec in sections:
        for n, sent in enumerate(sec.get("sentences", []), 1):
            where = f"{sec.get('heading', '?')} sentence {n}"
            ids = sent.get("sources", [])
            if not str(sent.get("text", "")).strip():
                errors.append(f"{where}: empty sentence.")
                continue
            if not ids:
                errors.append(f"{where}: no source cited.")
            unknown = [i for i in ids if i not in by_id]
            if unknown:
                errors.append(f"{where}: unknown source {', '.join(unknown)}.")
            for q in QUOTE.findall(sent["text"]):
                if not any(_norm(q) in _norm(by_id[i].text) for i in ids if i in by_id):
                    errors.append(f"{where}: quotation not found in the cited source: “{q[:60]}”.")
    return errors


def template_draft(sources: list[Source]) -> dict:
    """A plain, fully sourced draft built without an LLM."""
    case = sources[0]
    stress = next(s for s in sources if s.id.startswith("stress:"))
    events = [s for s in sources if s.id.startswith("event:")]
    promises = [s for s in sources if s.id.startswith("promise:")]
    tw = [s for s in sources if s.id.startswith("tw:")]
    return {"sections": [
        {"heading": "Summary", "sentences": [
            {"text": f"We write regarding the case of {case.label.split(': ', 1)[1]}.", "sources": [case.id]},
            {"text": f"Our rule check of Indonesia's reformed law gives this result: {stress.text}", "sources": [stress.id]},
        ]},
        {"heading": "The case", "sentences": [{"text": case.text, "sources": [case.id]}]
            + [{"text": e.text, "sources": [e.id]} for e in events]},
        {"heading": "The reform and how it applies", "sentences":
            [{"text": p.text, "sources": [p.id]} for p in promises]},
        {"heading": "International standards and TrialWatch's findings in similar cases", "sentences":
            [{"text": f"{s.label}: “{s.text[:300].rsplit(' ', 1)[0]}”", "sources": [s.id]} for s in tw]},
        {"heading": "Requested action", "sentences": [
            {"text": "We ask that you consider raising this case with the Government of Indonesia, "
                     "including whether the prosecution is consistent with the 2025 Constitutional Court ruling.",
             "sources": [stress.id] + [p.id for p in promises[:2]]},
        ]},
    ]}


DRAFT_SCHEMA = {
    "type": "object",
    "properties": {"sections": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "heading": {"type": "string", "enum": SECTIONS},
            "sentences": {"type": "array", "items": {
                "type": "object",
                "properties": {"text": {"type": "string"}, "sources": {"type": "array", "items": {"type": "string"}}},
                "required": ["text", "sources"],
            }},
        },
        "required": ["heading", "sentences"],
    }}},
    "required": ["sections"],
}

SYSTEM = f"""You draft a submission to the UN {RECIPIENT} for a human rights organisation's lawyers to review.

Rules:
- Use ONLY the numbered sources provided. Do not add facts, dates, names, numbers or legal claims that are not in them.
- Every sentence must list the ids of the sources it relies on in "sources".
- If you quote, copy the words exactly from the cited source and put them in quotation marks.
- Sections, in order: {", ".join(SECTIONS)}.
- In the international-standards section, explain how the arguments TrialWatch's experts made in similar past
  cases (legality and vagueness, legitimate aim, necessity and proportionality, overbreadth) apply to this case,
  naming the past case for each point. Say an outcome "followed", never that an argument "caused" it.
  Mention whether a past outcome is confirmed or unconfirmed when you rely on it.
- Describe the stress test as the authors' preliminary analysis for lawyer review, not a legal conclusion.
- Formal, factual tone. About 350 to 550 words."""


def _prompt(sources: list[Source], feedback: list[str]) -> str:
    lines = ["Sources:"]
    for s in sources:
        flag = "" if s.verified else " [unverified]"
        lines.append(f"[{s.id}] {s.label}{flag}\n{s.text}")
    if feedback:
        lines.append("\nYour previous draft was rejected for these reasons. Fix every one:\n- " + "\n- ".join(feedback))
    return "\n\n".join(lines)


def generate_draft(sources: list[Source], client=None, attempts: int = 3) -> tuple[dict, list[str]]:
    """Ask Gemini for a draft and re-ask with the problems until it validates. Returns (draft, problems)."""
    feedback: list[str] = []
    draft: dict = {}
    for _ in range(attempts):
        draft = generate_json(SYSTEM, _prompt(sources, feedback), DRAFT_SCHEMA, client=client, temperature=0.2)
        feedback = validate(draft, sources)
        if not feedback:
            return draft, []
    return draft, feedback


SUPPORT_SCHEMA = {
    "type": "object",
    "properties": {"checks": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "n": {"type": "integer"},
            "verdict": {"type": "string", "enum": ["supported", "partly supported", "not supported"]},
            "evidence": {"type": "string"},
            "reason": {"type": "string"},
        },
        "required": ["n", "verdict", "evidence", "reason"],
    }}},
    "required": ["checks"],
}

SUPPORT_SYSTEM = """You check a draft legal letter sentence by sentence. For each numbered sentence, decide
whether its cited sources state what the sentence says: "supported" (every claim is in the sources),
"partly supported" (some claims, or an inference beyond the sources), or "not supported".
Each source starts with a label (for TrialWatch reports: the case, page, argument category and the case outcome);
the label counts as part of the source. Sentences in the "Requested action" section are requests: check only that
the facts they rest on are in the sources.
Give "evidence": the exact words from the cited source that support it (empty if none), and a one-line reason.
Judge only against the cited sources, not your own knowledge."""


def sentences_of(draft: dict) -> list[dict]:
    """Flat list of the draft's sentences with their section."""
    return [{**sent, "heading": sec["heading"]} for sec in draft["sections"] for sent in sec["sentences"]]


def check_support(draft: dict, sources: list[Source], client=None) -> list[dict]:
    """Second pass: does each sentence's cited source actually say it? Evidence is checked verbatim."""
    by_id = {s.id: s for s in sources}
    sents = sentences_of(draft)
    blocks = []
    for n, sent in enumerate(sents, 1):
        cited = "\n".join(f"[{i}] {by_id[i].label}: {by_id[i].text}" for i in sent["sources"] if i in by_id)
        blocks.append(f"Sentence {n}: {sent['text']}\nCited sources:\n{cited}")
    result = generate_json(SUPPORT_SYSTEM, "\n\n".join(blocks), SUPPORT_SCHEMA, client=client)
    checks = {c["n"]: c for c in result.get("checks", [])}
    out = []
    for n, sent in enumerate(sents, 1):
        c = checks.get(n, {"verdict": "not checked", "evidence": "", "reason": "No answer for this sentence."})
        evidence = c.get("evidence", "")
        # The checker's evidence must itself be real text from a cited source.
        if c["verdict"] == "supported" and evidence and not any(
            _norm(evidence) in _norm(f"{by_id[i].label}: {by_id[i].text}") for i in sent["sources"] if i in by_id
        ):
            c = {**c, "verdict": "partly supported", "reason": "Quoted evidence not found in the source. " + c["reason"]}
        out.append({"n": n, "text": sent["text"], "heading": sent["heading"], **c})
    return out


def render(draft: dict, sources: list[Source], case_name: str) -> str:
    """Markdown letter with numbered citations and a source list."""
    order: list[str] = []
    for sec in draft["sections"]:
        for sent in sec["sentences"]:
            for i in sent["sources"]:
                if i not in order:
                    order.append(i)
    num = {i: n for n, i in enumerate(order, 1)}
    by_id = {s.id: s for s in sources}
    out = [f"**To:** {RECIPIENT}", f"**Re:** {case_name}", "",
           "*Draft for lawyer review. Not to be sent until approved.*", ""]
    for sec in draft["sections"]:
        out.append(f"### {sec['heading']}")
        out.append(" ".join(
            f"{s['text']} " + "".join(f"[{num[i]}]" for i in s["sources"] if i in num) for s in sec["sentences"]
        ))
        out.append("")
    out.append("### Sources")
    for i in order:
        s = by_id.get(i)
        if s:
            tag = "" if s.verified else " (unverified)"
            out.append(f"{num[i]}. {s.label}{tag}" + (f" — {s.url}" if s.url else ""))
    return "\n".join(out)


__all__ = ["LLMError", "SensitiveCaseError", "build_sources", "check_support", "generate_draft", "render",
           "sentences_of", "template_draft", "validate"]
