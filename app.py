"""
Interview Coding Platform — v3.0 (Bootstrap + Full Features)
Build: 2026-05-13 | Candidates: 3-col layout | Deactivate/Reactivate | PDF Export | Question Config
Stunning UI · CodeMirror Editor · Syntax Highlighting · Paste Blocked
"""
import streamlit as st
import streamlit.components.v1 as components
import warnings
warnings.filterwarnings('ignore', message='.*components.v1.html.*')
warnings.filterwarnings('ignore', message='.*use_container_width.*')
warnings.filterwarnings('ignore', message='.*label.*empty.*')
import pandas as pd
import time
import json

import db
import executor
from report_generator import generate_candidate_report

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CodeRound — Interview Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Bootstrap + Custom CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
/* Bootstrap via @import — works inside Streamlit's HTML sandbox */
@import url('https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css');
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Syne:wght@700;800&display=swap');
@import url('https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css');
/* ── Variables ── */
:root {
  --cr-orange:  #E86C2C;
  --cr-dark:    #1C1917;
  --cr-cream:   #F5F0E8;
  --cr-card:    #FFFFFF;
  --cr-border:  #E2D9CE;
  --cr-muted:   #6B6560;
  --cr-green:   #16A34A;
  --cr-red:     #DC2626;
  --cr-amber:   #D97706;
  --cr-blue:    #2563EB;
  --cr-sidebar: #1A1714;
}

/* ── App base ── */
html, body, .stApp { background: var(--cr-cream) !important; font-family: 'Inter', sans-serif !important; }
.block-container { padding: 1rem 2rem 2rem !important; max-width: 1600px !important; }

/* ── Hide Streamlit chrome ── */
header[data-testid="stHeader"], [data-testid="stDecoration"],
[data-testid="stToolbar"], .stAppHeader { display: none !important; }
.stApp > div:first-child { padding-top: 0 !important; }
[data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] { display: none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: var(--cr-sidebar) !important; border-right: none !important; box-shadow: 4px 0 20px rgba(0,0,0,0.15) !important; }
[data-testid="stSidebar"] * { color: #E7E5E0 !important; }
[data-testid="stSidebarContent"] { padding-top: 0 !important; }

/* ── Sidebar buttons (nav) ── */
/* Nav buttons */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    color: #C8C3BC !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    text-align: left !important;
    transition: all 0.15s ease !important;
    padding: 7px 12px !important;
    width: 100% !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(232,108,44,0.18) !important;
    border-color: var(--cr-orange) !important;
    color: #F0EDE6 !important;
}
/* Ensure ALL text inside sidebar buttons is light — covers p, span, div */
[data-testid="stSidebar"] .stButton > button p,
[data-testid="stSidebar"] .stButton > button span,
[data-testid="stSidebar"] .stButton > button div,
[data-testid="stSidebar"] .stButton > button * {
    color: #C8C3BC !important;
}
[data-testid="stSidebar"] .stButton > button:hover p,
[data-testid="stSidebar"] .stButton > button:hover span,
[data-testid="stSidebar"] .stButton > button:hover * {
    color: #F0EDE6 !important;
}
/* Logout button — distinct orange style */
[data-testid="stSidebar"] .stButton > button[kind="secondary"]:last-of-type,
[data-testid="stSidebar"] .stButton:last-child > button {
    background: rgba(232,108,44,0.12) !important;
    border-color: rgba(232,108,44,0.35) !important;
    color: #E86C2C !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] .stButton:last-child > button p,
[data-testid="stSidebar"] .stButton:last-child > button * {
    color: #E86C2C !important;
}
[data-testid="stSidebar"] .stButton:last-child > button:hover {
    background: #E86C2C !important;
    color: white !important;
}
[data-testid="stSidebar"] .stButton:last-child > button:hover * {
    color: white !important;
}
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.08) !important; }

/* ── Main inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background: #fff !important;
    border: 1.5px solid var(--cr-border) !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--cr-dark) !important;
    font-size: 0.9rem !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--cr-orange) !important;
    box-shadow: 0 0 0 3px rgba(232,108,44,0.12) !important;
    outline: none !important;
}

/* ── Buttons ── */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: all 0.15s ease !important;
    font-size: 0.875rem !important;
}
.stButton > button[kind="primary"] {
    background: var(--cr-orange) !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 2px 8px rgba(232,108,44,0.25) !important;
}
.stButton > button[kind="primary"]:hover {
    background: #D4551A !important;
    box-shadow: 0 4px 12px rgba(232,108,44,0.35) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:not([kind="primary"]) {
    background: #fff !important;
    border: 1.5px solid var(--cr-border) !important;
    color: var(--cr-dark) !important;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: var(--cr-orange) !important;
    color: var(--cr-orange) !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background: var(--cr-orange) !important;
    border: none !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(232,108,44,0.25) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #EDE8E0 !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 3px !important;
    border: none !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 7px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    color: var(--cr-muted) !important;
    border: none !important;
    padding: 7px 18px !important;
    font-size: 0.875rem !important;
}
.stTabs [aria-selected="true"] {
    background: #fff !important;
    color: var(--cr-dark) !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
}

/* ── Progress ── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, var(--cr-orange), #F5A623) !important;
    border-radius: 99px !important;
}
.stProgress > div > div { background: #DDD8CF !important; border-radius: 99px !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #fff !important;
    border: 1.5px solid var(--cr-border) !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: #fff !important;
    border: 1.5px solid var(--cr-border) !important;
    border-radius: 10px !important;
    padding: 16px 20px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}
[data-testid="stMetricValue"] { color: var(--cr-dark) !important; font-weight: 700 !important; }

/* ── Dataframe ── */
.stDataFrame { border-radius: 10px !important; overflow: hidden !important; border: 1.5px solid var(--cr-border) !important; }

/* ── Containers with border ── */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #fff !important;
    border: 1.5px solid var(--cr-border) !important;
    border-radius: 12px !important;
    padding: 4px 8px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] pre {
    background: #F3F0EB !important; border-radius: 6px !important;
    padding: 10px 14px !important; font-size: 12.5px !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] code {
    background: #F3F0EB !important; padding: 2px 6px !important;
    border-radius: 4px !important; font-size: 0.88em !important;
}

/* ── Native sidebar collapse button — always visible & styled ── */
[data-testid="stSidebarCollapseButton"] {
    position: fixed !important;
    z-index: 99999 !important;
    opacity: 1 !important;
    visibility: visible !important;
    display: flex !important;
}
[data-testid="stSidebarCollapseButton"] button {
    background: #1A1714 !important;
    border: 1px solid rgba(232,108,44,0.4) !important;
    border-radius: 0 8px 8px 0 !important;
    color: #E86C2C !important;
    width: 24px !important;
    height: 48px !important;
    padding: 0 !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
}
[data-testid="stSidebarCollapseButton"] button:hover {
    background: #E86C2C !important;
    border-color: #E86C2C !important;
}
[data-testid="stSidebarCollapseButton"] button:hover svg { fill: white !important; }
[data-testid="stSidebarCollapseButton"] button svg {
    fill: #E86C2C !important;
    width: 14px !important;
    height: 14px !important;
}
/* Collapsed state re-open button */
[data-testid="collapsedControl"] {
    position: fixed !important;
    left: 0 !important;
    top: 50vh !important;
    transform: translateY(-50%) !important;
    z-index: 99999 !important;
    opacity: 1 !important;
    visibility: visible !important;
    display: flex !important;
    background: #1A1714 !important;
    border-radius: 0 10px 10px 0 !important;
    box-shadow: 3px 0 16px rgba(0,0,0,0.4) !important;
    border: 1px solid rgba(232,108,44,0.4) !important;
    border-left: none !important;
    padding: 14px 8px !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
}
[data-testid="collapsedControl"]:hover {
    background: #E86C2C !important;
    padding-right: 12px !important;
}
[data-testid="collapsedControl"] svg {
    fill: #E86C2C !important;
    width: 18px !important;
    height: 18px !important;
}
[data-testid="collapsedControl"]:hover svg { fill: white !important; }

