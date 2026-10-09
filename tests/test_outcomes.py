"""Tests for src/outcomes.py, using made-up sentences."""

from src.outcomes import (
    defendants,
    full_name_keys,
    mentions,
    name_tokens,
    outcome_evidence,
    signals,
    suggest_label,
)


def test_defendants_from_titles():
    assert defendants("Turkey v. Veysel Ok") == ["Veysel Ok"]
    assert defendants("Cambodia vs. Uon Chhin and Yeang Sothearin") == ["Uon Chhin", "Yeang Sothearin"]
    assert defendants("Poland vs. A Podlesna, Anna Prus, and Joanna Gzyra") == ["A Podlesna", "Anna Prus", "Joanna Gzyra"]
    assert defendants("Kazakhstan v. Askhat Zheksebaev et al.") == ["Askhat Zheksebaev"]
    assert defendants("CFJ Fairness Report: Abzas Media") == ["Abzas Media"]
    assert defendants("Cambodia v. Theary Seng (September 2022)") == ["Theary Seng"]
    assert defendants("15 Post-Election Trials: A Window into Courts in Belarus") == []


def test_full_name_keys_handle_accents_and_middle_names():
    keys = full_name_keys(["Ahmet Tuna Altınel"])
    assert "ahmet tuna altinel" in keys and "ahmet altinel" in keys


def test_full_name_match_does_not_confuse_shared_surnames():
    keys = full_name_keys(["Kenia Hernandez"])
    assert mentions("Kenia Hernández was released.", keys)
    assert not mentions("Evelyn Hernandez was acquitted.", keys)


def test_signals():
    assert signals("She was acquitted on appeal.") == (["acquitted"], [])
    assert signals("He was convicted and sentenced to two years.")[1] == ["convicted", "sentenced"]
    assert "charges dropped" in signals("Prosecutors later dropped the charges against him.")[0]
    assert "charges dropped" in signals("The charges were dropped.")[0]
    assert "conviction overturned" in signals("The appeals court overturned the conviction.")[0]


def test_evidence_requires_defendant_name():
    text = ("The court acquitted another defendant in 2020. Chargui was convicted and sentenced to six months. "
            "Unrelated sentence about the weather in the capital city.")
    ev = outcome_evidence(text, name_tokens(["Emna Chargui"]))
    assert [e["sentence"] for e in ev] == ["Chargui was convicted and sentenced to six months."]


def test_suggest_label_uses_latest_evidence():
    convicted = {"good": [], "not_good": ["convicted"]}
    released = {"good": ["released"], "not_good": []}
    assert suggest_label([convicted, released]) == "good"
    assert suggest_label([released, convicted]) == "not good"
    assert suggest_label([{"good": ["acquitted"], "not_good": ["convicted"]}]) == "mixed"
    assert suggest_label([]) == "unknown"


def test_bail_is_not_a_good_outcome():
    assert signals("On June 15, Mbah was released on bail after 8 months.")[0] == []
    assert signals("Mbah was released from Kirikiri Prison on bail.")[0] == []
    assert signals("He was later released from prison.")[0] == ["released"]


def test_citations_are_skipped():
    text = "Rehman, Accountability Court, Reply to Acquittal Application, p. 12 (Rehman was acquitted)."
    assert outcome_evidence(text, ["rehman"]) == []
