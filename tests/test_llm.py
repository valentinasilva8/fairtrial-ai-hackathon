"""Tests for src/llm.py. A fake client stands in for the API, so no key is needed."""

import json
from types import SimpleNamespace

import pytest

from src.llm import (
    ExtractionError,
    extract_case_fields,
    quote_in_text,
    to_case_inputs,
    verify_extraction,
)
from src.stress_test import LIKELY_BARRED, evaluate_case

TEXT = (
    "On September 22, 2021, Pandjaitan filed a complaint for criminal defamation against "
    "Azhar and Maulidiyanti. In the complaint, he alleged violations of Article 27(3) of the "
    "EIT Law. The Report described links between military figures and gold mining in Intan Jaya."
)

GOOD = {
    "complainant": {"value": "Pandjaitan", "quote": "Pandjaitan filed a complaint", "reasoning": "Named as filer."},
    "complainant_type": {"value": "public_official", "quote": "Pandjaitan filed a complaint", "reasoning": "A minister."},
    "article": {"value": ["27(3)"], "quote": "violations of Article 27(3) of the\nEIT Law", "reasoning": "Stated."},
    "public_interest": {"value": "true", "quote": "links between military figures and gold mining", "reasoning": "Alleged wrongdoing."},
    "harm_shown": {"value": "unknown", "quote": "", "reasoning": "Not discussed."},
}


class FakeClient:
    def __init__(self, payload=None, stop_reason="end_turn", text=None):
        body = text if text is not None else json.dumps(payload)
        self.response = SimpleNamespace(
            stop_reason=stop_reason,
            content=[SimpleNamespace(type="text", text=body)],
        )
        self.calls = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


def test_quote_matching_ignores_whitespace_case_and_curly_quotes():
    assert quote_in_text("ARTICLE 27(3) of the   EIT law", TEXT)
    assert quote_in_text("“hello”", 'He said "hello".')
    assert not quote_in_text("Article 28(2)", TEXT)
    assert not quote_in_text("", TEXT)


def test_supported_fields_are_verified():
    out = verify_extraction(GOOD, TEXT)
    assert out["complainant_type"]["verified"]
    assert out["article"]["verified"]
    assert out["complainant_type"]["value"] == "public_official"


def test_fabricated_quote_resets_field_to_unknown():
    raw = {**GOOD, "complainant_type": {"value": "company", "quote": "a company complained", "reasoning": "x"}}
    out = verify_extraction(raw, TEXT)
    assert out["complainant_type"]["value"] == "unknown"
    assert not out["complainant_type"]["verified"]
    assert "not found" in out["complainant_type"]["note"]


def test_unknown_fields_stay_unverified():
    out = verify_extraction(GOOD, TEXT)
    assert out["harm_shown"]["value"] == "unknown"
    assert not out["harm_shown"]["verified"]


def test_missing_fields_default_to_unknown():
    out = verify_extraction({}, TEXT)
    assert out["article"]["value"] == ["unknown"]
    assert not any(f["verified"] for f in out.values())


def test_extraction_feeds_the_rule_engine():
    case = to_case_inputs(verify_extraction(GOOD, TEXT))
    assert case["article"] == "27(3)"
    assert case["public_interest"] is True and case["harm_shown"] is False
    assert evaluate_case(case)["verdict"] == LIKELY_BARRED


def test_extract_case_fields_with_fake_client():
    client = FakeClient(GOOD)
    out = extract_case_fields(TEXT, client=client)
    assert out["complainant_type"]["verified"]
    call = client.calls[0]
    assert call["model"] == "claude-opus-5-5"
    assert call["output_config"]["format"]["type"] == "json_schema"
    assert TEXT in call["messages"][0]["content"]


def test_refusal_raises():
    with pytest.raises(ExtractionError):
        extract_case_fields(TEXT, client=FakeClient(GOOD, stop_reason="refusal"))


def test_unparseable_answer_raises():
    with pytest.raises(ExtractionError):
        extract_case_fields(TEXT, client=FakeClient(text="not json"))


def test_empty_text_rejected():
    with pytest.raises(ValueError):
        extract_case_fields("   ", client=FakeClient(GOOD))