/* nav buttons styled per-key below */

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #EDE8E0; }
::-webkit-scrollbar-thumb { background: #C4BDB4; border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: var(--cr-orange); }

/* ── Custom Bootstrap-style components ── */

/* Header bar */
.cr-topbar {
    background: var(--cr-dark);
    border-radius: 12px;
    padding: 14px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    color: #F0EDE6;
}
.cr-logo { font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.3rem; }
.cr-logo span { color: var(--cr-orange); }

/* Category + difficulty badges */
.cr-badge {
    display: inline-flex; align-items: center;
    font-size: 0.72rem; font-weight: 700;
    padding: 3px 10px; border-radius: 999px;
    text-transform: uppercase; letter-spacing: 0.5px;
}
/* Light variants (used on light background — question bank, template editor) */
.cr-badge.cr-badge-sql    { background: #EFF6FF; color: #2563EB; border: 1px solid #BFDBFE; }
.cr-badge.cr-badge-python { background: #F0FDF4; color: #16A34A; border: 1px solid #BBF7D0; }
.cr-badge.cr-badge-pyspark{ background: #FFF7ED; color: #EA580C; border: 1px solid #FED7AA; }
.cr-badge-easy   { background: #F0FDF4; color: #16A34A; border: 1px solid #BBF7D0; }
.cr-badge-medium { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
.cr-badge-hard   { background: #FEF2F2; color: #DC2626; border: 1px solid #FCA5A5; }
/* Dark variants (used on dark header bar) */
.cr-badge-dark-sql    { background: rgba(37,99,235,0.25); color: #93C5FD; border: 1px solid rgba(37,99,235,0.5); }
.cr-badge-dark-python { background: rgba(22,163,74,0.25); color: #86EFAC; border: 1px solid rgba(22,163,74,0.5); }
.cr-badge-dark-pyspark{ background: rgba(234,88,12,0.25);  color: #FDBA74; border: 1px solid rgba(234,88,12,0.5); }
.cr-badge-dark-easy   { background: rgba(22,163,74,0.25);  color: #86EFAC; border: 1px solid rgba(22,163,74,0.5); }
.cr-badge-dark-medium { background: rgba(217,119,6,0.25);  color: #FCD34D; border: 1px solid rgba(217,119,6,0.5); }
.cr-badge-dark-hard   { background: rgba(220,38,38,0.25);  color: #FCA5A5; border: 1px solid rgba(220,38,38,0.5); }

/* Result alerts */
.cr-alert { display: flex; align-items: center; gap: 12px; border-radius: 10px; padding: 14px 18px; font-weight: 600; font-size: 0.95rem; }
.cr-alert-success { background: #F0FDF4; border: 1.5px solid #86EFAC; color: #15803D; }
.cr-alert-danger  { background: #FEF2F2; border: 1.5px solid #FCA5A5; color: #DC2626; }
.cr-alert-warning { background: #FFF8EC; border: 1.5px solid #FCD34D; color: #92400E; }

/* Timer */
.cr-timer {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.25rem; font-weight: 600;
    color: var(--cr-orange);
    background: #2D2926;
    border-radius: 8px;
    padding: 8px 14px;
    text-align: center;
    letter-spacing: 3px;
}

/* Nav labels */
.cr-nav-label {
    font-size: 0.65rem !important; font-weight: 700 !important;
    letter-spacing: 1.5px !important; text-transform: uppercase !important;
    color: #5C5852 !important; padding: 12px 0 5px 4px !important;
    display: block !important;
}

/* Section titles */
.cr-section-title {
    font-family: 'Inter', sans-serif;
    font-weight: 700; font-size: 0.72rem;
    letter-spacing: 1.2px; text-transform: uppercase;
    color: var(--cr-muted); margin: 0 0 10px 0;
}

/* Question title */
.cr-q-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.25rem; font-weight: 800;
    color: var(--cr-dark); margin: 6px 0 0 0; line-height: 1.3;
}

/* Stat pills */
.cr-stat-box {
    background: #2D2926; border-radius: 8px;
    padding: 8px 4px; text-align: center;
}
.cr-stat-val { font-size: 1.1rem; font-weight: 700; color: var(--cr-orange); font-family: 'Syne', sans-serif; }
.cr-stat-lbl { font-size: 0.65rem; color: #5C5852; }

/* Login brand */
.cr-login-brand {
    font-family: 'Syne', sans-serif; font-weight: 800;
    font-size: 2.8rem; color: var(--cr-dark);
    letter-spacing: -1px; text-align: center; margin-bottom: 6px;
}
.cr-login-brand span { color: var(--cr-orange); }

/* Info hint box */
.cr-hint-box {
    background: #FFF8EC; border: 1.5px solid #F5A623;
    border-radius: 10px; padding: 12px 16px;
    font-size: 0.9rem; color: #7C4A00; line-height: 1.6;
    margin-top: 6px;
}

/* Bootstrap overrides for Streamlit compatibility */
.container, .container-fluid { padding: 0 !important; }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "role": None, "user": None, "candidate_id": None,
        "questions": [], "q_index": 0, "answers": {},
        "start_time": None, "page": "login", "template_name": None, "session_resumed": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()
db.init_db()


# ── Auth ──────────────────────────────────────────────────────────────────────
def login_admin(u, p):
    if db.verify_admin(u, p):
        st.session_state.update(role="admin", user=u, page="admin")
        st.rerun()
    else:
        st.error("Invalid admin credentials")

def login_candidate(u, p):
    cand = db.verify_candidate(u, p)
    if cand:
        cid = cand["id"]

        # ── Check for an existing session to resume ───────────────────────────
        existing = db.get_active_session(cid)
        resumed  = False

        if existing and existing["question_ids"]:
            # Restore questions from the existing session
            questions = db.get_session_questions(existing["question_ids"])
            if questions:
                # Restore previous answers/code from submissions
                answers   = db.restore_session_answers(cid, existing["question_ids"])
                tmpl      = db.get_candidate_template(cid)
                tmpl_name = tmpl["name"] if tmpl else None
                resumed   = True

        if not resumed:
            # Fresh session — assign new questions
            questions, tmpl_name = db.get_questions_for_candidate(cid)
            if not questions:
                cfg = db.get_interview_config()
                questions = db.get_random_questions(
                    sql_count=cfg["sql_count"],
                    python_count=cfg["python_count"],
                    pyspark_count=cfg.get("pyspark_count", 0)
                )
                tmpl_name = None
            answers = {}
            db.start_interview_session(cid, [q["id"] for q in questions])

        st.session_state.update(
            role="candidate", user=u, candidate_id=cid,
            questions=questions, q_index=0, answers=answers,
            start_time=time.time(), page="exam",
            template_name=tmpl_name,
            session_resumed=resumed
        )
        st.rerun()
    else:
        st.error("Invalid credentials or inactive account")

def logout():
    for k in list(st.session_state.keys()): del st.session_state[k]
    init_session(); st.rerun()


# ── Code Editor — Ace Editor via streamlit-ace ───────────────────────────────
# streamlit-ace wraps the Ace editor as a proper Streamlit component.
# It returns the editor content as a real Python string every render.
# We layer paste-blocking JS on top via st.markdown.

def code_editor(language: str, qid_key: str, height: int = 360) -> str:
    """
    Ace Editor with syntax highlighting, auto-indent, and paste blocking.
    Returns the current code string reliably.
    """
    try:
        from streamlit_ace import st_ace
    except ImportError:
        st.error("Missing dependency: `pip install streamlit-ace`")
        return ""

    widget_key = f"ace_{qid_key}"
    store_key  = f"ace_store_{qid_key}"

    lang_mode  = "sql" if language == "SQL" else "python"
    lang_label = language
    placeholder_text = (
        "-- Write your SQL query here\nSELECT ..."
        if language == "SQL" else
        "# Write your Python function here\ndef solution(...):\n    pass"
    )

    # Seed initial value from saved answers on first load
    if store_key not in st.session_state:
        saved = st.session_state.answers.get(qid_key, {}).get("code", "")
        st.session_state[store_key] = saved if isinstance(saved, str) else ""

    initial_val = st.session_state[store_key]

    # ── Editor chrome top bar ──
    st.markdown(f"""
    <div id="editor-chrome-{qid_key}" style="
        background:#2D2926; border-radius:10px 10px 0 0;
        padding:9px 16px; display:flex; align-items:center;
        justify-content:space-between; border:1.5px solid #3D3A35;
        border-bottom:none; margin-bottom:-4px; position:relative; z-index:2;">
      <div style="display:flex;gap:6px;align-items:center;">
        <span style="width:11px;height:11px;border-radius:50%;background:#FF5F57;display:inline-block;"></span>
        <span style="width:11px;height:11px;border-radius:50%;background:#FFBD2E;display:inline-block;"></span>
        <span style="width:11px;height:11px;border-radius:50%;background:#28C840;display:inline-block;"></span>
      </div>
      <span style="font-size:0.72rem;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;
            color:#A8A39C;font-family:monospace;">{lang_label}</span>
      <span style="font-size:0.7rem;color:#5C5852;font-family:sans-serif;">⛔ No Paste · Type Only</span>
    </div>
    <div id="paste-warn-{qid_key}" style="display:none;background:#3D1515;
         border:1.5px solid #7F1D1D;border-top:none;border-bottom:none;
         color:#FCA5A5;padding:7px 16px;font-size:0.8rem;font-weight:600;
         position:relative;z-index:2;">
      ⛔ Paste is disabled — type your solution manually.
    </div>
    <style>
    /* Wrap the ace component to round the bottom corners */
    div[data-ace-wrap="{qid_key}"] > div {{
        border-radius: 0 0 10px 10px !important;
        overflow: hidden !important;
        border: 1.5px solid #3D3A35 !important;
        border-top: none !important;
    }}
    div[data-ace-wrap="{qid_key}"] .ace_editor {{
        border-radius: 0 0 10px 10px !important;
    }}
    </style>
    <div data-ace-wrap="{qid_key}">
    """, unsafe_allow_html=True)

    # ── Ace Editor ──
    result = st_ace(
        value=initial_val,
        language=lang_mode,
        theme="tomorrow_night",
        key=widget_key,
        height=height,
        font_size=14,
        tab_size=4,
        show_gutter=True,
        show_print_margin=False,
        wrap=False,
        auto_update=True,
        readonly=False,
        placeholder=placeholder_text,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Paste blocking JS ──
    st.markdown(f"""
    <script>
    (function() {{
      var QK = '{qid_key}';
      if (window['_aceBlocked_' + QK]) return;

      function hookAce() {{
        // Ace renders inside an iframe or a div with class ace_editor
        var aceEl = document.querySelector('[data-ace-wrap="' + QK + '"] .ace_text-input');
        if (!aceEl || aceEl._pasted) return;
        aceEl._pasted = true;

        aceEl.addEventListener('paste', function(e) {{
          e.preventDefault(); e.stopImmediatePropagation();
          showWarn();
        }}, true);

        // Also hook the ace_scroller (drag drop target)
        var scroller = aceEl.closest('.ace_editor');
        if (scroller) {{
          scroller.addEventListener('drop', function(e) {{
            e.preventDefault(); e.stopImmediatePropagation();
          }}, true);
        }}

        window['_aceBlocked_' + QK] = true;
      }}

      function showWarn() {{
        var w = document.getElementById('paste-warn-' + QK);
        if (!w) return;
        w.style.display = 'block';
        clearTimeout(w._t);
        w._t = setTimeout(function() {{ w.style.display = 'none'; }}, 3000);
      }}

      // Block Ctrl/Cmd+V globally when ace has focus
      document.addEventListener('keydown', function(e) {{
        if ((e.ctrlKey || e.metaKey) && e.key === 'v') {{
          var wrap = document.querySelector('[data-ace-wrap="' + QK + '"]');
          if (wrap && wrap.contains(document.activeElement)) {{
            e.preventDefault(); e.stopImmediatePropagation();
            showWarn();
          }}
        }}
      }}, true);

      hookAce();
      setTimeout(hookAce, 400);
      setTimeout(hookAce, 1200);
      new MutationObserver(hookAce).observe(document.body, {{childList:true, subtree:true}});
    }})();
    </script>
    """, unsafe_allow_html=True)

    # result is the string from ace editor (or None on first render before interaction)
    code = result if isinstance(result, str) else initial_val
    st.session_state[store_key] = code
    return code



# ── LOGIN PAGE ─────────────────────────────────────────────────────────────────
def page_login():
    _, center, _ = st.columns([1, 1.4, 1])
    with center:
        st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="cr-login-brand">Code<span>Round</span></div>
        <div style="text-align:center;color:#6B6560;font-size:1rem;margin-bottom:36px;">
            Technical Interview Assessment Platform
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🎓  Candidate Login", "🔐  Admin Login"])
        with tab1:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            c_user = st.text_input("Username", key="c_user", placeholder="your.username")
            c_pass = st.text_input("Password", type="password", key="c_pass", placeholder="••••••••")
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            if st.button("Start Interview →", width='stretch', type="primary"):
                if c_user and c_pass: login_candidate(c_user, c_pass)
                else: st.warning("Enter username and password")
        with tab2:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            a_user = st.text_input("Admin Username", key="a_user", placeholder="admin")
            a_pass = st.text_input("Password", type="password", key="a_pass", placeholder="••••••••")
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            if st.button("Access Admin Panel →", width='stretch'):
                if a_user and a_pass: login_admin(a_user, a_pass)
                else: st.warning("Enter credentials")

        st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style='display:flex;gap:8px;justify-content:center;flex-wrap:wrap;'>
          <span style='background:#FAFAF8;border:1.5px solid #E8E4DC;border-radius:99px;padding:5px 14px;font-size:0.8rem;font-weight:500;color:#6B6560;'>🗄️ SQL</span>
          <span style='background:#FAFAF8;border:1.5px solid #E8E4DC;border-radius:99px;padding:5px 14px;font-size:0.8rem;font-weight:500;color:#6B6560;'>🐍 Python</span>
          <span style='background:#FAFAF8;border:1.5px solid #E8E4DC;border-radius:99px;padding:5px 14px;font-size:0.8rem;font-weight:500;color:#6B6560;'>⚡ Syntax Highlighting</span>
          <span style='background:#FAFAF8;border:1.5px solid #E8E4DC;border-radius:99px;padding:5px 14px;font-size:0.8rem;font-weight:500;color:#6B6560;'>🔒 No Paste</span>
          <span style='background:#FAFAF8;border:1.5px solid #E8E4DC;border-radius:99px;padding:5px 14px;font-size:0.8rem;font-weight:500;color:#6B6560;'>✅ Live Feedback</span>
        </div>
        """, unsafe_allow_html=True)


# ── EXAM PAGE ──────────────────────────────────────────────────────────────────
@st.fragment(run_every=1)
def _render_timer():
    """Reruns every second in isolation — updates only the timer display."""
    if st.session_state.get("start_time"):
        elapsed = int(time.time() - st.session_state.start_time)
        h, rem = divmod(elapsed, 3600)
        m, s   = divmod(rem, 60)
        label  = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
        st.markdown(
            f"<div class='cr-timer'>{label}</div>",
            unsafe_allow_html=True
        )


def page_exam():
    questions = st.session_state.questions
    if not questions:
        st.warning("No questions assigned.")
        st.button("Logout", on_click=logout)
        return

    total     = len(questions)
    correct   = sum(1 for v in st.session_state.answers.values() if v.get("is_correct"))
    attempted = sum(1 for v in st.session_state.answers.values() if v.get("result") is not None)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        tmpl_info = st.session_state.get("template_name")
        tmpl_badge = (f"<div style='font-size:0.68rem;background:#E86C2C;color:#fff;"
                      f"border-radius:4px;padding:1px 7px;display:inline-block;"
                      f"margin-top:3px;'>📋 {tmpl_info}</div>") if tmpl_info else (
                      "<div style='font-size:0.68rem;color:#5C5852;margin-top:2px;'>🎲 Random mode</div>")
        st.markdown(f"""
        <div style='padding:12px 4px 6px;'>
          <div style='font-family:Syne,sans-serif;font-size:1.05rem;font-weight:800;color:#F0EDE6;'>
            Code<span style='color:#E86C2C;'>Round</span>
          </div>
          <div style='font-size:1.05rem;color:#A8A39C;margin-top:2px;'>👤 {st.session_state.user}</div>
          {tmpl_badge}
        </div>""", unsafe_allow_html=True)

        # Fragment reruns only the timer every second — no editor flicker
        _render_timer()

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        pct = int(correct/total*100) if total else 0
        st.markdown(f"""
        <div style='margin-bottom:8px;'>
          <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;'>
            <span style='font-size:0.7rem;color:#5C5852;font-weight:600;letter-spacing:0.8px;text-transform:uppercase;'>Progress</span>
            <span style='font-size:0.78rem;color:#E86C2C;font-weight:700;font-family:monospace;'>{correct}/{total} correct</span>
          </div>
          <div style='background:#2A2622;border-radius:99px;height:6px;overflow:hidden;'>
            <div style='background:linear-gradient(90deg,#E86C2C,#F5A623);height:100%;border-radius:99px;width:{pct}%;transition:width 0.4s;'></div>
          </div>
          <div style='display:flex;gap:6px;margin-top:8px;'>
            <div style='flex:1;background:#2A2622;border-radius:8px;padding:7px 4px;text-align:center;'>
              <div style='font-size:1rem;font-weight:700;color:#16A34A;'>{correct}</div>
              <div style='font-size:0.6rem;color:#5C5852;text-transform:uppercase;letter-spacing:0.5px;'>Correct</div>
            </div>
            <div style='flex:1;background:#2A2622;border-radius:8px;padding:7px 4px;text-align:center;'>
              <div style='font-size:1rem;font-weight:700;color:#D97706;'>{attempted}</div>
              <div style='font-size:0.6rem;color:#5C5852;text-transform:uppercase;letter-spacing:0.5px;'>Tried</div>
            </div>
            <div style='flex:1;background:#2A2622;border-radius:8px;padding:7px 4px;text-align:center;'>
              <div style='font-size:1rem;font-weight:700;color:#C8C3BC;'>{total-attempted}</div>
              <div style='font-size:0.6rem;color:#5C5852;text-transform:uppercase;letter-spacing:0.5px;'>Left</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        # ── Question Navigator ─────────────────────────────────────────────
        cat_colors = {'SQL': '#2563EB', 'Python': '#16A34A', 'PySpark': '#EA580C'}
        cat_bg     = {'SQL': '#1E2D4A', 'Python': '#1A3326', 'PySpark': '#3A1F0D'}
        cat_icons  = {'SQL': '🗄', 'Python': '🐍', 'PySpark': '⚡'}

        # ── Per-category CSS injected once ──────────────────────────────────
        st.markdown("""
        <style>
        /* Nav question buttons — fully custom styled */
        [data-testid="stSidebar"] .nav-btn-wrap { margin-bottom: 1px; }
        [data-testid="stSidebar"] .nav-btn-wrap button {
            background: transparent !important;
            border: none !important;
            border-left: 3px solid transparent !important;
            border-radius: 0 6px 6px 0 !important;
            padding: 6px 8px 6px 10px !important;
            width: 100% !important;
            text-align: left !important;
            cursor: pointer !important;
            transition: all 0.15s !important;
            min-height: 0 !important;
            height: auto !important;
            line-height: 1.2 !important;
            box-shadow: none !important;
        }
        [data-testid="stSidebar"] .nav-btn-wrap button p {
            font-family: 'Inter', monospace !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            margin: 0 !important;
            font-size: 0.78rem !important;
        }
        </style>
        """, unsafe_allow_html=True)

        for cat in ['SQL', 'Python', 'PySpark']:
            cat_qs = [(i, q) for i, q in enumerate(questions) if q['category'] == cat]
            if not cat_qs: continue
            c_color = cat_colors[cat]; c_bg = cat_bg[cat]; c_icon = cat_icons[cat]
            cat_correct = sum(1 for _,q in cat_qs if st.session_state.answers.get(str(q['id']),{}).get('is_correct'))
            cat_total   = len(cat_qs)

            # Category header
            st.markdown(
                f"<div style='display:flex;align-items:center;justify-content:space-between;"
                f"background:{c_bg};border-left:3px solid {c_color};"
                f"border-radius:0 6px 6px 0;padding:6px 10px;margin:10px 0 3px;'>"
                f"<span style='font-size:0.72rem;font-weight:700;color:{c_color};"
                f"letter-spacing:1.2px;text-transform:uppercase;'>{c_icon} {cat}</span>"
                f"<span style='font-size:0.68rem;color:#5C5852;font-weight:600;'>{cat_correct}/{cat_total}</span>"
                f"</div>",
                unsafe_allow_html=True
            )

            for i, q in cat_qs:
                qid          = q['id']
                ans          = st.session_state.answers.get(str(qid), {})
                is_correct   = ans.get('is_correct', False)
                is_attempted = ans.get('result') is not None
                is_current   = (i == st.session_state.q_index)
                diff_color   = {'Easy':'#16A34A','Medium':'#D97706','Hard':'#DC2626'}.get(q['difficulty'],'#6B6560')
                title_short  = q['title'][:20] + ('…' if len(q['title']) > 20 else '')

                if is_correct:     s_icon = '✓'; s_col = '#16A34A'
                elif is_attempted: s_icon = '✗'; s_col = '#EF4444'
                else:              s_icon = '·'; s_col = '#5C5852'

                rgba_c = ','.join(str(int(c_color.lstrip('#')[j:j+2],16)) for j in (0,2,4))
                if is_current:
                    btn_style = (f"background:rgba({rgba_c},0.18)!important;"
                                 f"border-left:3px solid {c_color}!important;")
                    lbl = f"{s_icon} {title_short}  ▶"
                else:
                    btn_style = ""
                    lbl = f"{s_icon} {title_short}"

                # Inject per-button style via unique class
                st.markdown(
                    f"<div class='nav-btn-wrap' id='navwrap_{qid}' "                    f"style='{btn_style}border-radius:0 6px 6px 0;margin-bottom:1px;'>",
                    unsafe_allow_html=True
                )
                if st.button(lbl, key=f'nav_{qid}', width='stretch'):
                    st.session_state.q_index = i; st.rerun()
                st.markdown(
                    f"<div style='font-size:0.6rem;color:{diff_color};font-weight:700;"
                    f"letter-spacing:0.6px;padding:0 0 3px 26px;margin-top:-6px;'"
                    f">{q['difficulty'].upper()}</div></div>",
                    unsafe_allow_html=True
                )

        st.markdown("<hr style='border-color:rgba(255,255,255,0.07);margin:10px 0 6px;'>", unsafe_allow_html=True)
        if st.button('🚪  End Interview', width='stretch'): logout()

    # ── Main ──────────────────────────────────────────────────────────────────
    idx = st.session_state.q_index
    q   = questions[idx]; qid = q["id"]; qid_key = str(qid)
    cat = q["category"]; diff = q["difficulty"]

    cat_badge = {"SQL":"cr-badge cr-badge-sql","Python":"cr-badge cr-badge-python","PySpark":"cr-badge cr-badge-pyspark"}.get(cat,"cr-badge cr-badge-sql")
    diff_cls  = {"Easy":"cr-badge cr-badge-easy","Medium":"cr-badge cr-badge-medium","Hard":"cr-badge cr-badge-hard"}.get(diff, "cr-badge")
    cat_icon  = {"SQL":"🗄️","Python":"🐍","PySpark":"⚡"}.get(cat,"📝")

    # Top header bar
    dark_cat_cls  = {"SQL":"cr-badge cr-badge-dark-sql","Python":"cr-badge cr-badge-dark-python","PySpark":"cr-badge cr-badge-dark-pyspark"}.get(cat,"cr-badge")
    dark_diff_cls = {"Easy":"cr-badge cr-badge-dark-easy","Medium":"cr-badge cr-badge-dark-medium","Hard":"cr-badge cr-badge-dark-hard"}.get(diff,"cr-badge")
    st.markdown(f"""
    <div style='background:#1C1917;border-radius:14px;padding:16px 24px;
                display:flex;align-items:center;gap:0;margin-bottom:14px;'>
      <!-- Left meta -->
      <div style='display:flex;align-items:center;gap:10px;flex-shrink:0;margin-right:18px;'>
        <span style='background:rgba(255,255,255,0.07);border-radius:6px;
                     padding:4px 10px;font-size:0.75rem;font-weight:700;
                     color:#A8A39C;letter-spacing:0.5px;white-space:nowrap;'>
          Q{idx+1} / {total}
        </span>
        <span class='{dark_cat_cls}' style='font-size:0.72rem;padding:4px 11px;'>
          {cat_icon} {cat}
        </span>
        <span class='{dark_diff_cls}' style='font-size:0.72rem;padding:4px 11px;font-weight:800;letter-spacing:0.8px;'>
          {diff.upper()}
        </span>
      </div>
      <!-- Title -->
      <div style='font-family:Syne,sans-serif;font-size:1.15rem;font-weight:700;
                  color:#F0EDE6;flex:1;line-height:1.3;'>
        {q["title"]}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Prev / Next navigation
    n1, _mid, n3 = st.columns([1, 14, 1])
    with n1:
        if idx > 0 and st.button("← Prev", key="prev"): st.session_state.q_index -= 1; st.rerun()
    with n3:
        if idx < total-1 and st.button("Next →", key="next"): st.session_state.q_index += 1; st.rerun()

    left, right = st.columns([1, 1], gap="large")

    # ── Problem ───────────────────────────────────────────────────────────────
    with left:
        st.markdown("<p class='cr-section-title'>📋 Problem Statement</p>", unsafe_allow_html=True)
        # Use CSS to style the native st.container — avoids split open/close div bug
        st.markdown("""
        <style>
        div[data-testid='stVerticalBlockBorderWrapper'] {
            background: #FAFAF8 !important;
            border: 1.5px solid #E8E4DC !important;
            border-radius: 16px !important;
            padding: 8px 12px !important;
        }
        </style>
        """, unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(q["description"])

    # ── Editor ────────────────────────────────────────────────────────────────
    with right:
        st.markdown("<p class='cr-section-title'>✏️ Your Solution</p>", unsafe_allow_html=True)

        # Pre-seed ace editor store from restored answers (re-login recovery)
        store_key = f"ace_store_{qid_key}"
        if store_key not in st.session_state:
            saved = st.session_state.answers.get(qid_key, {}).get("code", "")
            if saved:
                st.session_state[store_key] = saved

        current_code = code_editor(language=cat, qid_key=qid_key, height=360)

        # Sync editor value into answers dict
        if isinstance(current_code, str):
            if qid_key not in st.session_state.answers:
                st.session_state.answers[qid_key] = {}
            st.session_state.answers[qid_key]["code"] = current_code

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        b1, b2, b3 = st.columns([3, 1.2, 1])
        with b1:
            run_clicked = st.button("▶  Run Code", type="primary", width='stretch', key=f"run_{qid}")
        with b2:
            if st.button("🗑  Clear", width='stretch', key=f"clear_{qid}"):
                st.session_state.answers[qid_key] = {"code": ""}
                st.session_state[f"ace_store_{qid_key}"] = ""
                wk = f"ace_{qid_key}"
                if wk in st.session_state:
                    del st.session_state[wk]
                st.rerun()
        with b3:
            if st.button("💡 Hint", width='stretch', key=f"hint_{qid}"):
                st.session_state[f"show_hint_{qid_key}"] = not st.session_state.get(f"show_hint_{qid_key}", False)

        # Hint shown OUTSIDE narrow column — full width
        if st.session_state.get(f"show_hint_{qid_key}", False):
            if cat == "SQL":
                hint_text = "💡 Think about GROUP BY + HAVING, or window functions like DENSE_RANK() and ROW_NUMBER(). Use CTEs to deduplicate before selecting."
            else:
                hint_text = "💡 Try enumerate(), zip(), collections.defaultdict(), or a two-pointer approach. Think about time complexity before coding."
            st.markdown(f"<div class='cr-hint-box'><i class='bi bi-lightbulb-fill me-2'></i>{hint_text}</div>", unsafe_allow_html=True)

        if run_clicked:
            code_to_run = (
                st.session_state.get(f"ace_{qid_key}")
                or st.session_state.get(f"ace_store_{qid_key}")
                or st.session_state.answers.get(qid_key, {}).get("code", "")
                or ""
            )
            if not isinstance(code_to_run, str): code_to_run = ""
            if not code_to_run.strip():
                st.warning("Write your solution first!")
            else:
                with st.spinner("⚙️ Executing…"):
                    if cat == "SQL":
                        result = executor.execute_sql_code(code_to_run, q.get("test_input",""), q["expected_output"])
                    else:
                        result = executor.execute_python_code(code_to_run, q.get("test_input",""), q["expected_output"])
                st.session_state.answers[qid_key].update(result=result, is_correct=result["is_correct"])
                db.save_submission(st.session_state.candidate_id, qid, code_to_run, result["is_correct"])
                st.rerun()

        prev = st.session_state.answers.get(qid_key, {}).get("result")
        if prev is not None:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if prev["is_correct"]:
                st.markdown("""<div class='cr-alert cr-alert-success'>
                  <span style='font-size:1.4rem;'>✅</span>
                  <div><div>Correct! Well done.</div>
                  <div style='font-size:0.8rem;font-weight:400;opacity:0.8;margin-top:2px;'>Your solution produces the expected output.</div></div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div class='cr-alert cr-alert-danger'>
                  <span style='font-size:1.4rem;'>❌</span>
                  <div><div>Not quite — try again</div>
                  <div style='font-size:0.8rem;font-weight:400;opacity:0.8;margin-top:2px;'>Check your logic and edge cases.</div></div>
                </div>""", unsafe_allow_html=True)

            if prev.get("error"):
                with st.expander("🔴 Error details"):
                    st.code(prev["error"], language="text")

            if prev.get("df_data") and prev["df_data"]["rows"]:
                st.markdown("<p class='cr-section-title' style='margin-top:12px;'>Query Result</p>", unsafe_allow_html=True)
                df = pd.DataFrame(prev["df_data"]["rows"], columns=prev["df_data"]["columns"])
                st.dataframe(df, use_container_width=True, hide_index=True)
            elif prev.get("output") and not prev.get("df_data"):
                st.markdown("<p class='cr-section-title' style='margin-top:12px;'>Output</p>", unsafe_allow_html=True)
                st.code(prev["output"], language="text")


# ── ADMIN PAGE ─────────────────────────────────────────────────────────────────
def page_admin():
    with st.sidebar:
        st.markdown("""
        <div style='padding:12px 4px 6px;'>
          <div style='font-family:Syne,sans-serif;font-size:1.05rem;font-weight:800;color:#F0EDE6;'>
            Code<span style='color:#E86C2C;'>Round</span></div>
          <div style='font-size:0.75rem;color:#5C5852;margin-top:2px;'>Admin Console</div>
        </div>""", unsafe_allow_html=True)
        sec = st.radio("Navigation", ["👥  Candidates","📋  Templates","📚  Question Bank","➕  Add Question","📊  Submissions","🔑  Change Password"],
                       label_visibility="collapsed")
        st.markdown("---")
        if st.button("🚪 Logout", width='stretch'): logout()


    # Show expand button in main area if sidebar is collapsed
    st.markdown(f"""
    <div class='cr-topbar'>
      <div>
        <div style='font-size:0.7rem;color:#6B6560;letter-spacing:1.2px;text-transform:uppercase;font-weight:600;'>Admin Panel</div>
        <div class='cr-logo' style='font-size:1.35rem;margin-top:2px;'>{sec}</div>
      </div>
      <div class='cr-logo'>Code<span>Round</span></div>
    </div>""", unsafe_allow_html=True)

    if "Candidates" in sec:
        # ── Top row: Create | Manage | Question Override ─────────────────────
        c1, c2, c3 = st.columns([1, 1, 1], gap="medium")

        # ── CREATE ────────────────────────────────────────────────────────────
        with c1:
            with st.container(border=True):
                st.markdown("<p class='cr-section-title'>➕ Create Candidate</p>", unsafe_allow_html=True)
                nu  = st.text_input("Username", placeholder="e.g. john_doe_2024", key="nu")
                np_ = st.text_input("Temporary Password", type="password", key="np")

                st.markdown("<p style='font-size:0.78rem;color:#6B6560;margin:10px 0 4px;font-weight:600;'>QUESTION COUNT <span style='font-weight:400;'>(blank = global default)</span></p>", unsafe_allow_html=True)
                cfg_defaults = db.get_interview_config()
                avail = db.get_available_question_counts()
                ov1, ov2 = st.columns(2)
                with ov1:
                    nu_sql = st.number_input("SQL", min_value=0,
                        max_value=avail.get("SQL", 20), value=None,
                        placeholder=str(cfg_defaults["sql_count"]), key="nu_sql")
                with ov2:
                    nu_py  = st.number_input("Python", min_value=0,
                        max_value=avail.get("Python", 20), value=None,
                        placeholder=str(cfg_defaults["python_count"]), key="nu_py")

                if st.button("Create Account", type="primary", width='stretch'):
                    if nu and np_:
                        ok, msg = db.create_candidate(
                            nu, np_,
                            sql_count=int(nu_sql) if nu_sql is not None else None,
                            python_count=int(nu_py) if nu_py is not None else None,
                        )
                        if ok: st.success(f"✅ {msg}")
                        else:  st.error(f"❌ {msg}")
                    else:
                        st.warning("Username and password required")

        # ── MANAGE ────────────────────────────────────────────────────────────
        with c2:
            with st.container(border=True):
                st.markdown("<p class='cr-section-title'>⚙️ Manage Candidate</p>", unsafe_allow_html=True)
                all_cands = db.get_all_candidates(include_deactivated=True)
                if all_cands:
                    mgmt_user = st.selectbox(
                        "Select candidate",
                        [c["username"] for c in all_cands],
                        key="mgmt_sel",
                        format_func=lambda u: f"{'🔴 ' if next((c for c in all_cands if c['username']==u),{}).get('status')=='deactivated' else '🟢 '}{u}"
                    )
                    sel_cand     = next((c for c in all_cands if c["username"] == mgmt_user), None)
                    is_deactivated = sel_cand and sel_cand.get("status") == "deactivated"

                    # Status pill
                    pill_bg  = "#FEF2F2" if is_deactivated else "#F0FDF4"
                    pill_bd  = "#FCA5A5" if is_deactivated else "#86EFAC"
                    pill_col = "#DC2626" if is_deactivated else "#15803D"
                    pill_txt = "🔴 Deactivated" if is_deactivated else "🟢 Active"
                    st.markdown(
                        f"<div style='background:{pill_bg};border:1.5px solid {pill_bd};"
                        f"border-radius:8px;padding:6px 12px;text-align:center;"
                        f"font-size:0.82rem;font-weight:600;color:{pill_col};margin:8px 0;'>"
                        f"{pill_txt}</div>",
                        unsafe_allow_html=True
                    )
                    if is_deactivated:
                        if st.button("✅ Reactivate Candidate", width='stretch', key="react_btn"):
                            db.reactivate_candidate(mgmt_user)
                            st.success(f"'{mgmt_user}' reactivated — can login again")
                            st.rerun()
                    else:
                        if st.button("🚫 Deactivate Candidate", width='stretch', key="deact_btn"):
                            db.deactivate_candidate(mgmt_user)
                            st.warning(f"'{mgmt_user}' deactivated — history preserved")
                            st.rerun()

                    # Template assignment
                    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                    st.markdown("<p class='cr-section-title' style='margin-top:4px;'>📋 Assign Template</p>", unsafe_allow_html=True)
                    active_templates = db.get_all_templates(active_only=True)
                    tmpl_options = ["— Random questions (default) —"] + [t["name"] for t in active_templates]

                    # Get current assignment
                    cur_tmpl = db.get_candidate_template(sel_cand["id"]) if sel_cand else None
                    cur_idx = 0
                    if cur_tmpl:
                        for i, t in enumerate(active_templates, 1):
                            if t["id"] == cur_tmpl["id"]:
                                cur_idx = i
                                break

                    chosen = st.selectbox("Template", tmpl_options, index=cur_idx,
                                          key=f"tmpl_assign_{mgmt_user}",
                                          help="Assign a template to give this candidate a fixed question set")

                    if st.button("Save Assignment", key="save_tmpl_btn", width='stretch'):
                        if chosen.startswith("—"):
                            db.assign_template_to_candidate(sel_cand["id"], None)
                            st.success("✅ Cleared — candidate will get random questions")
                        else:
                            tmpl_obj = next(t for t in active_templates if t["name"] == chosen)
                            db.assign_template_to_candidate(sel_cand["id"], tmpl_obj["id"])
                            st.success(f"✅ Template '{chosen}' assigned to {mgmt_user}")
                        st.rerun()

                    if cur_tmpl:
                        st.markdown(
                            f"<div style='font-size:0.78rem;color:#16A34A;margin-top:4px;'>"
                            f"📋 Current: <b>{cur_tmpl['name']}</b></div>",
                            unsafe_allow_html=True
                        )
                else:
                    st.info("No candidates yet. Create one on the left.")

        # ── RESET PASSWORD ────────────────────────────────────────────────────
        if db.get_all_candidates(include_deactivated=True):
            with st.expander("🔑 Reset Candidate Password", expanded=False):
                all_cands_rp = db.get_all_candidates(include_deactivated=True)
                rp_col1, rp_col2 = st.columns([1, 1], gap="medium")
                with rp_col1:
                    rp_user = st.selectbox(
                        "Select candidate",
                        [c["username"] for c in all_cands_rp],
                        key="rp_user_sel"
                    )
                with rp_col2:
                    rp_new  = st.text_input("New Password", type="password", key="rp_new",
                                             placeholder="Min 6 characters")
                    rp_conf = st.text_input("Confirm Password", type="password", key="rp_conf",
                                             placeholder="Re-enter password")
                rp_btn_col, rp_msg_col = st.columns([1, 2])
                with rp_btn_col:
                    if st.button("Reset Password", key="rp_btn", type="primary", width="stretch"):
                        if not rp_new or not rp_conf:
                            st.error("Both password fields are required")
                        elif len(rp_new) < 6:
                            st.error("Password must be at least 6 characters")
                        elif rp_new != rp_conf:
                            st.error("Passwords do not match")
                        else:
                            ok = db.reset_candidate_password(rp_user, rp_new)
                            if ok:
                                st.success(f"✅ Password reset for **{rp_user}**")
                            else:
                                st.error("Reset failed — candidate not found")

        # ── QUICK STATS ───────────────────────────────────────────────────────
        with c3:
            with st.container(border=True):
                st.markdown("<p class='cr-section-title'>📊 Quick Overview</p>", unsafe_allow_html=True)
                all_c_list = db.get_all_candidates(include_deactivated=True)
                active_count = sum(1 for c in all_c_list if c.get("status","active") == "active")
                deact_count  = len(all_c_list) - active_count
                total_subs   = 0
                total_correct = 0
                for c in all_c_list:
                    d = db.get_candidate_detail(c["id"])
                    total_subs   += d["attempted_count"]
                    total_correct += d["correct_count"]
                st.metric("Total Candidates", len(all_c_list))
                st.metric("Active", active_count)
                st.metric("Submissions", total_subs)
                acc = f"{total_correct/total_subs*100:.0f}%" if total_subs else "—"
                st.metric("Overall Accuracy", acc)

        # ── Candidate history ─────────────────────────────────────────────────
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown("<p class='cr-section-title'>📋 All Candidates & History</p>", unsafe_allow_html=True)

        all_cands = db.get_all_candidates(include_deactivated=True)
        if not all_cands:
            st.info("No candidates yet")
        else:
            # Show summary table first
            summary_rows = []
            for c in all_cands:
                detail = db.get_candidate_detail(c["id"])
                summary_rows.append({
                    "Status":    "🟢 Active" if c.get("status","active") == "active" else "🔴 Deactivated",
                    "Username":  c["username"],
                    "Created":   c["created_at"],
                    "Assigned":  detail["assigned_count"],
                    "Attempted": detail["attempted_count"],
                    "Correct":   detail["correct_count"],
                    "Accuracy":  f"{detail['correct_count']/detail['attempted_count']*100:.0f}%" if detail["attempted_count"] else "—",
                })
            st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

            # Per-candidate expandable detail
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            sel_view = st.selectbox("View detailed history for:", [c["username"] for c in all_cands], key="view_hist")
            sel_c = next(c for c in all_cands if c["username"] == sel_view)
            detail = db.get_candidate_detail(sel_c["id"])

            # Stats row
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Assigned",  detail["assigned_count"])
            m2.metric("Attempted", detail["attempted_count"])
            m3.metric("Correct",   detail["correct_count"])
            not_tried = detail["assigned_count"] - detail["attempted_count"]
            m4.metric("Not Attempted", max(not_tried, 0))

            # Attempted questions table
            if detail["attempted"]:
                st.markdown("<p class='cr-section-title' style='margin-top:14px;'>✅ Attempted Questions</p>", unsafe_allow_html=True)
                att_rows = [{
                    "Question":    s["title"],
                    "Category":    s["category"],
                    "Difficulty":  s["difficulty"],
                    "Result":      "✅ Correct" if s["best_correct"] else "❌ Incorrect",
                    "Attempts":    s["attempts"],
                    "Last Tried":  s["last_attempt"],
                } for s in detail["attempted"]]
                st.dataframe(pd.DataFrame(att_rows), use_container_width=True, hide_index=True)

            # Not-attempted questions table
            if detail["not_attempted"]:
                st.markdown("<p class='cr-section-title' style='margin-top:14px;'>⏭️ Not Attempted</p>", unsafe_allow_html=True)
                na_rows = [{
                    "Question":   q["title"],
                    "Category":   q["category"],
                    "Difficulty": q["difficulty"],
                } for q in detail["not_attempted"]]
                st.dataframe(pd.DataFrame(na_rows), use_container_width=True, hide_index=True)

            if not detail["attempted"] and not detail["not_attempted"]:
                st.info("No interview session recorded for this candidate yet.")
            else:
                # ── Download PDF report ──
                st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
                with st.container(border=True):
                    pdf_col1, pdf_col2 = st.columns([3, 1])
                    with pdf_col1:
                        st.markdown(f"""
                        <div>
                          <div style='font-weight:700;font-size:1rem;color:#1C1917;'>📄 Interview Report — {sel_view}</div>
                          <div style='font-size:0.82rem;color:#6B6560;margin-top:3px;'>
                            Contains all attempted questions, submitted solutions, and results.
                            Ready to share with management.
                          </div>
                        </div>""", unsafe_allow_html=True)
                    with pdf_col2:
                        full_detail = db.get_candidate_detail_full(sel_c["id"])
                        try:
                            pdf_bytes = generate_candidate_report(sel_c, full_detail)
                            fname = f"CodeRound_{sel_view}_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                            st.download_button(
                                label="⬇ Download PDF",
                                data=pdf_bytes,
                                file_name=fname,
                                mime="application/pdf",
                                type="primary",
                                width='stretch',
                                key=f"dl_pdf_{sel_view}",
                            )
                        except Exception as e:
                            st.error(f"PDF error: {e}")

    elif "Question Bank" in sec:
        cf1, _ = st.columns([2, 5])
        with cf1: cat_f = st.selectbox("Category", ["All","SQL","Python","PySpark"])
        qs = db.get_all_questions()
        filtered = qs if cat_f == "All" else [q for q in qs if q["category"] == cat_f]
        st.markdown(f"<p style='color:#6B6560;font-size:0.83rem;'>{len(filtered)} question(s)</p>", unsafe_allow_html=True)
        for q in filtered:
            dot = "🟢" if q["is_active"] else "🔴"
            with st.expander(f"{dot}  [{q['category']}] {q['title']} — {q['difficulty']}"):
                st.markdown(q["description"])
                lbl = "Deactivate" if q["is_active"] else "Activate"
                if st.button(lbl, key=f"tog_{q['id']}"):
                    db.toggle_question(q["id"], not q["is_active"]); st.rerun()

    elif "Add Question" in sec:
        with st.container(border=True):
            with st.form("aq"):
                r1c1, r1c2, r1c3 = st.columns([3,1.5,1.5])
                with r1c1: title = st.text_input("Title *", placeholder="e.g. Find Duplicate Emails")
                with r1c2: cat_ = st.selectbox("Category *", ["SQL","Python","PySpark"])
                with r1c3: diff_ = st.selectbox("Difficulty *", ["Easy","Medium","Hard"])
                desc = st.text_area("Description * (Markdown)", height=200, placeholder="Problem description with examples...")
                r2c1, r2c2 = st.columns(2)
                with r2c1: ti = st.text_area("Test Setup", height=90, placeholder="SQL: CREATE TABLE; INSERT\nPython: nums=[1,2]; target=3")
                with r2c2: exp = st.text_input("Expected Output *", placeholder="Value to verify correctness")
                sol = st.text_area("Reference Solution (admin only)", height=80)
                if st.form_submit_button("Add Question", type="primary"):
                    if title and desc and exp:
                        db.add_question(title, desc, cat_, diff_, exp, sol, ti)
                        st.success(f"Question '{title}' added!")
                    else:
                        st.error("Title, Description and Expected Output required")

    elif "Submissions" in sec:
        cands = db.get_all_candidates()
        if not cands: st.info("No candidates yet"); return
        sf1, _ = st.columns([2,5])
        with sf1: sel = st.selectbox("Filter", ["All"]+[c["username"] for c in cands])
        all_subs = []
        if sel == "All":
            for c in cands:
                subs = db.get_candidate_submissions(c["id"])
                for s in subs: s["candidate"] = c["username"]
                all_subs.extend(subs)
        else:
            cand = next((c for c in cands if c["username"]==sel), None)
            if cand:
                all_subs = db.get_candidate_submissions(cand["id"])
                for s in all_subs: s["candidate"] = sel
        if all_subs:
            tot = len(all_subs); cor = sum(1 for s in all_subs if s["is_correct"])
            m1,m2,m3,m4 = st.columns(4)
            m1.metric("Submissions", tot); m2.metric("Correct", cor)
            m3.metric("Incorrect", tot-cor); m4.metric("Accuracy", f"{cor/tot*100:.0f}%" if tot else "—")
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            rows = [{"Candidate":s.get("candidate",""),"Question":s["title"],"Category":s["category"],
                     "Result":"✅ Correct" if s["is_correct"] else "❌ Wrong","Submitted":s["submitted_at"]}
                    for s in all_subs]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else: st.info("No submissions yet")

    elif "Templates" in sec:
        st.markdown("""
        <div style='background:#fff;border:1.5px solid #E2D9CE;border-radius:12px;
                    padding:14px 20px;margin-bottom:16px;display:flex;align-items:center;gap:12px;'>
          <span style='font-size:1.5rem;'>📋</span>
          <div>
            <div style='font-weight:700;font-size:0.95rem;color:#1C1917;'>Interview Templates</div>
            <div style='font-size:0.82rem;color:#6B6560;margin-top:2px;'>
              Create named sets of questions. Assign a template to a candidate so they always
              get those exact questions — regardless of random config.
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        tmpl_tab1, tmpl_tab2, tmpl_tab3 = st.tabs(["📋 All Templates", "➕ Create Template", "✏️ Edit Template"])

        # ── TAB 1: All Templates ──────────────────────────────────────────────
        with tmpl_tab1:
            templates = db.get_all_templates()
            if not templates:
                st.info("No templates yet. Create one in the ➕ tab.")
            else:
                for tmpl in templates:
                    active_icon = "🟢" if tmpl["is_active"] else "🔴"
                    with st.expander(f"{active_icon} **{tmpl['name']}** — {tmpl['q_count']} question(s)  ·  {tmpl.get('description','')[:60]}"):
                        qs = db.get_template_questions(tmpl["id"])

                        # Summary badges
                        cat_counts = {}
                        for q in qs:
                            cat_counts[q["category"]] = cat_counts.get(q["category"], 0) + 1
                        badge_html = " ".join(
                            f"<span class='cr-badge cr-badge-{c.lower()}'>{c}: {n}</span>"
                            for c, n in sorted(cat_counts.items())
                        )
                        st.markdown(f"<div style='margin:6px 0 12px;'>{badge_html}</div>", unsafe_allow_html=True)

                        if qs:
                            rows_df = [{"#": i+1, "Question": q["title"],
                                        "Category": q["category"], "Difficulty": q["difficulty"]}
                                       for i, q in enumerate(qs)]
                            st.dataframe(pd.DataFrame(rows_df), use_container_width=True, hide_index=True)
                        else:
                            st.caption("No questions added yet.")

                        col_a, col_b, col_c = st.columns([1, 1, 4])
                        with col_a:
                            lbl = "Deactivate" if tmpl["is_active"] else "Activate"
                            if st.button(lbl, key=f"tmpl_tog_{tmpl['id']}"):
                                db.toggle_template(tmpl["id"], not tmpl["is_active"])
                                st.rerun()
                        with col_b:
                            if st.button("🗑 Delete", key=f"tmpl_del_{tmpl['id']}"):
                                db.delete_template(tmpl["id"])
                                st.success(f"Template '{tmpl['name']}' deleted")
                                st.rerun()

        # ── TAB 2: Create Template ────────────────────────────────────────────
        with tmpl_tab2:
            left_c, right_c = st.columns([1, 1], gap="large")
            with left_c:
                with st.container(border=True):
                    st.markdown("<p class='cr-section-title'>📋 Template Details</p>", unsafe_allow_html=True)
                    tmpl_name = st.text_input("Template Name *", placeholder="e.g. Senior SQL Round, Python Basic", key="new_tmpl_name")
                    tmpl_desc = st.text_area("Description", placeholder="Brief description of this template's focus...", height=80, key="new_tmpl_desc")

                    if st.button("Create Template", type="primary", width="stretch", key="create_tmpl_btn"):
                        if tmpl_name.strip():
                            ok, tid, msg = db.create_template(tmpl_name, tmpl_desc)
                            if ok:
                                st.success(f"✅ Template '{tmpl_name}' created! Now add questions in ✏️ Edit tab.")
                                st.session_state["edit_tmpl_id"] = tid
                            else:
                                st.error(f"❌ {msg}")
                        else:
                            st.warning("Template name is required")

            with right_c:
                with st.container(border=True):
                    st.markdown("<p class='cr-section-title'>💡 How Templates Work</p>", unsafe_allow_html=True)
                    st.markdown("""
                    **1. Create** a named template here

                    **2. Add questions** in the ✏️ Edit tab — pick any active SQL, Python or PySpark questions

                    **3. Assign** the template to a candidate in the 👥 Candidates section

                    **4. Candidate logs in** → they get exactly those questions, in order

                    **If no template assigned** → candidate gets random questions based on the ⚙️ Question Config defaults

                    **Different candidates** can have different templates (e.g. Junior vs Senior round)
                    """)

        # ── TAB 3: Edit Template ──────────────────────────────────────────────
        with tmpl_tab3:
            templates = db.get_all_templates()
            if not templates:
                st.info("Create a template first in the ➕ tab.")
            else:
                # Pre-select if just created
                tmpl_names = [t["name"] for t in templates]
                default_idx = 0
                if "edit_tmpl_id" in st.session_state:
                    for i, t in enumerate(templates):
                        if t["id"] == st.session_state.get("edit_tmpl_id"):
                            default_idx = i
                            break

                sel_tmpl_name = st.selectbox("Select template to edit", tmpl_names,
                                              index=default_idx, key="edit_tmpl_sel")
                sel_tmpl = next(t for t in templates if t["name"] == sel_tmpl_name)
                current_qs = db.get_template_questions(sel_tmpl["id"])
                current_ids = {q["id"] for q in current_qs}

                edit_l, edit_r = st.columns([1, 1], gap="large")

                with edit_l:
                    with st.container(border=True):
                        st.markdown(f"<p class='cr-section-title'>✅ Questions in '{sel_tmpl_name}' ({len(current_qs)})</p>", unsafe_allow_html=True)
                        if current_qs:
                            for q in current_qs:
                                q_col1, q_col2 = st.columns([5, 1])
                                with q_col1:
                                    cat_cls = {"SQL":"cr-badge-sql","Python":"cr-badge-python","PySpark":"cr-badge-pyspark"}.get(q["category"],"")
                                    diff_cls = {"Easy":"cr-badge-easy","Medium":"cr-badge-medium","Hard":"cr-badge-hard"}.get(q["difficulty"],"")
                                    st.markdown(
                                        f"<div style='padding:6px 0;border-bottom:1px solid #F0EDE6;'>"
                                        f"<span class='cr-badge {cat_cls}' style='margin-right:6px;'>{q['category']}</span>"
                                        f"<span class='cr-badge {diff_cls}' style='margin-right:8px;'>{q['difficulty']}</span>"
                                        f"<span style='font-size:0.88rem;color:#1C1917;'>{q['title']}</span></div>",
                                        unsafe_allow_html=True
                                    )
                                with q_col2:
                                    if st.button("✕", key=f"rm_q_{sel_tmpl['id']}_{q['id']}", help="Remove"):
                                        db.remove_question_from_template(sel_tmpl["id"], q["id"])
                                        st.rerun()
                        else:
                            st.caption("No questions yet. Add from the right panel.")

                with edit_r:
                    with st.container(border=True):
                        st.markdown("<p class='cr-section-title'>➕ Add Questions</p>", unsafe_allow_html=True)
                        cat_filter = st.selectbox("Filter by category", ["All","SQL","Python","PySpark"],
                                                   key="edit_cat_filter")
                        diff_filter = st.selectbox("Filter by difficulty", ["All","Easy","Medium","Hard"],
                                                    key="edit_diff_filter")

                        all_qs = db.get_all_questions()
                        filtered = [q for q in all_qs if q["is_active"]
                                    and (cat_filter == "All" or q["category"] == cat_filter)
                                    and (diff_filter == "All" or q["difficulty"] == diff_filter)]

                        added_count = 0
                        for q in filtered:
                            already = q["id"] in current_ids
                            q_row1, q_row2 = st.columns([5, 1])
                            with q_row1:
                                cat_cls = {"SQL":"cr-badge-sql","Python":"cr-badge-python","PySpark":"cr-badge-pyspark"}.get(q["category"],"")
                                diff_cls = {"Easy":"cr-badge-easy","Medium":"cr-badge-medium","Hard":"cr-badge-hard"}.get(q["difficulty"],"")
                                st.markdown(
                                    f"<div style='padding:4px 0;'>"
                                    f"<span class='cr-badge {cat_cls}' style='margin-right:4px;font-size:0.65rem;'>{q['category']}</span>"
                                    f"<span class='cr-badge {diff_cls}' style='margin-right:6px;font-size:0.65rem;'>{q['difficulty']}</span>"
                                    f"<span style='font-size:0.82rem;color:{'#A8A39C' if already else '#1C1917'};'>{q['title']}</span>"
                                    f"{'<span style="color:#16A34A;font-size:0.75rem;"> ✓ added</span>' if already else ''}</div>",
                                    unsafe_allow_html=True
                                )
                            with q_row2:
                                if not already:
                                    if st.button("＋", key=f"add_q_{sel_tmpl['id']}_{q['id']}", help="Add to template"):
                                        db.add_question_to_template(sel_tmpl["id"], q["id"])
                                        st.rerun()
                            added_count += 1

                        if added_count == 0:
                            st.caption("No questions match the filter.")

    elif "Question Config" in sec:
        _, col, _ = st.columns([0.5, 2, 0.5])
        with col:
            cfg   = db.get_interview_config()
            avail = db.get_available_question_counts()
            with st.container(border=True):
                st.markdown("<p class='cr-section-title'>⚙️ Default Question Count Per Interview</p>", unsafe_allow_html=True)
                st.caption("Defaults used when creating candidates. Override per-candidate at account creation.")
                g1, g2, g3 = st.columns(3)
                with g1:
                    sql_n = st.number_input(f"🗄️ SQL (max {avail.get('SQL',0)})", min_value=0, max_value=avail.get('SQL',20), value=cfg['sql_count'], key='cfg_sql')
                with g2:
                    py_n  = st.number_input(f"🐍 Python (max {avail.get('Python',0)})", min_value=0, max_value=avail.get('Python',20), value=cfg['python_count'], key='cfg_py')
                with g3:
                    ps_n  = st.number_input(f"⚡ PySpark (max {avail.get('PySpark',0)})", min_value=0, max_value=max(avail.get('PySpark',0),1), value=cfg.get('pyspark_count',0), key='cfg_ps')
                total = int(sql_n) + int(py_n) + int(ps_n)
                st.info(f"Total: **{total}** questions per interview session")
                if st.button("Save Default Config", type="primary", width='stretch', key="save_cfg"):
                    if total == 0:
                        st.error("At least 1 question required.")
                    else:
                        db.set_interview_config(int(sql_n), int(py_n), int(ps_n))
                        st.success(f"✅ Saved: {int(sql_n)} SQL, {int(py_n)} Python, {int(ps_n)} PySpark")

            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            st.markdown("<p class='cr-section-title'>📋 Per-Candidate Question Counts</p>", unsafe_allow_html=True)
            all_c = db.get_all_candidates(include_deactivated=True)
            if all_c:
                conn2 = db.get_conn()
                rows_cfg = []
                for c in all_c:
                    r = conn2.execute('SELECT sql_count,python_count,pyspark_count FROM candidates WHERE id=?',(c['id'],)).fetchone()
                    eff = db.get_candidate_question_config(c['id'])
                    rows_cfg.append({
                        'Candidate': c['username'],
                        'SQL':     (str(r['sql_count'])+' (custom)') if r and r['sql_count'] is not None else str(eff['sql_count'])+' (default)',
                        'Python':  (str(r['python_count'])+' (custom)') if r and r['python_count'] is not None else str(eff['python_count'])+' (default)',
                        'PySpark': (str(r['pyspark_count'])+' (custom)') if r and r['pyspark_count'] is not None else str(eff.get('pyspark_count',0))+' (default)',
                        'Total':   eff['sql_count']+eff['python_count']+eff.get('pyspark_count',0),
                    })
                conn2.close()
                st.dataframe(pd.DataFrame(rows_cfg), use_container_width=True, hide_index=True)
            else:
                st.info("No candidates yet")

    elif "Change Password" in sec:

        _, col, _ = st.columns([1, 1.5, 1])
        with col:
            with st.container(border=True):
                st.markdown("<p class='cr-section-title'>🔑 Change Admin Password</p>", unsafe_allow_html=True)
                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
                cur_pass  = st.text_input("Current Password", type="password", key="cp_cur")
                new_pass1 = st.text_input("New Password", type="password", key="cp_new1", placeholder="Min 8 characters")
                new_pass2 = st.text_input("Confirm New Password", type="password", key="cp_new2")
                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
                if st.button("Update Password", type="primary", width='stretch', key="cp_btn"):
                    if not cur_pass or not new_pass1 or not new_pass2:
                        st.warning("All fields are required.")
                    elif not db.verify_admin(st.session_state.user, cur_pass):
                        st.error("❌ Current password is incorrect.")
                    elif len(new_pass1) < 8:
                        st.error("❌ New password must be at least 8 characters.")
                    elif new_pass1 != new_pass2:
                        st.error("❌ New passwords do not match.")
                    elif new_pass1 == cur_pass:
                        st.warning("New password must differ from current password.")
                    else:
                        db.change_admin_password(st.session_state.user, new_pass1)
                        st.success("✅ Password updated! Use your new password on next login.")
                        # Force logout so they re-authenticate with new password
                        import time as _t; _t.sleep(1.5)
                        logout()


# ── Hide native sidebar collapse button entirely — we use our own toggle ─────────
st.markdown("""
<style>
/* Hide Streamlit's native collapse/expand buttons completely */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)



# ── Router ─────────────────────────────────────────────────────────────────────
p = st.session_state.page
if p == "login": page_login()
elif p == "exam" and st.session_state.role == "candidate": page_exam()
elif p == "admin" and st.session_state.role == "admin":    page_admin()
else: page_login()
