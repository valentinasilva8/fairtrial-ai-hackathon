"""Precedent & Practice — entry point. Run: streamlit run app.py

Pages are grouped by TrialWatch's own process: Monitoring → Evaluation → Advocacy.
"""

from pathlib import Path

import streamlit as st

from src import theme

st.set_page_config(page_title="Precedent & Practice", page_icon="⚖️", layout="wide")

PAGES = Path(__file__).resolve().parent / "views"

monitoring = [st.Page(PAGES / "1_Cases.py", title="Cases", icon="📁")] if (PAGES / "1_Cases.py").exists() else []
nav = st.navigation({
    "Overview": [st.Page(PAGES / "0_Home.py", title="Start here", icon="🧭", default=True)],
    **({"Monitoring": monitoring} if monitoring else {}),
    "Evaluation": [
        st.Page(PAGES / "3_Argument_Bank.py", title="Argument Bank", icon="📚"),
        st.Page(PAGES / "2_Stress_Test.py", title="Stress Test", icon="⚖️"),
    ],
    "Advocacy": [st.Page(PAGES / "4_UN_Letter.py", title="UN Letter", icon="✉️")],
    "Accountability": [st.Page(PAGES / "5_Outcome_Updates.py", title="Outcome Updates", icon="📈")],
})
theme.apply()
nav.run()
theme.footer()

# FairTrial guide on every page. Fail-safe: if the assistant ever errors, the site still runs.
try:
    from src.assistant_ui import render_assistant

    render_assistant(nav.title)
except Exception:
    pass
