"""Tests for the FairTrial guide. A fake client stands in for Gemini, so no key is needed."""

import json
import re
from types import SimpleNamespace

import pytest

from src.assistant import ask, guides, knowledge, questions, validate_answer
from src.llm import LLMError

HAN = re.compile(r"[㐀-䶿一-鿿＀-￯　-〿]")


class FakeClient:
    def __init__(self, payload):
        self.response = SimpleNamespace(text=json.dumps(payload),
                                        candidates=[SimpleNamespace(finish_reason="FinishReason.STOP")])
        self.models = SimpleNamespace(generate_content=self._generate)
        self.calls = []

    def _generate(self, model, contents, config):
        self.calls.append(contents)
        return self.response


def reading(source_id):
    return next(s for s in knowledge() if s["id"] == source_id)


def test_library_loads_guides_and_readings():
    ids = [s["id"] for s in knowledge()]
    assert len(ids) == len(set(ids))
    assert len(guides()) >= 6 and len(questions()) >= 3
    readings = [s for s in knowledge() if s["kind"] == "reading"]
    assert len(readings) == 8
    assert all(r["text"] and r["title"] and r["url"].startswith("https://") for r in readings)
    assert "Indonesia" in reading("reading-indonesia")["title"]


def test_everything_shown_is_english():
    texts = [s["title"] + s["text"] for s in knowledge()] + questions()
    assert not [t for t in texts if HAN.search(t)]


def test_checked_answer_is_returned_with_evidence():
    src = reading("reading-legality")
    quote = src["text"][20:90]
    client = FakeClient({"answer": "Laws must be precise [reading-legality].",
                         "evidence": [{"source_id": "reading-legality", "quote": quote}]})
    answer = ask("What is legality?", [], "Start here", client=client)
    assert answer["evidence"] == [{"source_id": "reading-legality", "quote": quote}]
    sent = json.loads(client.calls[0])
    assert sent["question"] == "What is legality?" and sent["current_page"] == "Start here"


def test_invented_quote_is_rejected():
    with pytest.raises(LLMError):
        validate_answer({"answer": "x [reading-legality]",
                         "evidence": [{"source_id": "reading-legality", "quote": "words that are not there"}]},
                        knowledge())


def test_unknown_source_and_uncited_claim_are_rejected():
    with pytest.raises(LLMError):
        validate_answer({"answer": "x", "evidence": [{"source_id": "reading-nope", "quote": "x"}]}, knowledge())
    with pytest.raises(LLMError):
        validate_answer({"answer": "Says so [reading-vagueness].", "evidence": []}, knowledge())


def test_greeting_needs_no_evidence():
    assert validate_answer({"answer": "Hello! How can I help?", "evidence": []}, knowledge())["evidence"] == []


def test_empty_or_long_question_is_rejected():
    with pytest.raises(LLMError):
        ask("   ", [], "Start here", client=FakeClient({}))
    with pytest.raises(LLMError):
        ask("x" * 2001, [], "Start here", client=FakeClient({}))
