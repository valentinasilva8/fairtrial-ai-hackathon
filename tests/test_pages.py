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
