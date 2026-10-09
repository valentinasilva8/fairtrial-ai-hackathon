import importlib.util
from pathlib import Path

import pandas as pd

from src.data import load_all


def _page():
    path = Path("pages/1_Cases.py")
    spec = importlib.util.spec_from_file_location("cases_page", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sensitive_cases_stay_hidden_until_toggle():
    page = _page()
    cases = load_all().cases
    public = page.visible_cases(cases, show_sensitive=False)
    assert "khariq_anhar" not in set(public["case_id"])
    shown = page.visible_cases(cases, show_sensitive=True)
    assert "khariq_anhar" in set(shown["case_id"])


def test_filters_search_role_outcome_and_article():
    page = _page()
    cases = load_all().cases
    roy = page.filter_cases(cases, "suryo", "All", "All", "All")
    assert list(roy["case_id"]) == ["roy_suryo"]

    journalists = page.filter_cases(cases, "", "journalist", "All", "All")
    assert set(journalists["case_id"]) == {"tinus", "asrul"}

    convicted = page.filter_cases(cases, "", "All", "convicted", "28(2)")
    assert "roy_suryo" in set(convicted["case_id"])
    assert "madilis" not in set(convicted["case_id"])

    hoax = page.filter_cases(cases, "", "All", "All", "hoax")
    assert "madilis" in set(hoax["case_id"])
    assert "roy_suryo" not in set(hoax["case_id"])

    none = page.filter_cases(cases, "no-such-person", "All", "All", "All")
    assert none.empty


def test_timeline_is_oldest_first_and_empty_without_events():
    page = _page()
    data = load_all()
    roy = page.case_events(data.events, "roy_suryo")
    assert list(roy["date"])[:2] == ["2022-06-10", "2022-06-14"]
    assert roy["date"].tolist()[-1] == "2023-05-02"
    assert page.case_events(data.events, "meila").empty
    assert page.case_events(None, "roy_suryo").empty


def test_unverified_tag_is_dashed():
    page = _page()
    tag = page.unverified_tag()
    assert "unverified" in tag
    assert "dashed" in tag
