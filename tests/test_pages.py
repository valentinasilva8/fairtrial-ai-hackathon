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


def test_un_letter_for_a_new_case_in_another_country():
    at = AppTest.from_file("../pages/4_UN_Letter.py").run(timeout=30)
    at.selectbox(key="letter_case").set_value("new_case").run(timeout=30)
    at.text_input(key="lt_name").set_value("R. Example").run(timeout=30)
    at.text_input(key="lt_country").set_value("Kenya").run(timeout=30)
    at.text_area(key="lt_facts").set_value("Charged over a news report about police conduct.").run(timeout=30)
    at.multiselect(key="lt_charges").set_value(["false information"]).run(timeout=30)
    next(b for b in at.button if b.label == "Build plain draft (no AI)").click().run(timeout=30)
    assert not at.exception
    assert any("Citation check passed" in s.value for s in at.success)
    assert any("Government of Kenya" in m.value for m in at.markdown)


def test_un_letter_edit_review_and_download():
    at = AppTest.from_file("../pages/4_UN_Letter.py").run(timeout=30)
    next(b for b in at.button if b.label == "Build plain draft (no AI)").click().run(timeout=30)
    assert not at.exception
    editor = next(t for t in at.text_area if t.key and "_edit_" in t.key)
    editor.set_value(editor.value.replace("### Sources", "An added sentence with no citation at all, written by the reviewer.\n\n### Sources")).run(timeout=30)
    assert any("no citation" in w.value for w in at.warning)
    at.text_input(key=next(t.key for t in at.text_input if t.key and t.key.endswith("_reviewer"))).set_value("Tester").run(timeout=30)
    next(c for c in at.checkbox if c.key and c.key.endswith("_read")).check().run(timeout=30)
    save = lambda: next(b for b in at.button if b.label == "Save a copy in outputs/")
    assert save().disabled  # both source-check reviews still unticked
    next(c for c in at.checkbox if c.key and c.key.endswith("_pre_ok")).check().run(timeout=30)
    next(c for c in at.checkbox if c.key and c.key.endswith("_post_ok")).check().run(timeout=30)
    assert not at.exception
    assert not save().disabled


def test_arriving_from_argument_bank_prefills_and_drafts():
    at = AppTest.from_file("../pages/4_UN_Letter.py")
    at.session_state["letter_case"] = "fatia_haris"
    at.session_state["letter_n_past"] = 4
    at.session_state["letter_autodraft"] = True
    at.session_state["letter_features"] = {"case_id": "fatia_haris", "country": "Indonesia", "region": "Southeast Asia",
                                           "charges": ["defamation or insult"], "speech": ["online post"], "roles": []}
    at.run(timeout=30)
    assert not at.exception
    assert at.selectbox(key="letter_case").value == "fatia_haris"
    assert any("Citation check passed" in s.value for s in at.success)
    assert any("Argument Bank" in c.value for c in at.caption)


def test_argument_bank_has_letter_button():
    at = AppTest.from_file("../pages/3_Argument_Bank.py").run(timeout=30)
    assert any(b.label.endswith("Draft a UN letter for this case") for b in at.button)
