"""Load and validate the project CSVs in data/.

Hard problems (missing file, missing columns, duplicate ids, bad booleans)
raise DataValidationError. Soft problems (unknown enum values, missing
source, "TO VERIFY" placeholders) are returned as warnings so the UI can
show them, and the affected rows are marked unverified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

CASES_FILE = "cases_seed.csv"
PROMISES_FILE = "promises_seed.csv"
EVENTS_FILE = "events.csv"

CASE_COLUMNS = [
    "case_id", "name", "role", "complainant", "complainant_type", "article",
    "year_reported", "outcome", "outcome_detail", "public_interest",
    "harm_shown", "source", "verified", "sensitive",
]
CASE_BOOL_COLUMNS = ["public_interest", "harm_shown", "verified", "sensitive"]

PROMISE_COLUMNS = [
    "promise_id", "promise_text", "made_by", "date", "provision",
    "evidence_since", "status", "source", "verified",
]
PROMISE_BOOL_COLUMNS = ["verified"]

EVENT_COLUMNS = ["case_id", "date", "lane", "description", "source", "verified"]
EVENT_BOOL_COLUMNS = ["verified"]

# Allowed values from docs/stress_test_rules.md
COMPLAINANT_TYPES = {
    "individual_victim", "public_official", "government_body", "company",
    "group", "representative", "police", "unknown",
}
ARTICLE_TOKENS = {"27(3)", "27A", "28(2)", "hoax", "other", "unknown"}

OUTCOMES = {
    "acquitted", "acquitted_on_appeal", "convicted", "dropped", "pending",
    "summoned", "restorative_justice", "suspect_status_invalidated",
}
PROMISE_STATUSES = {"kept", "partly_kept", "broken", "no_evidence_yet"}

PLACEHOLDER = "TO VERIFY"

_TRUE = {"true", "1", "yes", "y"}
_FALSE = {"false", "0", "no", "n"}


class DataValidationError(ValueError):
    """Raised when a CSV is structurally unusable."""


@dataclass
class Dataset:
    cases: pd.DataFrame
    promises: pd.DataFrame
    events: pd.DataFrame | None
    warnings: list[str] = field(default_factory=list)


def _read_csv(path: Path, required: list[str]) -> pd.DataFrame:
    if not path.exists():
        raise DataValidationError(f"{path.name}: file not found at {path}")
    # Read everything as text; we parse types ourselves so nothing is guessed.
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise DataValidationError(f"{path.name}: missing columns {missing}")
    return df.apply(lambda col: col.str.strip())


def _parse_bools(df: pd.DataFrame, columns: list[str], file: str) -> None:
    for col in columns:
        lowered = df[col].str.lower()
        bad = df.loc[~lowered.isin(_TRUE | _FALSE), col]
        if not bad.empty:
            raise DataValidationError(
                f"{file}: column '{col}' has non-boolean values "
                f"{sorted(set(bad))} (rows {list(bad.index + 2)})"
            )
        df[col] = lowered.isin(_TRUE)


def _check_unique(df: pd.DataFrame, id_col: str, file: str) -> None:
    if (df[id_col] == "").any():
        raise DataValidationError(f"{file}: empty {id_col}")
    dupes = df.loc[df[id_col].duplicated(), id_col]
    if not dupes.empty:
        raise DataValidationError(f"{file}: duplicate {id_col} {sorted(set(dupes))}")


def split_articles(article: str) -> list[str]:
    """'27(3); hoax' -> ['27(3)', 'hoax']"""
    return [a.strip() for a in str(article).split(";") if a.strip()]


def _mark_unverified(df: pd.DataFrame, id_col: str, file: str, warnings: list[str]) -> None:
    """Rows with no source or a TO VERIFY placeholder cannot count as verified."""
    no_source = df["source"] == ""
    for rid in df.loc[no_source, id_col]:
        warnings.append(f"{file}: {rid} has no source — shown as unverified")

    text_cols = [c for c in df.columns if df[c].dtype == object]
    placeholder = df[text_cols].apply(
        lambda col: col.str.contains(PLACEHOLDER, case=False, na=False)
    ).any(axis=1)
    for rid in df.loc[placeholder & df["verified"], id_col]:
        warnings.append(f"{file}: {rid} contains '{PLACEHOLDER}' but verified=true — shown as unverified")

    df["verified"] = df["verified"] & ~no_source & ~placeholder


def load_cases(path: Path | None = None, warnings: list[str] | None = None) -> pd.DataFrame:
    path = path or DATA_DIR / CASES_FILE
    warnings = warnings if warnings is not None else []
    df = _read_csv(path, CASE_COLUMNS)
    _check_unique(df, "case_id", path.name)
    _parse_bools(df, CASE_BOOL_COLUMNS, path.name)

    for _, row in df.iterrows():
        cid = row["case_id"]
        if row["complainant_type"] not in COMPLAINANT_TYPES:
            warnings.append(f"{path.name}: {cid} has unknown complainant_type '{row['complainant_type']}'")
        if row["outcome"] not in OUTCOMES:
            warnings.append(f"{path.name}: {cid} has unknown outcome '{row['outcome']}'")
        for token in split_articles(row["article"]):
            if token not in ARTICLE_TOKENS:
                warnings.append(f"{path.name}: {cid} has unrecognised article '{token}'")

    df["year_reported"] = pd.to_numeric(df["year_reported"], errors="coerce").astype("Int64")
    _mark_unverified(df, "case_id", path.name, warnings)
    return df


def load_promises(path: Path | None = None, warnings: list[str] | None = None) -> pd.DataFrame:
    path = path or DATA_DIR / PROMISES_FILE
    warnings = warnings if warnings is not None else []
    df = _read_csv(path, PROMISE_COLUMNS)
    _check_unique(df, "promise_id", path.name)
    _parse_bools(df, PROMISE_BOOL_COLUMNS, path.name)

    for _, row in df.iterrows():
        if row["status"] not in PROMISE_STATUSES:
            warnings.append(f"{path.name}: {row['promise_id']} has unknown status '{row['status']}'")

    # Dates may be YYYY-MM or YYYY-MM-DD; anything else (e.g. TO VERIFY) -> NaT.
    df["date_parsed"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    _mark_unverified(df, "promise_id", path.name, warnings)
    return df


def load_events(
    path: Path | None = None,
    case_ids: set[str] | None = None,
    warnings: list[str] | None = None,
) -> pd.DataFrame | None:
    """Optional file; returns None if data/events.csv doesn't exist yet."""
    path = path or DATA_DIR / EVENTS_FILE
    warnings = warnings if warnings is not None else []
    if not path.exists():
        return None
    df = _read_csv(path, EVENT_COLUMNS)
    _parse_bools(df, EVENT_BOOL_COLUMNS, path.name)
    if case_ids is not None:
        for cid in sorted(set(df["case_id"]) - case_ids):
            warnings.append(f"{path.name}: case_id '{cid}' not in cases file")
    df["date_parsed"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    _mark_unverified(df, "case_id", path.name, warnings)
    return df


def load_all(data_dir: Path | None = None) -> Dataset:
    data_dir = data_dir or DATA_DIR
    warnings: list[str] = []
    cases = load_cases(data_dir / CASES_FILE, warnings)
    promises = load_promises(data_dir / PROMISES_FILE, warnings)
    events = load_events(data_dir / EVENTS_FILE, set(cases["case_id"]), warnings)
    return Dataset(cases=cases, promises=promises, events=events, warnings=warnings)


def public_cases(cases: pd.DataFrame) -> pd.DataFrame:
    """Cases safe for public views and briefs (sensitive ones removed)."""
    return cases[~cases["sensitive"]]
