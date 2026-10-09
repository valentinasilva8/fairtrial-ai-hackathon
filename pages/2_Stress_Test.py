"""Reform Stress Test: run every case through rules R1–R4."""

import re

import altair as alt
import pandas as pd
import streamlit as st

from src.data import DataValidationError, load_all, public_cases
from src.llm import ARTICLES, COMPLAINANT_TYPES, TRI_STATE, ExtractionError, extract_case_fields
from src.stress_test import (
    AT_RISK,
    LIKELY_BARRED,
    RULE_SOURCE,
    RULES,
    STILL_PROSECUTABLE,
    VERDICTS,
    evaluate_all,
    evaluate_case,
)

# Constitutional Court Decision 105/PUU-XXII/2024 was issued in 2025; cases
# reported from 2025 on are counted as post-ruling, not "past".
RULING_YEAR = 2025

VERDICT_COLORS = {
    LIKELY_BARRED: "#2e7d32",
    AT_RISK: "#ed8c00",
    STILL_PROSECUTABLE: "#c62828",
}
URL_RE = re.compile(r"https?://\S+")

st.set_page_config(page_title="Stress Test · Paper vs. Practice", page_icon="⚖️", layout="wide")

st.title("Reform Stress Test")
st.warning(
    "**For lawyer review — not legal advice.** Verdicts apply the rules in "
    "`docs/stress_test_rules.md` to the recorded facts; they are not legal conclusions.",
    icon="⚖️",
)


@st.cache_data
def get_results():
    data = load_all()
    cases = public_cases(data.cases).reset_index(drop=True)
    results = evaluate_all(cases)
    hidden = len(data.cases) - len(cases)
    return cases.merge(results.drop(columns=["source"]), on="case_id"), hidden


try:
    df, hidden = get_results()
except DataValidationError as e:
    st.error(f"Could not load data: {e}")
    st.stop()

df["past"] = df["year_reported"].isna() | (df["year_reported"] < RULING_YEAR)
past = df[df["past"]]
n_barred = int((past["verdict"] == LIKELY_BARRED).sum())

st.header(f"{n_barred} of {len(past)} past cases would likely be barred under the 2025 ruling")
st.caption(
    f"Past = reported before {RULING_YEAR} or year unknown. "
    f"{int((~past['verified']).sum())} of these {len(past)} cases are not yet source-verified."
    + (f" {hidden} sensitive case(s) hidden." if hidden else "")
)

post = df[~df["past"]]
if not post.empty:
    st.caption(
        f"Since the ruling: {len(post)} case(s) reported from {RULING_YEAR} on — "
        + ", ".join(f"{r.name} ({r.verdict.lower()})" for r in post.itertuples())
        + "."
    )

# --- filters ---------------------------------------------------------------
articles = sorted({a.strip() for v in df["article"] for a in str(v).split(";") if a.strip()})
f1, f2 = st.columns(2)
verdict_filter = f1.multiselect("Verdict", VERDICTS, default=VERDICTS)
article_filter = f2.multiselect("Article", articles, default=articles)

shown = df[
    df["verdict"].isin(verdict_filter)
    & df["article"].apply(lambda v: any(a.strip() in article_filter for a in str(v).split(";")))
].reset_index(drop=True)

# --- chart -----------------------------------------------------------------
counts = (
    shown["verdict"].value_counts().reindex(VERDICTS, fill_value=0)
    .rename_axis("verdict").reset_index(name="cases")
)
chart = (
    alt.Chart(counts)
    .mark_bar()
    .encode(
        x=alt.X("cases:Q", title="Cases", axis=alt.Axis(tickMinStep=1)),
        y=alt.Y("verdict:N", sort=VERDICTS, title=None, axis=alt.Axis(labelLimit=200)),
        color=alt.Color(
            "verdict:N",
            scale=alt.Scale(domain=VERDICTS, range=[VERDICT_COLORS[v] for v in VERDICTS]),
            legend=None,
        ),
        tooltip=["verdict", "cases"],
    )
    .properties(height=160)
)
st.altair_chart(chart, width="stretch")

# --- table -----------------------------------------------------------------
def first_url(source: str) -> str | None:
    m = URL_RE.search(str(source))
    return m.group(0) if m else None


table = pd.DataFrame({
    "Name": shown["name"],
    "Verdict": shown["verdict"],
    "Rules fired": shown["rules_fired"].apply(lambda r: ", ".join(r) or "—"),
    "Article": shown["article"],
    "Complainant": shown["complainant"],
    "Role": shown["role"],
    "Reason": shown["reasons"].apply(" ".join),
    "Source": shown["source"],
    "Link": shown["source"].apply(first_url),
    "Verified": shown["verified"].map({True: "verified", False: "unverified"}),
})


def badge(verdict: str) -> str:
    color = VERDICT_COLORS.get(verdict)
    return f"background-color: {color}; color: white; font-weight: 600" if color else ""


st.subheader("Cases")
st.caption("Click a row to see its reasoning.")
event = st.dataframe(
    table.style.map(badge, subset=["Verdict"]),
    hide_index=True,
    width="stretch",
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "Link": st.column_config.LinkColumn("Link", display_text="open"),
        "Reason": st.column_config.TextColumn(width="large"),
        "Source": st.column_config.TextColumn(width="medium"),
    },
)

