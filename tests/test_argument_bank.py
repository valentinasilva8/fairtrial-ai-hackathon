"""Tests for src/argument_bank.py. Uses the committed CSVs; argument text is local-only."""

from src.argument_bank import BOILERPLATE, FOOTNOTE, is_good, outcome_of, page_link, similar_cases
from src.similarity import features_from_case


def test_outcome_needs_a_person_to_be_confirmed():
    assert outcome_of({"suggested_label": "good", "outcome_label": "", "verified_by": ""}) == ("good", False)
    assert outcome_of({"suggested_label": "good", "outcome_label": "acquitted", "verified_by": "Layla"}) == ("acquitted", True)
    assert outcome_of({"suggested_label": "good", "outcome_label": "acquitted", "verified_by": ""}) == ("good", False)


def test_good_outcome_labels():
    assert is_good("acquitted", True) and not is_good("convicted", True)
    assert is_good("good", False) and not is_good("not good", False)


def test_similar_cases_share_a_charge_and_explain_why():
    current = features_from_case({"article": "27(3)", "role": "human rights defenders"})
    df = similar_cases(current, top_n=5)
    assert 0 < len(df) <= 5
    assert all(any(w.startswith("same charge") for w in why) for why in df["why"])
    # good outcomes are listed first among the top matches
    assert list(df["good_outcome"]) == sorted(df["good_outcome"], reverse=True)


def test_boilerplate_is_recognised():
    assert BOILERPLATE.search("Experts should assign a grade of A, B, C, D, or F")
    assert not BOILERPLATE.search("The law is insufficiently precise to satisfy the legality requirement.")


def test_page_link():
    assert page_link("https://cfj.org/r.pdf", 12) == "https://cfj.org/r.pdf#page=12"
    assert page_link("", 3) == ""


def test_footnotes_are_recognised():
    assert FOOTNOTE.search("87 Conversation with staff, November 22, 2022. Available at https://www.reuters.com/x")
    assert not FOOTNOTE.search("Article 495 is insufficiently precise and fails the legality requirement.")


def test_published_excerpts_are_attributed_and_located():
    import json
    from pathlib import Path

    from src.argument_bank import EXCERPTS

    assert "All rights reserved by CFJ" in Path("data/NOTICE.md").read_text()
    recs = [json.loads(line) for line in open(EXCERPTS)]
    paras = [r for r in recs if "text" in r]
    assert paras and all(r["url"].startswith("https://cfj.org/reports/") and r["page"] >= 1 for r in paras)
    # only the displayed paragraphs: a small fraction of the ~2,300 extracted
    assert len(paras) < 300


def test_same_drafting_and_grouping(monkeypatch):
    import pandas as pd

    import src.argument_bank as ab

    shared = "In order to comply with the principle of legality, legislation must be formulated with sufficient precision."
    other = "The sentence of two years' imprisonment was disproportionate to any legitimate aim pursued."
    assert ab.same_drafting(shared, shared.replace("legislation", "a law")) and not ab.same_drafting(shared, other)
    paras = {"u1": {"legality": [{"page": 3, "text": shared}]},
             "u2": {"legality": [{"page": 9, "text": shared + " 12"}]},
             "u3": {"legality": [{"page": 5, "text": other}]}}
    monkeypatch.setattr(ab, "best_arguments", lambda url: paras[url])
    matches = pd.DataFrame([
        {"report_url": u, "case": c, "author": a, "pdf_url": "", "outcome": o, "outcome_confirmed": True, "good_outcome": g}
        for u, c, a, o, g in [("u1", "A v. X", "Ann", "convicted", False), ("u2", "B v. Y", "Ben", "acquitted", True),
                              ("u3", "C v. Z", "", "convicted", False)]])
    groups = ab.grouped_arguments(matches, ["legality"])["legality"]
    assert [len(g["cases"]) for g in groups] == [2, 1]          # shared drafting counted once, good outcome first
    assert {c["author"] for c in groups[0]["cases"]} == {"Ann", "Ben"}
