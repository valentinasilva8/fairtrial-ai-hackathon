"""Argument Bank: past TrialWatch cases like this one, what happened, and the arguments made."""

import streamlit as st

from src.argument_bank import (
    CATEGORY_LABELS,
    MENTOR_LABELS,
    grouped_arguments,
    arguments_available,
    best_arguments,
    hrc_decisions,
    page_link,
    similar_cases,
)
from src.data import DataValidationError, load_all, public_cases
from src.impacts import impact_lines, impact_markdown, load_impacts
from src.similarity import CHARGES, COUNTRIES, REGION, ROLES, SPEECH, features_from_case, region_of


st.title("Argument Bank")
st.caption(
    "Past TrialWatch cases similar to a current case, what happened in them, and the arguments "
    "TrialWatch's experts made, from 47 graded freedom-of-expression reports on cfj.org (2,075 PDF pages)."
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
NEW = "__new__"
names = {NEW: "➕ A new case (describe it below)", **dict(zip(cases["case_id"], cases["name"]))}
case_id = st.selectbox("Current case", list(names), index=1, format_func=names.get, key="ab_case")
if case_id == NEW:
    st.text_input("Case name (for your reference)", key="ab_new_name", placeholder="e.g. a journalist charged over a Facebook post")
    new_country = st.selectbox("Country (optional; listed if TrialWatch has graded a trial there)",
                               [""] + COUNTRIES, key="ab_new_country")
    default = {"country": new_country, "region": region_of(new_country) or "Southeast Asia",
               "charges": [], "speech": [], "roles": []}
else:
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

# --- hand the same case to the UN Letter page ------------------------------------
if st.button("✉️ Draft a UN letter for this case", type="primary", key="ab_to_letter"):
    st.session_state["letter_case"] = "new_case" if case_id == NEW else case_id
    st.session_state["letter_features"] = {"case_id": st.session_state["letter_case"], **current}
    st.session_state["letter_n_past"] = min(top_n, 5)
    st.session_state["letter_autodraft"] = True
    if case_id == NEW:
        st.session_state["lt_name"] = st.session_state.get("ab_new_name", "")
        st.session_state["lt_country"] = current["country"]
        st.session_state["lt_charges"] = charges
        st.session_state["lt_speech"] = speech
        st.session_state["lt_roles"] = roles
        st.session_state["lt_region"] = region
    st.switch_page("pages/4_UN_Letter.py")

n_good = int(matches["good_outcome"].sum())
st.header(f"{len(matches)} similar TrialWatch cases · {n_good} with a good outcome")
st.caption("Outcomes marked *unconfirmed* are machine suggestions waiting for a person to check them "
           "(see docs/VERIFY_OUTCOMES.md). Argument labels are assigned by keyword matching and a person should "
           "confirm them (spot checks of our earlier labels: about 75–80% right); every page link shows the exact text.")

impacts = load_impacts()  # small CSV; not cached so a rebuilt sheet shows at once
if not impacts:
    st.caption("The impact sheet isn't built on this machine (`python scripts/build_impacts.py`); "
               "everything else works.")

if not arguments_available():
    st.info(
        "Argument text isn't loaded on this machine (it's CFJ's text, so it isn't in the repository). "
        "Run `python scripts/fetch_trialwatch_reports.py` then `python scripts/build_report_index.py`. "
        "Matches, outcomes and links still work."
    )

by_argument, by_case = st.tabs(["By argument", "By case"])

# --- by argument: the five labels across all similar cases -----------------
with by_argument:
    st.caption(
        "The arguments made in the similar cases, grouped by the five labels (then other recurring points). "
        "Identical paragraphs reused across reports are shown once, with every report that uses them. "
        "Each report's analysis is its named author's, not necessarily the Clooney Foundation for Justice's."
    )
    groups = grouped_arguments(matches)
    if not groups:
        st.info("No argument text available for these cases.")
    for label in list(MENTOR_LABELS) + [c for c in CATEGORY_LABELS if c not in MENTOR_LABELS]:
        if label not in groups:
            continue
        n_reports = sum(len(g["cases"]) for g in groups[label])
        with st.expander(f"{CATEGORY_LABELS[label]} · {len(groups[label])} distinct arguments from {n_reports} reports",
                         expanded=label == "legality"):
            for g in groups[label]:
                shared = len(g["cases"]) > 1
                for c in g["cases"]:
                    tag = (":green-background[" if c["good"] else ":gray-background[") + \
                          f"{c['outcome']}{'' if c['confirmed'] else ' · unconfirmed'}" + \
                          (" · changed for the better" if c.get("improved") else "") + "]"
                    by = f" · report by {c['author']}" if c["author"] else ""
                    st.markdown(f"**{c['case']}**{by} · [page {c['page']}]({c['link']}) {tag}")
                if shared:
                    st.caption(f"Same paragraph in {len(g['cases'])} reports — one drafting, counted once.")
                st.markdown(f"> {g['text']}")
                st.divider()

# --- by case ------------------------------------------------------------------
with by_case:
    for m in matches.itertuples():
        color = "green" if m.good_outcome else "gray"
        confirmed = "confirmed" if m.outcome_confirmed else "unconfirmed"
        with st.expander(f"{m.case} · grade {m.grade} · outcome: {m.outcome} ({confirmed})", expanded=m.Index == 0):
            st.markdown(
                f":{color}-background[{m.outcome} · {confirmed}] · TrialWatch grade **{m.grade}** · "
                f"match score {m.score}"
            )
            st.caption("Why it matched: " + "; ".join(m.why))
            if m.outcome_history:
                mark = " · :green-background[changed for the better]" if m.outcome_improved else ""
                st.markdown("**Outcome history:** " + " → then ".join(m.outcome_history) + mark)
                st.caption("Recorded in data/trialwatch_outcome_updates.csv after a person checked the source. "
                           "The change followed TrialWatch's work; we don't claim it caused it.")
            if m.author:
                st.caption(f"Report by {m.author} for TrialWatch. The analysis is the author's and not necessarily "
                           "the Clooney Foundation for Justice's.")
            links = [f"[TrialWatch report]({m.report_url})"]
            if m.pdf_url:
                links.append(f"[PDF]({m.pdf_url})")
            if m.outcome_confirmed and m.outcome_source_url:
                links.append(f"[outcome source]({m.outcome_source_url})")
            elif m.suggested_from:
                links.append(f"[source of suggested outcome]({m.suggested_from})")
            st.markdown(" · ".join(links))

            row = impacts.get(m.report_url)
            if row:
                lines = impact_lines(row)
                st.markdown("**Impact on the defendant** (sentences from the report that state it; "
                            "found by pattern matching, so they can miss things)")
                if lines:
                    st.markdown("\n".join(impact_markdown(lines)))
                else:
                    st.caption("No impact sentence found for the defendant in this report's text.")

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