# --- reasoning for the selected case ---------------------------------------
rows = event.selection.rows
if rows:
    case = shown.iloc[rows[0]]
    st.divider()
    st.subheader(case["name"])
    st.markdown(
        f"**Verdict:** :{'green' if case['verdict'] == LIKELY_BARRED else 'orange' if case['verdict'] == AT_RISK else 'red'}"
        f"-background[{case['verdict']}]"
        + ("" if case["verified"] else " · :gray-background[unverified]")
        + (" · :violet-background[displacement watch]" if case["displacement_watch"] else "")
    )

    left, right = st.columns(2)
    with left:
        st.markdown("**Rule inputs**")
        st.markdown(
            f"- Article: `{case['article']}`\n"
            f"- Complainant: {case['complainant']} (`{case['complainant_type']}`)\n"
            f"- Public interest: `{str(case['public_interest']).lower()}`\n"
            f"- Real, imminent harm shown: `{str(case['harm_shown']).lower()}`"
        )
        st.markdown("**Outcome**")
        st.write(case["outcome_detail"])
    with right:
        st.markdown("**Reasoning**")
        for reason in case["reasons"]:
            st.markdown(f"- {reason}")
        for rule in case["rules_fired"]:
            st.markdown(f"**{rule} — {RULES[rule]['name']}.** {RULES[rule]['basis']}")
        st.caption(f"Rule source: {RULE_SOURCE}.")

    st.markdown("**Case source**")
    for part in str(case["source"]).split("|"):
        st.markdown(f"- {part.strip()}")

# --- add a case from text (LLM-assisted, human-checked) --------------------
st.divider()
with st.expander("Add a case from text"):
    st.caption(
        "Paste a news article or report passage. Claude suggests the rule inputs, each with a "
        "verbatim quote; any field whose quote isn't in the text is reset to unknown. "
        "Check and edit every field before running the test. Nothing is saved unless you click Download."
    )
    source_text = st.text_area("Text", height=200, key="extract_text")
    source_ref = st.text_input("Source (URL or citation)", key="extract_source")

    if st.button("Extract fields", disabled=not source_text.strip()):
        try:
            with st.spinner("Reading the text…"):
                st.session_state["extracted"] = extract_case_fields(source_text)
        except ExtractionError as e:
            st.error(f"{e} You can still fill the fields by hand below.")

    fields = st.session_state.get("extracted")
    if fields:
        st.markdown("**What Claude found**")
        for name, f in fields.items():
            value = "; ".join(f["value"]) if isinstance(f["value"], list) else f["value"]
            tag = ":green-background[quoted]" if f["verified"] else ":gray-background[unverified]"
            st.markdown(f"- **{name}**: `{value}` {tag}")
            if f["quote"]:
                st.caption(f"> {f['quote']}")
            if f["reasoning"]:
                st.caption(f"Reasoning: {f['reasoning']}")
            if f["note"]:
                st.caption(f"⚠️ {f['note']}")

    def _get(name, default):
        return fields[name]["value"] if fields else default

    st.markdown("**Your inputs** (edit before running)")
    c1, c2 = st.columns(2)
    name_in = c1.text_input("Case name", key="manual_name")
    complainant_in = c2.text_input("Complainant", value=_get("complainant", "unknown"))
    complainant_type_in = c1.selectbox(
        "Complainant type", COMPLAINANT_TYPES,
        index=COMPLAINANT_TYPES.index(_get("complainant_type", "unknown")),
    )
    article_in = c2.multiselect("Article", ARTICLES, default=_get("article", ["unknown"]))
    public_interest_in = c1.radio(
        "Public interest", TRI_STATE, index=TRI_STATE.index(_get("public_interest", "unknown")), horizontal=True
    )
    harm_shown_in = c2.radio(
        "Real, imminent harm shown", TRI_STATE, index=TRI_STATE.index(_get("harm_shown", "unknown")), horizontal=True
    )

    if st.button("Run stress test"):
        manual_case = {
            "case_id": "new_case",
            "name": name_in,
            "complainant": complainant_in,
            "complainant_type": complainant_type_in,
            "article": "; ".join(article_in) or "unknown",
            "public_interest": public_interest_in == "true",
            "harm_shown": harm_shown_in == "true",
            "source": source_ref,
        }
        result = evaluate_case(manual_case)
        st.markdown(f"**Verdict:** {result['verdict']} — for lawyer review")
        for reason in result["reasons"]:
            st.markdown(f"- {reason}")
        if "unknown" in (public_interest_in, harm_shown_in):
            st.caption("Fields left as unknown are treated as false by the rules.")

        row = pd.DataFrame([{
            **{k: manual_case[k] for k in ["name", "complainant", "complainant_type", "article"]},
            "public_interest": str(manual_case["public_interest"]).lower(),
            "harm_shown": str(manual_case["harm_shown"]).lower(),
            "source": source_ref,
            "verified": "false",
            "sensitive": "false",
        }])
        st.download_button(
            "Download as CSV row (unverified)", row.to_csv(index=False),
            file_name="new_case.csv", mime="text/csv",
        )
