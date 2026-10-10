"""Promise Clock: how long since each official pledge, without overstating precision."""

from __future__ import annotations

import re
from datetime import date

STATUS_LABELS = {
    "kept": "Kept",
    "partly_kept": "Partly kept",
    "broken": "Broken",
    "no_evidence_yet": "No evidence yet",
}
PLACEHOLDER = re.compile(r"^\s*TO (FILL|VERIFY)\b", re.I)


def parse_pledge_date(value: str) -> tuple[date | None, str]:
    """'2025-04-17' -> (date, 'day'); '2025-04' -> (1 April 2025, 'month'); else (None, '')."""
    value = str(value).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        y, m, d = map(int, value.split("-"))
        return date(y, m, d), "day"
    if re.fullmatch(r"\d{4}-\d{2}", value):
        y, m = map(int, value.split("-"))
        return date(y, m, 1), "month"
    return None, ""


def days_since(value: str, today: date) -> tuple[int | None, str]:
    """Days from the pledge to today, and how to describe it.

    Month-only dates count from the 1st of that month and are labelled "about".
    """
    d, precision = parse_pledge_date(value)
    if d is None:
        return None, "date to verify"
    days = (today - d).days
    if precision == "month":
        return days, f"about {days:,} days since {d.strftime('%B %Y')}"
    return days, f"{days:,} days since {d.strftime('%-d %B %Y')}"


def evidence_text(value: str) -> str:
    """Hide 'TO FILL' placeholders from the public view."""
    value = str(value).strip()
    if not value or PLACEHOLDER.match(value):
        return "No evidence collected yet."
    return value


def status_label(value: str) -> str:
    return STATUS_LABELS.get(str(value).strip(), "Unknown")
