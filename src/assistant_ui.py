"""Floating FairTrial guide: a robot in the lower-right corner of every page.

Click the robot to open the chat panel (quick guides, suggested legal questions, chat).
While it works, the robot bobs and a "thinking" bubble appears above its head; the
answer then pops up in that speech bubble. Native Streamlit only: the CSS is scoped to
the pa_* container keys.
"""

from __future__ import annotations

import base64
import time
from functools import lru_cache

import streamlit as st
from streamlit.errors import StreamlitAPIException

from src.assistant import MAX_HISTORY, MAX_QUESTION, ROOT, answer_for, guides, knowledge, questions
from src.llm import LLMError

ROBOT = ROOT / "assets" / "assistant_robot.png"
THINK_SECONDS = 1.6  # how long the thinking animation shows

CSS = """<style>
.st-key-pa_launcher {position:fixed!important; right:20px; bottom:24px; width:124px!important; z-index:999990;}
.st-key-pa_launcher button {width:120px; height:120px; border:0; border-radius:24px; box-shadow:none;
  background:transparent url('data:image/png;base64,%(robot)s') center/contain no-repeat;
  filter:drop-shadow(0 6px 8px #24141633); transition:transform .15s ease;}
.st-key-pa_launcher button:hover {transform:translateY(-3px); background-color:transparent;}
.st-key-pa_launcher button:focus-visible {outline:3px solid #7b1e2b; outline-offset:4px;}
.st-key-pa_launcher button p {position:absolute; width:1px; height:1px; overflow:hidden; clip-path:inset(50%%);}
.st-key-pa_bubble {position:fixed!important; right:20px; bottom:156px; width:min(330px, calc(100vw - 40px))!important;
  max-height:46vh; overflow:visible; z-index:999991; background:#fff; color:#241a1b; border:1px solid #e3d3d0;
  border-radius:18px; padding:12px 14px; box-shadow:0 10px 32px #24141626; gap:6px!important;
  animation:pa-pop .22s ease-out; box-sizing:border-box;}
.st-key-pa_bubble::after {content:""; position:absolute; right:56px; bottom:-9px; width:16px; height:16px;
  background:#fff; border-right:1px solid #e3d3d0; border-bottom:1px solid #e3d3d0; transform:rotate(45deg);}
.st-key-pa_bubble_body {max-height:calc(46vh - 60px); overflow-y:auto; font-size:14px;}
.st-key-pa_bubble_close {position:absolute!important; top:2px; right:4px; width:auto!important; z-index:2;}
.st-key-pa_bubble_close button {border:0; background:transparent; min-height:0; padding:2px 8px;}
.st-key-pa_panel {position:fixed!important; right:%(panel_right)s; bottom:24px; width:min(390px, calc(100vw - 32px))!important;
  max-height:calc(100vh - 110px); overflow-y:auto; z-index:999989; box-sizing:border-box; padding:16px;
  background:#faf7f5; border:1px solid #e3d3d0; border-radius:20px; box-shadow:0 12px 44px #24141633; gap:8px!important;}
.st-key-pa_panel h3 {font-size:19px; padding:0; margin:0;}
.st-key-pa_panel [data-testid="stHorizontalBlock"] {flex-wrap:nowrap!important; align-items:center;}
.st-key-pa_panel [data-testid="stColumn"] {min-width:0!important; width:auto!important; flex:1 1 0!important;}
.st-key-pa_panel [data-testid="stColumn"]:first-child {flex:5 1 0!important;}
.st-key-pa_panel [data-testid="stChatMessage"] {padding:8px; font-size:14px;}
.st-key-pa_chips button, .st-key-pa_legal button {width:100%%; justify-content:flex-start; text-align:left;
  font-size:13px; min-height:0; padding:5px 10px; border-radius:14px; border-color:#d9c3bf;}
.pa-label {font-size:12px; color:#7a6466; margin:6px 0 2px;}
.pa-thinking {display:flex; align-items:center; gap:10px; font-size:14px; color:#5b4547;}
.pa-dots {display:inline-flex; gap:5px;}
.pa-dots span {width:8px; height:8px; border-radius:50%%; background:#7b1e2b; animation:pa-bounce 1.2s infinite ease-in-out;}
.pa-dots span:nth-child(2) {animation-delay:.15s;} .pa-dots span:nth-child(3) {animation-delay:.3s;}
@keyframes pa-bounce {0%%,80%%,100%% {transform:translateY(0); opacity:.35;} 40%% {transform:translateY(-6px); opacity:1;}}
@keyframes pa-pop {from {transform:translateY(8px) scale(.96); opacity:0;} to {transform:none; opacity:1;}}
@keyframes pa-bob {0%%,100%% {transform:translateY(0) rotate(0);} 25%% {transform:translateY(-5px) rotate(-3deg);}
  75%% {transform:translateY(-5px) rotate(3deg);}}
%(thinking)s
@media (max-width:700px) {
  .st-key-pa_launcher {right:12px; bottom:16px; width:88px!important;}
  .st-key-pa_launcher button {width:84px; height:84px;}
  .st-key-pa_bubble {right:12px; bottom:110px;}
  .st-key-pa_panel {right:12px; bottom:110px; max-height:60vh;}
}
</style>"""
THINKING_CSS = ".st-key-pa_launcher button {animation:pa-bob 1s infinite ease-in-out;}"
THINKING_HTML = ('<div class="pa-thinking"><span class="pa-dots"><span></span><span></span><span></span></span>'
                 "Thinking…</div>")


