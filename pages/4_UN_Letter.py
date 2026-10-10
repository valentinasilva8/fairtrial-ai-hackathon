"""UN Special Rapporteur letter: a sourced draft built from the case, the reform and past TrialWatch arguments."""

import re
from datetime import datetime
from pathlib import Path

import streamlit as st

from src.argument_bank import arguments_available, best_arguments, similar_cases
from src.impacts import impacts_for, load_impacts
from src.data import DataValidationError, load_all, public_cases
from src.letter import (
    LLMError,
    SensitiveCaseError,
    build_sources,
    check_support,
    generate_draft,
    render,
    template_draft,
    validate,
)
from src.similarity import CHARGES, COUNTRIES, REGION, ROLES, SPEECH, features_from_case
from src.stress_test import evaluate_case

OUT_DIR = Path(__file__).resolve().parent.parent / "outputs" / "briefs"
VERDICT_COLORS = {"supported": "green", "partly supported": "orange", "not supported": "red", "not checked": "gray"}

st.title("UN Special Rapporteur letter")
st.caption(
    "A draft submission to the UN Special Rapporteur on freedom of opinion and expression, built from the case "
    "record, the reform stress test, official pledges and arguments from similar TrialWatch cases."
)
st.warning(
    "**Draft for lawyer review.** Every sentence cites its sources, and drafts with an uncited sentence, an "
    "unknown source or an invented quotation are rejected. A second check flags sentences the sources don't "
    "fully support. Nothing is sent from here. Sensitive cases can't be used, because Gemini's free tier may "
    "use prompts to improve Google's products.",
    icon="⚖️",
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
NEW = "new_case"
names = {NEW: "➕ A new case, any country (describe it below)", **dict(zip(cases["case_id"], cases["name"]))}
case_id = st.selectbox("Case", list(names), index=1, format_func=names.get, key="letter_case")

if case_id == NEW:
    st.markdown("**Describe the case.** Only what you enter here is used about the case, and it is marked "
                "unverified until a person checks it against a source.")
    n1, n2 = st.columns(2)
    name = n1.text_input("Defendant's name", key="lt_name")
    role = n2.text_input("Who they are (e.g. journalist, activist)", key="lt_role")
    country = n1.text_input("Country", key="lt_country")
    law = n2.text_input("Law or charge", key="lt_law", placeholder="e.g. Article 495 of the Criminal Code")
    facts = st.text_area("What happened (facts only)", key="lt_facts", height=100)
    source = st.text_input("Source for these facts (URL or citation)", key="lt_source")
    f1, f2 = st.columns(2)
    charges = f1.multiselect("Charge type (for finding similar TrialWatch trials)", list(CHARGES), key="lt_charges")
    speech = f2.multiselect("Kind of speech", list(SPEECH), key="lt_speech")
    roles = f1.multiselect("Defendant", list(ROLES), key="lt_roles")
    region = f2.selectbox("Region", list(REGION), key="lt_region")
    at_risk = st.checkbox("This person is at risk and the case should stay out of AI tools (sensitive)", key="lt_sensitive")
    if not (name and country and facts and charges):
        st.info("Enter at least the name, country, facts and one charge type.")
        st.stop()
    case = {"case_id": NEW, "name": name, "role": role or "not given", "country": country,
            "law": law or "a speech-related charge", "complainant": "not given", "complainant_type": "unknown",
            "article": law or "not given", "year_reported": "not given", "outcome": "as described",
            "outcome_detail": facts, "source": source, "verified": False, "sensitive": at_risk}
    features = {"country": country if country in COUNTRIES else "", "region": region,
                "charges": charges, "speech": speech, "roles": roles}
    stress, promises, events = None, [], []
else:
    case = {**cases.set_index("case_id").loc[case_id].to_dict(), "case_id": case_id}
    features = features_from_case(case)
    stress, promises = evaluate_case(case), data.promises.to_dict("records")
    events = data.events[data.events["case_id"] == case_id].to_dict("records") if data.events is not None else []

n_past = st.slider("Similar TrialWatch cases to draw arguments from", 1, 5, 3)
if not arguments_available():
    st.info("Argument text isn't loaded on this machine; the letter will cite the case, reform and pledges only. "
            "Run the scripts in docs/ARGUMENT_BANK.md to add TrialWatch arguments.")

matches = similar_cases(features, top_n=n_past)
impact_sheet = load_impacts()
past = [{**m, "arguments": best_arguments(m["report_url"]), "impacts": impacts_for(m["report_url"], impact_sheet)}
        for m in matches.to_dict("records")]
try:
    sources = build_sources(case, events, stress, promises, past)
except SensitiveCaseError as e:
    st.warning(f"{e} Nothing has been sent to any AI tool.")
    st.stop()

with st.expander(f"Sources the letter may use ({len(sources)})"):
    for s in sources:
        tag = "" if s.verified else " · :gray-background[unverified]"
        st.markdown(f"`{s.id}` **{s.label}**{tag}" + (f" — {s.url}" if s.url else ""))

key = f"letter_{case_id}_{n_past}_{hash(str(case))}"
b1, b2 = st.columns(2)
if b1.button("Draft with Gemini", type="primary"):
    try:
        with st.spinner("Drafting and checking every citation…"):
            draft, problems = generate_draft(sources)
        st.session_state[key] = {"draft": draft, "problems": problems, "by": "Gemini"}
    except LLMError as e:
        st.error(f"{e} You can build a plain draft without AI instead.")
if b2.button("Build plain draft (no AI)"):
    d = template_draft(sources)
    st.session_state[key] = {"draft": d, "problems": validate(d, sources), "by": "template"}

state = st.session_state.get(key)
if not state:
    st.stop()

if state["problems"]:
    st.error("This draft failed the citation check after 3 attempts and must not be used:\n- "
             + "\n- ".join(state["problems"]))
    st.stop()

st.success("Citation check passed: every sentence cites a known source and every quotation is in its source.")
letter = render(state["draft"], sources, case["name"])
st.markdown(letter)

# --- second check: does each source actually say it? ----------------------
st.divider()
st.subheader("Sentence-by-sentence support check")
if st.button("Check each sentence against its sources"):
    try:
        with st.spinner("Checking…"):
            state["support"] = check_support(state["draft"], sources)
    except LLMError as e:
        st.error(str(e))
if state.get("support"):
    support = state["support"]
    flagged = [c for c in support if c["verdict"] != "supported"]
    st.markdown(f"**{len(support) - len(flagged)} of {len(support)} sentences fully supported.** "
                "Review every flagged sentence before approving.")
    for c in flagged:
        st.markdown(f":{VERDICT_COLORS.get(c['verdict'], 'gray')}-background[{c['verdict']}] "
                    f"*{c['heading']}*, sentence {c['n']}: {c['text']}")
        st.caption(c["reason"])

# --- human decision ---------------------------------------------------------
st.divider()
st.subheader("Review")
reviewer = st.text_input("Reviewer name", key=f"{key}_reviewer")
read_all = st.checkbox("I have read the whole draft and every flagged sentence", key=f"{key}_read")
a1, a2 = st.columns(2)
if a1.button("Approve and save", disabled=not (reviewer.strip() and read_all)):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = OUT_DIR / f"{re.sub(r'[^a-z0-9_]', '', case_id)}_{stamp}.md"
    checked = state.get("support")
    note = (f"{sum(c['verdict'] == 'supported' for c in checked)}/{len(checked)} sentences fully supported"
            if checked else "support check not run")
    path.write_text(f"<!-- approved by {reviewer.strip()} on {stamp}; drafted by {state['by']}; {note} -->\n\n{letter}\n")
    st.success(f"Saved to outputs/briefs/{path.name}.")
if a2.button("Mark sensitive (don't use)"):
    st.session_state.pop(key, None)
    st.warning(f"Draft discarded. To keep {case['name']} out of all public views and briefs, set "
               f"sensitive=true for `{case_id}` in data/cases_seed.csv.")
