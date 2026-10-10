"""Tests for src/letter.py with made-up data and a fake Gemini client."""

import json
from types import SimpleNamespace

import pytest

from src.letter import SensitiveCaseError, build_sources, generate_draft, render, template_draft, validate

CASE = {"case_id": "x", "name": "A. Person", "role": "journalist", "complainant": "A minister",
        "complainant_type": "public_official", "article": "27(3)", "year_reported": "2021",
        "outcome": "acquitted", "outcome_detail": "Acquitted in 2024", "source": "http://example.org/case",
        "verified": True, "sensitive": False}
EVENTS = [{"date": "2021-09", "description": "Reported to police", "source": "http://example.org/e", "verified": False}]
STRESS = {"verdict": "LIKELY BARRED", "reasons": ["R1: defamation complaint by a public official."]}
PROMISES = [{"promise_id": "p2", "made_by": "Constitutional Court", "promise_text": "Only individuals can be victims",
             "date": "2025-04", "status": "no_evidence_yet", "source": "http://example.org/p", "verified": True}]
PAST = [{"case": "Thailand v. B", "report_url": "https://cfj.org/reports/thailand-v-b/", "pdf_url": "https://cfj.org/b.pdf",
         "outcome": "good", "outcome_confirmed": False,
         "arguments": {"legality_vagueness": [{"page": 19, "text": "Restrictions must be prescribed by law and proportionate."}]},
         "impacts": [{"category": "pretrial_detention", "label": "Detention", "page": 17, "quantities": ["five months"],
                      "sentence": "Mr. B was detained for five months prior to trial.",
                      "url": "https://cfj.org/b.pdf#page=17", "confirmed": False}]}]


def sources():
    return build_sources(CASE, EVENTS, STRESS, PROMISES, PAST)


def test_sources_cover_all_inputs():
    ids = [s.id for s in sources()]
    assert ids == ["case:x", "event:x:1", "stress:x", "promise:p2", "tw:thailand-v-b:p19",
                   "impact:thailand-v-b:pretrial_detention"]
    tw = next(s for s in sources() if s.id.startswith("tw:"))
    assert tw.url == "https://cfj.org/b.pdf#page=19" and "unconfirmed" in tw.label


def test_impact_source_keeps_the_sentence_and_is_unverified_until_confirmed():
    imp = next(s for s in sources() if s.id.startswith("impact:"))
    assert imp.text == "Mr. B was detained for five months prior to trial."
    assert imp.url == "https://cfj.org/b.pdf#page=17" and "Detention" in imp.label and "unconfirmed" in imp.label
    assert imp.verified is False
    confirmed = [{**PAST[0], "impacts": [{**PAST[0]["impacts"][0], "confirmed": True}]}]
    imp = next(s for s in build_sources(CASE, EVENTS, STRESS, PROMISES, confirmed) if s.id.startswith("impact:"))
    assert imp.verified is True and "confirmed" in imp.label and "unconfirmed" not in imp.label


def test_a_past_case_without_impacts_still_works():
    past = [{k: v for k, v in PAST[0].items() if k != "impacts"}]
    ids = [s.id for s in build_sources(CASE, EVENTS, STRESS, PROMISES, past)]
    assert not any(i.startswith("impact:") for i in ids)


def test_a_draft_may_cite_an_impact_source_and_quote_it_exactly():
    ok = {"sections": [{"heading": "Summary", "sentences": [
        {"text": "In that case, the report records that “Mr. B was detained for five months prior to trial”.",
         "sources": ["impact:thailand-v-b:pretrial_detention"]}]}]}
    changed = {"sections": [{"heading": "Summary", "sentences": [
        {"text": "In that case, the report records that “Mr. B was detained for six months prior to trial”.",
         "sources": ["impact:thailand-v-b:pretrial_detention"]}]}]}
    assert validate(ok, sources()) == []
    assert any("quotation not found" in e for e in validate(changed, sources()))


def test_sensitive_case_blocked():
    with pytest.raises(SensitiveCaseError):
        build_sources({**CASE, "sensitive": True}, [], STRESS, [], [])