@lru_cache(maxsize=1)
def robot_data() -> str:
    return base64.b64encode(ROBOT.read_bytes()).decode()


def _state():
    ss = st.session_state
    ss.setdefault("pa_open", False)
    ss.setdefault("pa_messages", [])
    ss.setdefault("pa_pending", None)   # question waiting for an answer
    ss.setdefault("pa_bubble", None)    # assistant message shown in the speech bubble
    return ss


def _remember(*messages):
    ss = st.session_state
    ss.pa_messages = (ss.pa_messages + list(messages))[-MAX_HISTORY:]


def _toggle():
    st.session_state.pa_open = not st.session_state.pa_open


def _clear():
    st.session_state.update(pa_messages=[], pa_bubble=None, pa_pending=None)
    st.session_state.pop("pa_error", None)


def _close_bubble():
    st.session_state.pa_bubble = None


def _guide(source: dict):
    answer = {"role": "assistant", "content": source["text"], "generated": False,
              "evidence": [{"source_id": source["id"], "quote": source["text"]}]}
    _remember({"role": "user", "content": source["title"]}, answer)
    st.session_state.pa_bubble = answer
    st.session_state.pop("pa_error", None)


def _queue(question: str):
    ss = st.session_state
    question = (question or "").strip()
    if not question:
        return
    ss.pop("pa_error", None)
    _remember({"role": "user", "content": question})
    ss.pa_pending = question


def _submit():
    _queue(st.session_state.get("pa_input", ""))


def _sources(message: dict, lookup: dict):
    if message.get("evidence") and message.get("generated"):
        with st.expander("Sources"):
            for item in message["evidence"]:
                source = lookup[item["source_id"]]
                by = f" · {source['author']}" if source.get("author") else ""
                st.caption(f"[{source['id']}] {source['title']}{by}")
                st.markdown("> " + item["quote"].replace("\n", "\n> "))
                if source.get("url"):
                    st.link_button(f"Open report · p. {source['page']}", source["url"])
    elif message.get("generated"):
        st.caption("No supporting excerpt attached.")


def _panel(lookup: dict):
    ss = st.session_state
    with st.container(key="pa_panel"):
        title, clear, close = st.columns([5, 1, 1])
        title.markdown("### FairTrial guide")
        clear.button("↺", key="pa_clear", help="Clear chat", on_click=_clear)
        close.button("✕", key="pa_close", help="Close", on_click=_toggle)
        if not ss.pa_messages:
            st.markdown("Hi! I can show you around the website and explain fair-trial and free-expression "
                        "standards from TrialWatch reports. Pick a question to start.")
        st.markdown('<p class="pa-label">Quick guides</p>', unsafe_allow_html=True)
        with st.container(key="pa_chips"):
            for source in guides():
                st.button(source["title"], key="pa_" + source["id"], on_click=_guide, args=(source,))
        st.markdown('<p class="pa-label">Ask the legal guide</p>', unsafe_allow_html=True)
        with st.container(key="pa_legal"):
            for i, q in enumerate(questions()):
                st.button(q, key=f"pa_q{i}", on_click=_queue, args=(q,))
        if ss.pa_messages:
            with st.container(height=200, key="pa_history"):
                for message in ss.pa_messages:
                    avatar = str(ROBOT) if message["role"] == "assistant" else None
                    with st.chat_message(message["role"], avatar=avatar):
                        st.markdown(message["content"])
                        if message["role"] == "assistant":
                            _sources(message, lookup)
        st.caption("Answers come from a curated library of TrialWatch reports. For lawyer review, not legal "
                   "advice. Don't share sensitive case details.")
        if ss.get("pa_error"):
            st.warning(ss.pa_error)
        st.chat_input("Ask a question…", key="pa_input", max_chars=MAX_QUESTION,
                      on_submit=_submit)


def _bubble(page: str, lookup: dict):
    ss = st.session_state
    if ss.pa_pending:
        with st.container(key="pa_bubble"):
            st.markdown(THINKING_HTML, unsafe_allow_html=True)
        question, ss.pa_pending = ss.pa_pending, None
        try:
            time.sleep(THINK_SECONDS)
            answer = answer_for(question)
            _remember(answer)
            ss.pa_bubble = answer
        except LLMError as exc:
            ss.pa_error = f"{exc} Your question: {question}"
            ss.pa_bubble = {"role": "assistant", "content": str(exc), "generated": False, "evidence": []}
        try:
            st.rerun(scope="fragment")
        except StreamlitAPIException:  # not inside a fragment rerun
            st.rerun()
    if ss.pa_bubble:
        with st.container(key="pa_bubble"):
            st.button("✕", key="pa_bubble_close", help="Dismiss", on_click=_close_bubble)
            with st.container(key="pa_bubble_body"):
                st.markdown(ss.pa_bubble["content"])
                _sources(ss.pa_bubble, lookup)


@st.fragment
def render_assistant(page: str = "Start here"):
    ss = _state()
    thinking = bool(ss.pa_pending)
    bubble_shown = thinking or bool(ss.pa_bubble)
    st.markdown(CSS % {"robot": robot_data(), "thinking": THINKING_CSS if thinking else "",
                       "panel_right": "366px" if bubble_shown else "156px"}, unsafe_allow_html=True)
    with st.container(key="pa_launcher"):
        st.button("Close the FairTrial guide" if ss.pa_open else "Open the FairTrial guide",
                  key="pa_toggle", help="Ask the FairTrial guide", on_click=_toggle)
    lookup = {s["id"]: s for s in knowledge()}
    if ss.pa_open:
        _panel(lookup)
    _bubble(page, lookup)
