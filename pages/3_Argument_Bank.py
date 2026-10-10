"""Argument Bank: past TrialWatch cases like this one, what happened, and the arguments made."""

import streamlit as st

from src.argument_bank import (
    CATEGORY_LABELS,
    arguments_available,
    best_arguments,
    hrc_decisions,
    page_link,
    similar_cases,
)
from src.data import DataValidationError, load_all, public_cases
from src.similarity import CHARGES, REGION, ROLES, SPEECH, features_from_case


st.title("Argument Bank")
st.caption(
    "Past TrialWatch cases similar to a current case, what happened in them, and the arguments "
    "TrialWatch's experts made, from 47 graded freedom-of-expression reports on cfj.org."
)
st.warning(
    "**For lawyer review — not legal advice.** The arguments are TrialWatch experts' analysis in "
    "their fairness reports, not necessarily what was argued in court. A good outcome *followed* "
    "these cases; we do not claim the arguments caused it.",
    icon="⚖️",
)


@st.cache_data
def get_cases():
    return public_cases(load_all().cases)


try:
    cases = get_cases()
except DataValidationError as e:
    st.error(f"Could not load data: {e}")
    st.stop()

# --- the current case ------------------------------------------------------
names = dict(zip(cases["case_id"], cases["name"]))
case_id = st.selectbox("Current case", list(names), format_func=names.get, key="ab_case")
case = cases.set_index("case_id").loc[case_id].to_dict()
default = features_from_case(case)

st.markdown("**How we describe this case for matching** (edit if the data is incomplete)")
c1, c2 = st.columns(2)
c3, c4 = st.columns(2)
charges = c1.multiselect("Charge type", list(CHARGES), default=default["charges"], key=f"ab_ch_{case_id}")
speech = c2.multiselect("Kind of speech", list(SPEECH), default=default["speech"], key=f"ab_sp_{case_id}")
roles = c3.multiselect("Defendant", list(ROLES), default=default["roles"], key=f"ab_ro_{case_id}")
region = c4.selectbox("Region", list(REGION), index=list(REGION).index(default["region"]), key=f"ab_re_{case_id}")
current = {"country": default["country"] if region == default["region"] else "",
           "region": region, "charges": charges, "speech": speech, "roles": roles}

o1, o2 = st.columns(2)
top_n = o1.slider("Number of similar cases", 3, 15, 6)
good_first = o2.toggle("List good outcomes first", value=True)

if not charges:
    st.info("Choose at least one charge type to find similar cases.")
    st.stop()

matches = similar_cases(current, top_n=top_n, good_first=good_first)
if matches.empty:
    st.info("No past TrialWatch case shares a charge type with this one.")
    st.stop()

n_good = int(matches["good_outcome"].sum())
st.header(f"{len(matches)} similar TrialWatch cases · {n_good} with a good outcome")
st.caption("Outcomes marked *unconfirmed* are machine suggestions waiting for a person to check them "
           "(see docs/VERIFY_OUTCOMES.md). Argument categories are assigned by keyword matching and are "
           "about 75–80% right in our spot checks; the page link always shows the exact text.")

if not arguments_available():
    st.info(
        "Argument text isn't loaded on this machine (it's CFJ's text, so it isn't in the repository). "
        "Run `python scripts/fetch_trialwatch_reports.py` then `python scripts/build_report_index.py`. "
        "Matches, outcomes and links still work."
    )

# --- similar cases ---------------------------------------------------------
for m in matches.itertuples():
    color = "green" if m.good_outcome else "gray"
    confirmed = "confirmed" if m.outcome_confirmed else "unconfirmed"
    with st.expander(f"{m.case} · grade {m.grade} · outcome: {m.outcome} ({confirmed})", expanded=m.Index == 0):
        st.markdown(
            f":{color}-background[{m.outcome} · {confirmed}] · TrialWatch grade **{m.grade}** · "
            f"match score {m.score}"
        )
        st.caption("Why it matched: " + "; ".join(m.why))
        links = [f"[TrialWatch report]({m.report_url})"]
        if m.pdf_url:
            links.append(f"[PDF]({m.pdf_url})")
        if m.outcome_confirmed and m.outcome_source_url:
            links.append(f"[outcome source]({m.outcome_source_url})")
        elif m.suggested_from:
            links.append(f"[source of suggested outcome]({m.suggested_from})")
        st.markdown(" · ".join(links))

        args = best_arguments(m.report_url)
        for cat, label in CATEGORY_LABELS.items():
            if cat not in args:
                continue
            p = args[cat][0]
            st.markdown(f"**{label}** — [page {p['page']}]({page_link(m.pdf_url, p['page'])})")
            st.markdown(f"> {p['text']}")

        decisions = hrc_decisions(m.report_url)
        if decisions:
            st.caption(f"UN Human Rights Committee decisions cited in this report ({len(decisions)}): "
                       + ", ".join(decisions))
