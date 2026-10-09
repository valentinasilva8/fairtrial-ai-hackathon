"""LLM helpers.

extract_case_fields() asks Claude to fill the stress-test inputs from a news
article or report passage, with a verbatim quote for each field. The quotes are
then checked against the text in code: a field whose quote isn't actually in
the passage is reset to "unknown" and marked unverified. The rule engine
(src/stress_test.py) never calls the LLM.
"""

from __future__ import annotations

import json
import re

from dotenv import load_dotenv

load_dotenv()  # ANTHROPIC_API_KEY from .env, if present

MODEL = "claude-opus-5-5"

COMPLAINANT_TYPES = [
    "individual_victim", "public_official", "government_body", "company",
    "group", "representative", "police", "unknown",
]
ARTICLES = ["27(3)", "27A", "28(2)", "hoax", "other", "unknown"]
TRI_STATE = ["true", "false", "unknown"]

FIELDS = ["complainant", "complainant_type", "article", "public_interest", "harm_shown"]

SYSTEM_PROMPT = """You extract facts about a speech prosecution in Indonesia from a passage of text, \
to fill the inputs of a rule check that lawyers will review. You never decide the legal outcome.

Fields:
- complainant: who filed the police report or complaint, as named in the text.
- complainant_type: one of individual_victim (a person complaining about speech about themselves), \
public_official, government_body, company, group (several people or an association), \
representative (a lawyer or agent filing for the alleged victim), police, unknown.
- article: the charges, as a list from 27(3) (ITE defamation), 27A (new defamation article), \
28(2) (ITE hate speech), hoax (Law 1/1946 Arts. 14/15 false news), other, unknown.
- public_interest: "true" if the speech exposed alleged wrongdoing or a matter of public concern \
(corruption, environment, labor abuse, human rights); "false" if clearly not; otherwise "unknown".
- harm_shown: "true" only if the text shows real, imminent harm caused by the speech (violence, a threat), \
not just offence or hurt feelings; "false" if the text shows the speech caused no such harm \
or only offence; otherwise "unknown".

For every field give:
- value
- quote: a short passage copied character for character from the text that supports the value. \
Do not paraphrase, translate or join separate sentences. If no passage supports a value, \
set the value to "unknown" (article: ["unknown"]) and the quote to "".
- reasoning: one sentence on how the quote supports the value.

Use only the text provided. Do not use outside knowledge about the people or the case."""


def _field_schema(value_schema: dict) -> dict:
    return {
        "type": "object",
        "properties": {
            "value": value_schema,
            "quote": {"type": "string"},
            "reasoning": {"type": "string"},
        },
        "required": ["value", "quote", "reasoning"],
        "additionalProperties": False,
    }


OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "complainant": _field_schema({"type": "string"}),
        "complainant_type": _field_schema({"type": "string", "enum": COMPLAINANT_TYPES}),
        "article": _field_schema({"type": "array", "items": {"type": "string", "enum": ARTICLES}}),
        "public_interest": _field_schema({"type": "string", "enum": TRI_STATE}),
        "harm_shown": _field_schema({"type": "string", "enum": TRI_STATE}),
    },
    "required": FIELDS,
    "additionalProperties": False,
}


class ExtractionError(RuntimeError):
    """The model declined or returned something unusable."""


def _normalize(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip().lower()


def quote_in_text(quote: str, text: str) -> bool:
    """True if the quote appears in the text (ignoring case, whitespace and curly quotes)."""
    q = _normalize(quote)
    return bool(q) and q in _normalize(text)


def _unknown_value(field: str):
    return ["unknown"] if field == "article" else "unknown"


def verify_extraction(raw: dict, text: str) -> dict:
    """Check each field's quote against the source text.

    Returns {field: {value, quote, reasoning, verified, note}}. A field is
    verified only if its value is known and its quote is found verbatim in the
    text; a field with an unsupported quote is reset to unknown.
    """
    out = {}
    for field in FIELDS:
        item = raw.get(field) or {}
        value = item.get("value", _unknown_value(field))
        quote = str(item.get("quote", "")).strip()
        is_unknown = value in ("unknown", ["unknown"], [], "")
        entry = {"value": value, "quote": quote, "reasoning": item.get("reasoning", ""),
                 "verified": False, "note": ""}
        if is_unknown:
            entry["value"] = _unknown_value(field)
            entry["note"] = "No supporting passage found."
        elif not quote_in_text(quote, text):
            entry["value"] = _unknown_value(field)
            entry["note"] = "Quote not found in the text — value discarded."
        else:
            entry["verified"] = True
        out[field] = entry
    return out


def to_case_inputs(fields: dict) -> dict:
    """Turn verified extraction fields into a row the rule engine accepts."""
    return {
        "complainant": fields["complainant"]["value"],
        "complainant_type": fields["complainant_type"]["value"],
        "article": "; ".join(fields["article"]["value"]),
        "public_interest": fields["public_interest"]["value"] == "true",
        "harm_shown": fields["harm_shown"]["value"] == "true",
    }


def get_client():
    import anthropic

    return anthropic.Anthropic()


def _create(client, text: str):
    return client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={
            "effort": "medium",
            "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
        },
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"<text>\n{text}\n</text>"}],
    )


def extract_case_fields(text: str, client=None) -> dict:
    """Extract stress-test inputs from text with Claude, then verify every quote."""
    import anthropic

    if not text.strip():
        raise ValueError("No text provided.")
    client = client or get_client()
    try:
        response = _create(client, text)
    except TypeError as e:  # raised by the SDK when no credentials are configured
        raise ExtractionError("No API key found. Add ANTHROPIC_API_KEY to .env.") from e
    except anthropic.AuthenticationError as e:
        raise ExtractionError("The API key was rejected. Check ANTHROPIC_API_KEY in .env.") from e
    except anthropic.APIConnectionError as e:
        raise ExtractionError("Could not reach the Anthropic API. Check your connection.") from e
    except anthropic.APIStatusError as e:
        raise ExtractionError(f"Anthropic API error {e.status_code}. Try again.") from e

    if response.stop_reason == "refusal":
        raise ExtractionError("The model declined to process this text.")
    if response.stop_reason == "max_tokens":
        raise ExtractionError("The response was cut off; try a shorter passage.")
    body = next((b.text for b in response.content if b.type == "text"), "")
    try:
        raw = json.loads(body)
    except json.JSONDecodeError as e:
        raise ExtractionError(f"Could not parse the model's answer: {e}") from e
    return verify_extraction(raw, text)
