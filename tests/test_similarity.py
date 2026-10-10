"""Tests for src/similarity.py with made-up text."""

from src.similarity import features_from_case, features_from_report, match, region_of


def test_region():
    assert region_of("Cambodia") == "Southeast Asia"
    assert region_of("Atlantis") == ""


def test_report_features_count_threshold():
    text = ("He was charged with defamation over a Facebook post. " * 4) + "The journalist was named once."
    f = features_from_report("Cambodia v. Someone", text)
    assert f["country"] == "Cambodia"
    assert f["charges"] == ["defamation or insult"]
    assert "online post" in f["speech"]
    assert "journalist" not in f["roles"]  # one mention is below the threshold


def test_current_case_features_from_ite_articles():
    f = features_from_case({"article": "27(3); hoax", "role": "journalist"})
    assert f["charges"] == ["defamation or insult", "false information"]
    assert f["region"] == "Southeast Asia"
    assert f["speech"] == ["online post", "journalism"]
    assert features_from_case({"article": "28(2)", "role": "journalist / HRD"})["roles"] == [
        "human rights defender or activist", "journalist"]


def test_match_scores_and_explains():
    current = features_from_case({"article": "27(3)", "role": "journalist"})
    past = {"country": "Thailand", "region": "Southeast Asia", "charges": ["defamation or insult"],
            "speech": ["online post"], "roles": ["journalist"]}
    score, reasons = match(current, past)
    assert score == 3 + 1 + 1 + 1
    assert reasons == ["same charge: defamation or insult", "same kind of speech: online post",
                       "same defendant: journalist", "same region: Southeast Asia"]


def test_same_country_beats_region():
    current = features_from_case({"article": "28(2)", "role": "activist"})
    past = {"country": "Indonesia", "region": "Southeast Asia", "charges": [], "speech": [], "roles": []}
    assert match(current, past) == (2, ["same country: Indonesia"])
