"""Look and feel: burgundy styling, a gavel cursor across the app, a courtroom-door intro and a credits footer.

Pure CSS injected through st.markdown, so it works on Streamlit Community Cloud with no extra packages.
Animations are skipped for people who ask their system for reduced motion.
"""

from urllib.parse import quote

import streamlit as st

# A small gavel, drawn as SVG and used as the cursor everywhere except text boxes (hotspot at the head's tip).
GAVEL_SVG = """<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 32 32'>
<g transform='rotate(-40 16 16)'>
<rect x='14.5' y='12' width='3' height='18' rx='1.5' fill='#7a4a24' stroke='#3b2412' stroke-width='0.8'/>
<rect x='7' y='4' width='18' height='9' rx='2.5' fill='#a8692f' stroke='#3b2412' stroke-width='1'/>
<rect x='5' y='5' width='3' height='7' rx='1' fill='#c9a227' stroke='#3b2412' stroke-width='0.8'/>
<rect x='24' y='5' width='3' height='7' rx='1' fill='#c9a227' stroke='#3b2412' stroke-width='0.8'/>
</g></svg>"""
GAVEL_CURSOR = f"url(\"data:image/svg+xml;utf8,{quote(GAVEL_SVG)}\") 6 6, pointer"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Inter:wght@400;500;600&display=swap');

html, body, [data-testid="stAppViewContainer"] { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4, [data-testid="stHeading"] * { font-family: 'Libre Baskerville', Georgia, serif !important; letter-spacing: -0.01em; }
h1 { color: #7b1e2b; }

/* Gavel cursor across the whole app; text boxes keep the text cursor so typing still feels normal */
html, body, *, *::before, *::after { cursor: %(cursor)s !important; }
input:not([type="checkbox"]):not([type="radio"]), textarea, [contenteditable="true"],
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea { cursor: text !important; }

/* Soft cards (containers keyed "pp-card-...") that lift a little on hover */
[data-testid="stMetric"] { padding: 14px 18px; box-sizing: border-box; }
[class*="st-key-pp-card"], [data-testid="stMetric"] { border-radius: 14px; background: #ffffff;
  transition: transform .15s ease, box-shadow .15s ease; }
[class*="st-key-pp-card"]:hover, [data-testid="stMetric"]:hover { box-shadow: 0 6px 18px rgba(123, 30, 43, .16); transform: translateY(-2px); }
[data-testid="stMetricValue"] { color: #7b1e2b; font-family: 'Libre Baskerville', Georgia, serif; }

/* Sidebar: a dark burgundy panel */
[data-testid="stSidebar"] { background: linear-gradient(180deg, #3d0c14 0%%, #6e1a27 100%%); }
[data-testid="stSidebar"] * { color: #f1efe6 !important; }
[data-testid="stSidebarNav"] a[aria-current="page"] { background: rgba(201, 162, 39, .25) !important; border-radius: 8px; }

/* Buttons */
.stButton > button, .stDownloadButton > button { border-radius: 999px; font-weight: 600; }
</style>
"""

DOORS = """
<style>
.pp-court { position: fixed; inset: 0; z-index: 999999; pointer-events: none; perspective: 1600px;
  animation: pp-fade .6s ease 3.2s forwards; }
.pp-door { position: absolute; top: 0; width: 50%; height: 100%;
  background: repeating-linear-gradient(90deg, #4e1519 0 14px, #5e1c21 14px 30px, #4a1418 30px 44px);
  box-shadow: inset 0 0 0 14px #2a0a0e, inset 0 0 0 18px #c9a227; }
.pp-door::before { content: ""; position: absolute; inset: 12%% 14%%; border: 3px solid #c9a227; border-radius: 6px;
  box-shadow: inset 0 0 0 10px rgba(0, 0, 0, .18); }
.pp-left { left: 0; transform-origin: left center; animation: pp-open-left 1.5s cubic-bezier(.6, .05, .3, 1) 1.5s forwards; }
.pp-right { right: 0; transform-origin: right center; animation: pp-open-right 1.5s cubic-bezier(.6, .05, .3, 1) 1.5s forwards; }
.pp-handle { position: absolute; top: 50%%; width: 14px; height: 70px; margin-top: -35px; border-radius: 7px;
  background: linear-gradient(#f3d77a, #a8801b); }
.pp-left .pp-handle { right: 26px; } .pp-right .pp-handle { left: 26px; }
.pp-sign { position: absolute; top: 7%%; left: 0; right: 0; z-index: 2; text-align: center; padding: 18px 0 22px;
  background: linear-gradient(180deg, rgba(40, 6, 12, .92), rgba(40, 6, 12, .75)); border-bottom: 3px solid #c9a227;
  font-family: 'Libre Baskerville', Georgia, serif; color: #f6e7b0; text-shadow: 0 2px 8px rgba(0, 0, 0, .6);
  animation: pp-fade .5s ease 1.6s forwards; }
.pp-sign .pp-gavel { font-size: 64px; display: inline-block; transform-origin: 80%% 80%%; animation: pp-strike .3s ease-in .2s 4 alternate; }
.pp-sign .pp-title { font-size: 34px; font-weight: 700; margin-top: 8px; }
.pp-sign .pp-sub { font-size: 15px; letter-spacing: .2em; text-transform: uppercase; margin-top: 6px; }
@keyframes pp-open-left { to { transform: rotateY(-100deg); } }
@keyframes pp-open-right { to { transform: rotateY(100deg); } }
@keyframes pp-fade { to { opacity: 0; visibility: hidden; } }
@keyframes pp-strike { from { transform: rotate(0deg); } to { transform: rotate(-35deg); } }
@media (prefers-reduced-motion: reduce) { .pp-court { display: none; } }
</style>
<div class="pp-court" aria-hidden="true">
  <div class="pp-door pp-left"><div class="pp-handle"></div></div>
  <div class="pp-door pp-right"><div class="pp-handle"></div></div>
  <div class="pp-sign"><div class="pp-gavel">🔨</div><div class="pp-title">Precedent &amp; Practice</div>
  <div class="pp-sub">Court is now in session</div></div>
</div>
"""


FOOTER = (
    "Built by **Shreya, Valentina, Ungu, Layla and Yuki** · TrialWatch Fair Trial & AI Hackathon, Columbia Law "
    "School, October 2026 · © 2026 the Precedent & Practice team; code under the MIT license; TrialWatch report "
    "excerpts © Clooney Foundation for Justice, all rights reserved · An independent project, not endorsed by the "
    "Clooney Foundation for Justice, TrialWatch® or Columbia Law School."
)


def apply() -> None:
    """Style every page (call before the page runs)."""
    st.markdown(CSS % {"cursor": GAVEL_CURSOR}, unsafe_allow_html=True)


def doors() -> None:
    """The courtroom doors open; played each time the Start here page is opened."""
    st.markdown(DOORS.replace("%%", "%"), unsafe_allow_html=True)


def footer() -> None:
    """Team credits at the bottom of every page (call after the page runs)."""
    st.divider()
    st.caption(FOOTER)
