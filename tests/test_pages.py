"""Smoke tests: each Streamlit page runs without errors."""

from streamlit.testing.v1 import AppTest


def test_home_page_runs():
    at = AppTest.from_file("../app.py").run(timeout=30)
    assert not at.exception


def test_stress_test_page_runs():
    at = AppTest.from_file("../pages/2_Stress_Test.py").run(timeout=30)
    assert not at.exception
    assert any("would likely be barred" in h.value for h in at.header)
    assert any("not legal advice" in w.value for w in at.warning)


def test_stress_test_verdict_filter():
    at = AppTest.from_file("../pages/2_Stress_Test.py").run(timeout=30)
    at.multiselect[0].set_value(["AT RISK"]).run(timeout=30)
    assert not at.exception


def test_add_case_by_hand_runs_stress_test():
    at = AppTest.from_file("../pages/2_Stress_Test.py").run(timeout=30)
    at.selectbox[0].set_value("public_official")
    at.multiselect[2].set_value(["27(3)"])
    next(b for b in at.button if b.label == "Run stress test").click().run(timeout=30)
    assert not at.exception
    assert any("LIKELY BARRED" in m.value for m in at.markdown)


def test_home_page_shows_promise_clock():
    at = AppTest.from_file("../app.py").run(timeout=30)
    assert not at.exception
    assert any(h.value == "Promise Clock" for h in at.header)
    assert any("date to verify" in m.value for m in at.markdown)


def test_argument_bank_page_runs():
    at = AppTest.from_file("../pages/3_Argument_Bank.py").run(timeout=30)
    assert not at.exception
    assert any("similar TrialWatch cases" in h.value for h in at.header)


def test_un_letter_page_builds_plain_draft():
    at = AppTest.from_file("../pages/4_UN_Letter.py").run(timeout=30)
    assert not at.exception
    next(b for b in at.button if b.label == "Build plain draft (no AI)").click().run(timeout=30)
    assert not at.exception
    assert any("Citation check passed" in s.value for s in at.success)
    assert any("Special Rapporteur" in m.value for m in at.markdown)


def test_stress_test_page_shows_sensitivity():
    at = AppTest.from_file("../pages/2_Stress_Test.py").run(timeout=30)
    assert not at.exception
    assert any("How robust" in e.label for e in at.expander)


def test_argument_bank_shows_impact_on_the_defendant(tmp_path, monkeypatch):
    import src.impacts as impacts
    from src.argument_bank import similar_cases
    from src.data import load_all, public_cases
    from src.similarity import features_from_case

    cases = public_cases(load_all().cases)
    first = cases.iloc[0].to_dict()
    top = similar_cases(features_from_case(first), top_n=6)
    url = top.iloc[0]["report_url"]
    row = impacts.case_row(
        {"url": url, "title": "Country v. Anna Rowe", "grade": "D", "pdf_url": "https://cfj.org/x.pdf"},
        ["Anna Rowe"],
        {"pretrial_detention": [{"sentence": "Ms. Rowe was detained for five months before trial.",
                                 "page": 17, "quantities": ["five months"]}]},
    )
    sheet = tmp_path / "impacts.csv"
    import csv
    with open(sheet, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        w.writeheader()
        w.writerow(row)
    monkeypatch.setattr(impacts, "IMPACTS_CSV", sheet)
    at = AppTest.from_file("../pages/3_Argument_Bank.py").run(timeout=30)
    assert not at.exception
    text = "\n".join(m.value for m in at.markdown)
    assert "Impact on the defendant" in text
    assert "**Detention** (five months) · *unconfirmed*" in text and "#page=17" in text


def test_argument_bank_new_case_and_by_argument_tab():
    at = AppTest.from_file("../pages/3_Argument_Bank.py").run(timeout=30)
    assert not at.exception
    assert [t.label for t in at.tabs] == ["By argument", "By case"]
    at.selectbox(key="ab_case").set_value("__new__").run(timeout=30)
    assert not at.exception
    assert any("at least one charge type" in i.value for i in at.info)