def test_template_draft_is_fully_sourced():
    assert validate(template_draft(sources()), sources()) == []


def test_validate_catches_unsourced_unknown_and_invented_quotes():
    draft = {"sections": [{"heading": "Summary", "sentences": [
        {"text": "No source here.", "sources": []},
        {"text": "Made-up source.", "sources": ["case:nope"]},
        {"text": "TrialWatch said “restrictions are always fine in every case”.", "sources": ["tw:thailand-v-b:p19"]},
        {"text": "TrialWatch said “prescribed by law and proportionate”.", "sources": ["tw:thailand-v-b:p19"]},
    ]}]}
    errors = validate(draft, sources())
    assert len(errors) == 3
    assert "no source" in errors[0] and "unknown source" in errors[1] and "quotation not found" in errors[2]


class FakeGemini:
    def __init__(self, drafts):
        self.drafts, self.prompts = list(drafts), []
        self.models = SimpleNamespace(generate_content=self._gen)

    def _gen(self, **kw):
        self.prompts.append(kw["contents"])
        return SimpleNamespace(text=json.dumps(self.drafts.pop(0)), candidates=[SimpleNamespace(finish_reason="STOP")])


def test_generate_draft_retries_with_feedback():
    bad = {"sections": [{"heading": "Summary", "sentences": [{"text": "Unsourced.", "sources": []}]}]}
    good = template_draft(sources())
    client = FakeGemini([bad, good])
    draft, problems = generate_draft(sources(), client=client)
    assert problems == [] and draft == good
    assert "rejected" in client.prompts[1] and "no source" in client.prompts[1]


def test_generate_draft_reports_problems_after_last_attempt():
    bad = {"sections": [{"heading": "Summary", "sentences": [{"text": "Unsourced.", "sources": []}]}]}
    draft, problems = generate_draft(sources(), client=FakeGemini([bad, bad, bad]))
    assert problems


def test_render_numbers_citations_and_lists_sources():
    md = render(template_draft(sources()), sources(), "A. Person")
    assert "Draft for lawyer review" in md
    assert "[1]" in md and "### Sources" in md
    assert "(unverified)" in md  # the event source is unverified


def test_check_support_downgrades_fake_evidence():
    from src.letter import check_support, sentences_of

    draft = template_draft(sources())
    n = len(sentences_of(draft))
    checks = [{"n": i, "verdict": "supported", "evidence": "", "reason": "ok"} for i in range(1, n + 1)]
    checks[0] = {"n": 1, "verdict": "supported", "evidence": "words that are nowhere in the source", "reason": "ok"}
    result = check_support(draft, sources(), client=FakeGemini([{"checks": checks}]))
    assert len(result) == n
    assert result[0]["verdict"] == "partly supported"
    assert result[1]["verdict"] == "supported"


def test_check_support_accepts_evidence_in_pieces():
    from src.letter import check_support, sentences_of

    draft = template_draft(sources())
    n = len(sentences_of(draft))
    checks = [{"n": i, "verdict": "supported", "evidence": "", "reason": "ok"} for i in range(1, n + 1)]
    checks[0] = {"n": 1, "verdict": "supported", "evidence": "A. Person … charged under: 27(3)", "reason": "ok"}
    result = check_support(draft, sources(), client=FakeGemini([{"checks": checks}]))
    assert result[0]["verdict"] == "supported"


def test_quote_check_ignores_punctuation_but_not_words():
    from src.letter import Source

    src = [Source("tw:a:p1", "TrialWatch report", "[T[he subjective character of many defamation laws, their overly broad scope")]
    ok = {"sections": [{"heading": "Summary", "sentences": [
        {"text": "It noted “the subjective character of many defamation laws their overly broad scope”.", "sources": ["tw:a:p1"]}]}]}
    changed = {"sections": [{"heading": "Summary", "sentences": [
        {"text": "It noted “the subjective nature of many defamation laws”.", "sources": ["tw:a:p1"]}]}]}
    assert validate(ok, src) == []
    assert validate(changed, src)
