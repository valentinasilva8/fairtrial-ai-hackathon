import pandas as pd
import pytest

from src.data import (
    CASES_FILE,
    DataValidationError,
    load_all,
    load_cases,
    public_cases,
    split_articles,
)


def test_seed_data_loads():
    data = load_all()
    assert len(data.cases) > 0
    assert len(data.promises) > 0
    assert data.cases["case_id"].is_unique
    for col in ["public_interest", "harm_shown", "verified", "sensitive"]:
        assert data.cases[col].dtype == bool


def test_placeholder_rows_are_unverified():
    cases = load_all().cases.set_index("case_id")
    assert not cases.loc["asrul", "verified"]  # complainant is "TO VERIFY"
    assert cases.loc["fatia_haris", "verified"]


def test_split_articles():
    assert split_articles("27(3); hoax") == ["27(3)", "hoax"]
    assert split_articles("28(2)") == ["28(2)"]


def _write_cases(tmp_path, rows):
    src = load_all().cases.iloc[:1].copy()
    df = pd.DataFrame([{**src.iloc[0].to_dict(), **r} for r in rows])
    path = tmp_path / CASES_FILE
    df.drop(columns=["year_reported"]).assign(year_reported="2021").to_csv(path, index=False)
    return path


def test_duplicate_case_id_raises(tmp_path):
    path = _write_cases(tmp_path, [{"case_id": "x"}, {"case_id": "x"}])
    with pytest.raises(DataValidationError, match="duplicate"):
        load_cases(path)


def test_bad_boolean_raises(tmp_path):
    path = _write_cases(tmp_path, [{"case_id": "x", "sensitive": "maybe"}])
    with pytest.raises(DataValidationError, match="non-boolean"):
        load_cases(path)


def test_missing_source_is_unverified_and_warned(tmp_path):
    path = _write_cases(tmp_path, [{"case_id": "x", "source": "", "verified": "true"}])
    warnings = []
    df = load_cases(path, warnings)
    assert not df.loc[0, "verified"]
    assert any("no source" in w for w in warnings)


def test_sensitive_cases_hidden(tmp_path):
    path = _write_cases(
        tmp_path,
        [{"case_id": "a", "sensitive": "true"}, {"case_id": "b", "sensitive": "false"}],
    )
    assert list(public_cases(load_cases(path))["case_id"]) == ["b"]
