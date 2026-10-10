"""Start here: what the tool does, links to every page, the headline numbers, the Indonesian cases and the Promise Clock."""

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from src.argument_bank import past_cases
from src.data import DataValidationError, load_all, public_cases
from src.promise_clock import days_since, evidence_text, status_label
from src.stress_test import LIKELY_BARRED, evaluate_all

PROJECT_NAME = "Precedent & Practice"
SUBTITLE = "A human rights advocacy tracker built on TrialWatch's fairness reports"
VERIFICATION_LOG = Path(__file__).resolve().parent.parent / "data" / "verification_log.csv"
# What keeps a checked case from being fully confirmed (from the case rows' own notes).
OPEN_DETAIL = {
    "nugroho": "the complainant is not named in the sources found; the court decision needs checking",
    "laras_faizati": "the complainant rests on a single source, and which Penal Code version the court applied is unconfirmed",
}
HOOK = (
    "TrialWatch has analysed dozens of trials of journalists and critics. We turn those reports into "
    "arguments, precedents and sourced UN submissions for the next person prosecuted for speech."
)

st.title(f"⚖️ {PROJECT_NAME}")
st.markdown(f"#### {SUBTITLE}")
with st.container(border=True):
    st.markdown(f"*{HOOK}*")
    st.page_link("pages/3_Argument_Bank.py", label="**Start with a case in the Argument Bank →**", icon="📚")
st.caption(
    "TrialWatch Fair Trial & AI Hackathon · Track 3: Advocacy & Impact · Team: Shreya, Valentina, Ungu, Layla, Yuki. "
    "An independent hackathon project, not endorsed by the Clooney Foundation for Justice, TrialWatch or Columbia "
    "Law School. All outputs are drafts for lawyer review, not legal conclusions."
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

# --- overview ----------------------------------------------------------------
results = evaluate_all(cases.reset_index(drop=True)).merge(cases[["case_id", "year_reported"]], on="case_id")
past = results[results["year_reported"].isna() | (results["year_reported"] < 2025)]
bank = past_cases()

m1, m2, m3, m4 = st.columns(4)
m1.metric("📄 Fairness reports", len(bank), border=True, height="stretch",
          help="TrialWatch fairness reports searchable by argument: graded reports that analyse freedom of expression (2,075 PDF pages; some reports cover several trials or defendants)")
m2.metric("🌍 Countries covered", bank["country"].nunique(), border=True, height="stretch")
m3.metric("✅ Good outcomes", f"{int(bank['good_outcome'].sum())} of {len(bank)}", border=True, height="stretch",
          help="Good outcomes that followed TrialWatch's work: acquittal, charges dropped, conviction overturned, release, or a UN finding of arbitrary detention; "
               "each confirmed by a teammate with a source")
m4.metric("🇮🇩 Likely barred by reform", f"{int((past['verdict'] == LIKELY_BARRED).sum())} of {len(past)}",
          border=True, height="stretch", help="Past Indonesian cases the 2024–25 reform would likely bar today (for lawyer review)")

st.header("What you can do")
st.caption("Following TrialWatch's own process: evaluate a case, advocate for the defendant, then track what followed.")
PAGES = [
    ("1 · Evaluation", "pages/3_Argument_Bank.py", "Argument Bank", "📚",
     "For any case, in any country: the most similar TrialWatch trials, what followed, and their arguments on "
     "legality, vagueness, broadness, necessity and proportionality, each with its author and page."),
    ("1 · Evaluation", "pages/2_Stress_Test.py", "Stress Test", "⚖️",
     "Where a speech law was just reformed (Indonesia, 2024–25): would the reform already bar each case, by "
     "which rule, and how sure we are across ten legal readings."),
    ("2 · Advocacy", "pages/4_UN_Letter.py", "UN Letter", "✉️",
     "A submission to the UN Special Rapporteur built only from numbered sources: check, edit, check again, "
     "then a named reviewer approves and downloads it as Word."),
    ("3 · Accountability", "pages/5_Outcome_Updates.py", "Outcome Updates", "📈",
     "TrialWatch's impact after the report: verified later changes, such as a conviction overturned on "
     "appeal, and a form to record a new one."),
]
for col, (stage, path, title, icon, text) in zip(st.columns(4), PAGES):
    with col.container(border=True, height="stretch", vertical_alignment="distribute"):
        with st.container(gap="small"):
            st.caption(stage)
            st.markdown(f"#### {icon} {title}")
            st.markdown(text)
        st.page_link(path, label=f"Open {title} →")

improved = bank[bank["outcome_improved"]]
if not improved.empty:
    with st.container(border=True):
        st.markdown(f"##### 📈 Outcomes that changed for the better after TrialWatch's work: {len(improved)}")
        for r in improved.itertuples():
            st.markdown(f"- **{r.case}**: " + " → then ".join(r.outcome_history))
        st.caption("Verified updates. They *followed* TrialWatch's work; we don't claim it caused them. "
                   "The Promise Clock (below) shows whether officials kept their pledges.")

st.header("Indonesian cases by outcome")
st.caption("The cases behind the Stress Test and the UN letter examples, each checked by a teammate "
           "(data/verification_log.csv).")

log = pd.read_csv(VERIFICATION_LOG, dtype=str).fillna("")
checked = set(log.loc[log["verified_by"].str.strip() != "", "case_id"]) | set(cases.loc[cases["verified"], "case_id"])
open_items = cases[~cases["verified"]]
c1, c2, c3 = st.columns(3)
c1.metric("Cases", len(cases), border=True)
c2.metric("Checked by a teammate", f"{int(cases['case_id'].isin(checked).sum())} of {len(cases)}", border=True)
c3.metric("Fully confirmed", f"{int(cases['verified'].sum())} of {len(cases)}", border=True,
          help="Checked, with every field confirmed by a source. The rest were checked but one detail is still open.")
if not open_items.empty:
    with st.expander(f"{len(open_items)} checked case(s) with one detail still open"):
        for r in open_items.itertuples():
            st.markdown(f"- **{r.name}**: {OPEN_DETAIL.get(r.case_id, 'see the case notes')}")

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
