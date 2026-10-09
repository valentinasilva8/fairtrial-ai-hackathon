"""Case list and source-linked timeline.

Run from the project root: streamlit run app.py
"""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from src.data import DataValidationError, load_all, public_cases, split_articles

ALL = "All"


def visible_cases(cases: pd.DataFrame, show_sensitive: bool) -> pd.DataFrame:
    """Public cases, plus sensitive ones when the internal toggle is on."""
    if show_sensitive:
        return cases
    return public_cases(cases)


def filter_cases(
    cases: pd.DataFrame,
    query: str,
    role: str,
    outcome: str,
    article: str,
) -> pd.DataFrame:
    """Apply the search box and the role, outcome, and article filters."""
    df = cases
    text = query.strip().casefold()
    if text:
        haystack = (
            df["name"].str.casefold()
            + " "
            + df["case_id"].str.casefold()
            + " "
            + df["role"].str.casefold()
            + " "
            + df["complainant"].str.casefold()
        )
        df = df[haystack.str.contains(text, regex=False, na=False)]
    if role != ALL:
        df = df[df["role"] == role]
    if outcome != ALL:
        df = df[df["outcome"] == outcome]
    if article != ALL:
        df = df[df["article"].map(lambda value: article in split_articles(value))]
    return df


def case_events(events: pd.DataFrame | None, case_id: str) -> pd.DataFrame:
    """Events for one case, oldest first. Missing dates sort last."""
    if events is None or events.empty:
        return pd.DataFrame()
    rows = events[events["case_id"] == case_id].copy()
    if rows.empty:
        return rows
    rows["_sort"] = rows["date_parsed"]
    return rows.sort_values("_sort", na_position="last", kind="stable")


def unverified_tag() -> str:
    return (
        '<span style="border: 1px dashed #9a7b4f; border-radius: 4px; '
        'padding: 0 0.4rem; font-size: 0.8rem; white-space: nowrap;">unverified</span>'
    )


def source_links(source: str) -> str:
    """Turn a pipe-separated source cell into plain text plus markdown links."""
    parts = [part.strip() for part in str(source).split("|") if part.strip()]
    rendered = []
    for part in parts:
        if part.startswith("http://") or part.startswith("https://"):
            rendered.append(f"[{part}]({part})")
        else:
            rendered.append(part)
    return " · ".join(rendered)


def _label(value: str) -> str:
    return str(value).replace("_", " ")


def main() -> None:
    st.markdown(
        """
        <style>
        .timeline-item {
            border-left: 3px solid rgba(154, 123, 79, 0.7);
            margin: 0 0 1rem 0.2rem;
            padding: 0 0 0.2rem 0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Cases")
    st.caption(
        "Each case on one source-linked timeline. "
        "Rows without a checked source are marked unverified. "
        "For lawyer review, not a legal conclusion."
    )

    @st.cache_data
    def get_data():
        return load_all()

    try:
        data = get_data()
    except DataValidationError as exc:
        st.error(f"Could not load data: {exc}")
        st.stop()

    show_sensitive = st.sidebar.toggle("Show sensitive (internal)", value=False)
    shown = visible_cases(data.cases, show_sensitive)
    hidden = len(data.cases) - len(public_cases(data.cases))

    query = st.sidebar.text_input("Search", placeholder="Name, role, or complainant")
    # Options come from the full file so the widgets stay valid when sensitive cases are hidden.
    role = st.sidebar.selectbox("Role", [ALL, *sorted(data.cases["role"].unique())])
    outcome = st.sidebar.selectbox("Outcome", [ALL, *sorted(data.cases["outcome"].unique())])
    articles = sorted({token for value in data.cases["article"] for token in split_articles(value)})
    article = st.sidebar.selectbox("Article", [ALL, *articles])

    matched = filter_cases(shown, query, role, outcome, article)
    st.caption(f"{len(matched)} case{'s' if len(matched) != 1 else ''} shown.")
    if hidden and not show_sensitive:
        st.caption(f"{hidden} sensitive case(s) hidden. Turn on “Show sensitive (internal)” to see them.")

    if matched.empty:
        st.info("No cases match these filters.")
        st.stop()

    labels = {
        row["case_id"]: f"{row['name']} — {_label(row['outcome'])}"
        for row in matched.to_dict("records")
    }
    option_ids = list(matched["case_id"])
    case_id = st.selectbox(
        "Case",
        option_ids,
        format_func=lambda cid: labels[cid],
        key="case_picker_" + "|".join(option_ids),
    )
    case = matched.set_index("case_id").loc[case_id]

    title = case["name"]
    if not bool(case["verified"]):
        st.markdown(f"### {html.escape(str(title))} {unverified_tag()}", unsafe_allow_html=True)
    else:
        st.subheader(title)
    if bool(case["sensitive"]):
        st.warning("Sensitive case. Hidden from the public list unless the sidebar toggle is on.")

    left, right = st.columns(2)
    year = case["year_reported"]
    year_text = "unknown" if pd.isna(year) else str(int(year))
    with left:
        st.markdown(f"**Role.** {case['role']}")
        st.markdown(f"**Complainant.** {case['complainant']} ({_label(case['complainant_type'])})")
        st.markdown(f"**Article.** {case['article']}")
    with right:
        st.markdown(f"**Year reported.** {year_text}")
        st.markdown(f"**Outcome.** {_label(case['outcome'])}")
        st.markdown(
            f"**Public interest.** {str(bool(case['public_interest'])).lower()} · "
            f"**Harm shown.** {str(bool(case['harm_shown'])).lower()}"
        )
    st.markdown(case["outcome_detail"])
    st.markdown(f"**Source.** {source_links(case['source'])}")

    st.header("Timeline")
    events = case_events(data.events, case_id)
    if events.empty:
        st.info("No timeline events for this case yet.")
        return

    for event in events.itertuples(index=False):
        when = event.date if pd.isna(event.date_parsed) else event.date
        tag = f" {unverified_tag()}" if not bool(event.verified) else ""
        st.markdown(
            "<div class=\"timeline-item\">"
            f"<strong>{html.escape(str(when))}</strong> · {html.escape(_label(event.lane))}{tag}"
            f"<br>{html.escape(str(event.description))}</div>",
            unsafe_allow_html=True,
        )
        st.caption(source_links(event.source))


if __name__ == "__main__":
    main()
