"""LLM helpers (Google Gemini, free tier).

extract_case_fields() asks Gemini to fill the stress-test inputs from a news
article or report passage, with a verbatim quote for each field. The quotes are
then checked against the text in code: a field whose quote isn't actually in
the passage is reset to "unknown" and marked unverified. The rule engine
(src/stress_test.py) never calls the LLM.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")  # GEMINI_API_KEY, if present

# gemini-flash-latest tracks Google's current Flash model, which is on the free tier.
# Note: on the free tier Google may use prompts to improve its products, so never send
# cases marked sensitive.
MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
# Tried in order when the model above is overloaded (503) on the free tier.
FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-flash-lite-latest"]

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


class LLMError(RuntimeError):
    """The model call failed, declined, or returned something unusable."""


ExtractionError = LLMError  # name used by the Stress Test page


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
    from google import genai

    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise LLMError("No API key found. Add GEMINI_API_KEY to .env.")
    return genai.Client(api_key=key)


def generate_json(system: str, user: str, schema: dict, client=None, temperature: float = 0.0) -> dict:
    """One Gemini call that must return JSON matching `schema`."""
    from google.genai import errors, types

    client = client or get_client()
    config = types.GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json",
        response_json_schema=schema,
        temperature=temperature,
    )
    response = None
    for model in [MODEL, *[m for m in FALLBACK_MODELS if m != MODEL]]:
        try:
            response = client.models.generate_content(model=model, contents=user, config=config)
            break
        except errors.ClientError as e:
            if e.code == 429:
                raise LLMError("Gemini free-tier rate limit reached. Wait a minute and try again.") from e
            if e.code in (400, 401, 403):
                raise LLMError("Gemini rejected the request. Check GEMINI_API_KEY in .env.") from e
            raise LLMError(f"Gemini API error {e.code}.") from e
        except errors.ServerError:
            continue  # overloaded: try the next model
        except OSError as e:
            raise LLMError("Could not reach the Gemini API. Check your connection.") from e
    if response is None:
        raise LLMError("Gemini is overloaded right now. Try again in a minute.")

    finish = str(response.candidates[0].finish_reason) if response.candidates else "NO_CANDIDATES"
    if "MAX_TOKENS" in finish:
        raise LLMError("The response was cut off; try a shorter passage.")
    if not response.text:
        raise LLMError(f"The model returned no answer ({finish}).")
    try:
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        raise LLMError(f"Could not parse the model's answer: {e}") from e


def extract_case_fields(text: str, client=None) -> dict:
    """Extract stress-test inputs from text with Gemini, then verify every quote."""
    if not text.strip():
        raise ValueError("No text provided.")
    raw = generate_json(SYSTEM_PROMPT, f"<text>\n{text}\n</text>", OUTPUT_SCHEMA, client=client)
    return verify_extraction(raw, text)
