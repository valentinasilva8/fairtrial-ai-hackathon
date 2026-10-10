"""Outcome updates: record later verified changes to a TrialWatch case (e.g. a conviction overturned)."""

from datetime import date

import pandas as pd
import streamlit as st

from src import outcome_updates as ou
from src.argument_bank import past_cases

REPO = "https://github.com/valentinasilva8/fairtrial-ai-hackathon"
EDIT_URL = f"{REPO}/edit/main/data/trialwatch_outcome_updates.csv"

st.title("Outcome updates")
st.caption(
    "TrialWatch cases keep moving after a report: convictions are overturned on appeal, people are released, "
    "UN bodies rule. Each verified change is added to an append-only log, and the latest one becomes the case's "
    "current outcome everywhere in the app. We say a change *followed* TrialWatch's work, never that it caused it."
)

bank = past_cases()
log = ou.load()

# --- the impact so far -----------------------------------------------------------
improved = bank[bank["outcome_improved"]]
c1, c2, c3 = st.columns(3)
c1.metric("Verified updates in the log", len(log[log["verified_by"].str.strip() != ""]))
c2.metric("Cases changed for the better", len(improved))
c3.metric("Good outcomes now", f"{int(bank['good_outcome'].sum())} of {len(bank)}")

st.subheader("Log")
if log.empty:
    st.info("No updates recorded yet.")
else:
    st.dataframe(
        log[["event_date", "case", "previous_outcome", "new_outcome", "summary", "source_url", "verified_by"]]
        .sort_values("event_date", ascending=False),
        hide_index=True, width="stretch",
        column_config={"source_url": st.column_config.LinkColumn("Source", display_text="open"),
                       "event_date": "Date", "case": "Case", "previous_outcome": "Before",
                       "new_outcome": "After", "summary": "What happened", "verified_by": "Verified by"},
    )
problems = ou.problems(log, set(bank["report_url"]))
if problems:
    st.error("The log has problems and those rows can't be trusted:\n- " + "\n- ".join(problems))

# --- record a new change ---------------------------------------------------------
st.divider()
st.subheader("Record a new change")
st.markdown(
    "1. Find the source: ideally the judgment or court record, otherwise a reliable report naming the defendant.\n"
    "2. Fill in the form; it checks the entry.\n"
    "3. Copy the line it produces, open the log on GitHub, paste it as a new last line, and commit it as a pull "
    "request. The automated tests check it again before it can be merged. Then sync the fork so the live app updates."
)
names = dict(zip(bank["report_url"], bank["case"]))
url = st.selectbox("Case", list(names), format_func=names.get, key="ou_case")
row = bank.set_index("report_url").loc[url]
current = row["outcome"]
st.caption(f"Current outcome: **{current}**" + ("" if row["outcome_confirmed"] else " (unconfirmed)")
           + (f" · history: {' → then '.join(row['outcome_history'])}" if row["outcome_history"] else ""))

f1, f2 = st.columns(2)
new = f1.selectbox("New outcome", ou.LABELS, index=ou.LABELS.index("conviction overturned"), key="ou_new")
event_date = f2.text_input("Date of the decision (YYYY, YYYY-MM or YYYY-MM-DD)", key="ou_date")
summary = st.text_area("What happened (one or two sentences, facts only)", key="ou_summary")
source = st.text_input("Source URL", key="ou_source")
verifier = st.text_input("Verified by (your name)", key="ou_verifier")
notes = st.text_input("Notes (optional)", key="ou_notes")
checked = st.checkbox(
    "I checked the source myself: it names this defendant in full, it is a decision and not bail or an interim "
    "step, and the date is the decision's date.", key="ou_checked")

draft = {"report_url": url, "case": names[url], "event_date": event_date.strip(), "previous_outcome": current,
         "new_outcome": new, "summary": summary.strip(), "source_url": source.strip(),
         "verified_by": verifier.strip(), "entered_on": date.today().isoformat(), "notes": notes.strip()}
issues = ou.problems(pd.DataFrame([draft]), set(bank["report_url"]))
if not checked:
    issues.append("Tick the box to confirm you checked the source.")
if new == current:
    issues.append("The new outcome is the same as the current one.")

if issues:
    st.info("Complete the form:\n- " + "\n- ".join(i.rsplit("): ", 1)[-1] for i in issues))
else:
    line = ou.update_row(url, names[url], draft["event_date"], draft["previous_outcome"], new, draft["summary"],
                         draft["source_url"], draft["verified_by"], draft["entered_on"], draft["notes"])
    st.success(f"Entry checked: {ou.describe(draft)}" + (" · changed for the better" if ou.improved(draft) else ""))
    st.code(line, language="text")
    st.markdown(f"[Open the log on GitHub to add this line]({EDIT_URL}) — paste it as the last line, then "
                "choose **Create a new branch and start a pull request**.")
    st.download_button("Download this line (.csv)", data=line + "\n", file_name="outcome_update.csv", mime="text/csv")
