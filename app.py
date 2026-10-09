"""Paper vs. Practice — Streamlit home page.

Run: streamlit run app.py
"""

from datetime import date

import streamlit as st

from src.data import DataValidationError, load_all, public_cases
from src.promise_clock import days_since, evidence_text, status_label

PROJECT_NAME = "Paper vs. Practice"
HOOK = (
    "Indonesia reformed its speech law. We stress-tested the reform: how many "
    "past prosecutions would it have stopped — and is it stopping new ones?"
)

st.set_page_config(page_title=PROJECT_NAME, page_icon="⚖️", layout="wide")

st.title(PROJECT_NAME)
st.markdown(f"> *{HOOK}*")
st.caption(
    "TrialWatch Fair Trial & AI Hackathon · Track 3: Advocacy & Impact. "
    "All outputs are drafts for lawyer review, not legal conclusions."
)


@st.cache_data
def get_data():
    return load_all()


try:
    data = get_data()
except DataValidationError as e:
    st.error(f"Could not load data: {e}")
    st.stop()

cases = public_cases(data.cases)
hidden = len(data.cases) - len(cases)

st.header("Cases by outcome")

c1, c2, c3 = st.columns(3)
c1.metric("Cases", len(cases))
c2.metric("Source-verified", int(cases["verified"].sum()))
c3.metric("Unverified", int((~cases["verified"]).sum()))

counts = (
    cases["outcome"]
    .str.replace("_", " ")
    .value_counts()
    .rename_axis("outcome")
    .reset_index(name="cases")
)

left, right = st.columns([2, 1])
with left:
    st.bar_chart(counts, x="outcome", y="cases", horizontal=True)
with right:
    st.dataframe(counts, hide_index=True, width="stretch")

if hidden:
    st.caption(f"{hidden} sensitive case(s) hidden from this public view.")

# --- Promise Clock ---------------------------------------------------------
STATUS_COLORS = {"Kept": "green", "Broken": "red", "No evidence yet": "orange", "Unknown": "gray"}

st.header("Promise Clock")
st.caption("How long since each official pledge, and the evidence that it has been carried out.")

today = date.today()
for p in data.promises.itertuples():
    days, since = days_since(p.date, today)
    label = status_label(p.status)
    with st.container(border=True):
        left, right = st.columns([3, 1])
        with left:
            st.markdown(f"**{p.promise_text}**")
            st.caption(f"{p.made_by} · provision {p.provision}")
            st.markdown(f"Evidence: {evidence_text(p.evidence_since)}")
            source = p.source if p.source.startswith("http") else f"`{p.source}`"
            st.caption(f"Source: {source}" + ("" if p.verified else " · :gray-background[unverified]"))
        with right:
            if days is None:
                st.markdown(":gray-background[date to verify]")
            else:
                st.metric("Days since pledge", f"{days:,}", help=since)
                st.caption(since)
            st.markdown(f":{STATUS_COLORS[label]}-background[{label}]")

if data.warnings:
    with st.expander(f"Data checks ({len(data.warnings)} warnings)"):
        for w in data.warnings:
            st.write(f"- {w}")
