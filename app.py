"""Paper vs. Practice — Streamlit home page.

Run: streamlit run app.py
"""

import streamlit as st

from src.data import DataValidationError, load_all, public_cases

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

if data.warnings:
    with st.expander(f"Data checks ({len(data.warnings)} warnings)"):
        for w in data.warnings:
            st.write(f"- {w}")
