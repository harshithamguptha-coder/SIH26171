"""
app.py
======
LOCALIS: Privacy-Preserving On-Device Browser Agent

"On-device Visual Perception for Lightweight Browser Agents"

A professional, privacy-first AI operations console for multi-step browser automation.
100% On-Device visual perception, OCR, and privacy redaction. Zero cloud API calls.
"""

from __future__ import annotations

import datetime
import os
import queue
import sys
import threading
import time
from pathlib import Path

import streamlit as st
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from agent.controller import AgentController, ExecutionResult
from agent.privacy import create_synthetic_demo_screenshot, protect_screenshot
from agent.screenshot import capture_google_search_demo
from agent.vision import LocalVision


# Page configuration
st.set_page_config(
    page_title="LOCALIS | On-Device Browser Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom High-End AI Security Operations CSS
st.markdown(
    """
    <style>
        /* Base Light Architecture */
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #000000 !important;
        }

        /* Remove Streamlit default top decoration / dark blue bar */
        header[data-testid="stHeader"],
        div[data-testid="stDecoration"] {
            display: none !important;
            height: 0px !important;
            visibility: hidden !important;
        }

        .stApp {
            background-color: #edf2f7 !important;
            background-image: 
                radial-gradient(at 0% 0%, rgba(199, 210, 254, 0.45) 0px, transparent 60%),
                radial-gradient(at 100% 100%, rgba(186, 230, 253, 0.5) 0px, transparent 60%),
                radial-gradient(at 50% 50%, rgba(243, 244, 246, 0.6) 0px, transparent 100%) !important;
            color: #000000 !important;
        }

        /* General Typography outside buttons */
        p:not(button *), span:not(button *), label:not(button *), h1, h2, h3, h4, h5, h6, [data-testid="stMarkdownContainer"]:not(button *) p {
            color: #000000;
        }

        /* Streamlit Alerts & Warnings (st.warning, st.info, st.error, st.success) */
        div[data-testid="stAlert"],
        div[data-testid="stAlert"] *,
        div[data-testid="stAlert"] p,
        div[data-testid="stAlert"] span,
        div[data-testid="stAlert"] div,
        div[role="alert"],
        div[role="alert"] *,
        .stAlert,
        .stAlert *,
        .stAlert p,
        div[data-baseweb="notification"],
        div[data-baseweb="notification"] * {
            color: #000000 !important;
            font-weight: 600 !important;
        }

        .block-container {
            max-width: 1380px;
            padding-top: 1.4rem;
            padding-bottom: 3.5rem;
        }

        /* Brand Headers */
        .brand-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 1.2rem;
            border-bottom: 1px solid #cbd5e1;
            margin-bottom: 1.4rem;
        }

        .brand-title-wrap {
            display: flex;
            align-items: baseline;
            gap: 12px;
        }

        .brand-title {
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            color: #000000 !important;
            margin: 0;
            line-height: 1.1;
        }

        .brand-sub {
            font-size: 0.95rem;
            color: #000000 !important;
            margin-top: 0.35rem;
            font-weight: 500;
        }

        .brand-pillars {
            display: flex;
            gap: 18px;
            margin-top: 0.75rem;
            font-size: 0.8rem;
            font-weight: 700;
            color: #000000 !important;
            letter-spacing: 0.03em;
        }

        .pillar-item {
            display: flex;
            align-items: center;
            gap: 5px;
            background: #ffffff;
            border: 1px solid #cbd5e1;
            color: #000000 !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
            padding: 4px 10px;
            border-radius: 6px;
        }

        /* Architecture Indicator */
        .arch-strip {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #ffffff;
            border: 1px solid #cbd5e1;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            border-radius: 8px;
            padding: 0.75rem 1.25rem;
            margin-bottom: 1.5rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.82rem;
        }

        .arch-node {
            color: #0284c7;
            font-weight: 700;
        }

        .arch-arrow {
            color: #64748b;
            font-weight: 700;
        }

        /* Control Area */
        .cmd-label {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
            font-weight: 700;
            color: #000000 !important;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 0.4rem;
        }

        /* Custom Input */
        .stTextInput > div > div > input {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 8px !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.92rem !important;
            padding: 0.7rem 1rem !important;
        }

        .stTextInput > div > div > input:focus {
            border-color: #0284c7 !important;
            box-shadow: 0 0 0 2px rgba(2, 132, 199, 0.2) !important;
        }

        /* =====================================================================
           BUTTON STYLES (CLEAN BOX MODEL, ZERO OVERLAPPING, WHITE TEXT)
           ===================================================================== */
        /* Base reset so children never duplicate borders, paddings, or backgrounds */
        button:not([data-baseweb="tab"]) * {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }

        /* Action and scenario buttons white text */
        button[kind="primary"] *,
        div[data-testid="stHorizontalBlock"] button *,
        div[data-testid="stColumn"] button * {
            color: #ffffff !important;
        }

        /* 1. Primary Action Button (RUN AGENT) */
        button[kind="primary"],
        div[data-testid="stHorizontalBlock"] button[kind="primary"] {
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
            border: 1px solid #38bdf8 !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 14px rgba(2, 132, 199, 0.3) !important;
            height: 46px !important;
            padding: 0 20px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        button[kind="primary"] * {
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            letter-spacing: 0.03em !important;
            color: #ffffff !important;
        }

        button[kind="primary"]:hover {
            background: linear-gradient(135deg, #0369a1 0%, #075985 100%) !important;
            border-color: #7dd3fc !important;
        }

        /* 2. Secondary Action Button (STOP) */
        div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
            background-color: #1a2234 !important;
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
            height: 46px !important;
            padding: 0 20px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        div[data-testid="stHorizontalBlock"] button[kind="secondary"] * {
            color: #ffffff !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
        }

        div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
            border-color: #ef4444 !important;
            background-color: #241922 !important;
        }

        div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover * {
            color: #f87171 !important;
        }

        /* 3. Preset Scenario Buttons */
        div[data-testid="stColumn"] button {
            background-color: #1a2234 !important;
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
            min-height: 64px !important;
            height: auto !important;
            padding: 12px 16px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1) !important;
            width: 100% !important;
        }

        div[data-testid="stColumn"] button div[data-testid="stMarkdownContainer"],
        div[data-testid="stColumn"] button p {
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            margin: 0 !important;
            color: #ffffff !important;
            font-size: 0.86rem !important;
            font-weight: 600 !important;
            line-height: 1.45 !important;
            white-space: pre-line !important;
            text-align: left !important;
        }

        div[data-testid="stColumn"] button:hover {
            border-color: #38bdf8 !important;
            background-color: #111c30 !important;
        }

        div[data-testid="stColumn"] button:hover * {
            color: #38bdf8 !important;
        }

        /* Operations Panels & Cards */
        .ops-panel {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 1.25rem 1.4rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }

        .ops-panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.9rem;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 0.6rem;
        }

        .ops-title {
            font-size: 0.88rem;
            font-weight: 700;
            color: #0f172a;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .ops-badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            padding: 2px 7px;
            border-radius: 4px;
            font-weight: 600;
        }

        .badge-cyan { background: #e0f2fe; color: #0284c7; border: 1px solid #bae6fd; }
        .badge-green { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
        .badge-amber { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }

        /* Metric Tiles */
        .metric-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 1.2rem;
        }

        .metric-tile {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1rem 1.2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }

        .metric-tile-label {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            color: #64748b;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        .metric-tile-val {
            font-size: 1.35rem;
            font-weight: 800;
            color: #0f172a;
            margin-top: 4px;
        }

        /* Result Banners */
        .result-banner {
            border-radius: 8px;
            padding: 1.1rem 1.4rem;
            margin-bottom: 1.3rem;
        }

        .result-success {
            background: #f0fdf4;
            border: 1px solid #86efac;
            border-left: 5px solid #10b981;
        }

        .result-auth {
            background: #fffbeb;
            border: 1px solid #fde68a;
            border-left: 5px solid #f59e0b;
        }

        .result-stopped {
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            border-left: 5px solid #64748b;
        }

        .result-heading {
            font-size: 1.05rem;
            font-weight: 800;
            letter-spacing: 0.02em;
        }

        .result-sub {
            font-size: 0.88rem;
            color: #334155;
            margin-top: 4px;
            line-height: 1.4;
        }

        /* Terminal Activity Log */
        .terminal-box {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1rem 1.2rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.82rem;
            line-height: 1.6;
            color: #1e293b;
            max-height: 320px;
            overflow-y: auto;
        }

        .log-line {
            display: flex;
            gap: 12px;
            padding: 3px 0;
            border-bottom: 1px solid #f1f5f9;
        }

        .log-time { color: #64748b; min-width: 65px; }
        .log-tag { font-weight: 700; min-width: 80px; }
        .log-msg { color: #0f172a; flex: 1; }

        .tag-agent { color: #0284c7; }
        .tag-observe { color: #7c3aed; }
        .tag-privacy { color: #059669; }
        .tag-perception { color: #db2777; }
        .tag-plan { color: #d97706; }
        .tag-action { color: #0284c7; }
        .tag-verify { color: #059669; }

        /* Timeline Tree View */
        .tree-timeline {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1rem 1.3rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.82rem;
            line-height: 1.7;
            color: #059669;
            max-height: 260px;
            overflow-y: auto;
        }

        /* Decision Panel Grid */
        .decision-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }

        .decision-cell-label {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.7rem;
            color: #64748b;
            text-transform: uppercase;
        }

        .decision-cell-val {
            font-size: 0.95rem;
            font-weight: 700;
            color: #0f172a;
            margin-top: 2px;
        }

        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 2px solid #cbd5e1;
            padding-bottom: 4px;
        }

        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 8px 16px;
        }

        .stTabs button,
        .stTabs button *,
        .stTabs [data-baseweb="tab"],
        .stTabs [data-baseweb="tab"] *,
        .stTabs [data-baseweb="tab"] p,
        .stTabs [data-baseweb="tab"] span,
        .stTabs [data-baseweb="tab"] div {
            color: #000000 !important;
            font-weight: 700 !important;
            font-size: 0.92rem !important;
        }

        .stTabs [aria-selected="true"] {
            background-color: #dbeafe !important;
            border-color: #3b82f6 !important;
        }

        .stTabs [aria-selected="true"],
        .stTabs [aria-selected="true"] *,
        .stTabs [aria-selected="true"] p,
        .stTabs [aria-selected="true"] span,
        .stTabs [aria-selected="true"] div {
            color: #000000 !important;
            font-weight: 800 !important;
        }

        /* Dataframe styling */
        div[data-testid="stDataFrame"] {
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            overflow: hidden !important;
        }

        .action-log-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #0284c7;
            border-radius: 6px;
            padding: 0.65rem 0.95rem;
            margin-bottom: 0.6rem;
            font-size: 0.88rem;
            color: #1e293b;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def fix_event_loop() -> None:
    """Ensures WindowsProactorEventLoopPolicy is set for Playwright child processes."""
    if sys.platform == "win32":
        import asyncio
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except Exception:
            pass


def show_image(path: str | None, caption: str) -> None:
    """Helper to render images with dark container styling."""
    if path and os.path.exists(path):
        st.image(Image.open(path), caption=caption, use_container_width=True)
    else:
        st.info("Artifact not yet generated for this step.")


# ==============================================================================
# RUNTIME CONFIGURATION (Clean & Headed by default for demonstration)
# ==============================================================================
is_headless = False  # Visible Chromium browser for real-time demonstration
slow_mo_val = 50     # Keystroke and cursor pacing (50ms)
max_steps_val = 10   # Max action safety threshold (MAX_STEPS)



# ==============================================================================
# MAIN APPLICATION HEADER
# ==============================================================================
st.markdown(
    """
    <div class="brand-container">
        <div>
            <div class="brand-title-wrap">
                <h1 class="brand-title">LOCALIS</h1>
            </div>
            <div class="brand-sub">Privacy-Preserving On-Device Browser Agent · Visual intelligence that stays on your device.</div>
            <div class="brand-pillars">
                <span class="pillar-item">PERCEIVE LOCALLY</span>
                <span class="pillar-item">PROTECT PRIVATELY</span>
                <span class="pillar-item">ACT INTELLIGENTLY</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Compact Architecture Indicator
st.markdown(
    """
    <div class="arch-strip">
        <span class="arch-node">1. PERCEIVE LOCALLY</span>
        <span class="arch-arrow">➔</span>
        <span class="arch-node">2. PROTECT PRIVATELY</span>
        <span class="arch-arrow">➔</span>
        <span class="arch-node">3. ACT INTELLIGENTLY</span>
        <span class="arch-arrow">➔</span>
        <span class="arch-node">4. VERIFY STATE</span>
        <span class="arch-arrow">↺</span>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# NAVIGATION TABS
# ==============================================================================
tab_agent, tab_privacy, tab_perception, tab_activity, tab_l1 = st.tabs([
    "AGENT",
    "PRIVACY",
    "PERCEPTION",
    "ACTIVITY",
    "LEVEL 1 INSPECTOR",
])


# ==============================================================================
# TAB 1: AGENT VIEW (PRIMARY CONTROLLER)
# ==============================================================================
with tab_agent:

    # Demo Scenarios
    st.markdown('<div class="cmd-label">DEMO SCENARIOS</div>', unsafe_allow_html=True)
    sc_col1, sc_col2, sc_col3 = st.columns(3)

    with sc_col1:
        if st.button("01 GITHUB LOGIN\nNavigate to GitHub authentication", use_container_width=True):
            st.session_state["task_input"] = "Open GitHub and navigate to the login page"

    with sc_col2:
        if st.button("02 PRIVATE FORM\nComplete local form with PII protection", use_container_width=True):
            st.session_state["task_input"] = "Open the demo form, enter my name, and submit the form"

    with sc_col3:
        if st.button("03 WEB SEARCH\nSearch using visual browser interaction", use_container_width=True):
            st.session_state["task_input"] = "Open Google and search for Artificial Intelligence"

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # Command Input
    st.markdown('<div class="cmd-label">WHAT SHOULD I DO?</div>', unsafe_allow_html=True)
    user_task = st.text_input(
        "Task Input",
        value=st.session_state.get("task_input", "Open GitHub and navigate to the login page"),
        label_visibility="collapsed",
        key="main_user_task_input",
    )

    # Action Controls
    ctrl_c1, ctrl_c2, _ = st.columns([1.6, 1.4, 4.0])
    with ctrl_c1:
        run_agent_clicked = st.button("▶ RUN AGENT", type="primary", use_container_width=True)
    with ctrl_c2:
        stop_agent_clicked = st.button("■ STOP", type="secondary", use_container_width=True)

    # Handle Stop Signal
    if stop_agent_clicked:
        if "controller" in st.session_state:
            st.session_state["controller"].stop()
            st.warning("Cancellation signal dispatched to agent controller. Safe halt in progress...")

    # Handle Agent Execution via Thread-Safe Event Queue
    if run_agent_clicked:
        fix_event_loop()
        controller = AgentController(
            headless=is_headless,
            max_steps=int(max_steps_val),
            slow_mo=int(slow_mo_val),
            debug=True,
        )
        st.session_state["controller"] = controller

        status_placeholder = st.empty()
        live_timeline_events: list[str] = []
        structured_log_records: list[dict[str, str]] = []

        event_queue: queue.Queue = queue.Queue()

        def queue_event_callback(msg: str, current_state=None):
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            event_queue.put(("EVENT", msg, timestamp, current_state))

        def execute_in_thread():
            fix_event_loop()
            try:
                outcome = controller.run(user_task, progress_callback=queue_event_callback)
                event_queue.put(("DONE", outcome))
            except Exception as ex:
                event_queue.put(("EXCEPTION", ex))

        worker = threading.Thread(target=execute_in_thread, daemon=True)
        worker.start()

        execution_result = None
        encountered_error = None

        with st.spinner("LOCALIS agent processing on-device closed loop..."):
            while worker.is_alive() or not event_queue.empty():
                try:
                    payload = event_queue.get(timeout=0.08)
                    kind = payload[0]

                    if kind == "EVENT":
                        raw_msg = payload[1]
                        t_stamp = payload[2]
                        live_timeline_events.append(raw_msg)

                        # Parse formatted tag if present [TAG] Message
                        tag = "AGENT"
                        body = raw_msg
                        if raw_msg.startswith("[") and "]" in raw_msg:
                            parts = raw_msg[1:].split("]", 1)
                            tag = parts[0]
                            body = parts[1].strip()

                        structured_log_records.append({
                            "time": t_stamp,
                            "tag": tag,
                            "msg": body,
                        })

                        # Format timeline tree
                        timeline_html = "<br>".join(
                            f"├── <span style='color:#38bdf8;'>✓</span> {m}" for m in live_timeline_events[-10:]
                        )
                        status_placeholder.markdown(
                            f"""
                            <div class="ops-panel">
                                <div class="ops-panel-header">
                                    <span class="ops-title">LIVE EXECUTION TIMELINE</span>
                                    <span class="ops-badge badge-cyan">ON-DEVICE</span>
                                </div>
                                <div class="tree-timeline">
                                    ● TASK STARTED<br>│<br>{timeline_html}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    elif kind == "DONE":
                        execution_result = payload[1]
                    elif kind == "EXCEPTION":
                        encountered_error = payload[1]

                except queue.Empty:
                    pass

        if encountered_error:
            st.error(f"Execution Error: {encountered_error}")
        elif execution_result:
            st.session_state["level2_result"] = execution_result
            st.session_state["persistent_timeline"] = live_timeline_events
            st.session_state["persistent_logs"] = structured_log_records

    # Render Persistent Results
    if "level2_result" in st.session_state:
        res: ExecutionResult = st.session_state["level2_result"]

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Task Result Banner
        if res.status == "TASK COMPLETED":
            st.markdown(
                f"""
                <div class="result-banner result-success">
                    <div class="result-heading" style="color:#059669;">TASK COMPLETED</div>
                    <div class="result-sub">All planned actions were successfully verified locally on-device.<br><b>Detail:</b> {res.message}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif "USER INPUT REQUIRED" in res.status or "AUTH" in res.status:
            st.markdown(
                f"""
                <div class="result-banner result-auth">
                    <div class="result-heading" style="color:#d97706;">AUTHENTICATION REQUIRED</div>
                    <div class="result-sub"><b>Agent paused safely and is waiting for user input.</b><br>
                    SIH Safety Policy Enforced: Autonomous agent stops when credentials or passwords are required. Real credentials are never automatically submitted.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="result-banner result-stopped">
                    <div class="result-heading" style="color:#334155;">{res.status}</div>
                    <div class="result-sub">{res.message}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Agent Decision Panel (What the agent is doing)
        final_state = res.final_screen_state
        last_action_log = res.action_logs[-1] if res.action_logs else None
        target_name = last_action_log.target if last_action_log else "None"
        next_act = last_action_log.action if last_action_log else "COMPLETE"
        exec_method = last_action_log.method if last_action_log else "Visual perception → action"

        st.markdown(
            f"""
            <div class="decision-grid">
                <div>
                    <div class="decision-cell-label">CURRENT PAGE</div>
                    <div class="decision-cell-val">{final_state.page if final_state else 'Active Webpage'}</div>
                </div>
                <div>
                    <div class="decision-cell-label">DETECTED TARGET</div>
                    <div class="decision-cell-val" style="color:#0284c7;">{target_name}</div>
                </div>
                <div>
                    <div class="decision-cell-label">ACTION / METHOD</div>
                    <div class="decision-cell-val">{next_act} ({exec_method})</div>
                </div>
                <div>
                    <div class="decision-cell-label">STEPS EXECUTED</div>
                    <div class="decision-cell-val" style="color:#059669;">{res.steps_completed} / {max_steps_val}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Split-Screen Comparison: RAW SCREEN vs PROTECTED VIEW
        st.markdown(
            """
            <div class="ops-panel-header" style="margin-top:1rem;">
                <span class="ops-title">LIVE SCREEN ANALYSIS (SPLIT-SCREEN VERIFICATION)</span>
                <span class="ops-badge badge-green">LOCAL PROCESSING · NO CLOUD UPLOAD</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        scr_col1, scr_col2 = st.columns(2, gap="medium")
        with scr_col1:
            st.markdown(
                """
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#64748b; font-weight:700; margin-bottom:6px;">
                    [RAW SCREEN] ORIGINAL UNPROCESSED CAPTURE
                </div>
                """,
                unsafe_allow_html=True,
            )
            if final_state and final_state.raw_screenshot:
                show_image(final_state.raw_screenshot, "Raw local browser viewport")
            else:
                st.info("Raw screen capture not available.")

        with scr_col2:
            st.markdown(
                """
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#059669; font-weight:700; margin-bottom:6px;">
                    [PROTECTED VIEW] ON-DEVICE PRIVACY MASKED (PII REDACTED)
                </div>
                """,
                unsafe_allow_html=True,
            )
            if final_state and final_state.protected_screenshot:
                show_image(final_state.protected_screenshot, "Privacy-masked local view")
            else:
                st.info("Protected screen capture not available.")

        # Visual Annotations toggle/view
        with st.expander("🔍 View Visual Perception Annotations (Bounding Boxes & OCR Tokens)"):
            if final_state and final_state.annotated_screenshot:
                show_image(final_state.annotated_screenshot, "On-device OCR and contour annotations")
            else:
                st.info("Perception annotation artifact not found.")

        # Structured Action Log
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="ops-panel-header">
                <span class="ops-title">STRUCTURED ACTION LOG (STEP-BY-STEP AUDIT)</span>
                <span class="ops-badge badge-cyan">OBSERVE ➔ ACT ➔ VERIFY</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for log in res.action_logs:
            coord_text = f" at ({log.coordinates[0]}, {log.coordinates[1]})" if log.coordinates else ""
            status_color = "#059669" if log.status == "SUCCESS" else ("#d97706" if "AUTH" in log.status else "#dc2626")
            st.markdown(
                f"""
                <div class="action-log-card">
                    <span style="font-family:'JetBrains Mono',monospace; font-weight:700; color:#0284c7;">[STEP {log.step_number}]</span>
                    <span style="font-weight:700; color:#0f172a; margin-left:8px;">{log.action}</span>
                    <span style="color:#64748b;"> target:</span> <span style="color:#0f172a; font-family:'JetBrains Mono',monospace;">"{log.target}"{coord_text}</span>
                    <span style="float:right; font-family:'JetBrains Mono',monospace; font-weight:700; color:{status_color};">{log.status}</span>
                    <br>
                    <span style="font-size:0.78rem; color:#64748b; font-family:'JetBrains Mono',monospace;">Method: {log.method}</span>
                    {f'<br><span style="font-size:0.78rem; color:#475569;">{log.details}</span>' if log.details else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )


# ==============================================================================
# TAB 2: PRIVACY CENTER
# ==============================================================================
with tab_privacy:
    st.markdown(
        """
        <div class="ops-panel-header">
            <span class="ops-title">ON-DEVICE PRIVACY CENTER</span>
            <span class="ops-badge badge-green">LOCAL PROTECTION ACTIVE</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    priv_data = res.privacy_summary if "level2_result" in st.session_state else {
        "processing": "LOCAL",
        "cloud_uploads": "NONE",
        "total_sensitive_items_masked": 0,
        "categories_detected": [],
    }

    # 3 Large Metrics
    st.markdown(
        f"""
        <div class="metric-row">
            <div class="metric-tile">
                <div class="metric-tile-label">LOCAL PROCESSING</div>
                <div class="metric-tile-val" style="color:#059669;">ACTIVE</div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:4px;">100% CPU/GPU on-device computation</div>
            </div>
            <div class="metric-tile">
                <div class="metric-tile-label">CLOUD SCREEN UPLOAD</div>
                <div class="metric-tile-val" style="color:#0284c7;">NONE</div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:4px;">0 bytes transmitted to external APIs</div>
            </div>
            <div class="metric-tile">
                <div class="metric-tile-label">SENSITIVE ITEMS MASKED</div>
                <div class="metric-tile-val" style="color:#d97706;">{priv_data.get('total_sensitive_items_masked', 0)}</div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:4px;">Redacted before visual perception</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="background:#f1f5f9; border:1px solid #e2e8f0; border-radius:8px; padding:14px 18px; margin-bottom:1.4rem;">
            <div style="font-size:0.85rem; font-weight:700; color:#0f172a; margin-bottom:4px;">
                Before visual reasoning, sensitive screen information is detected and masked locally.
            </div>
            <div style="font-size:0.8rem; color:#475569; line-height:1.5;">
                Local regex scanners and contour models detect Personally Identifiable Information (PII) on the captured framebuffer. 
                Sensitive pixels are blacked out or blurred with OpenCV before visual tokens are processed.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Detected Information & Redaction Examples
    st.markdown('<div class="cmd-label">DETECTED INFORMATION & REDACTION POLICY</div>', unsafe_allow_html=True)
    p_info1, p_info2, p_info3 = st.columns(3)

    with p_info1:
        st.markdown(
            """
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:12px 14px; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
                <div style="color:#0284c7; font-weight:700; font-size:0.84rem;">EMAIL ADDRESSES</div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.82rem; color:#334155; margin:6px 0;">rahul••••@••••.com</div>
                <div style="font-size:0.74rem; color:#64748b;">Masked locally via RFC 5322 regex</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with p_info2:
        st.markdown(
            """
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:12px 14px; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
                <div style="color:#0284c7; font-weight:700; font-size:0.84rem;">PHONE / CONTACTS</div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.82rem; color:#334155; margin:6px 0;">+91 ••••• •••••</div>
                <div style="font-size:0.74rem; color:#64748b;">Pattern matched and blacked out</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with p_info3:
        st.markdown(
            """
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:12px 14px; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
                <div style="color:#0284c7; font-weight:700; font-size:0.84rem;">PASSWORDS / API KEYS</div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.82rem; color:#334155; margin:6px 0;">token_sk_••••••••</div>
                <div style="font-size:0.74rem; color:#64748b;">Security tokens shielded from logs</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==============================================================================
# TAB 3: VISUAL PERCEPTION PANEL
# ==============================================================================
with tab_perception:
    st.markdown(
        """
        <div class="ops-panel-header">
            <span class="ops-title">VISUAL PERCEPTION (ON-DEVICE ELEMENT DETECTION)</span>
            <span class="ops-badge badge-cyan">OPENCV + LOCAL TESSERACT OCR</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "level2_result" in st.session_state and st.session_state["level2_result"].final_screen_state:
        f_state = st.session_state["level2_result"].final_screen_state
        if f_state.elements:
            table_rows = []
            for elem in f_state.elements:
                conf_pct = int(elem.confidence * 100) if elem.confidence <= 1.0 else int(elem.confidence)
                table_rows.append({
                    "ELEMENT": elem.text if elem.text else elem.element_type,
                    "TYPE": elem.element_type.upper(),
                    "CONFIDENCE": f"{conf_pct}%",
                    "POSITION": f"({elem.x}, {elem.y})",
                    "DIMENSIONS": f"{elem.width} × {elem.height} px",
                    "METHOD": "OCR" if "ocr" in elem.method.lower() else "Contour Geometry",
                })
            st.dataframe(table_rows, use_container_width=True)
        else:
            st.info("No interactive UI elements detected on final screen.")
    else:
        st.info("Run an agent workflow to populate the real-time visual perception map.")


# ==============================================================================
# TAB 4: ACTIVITY LOG (TERMINAL OPERATIONS CONSOLE)
# ==============================================================================
with tab_activity:
    st.markdown(
        """
        <div class="ops-panel-header">
            <span class="ops-title">ACTIVITY / EVENT LOG</span>
            <span class="ops-badge badge-cyan">MONOSPACE STREAM</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    log_entries = st.session_state.get("persistent_logs", [])
    if log_entries:
        rendered_lines = []
        for entry in log_entries:
            t = entry.get("time", "")
            tag = entry.get("tag", "AGENT")
            msg = entry.get("msg", "")

            tag_class = "tag-agent"
            tag_upper = tag.upper()
            if "OBSERVE" in tag_upper or "SCREEN" in tag_upper:
                tag_class = "tag-observe"
            elif "PRIVACY" in tag_upper:
                tag_class = "tag-privacy"
            elif "PERCEPTION" in tag_upper or "VISION" in tag_upper:
                tag_class = "tag-perception"
            elif "PLAN" in tag_upper:
                tag_class = "tag-plan"
            elif "VERIFY" in tag_upper:
                tag_class = "tag-verify"

            rendered_lines.append(
                f'<div class="log-line"><span class="log-time">{t}</span>'
                f'<span class="log-tag {tag_class}">{tag:<9}</span>'
                f'<span class="log-msg">{msg}</span></div>'
            )
        st.markdown(f'<div class="terminal-box">{"".join(rendered_lines)}</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            """
            <div class="terminal-box" style="color:#64748b;">
                System initialized. Waiting for task execution to stream operations log...
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==============================================================================
# TAB 5: LEVEL 1 SINGLE-ACTION INSPECTOR (PRESERVED)
# ==============================================================================
with tab_l1:
    st.markdown(
        """
        <div class="ops-panel-header">
            <span class="ops-title">LEVEL 1: SINGLE-ACTION & PRIVACY INSPECTOR</span>
            <span class="ops-badge badge-cyan">BASELINE VALIDATION</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    l1_c1, l1_c2 = st.columns(2)
    with l1_c1:
        l1_src = st.radio("Level 1 Capture Source", ["Synthetic sample (recommended)", "Live browser capture"], index=0, key="l1_source_radio")
    with l1_c2:
        l1_mask = st.selectbox("Masking Mode", ["blackout", "blur"], index=0, key="l1_mask_sel")

    if l1_src == "Live browser capture":
        l1_q = st.text_input("Search Term", value="Artificial Intelligence", key="l1_q_in")
        l1_eng = st.selectbox("Search Engine", ["Bing (Recommended)", "Google"], index=0, key="l1_eng_in")
        l1_vis = st.checkbox("Visible Window", value=False, key="l1_vis_chk")
    else:
        l1_q = "Artificial Intelligence"
        l1_eng = "Synthetic"
        l1_vis = False

    if st.button("RUN LEVEL 1 INSPECTOR", type="primary", use_container_width=True):
        with st.spinner("Processing Level 1 pipeline on-device..."):
            fix_event_loop()
            if l1_src == "Live browser capture":
                target_engine = "Bing" if "bing" in l1_eng.lower() else "Google"
                raw_path = capture_google_search_demo(query=l1_q, visible=l1_vis, engine=target_engine)
            else:
                raw_path = create_synthetic_demo_screenshot()

            orig_path, prot_path, cats = protect_screenshot(raw_path, redact_mode=l1_mask)
            vision_data = LocalVision(debug=True, redact_mode=l1_mask).analyse(raw_path)

            st.session_state["l1_artifacts"] = {
                "raw": raw_path,
                "prot": prot_path,
                "annotated": vision_data.get("debug_image"),
                "categories": cats,
            }

    if "l1_artifacts" in st.session_state:
        l1_art = st.session_state["l1_artifacts"]
        c_a, c_b, c_c = st.columns(3)
        with c_a:
            show_image(l1_art["raw"], "1. Raw Screenshot")
        with c_b:
            show_image(l1_art["prot"], "2. Privacy-Masked View")
        with c_c:
            show_image(l1_art["annotated"], "3. Visual Perception Annotations")

        st.markdown(f"**Sensitive Information Detected & Shielded:** `{', '.join(l1_art['categories']) if l1_art['categories'] else 'None'}`")


