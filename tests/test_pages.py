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
