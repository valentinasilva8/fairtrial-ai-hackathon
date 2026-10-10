"""Precedent & Practice — entry point. Run: streamlit run app.py

Pages are grouped by TrialWatch's own process: Monitoring → Evaluation → Advocacy.
"""

from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Precedent & Practice", page_icon="⚖️", layout="wide")

PAGES = Path(__file__).resolve().parent / "pages"

monitoring = [st.Page(PAGES / "1_Cases.py", title="Cases", icon="📁")] if (PAGES / "1_Cases.py").exists() else []
nav = st.navigation({
    "Overview": [st.Page(PAGES / "0_Home.py", title="Home", icon="🏠", default=True)],
    **({"Monitoring": monitoring} if monitoring else {}),
    "Evaluation": [
        st.Page(PAGES / "3_Argument_Bank.py", title="Argument Bank", icon="📚"),
        st.Page(PAGES / "2_Stress_Test.py", title="Stress Test", icon="⚖️"),
    ],
    "Advocacy": [st.Page(PAGES / "4_UN_Letter.py", title="UN Letter", icon="✉️")],
})
nav.run()
