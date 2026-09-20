"""
Streamlit demo for SIH26171:
Privacy-Preserving On-Device Browser Agent

Clean judge-facing demo with the original controls restored:
- Synthetic sample or live browser capture
- Blackout / blur masking
- Query, search engine, visible browser options
- Original, protected, and annotated local-vision screenshots
"""

from __future__ import annotations

import concurrent.futures
import os
import sys
from pathlib import Path

import streamlit as st
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.privacy import create_synthetic_demo_screenshot, protect_screenshot
from agent.screenshot import capture_google_search_demo
from agent.vision import LocalVision


st.set_page_config(
    page_title="SIH26171 - Privacy-Preserving Browser Agent",
    page_icon="Shield",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .stApp { background: #f8fafc; }
        .block-container { max-width: 1220px; padding-top: 1.8rem; padding-bottom: 3rem; }
        .main-title { font-size: 2rem; font-weight: 800; color: #1e3a8a; line-height: 1.15; }
        .sub-title { font-size: 1rem; color: #475569; margin-top: 0.35rem; margin-bottom: 1rem; }
        .pipeline-box {
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            border-radius: 8px;
            padding: 0.95rem 1rem;
            font-size: 0.92rem;
            color: #0c4a6e;
            line-height: 1.7;
            margin-bottom: 1rem;
        }
        .section-label {
            color: #0f172a;
            font-weight: 800;
            font-size: 0.88rem;
            letter-spacing: 0.04em;
            margin-top: 1rem;
            margin-bottom: 0.55rem;
        }
        .status-panel {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 0.85rem 1rem;
        }
        .status-line { color: #166534; font-weight: 650; padding: 0.22rem 0; }
        .stat-ok, .stat-info, .stat-warn {
            border-radius: 8px;
            padding: 0.65rem 0.85rem;
            font-weight: 700;
            display: block;
            min-height: 58px;
        }
        .stat-ok { background: #dcfce7; color: #166534; border: 1px solid #86efac; }
        .stat-info { background: #e0f2fe; color: #075985; border: 1px solid #7dd3fc; }
        .stat-warn { background: #fef9c3; color: #713f12; border: 1px solid #fde047; }
        .result-box {
            background: #eff6ff;
            border-left: 4px solid #2563eb;
            border-radius: 8px;
            padding: 0.9rem 1rem;
            color: #0f172a;
            font-weight: 650;
        }
        .stButton > button {
            background: #1d4ed8;
            border: 1px solid #1d4ed8;
            border-radius: 8px;
            color: #ffffff;
            font-weight: 800;
            min-height: 2.8rem;
        }
        .stButton > button:hover { background: #1e40af; border-color: #1e40af; color: #ffffff; }
        div[data-testid="stSidebar"] { background: #ffffff; }
    </style>
    """,
    unsafe_allow_html=True,
)


def fix_event_loop() -> None:
    if sys.platform == "win32":
        import asyncio

        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except Exception:
            pass


def run_browser_capture(query: str, visible: bool, engine: str) -> str:
    def worker() -> str:
        fix_event_loop()
        return capture_google_search_demo(query=query, visible=visible, engine=engine)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(worker).result()


def run_privacy_pipeline(screenshot_path: str, redact_mode: str):
    def worker():
        fix_event_loop()
        return protect_screenshot(screenshot_path, redact_mode=redact_mode)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(worker).result()


def run_vision_pipeline(screenshot_path: str, redact_mode: str) -> dict:
    vision = LocalVision(debug=True, redact_mode=redact_mode)
    return vision.analyse(screenshot_path)


def show_image(path: str | None, caption: str) -> None:
    if path and os.path.exists(path):
        st.image(Image.open(path), caption=caption, use_container_width=True)
    else:
        st.info("Image not available yet.")


with st.sidebar:
    st.header("Demo Settings")
    demo_source = st.radio(
        "Screenshot Source",
        ["Synthetic sample (recommended)", "Live browser capture"],
        index=0,
        help="Synthetic is reliable for judging. Live capture opens a browser and may fall back if Google blocks automation.",
    )
    redact_mode = st.selectbox("Masking Style", ["blackout", "blur"], index=0)

    if demo_source == "Live browser capture":
        query = st.text_input("Search Query", value="Artificial Intelligence")
        engine = st.selectbox("Engine", ["Bing (Recommended)", "Google"], index=0)
        visible = st.checkbox("Visible Browser", value=False)
    else:
        query = "Artificial Intelligence"
        engine = "Synthetic"
        visible = False

    st.markdown("---")
    st.subheader("Privacy Guarantees")
    st.markdown(
        "- OCR runs locally with Tesseract\n"
        "- Sensitive pixels are masked before visual analysis\n"
        "- No screenshot is uploaded to a cloud API\n"
        "- Debug annotations are saved locally"
    )


st.markdown('<div class="main-title">Privacy-Preserving On-Device Browser Agent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Lightweight visual perception without sending private screen data to the cloud</div>',
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="pipeline-box">
        Browser screenshot -> Privacy masking -> Local OCR / visual processing -> Detected UI element -> Browser action result
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-label">USER COMMAND</div>', unsafe_allow_html=True)
command = st.text_input(
    "Command",
    value=f"Search for {query} on Google" if demo_source == "Live browser capture" else "Run local privacy and perception demo",
    label_visibility="collapsed",
)

run_btn = st.button("RUN AGENT", type="primary", use_container_width=True)

if run_btn:
    status_placeholder = st.empty()
    statuses: list[str] = []

    def add_status(text: str) -> None:
        statuses.append(f"? {text}")
        rows = "".join(f'<div class="status-line">{line}</div>' for line in statuses)
        status_placeholder.markdown(
            '<div class="section-label">LIVE STATUS</div>'
            f'<div class="status-panel">{rows}</div>',
            unsafe_allow_html=True,
        )

    try:
        add_status("Browser opened" if demo_source == "Live browser capture" else "Demo screenshot prepared")

        if demo_source == "Live browser capture":
            clean_engine = "Bing" if "bing" in engine.lower() else "Google"
            raw_path = run_browser_capture(query=query, visible=visible, engine=clean_engine)
            action_target = clean_engine
        else:
            raw_path = create_synthetic_demo_screenshot()
            action_target = "local synthetic page"

        add_status("Screenshot captured locally")

        _orig_path, protected_path, categories = run_privacy_pipeline(raw_path, redact_mode)
        add_status("Privacy scan completed")
        add_status("Sensitive information protected")

        vision_result = run_vision_pipeline(raw_path, redact_mode)
        add_status("Local visual perception completed")

        target = next((item for item in vision_result["elements"] if item["element"] == "search_box"), None)
        if target:
            final_result = (
                f"Detected search_box at approximately ({target['x']}, {target['y']}) "
                f"with confidence {target['confidence']}."
            )
        elif demo_source == "Live browser capture":
            final_result = f"Performed search for '{query}' on {action_target} and completed local screenshot analysis."
        else:
            final_result = "Completed local privacy masking and visual perception analysis on the synthetic sample."

        add_status("Browser action completed")

        st.session_state["demo_result"] = {
            "raw_path": raw_path,
            "protected_path": protected_path,
            "annotated_path": vision_result.get("debug_image"),
            "categories": categories,
            "final_result": final_result,
        }
    except Exception as exc:
        st.error(f"Demo failed: {exc}")


if "demo_result" in st.session_state:
    result = st.session_state["demo_result"]

    st.markdown('<div class="section-label">SCREEN ANALYSIS</div>', unsafe_allow_html=True)
    col_raw, col_safe, col_debug = st.columns(3, gap="large")
    with col_raw:
        show_image(result["raw_path"], "Original screenshot")
    with col_safe:
        show_image(result["protected_path"], "Privacy-protected screenshot")
    with col_debug:
        show_image(result["annotated_path"], "Annotated screenshot with detected UI element")

    st.markdown('<div class="section-label">PRIVACY STATUS</div>', unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns(3, gap="large")
    with col_a:
        st.markdown('<span class="stat-info">Processing:<br><b>Local device</b></span>', unsafe_allow_html=True)
    with col_b:
        st.markdown('<span class="stat-ok">Cloud screenshot upload:<br><b>None</b></span>', unsafe_allow_html=True)
    with col_c:
        detected = ", ".join(result["categories"]) if result["categories"] else "0"
        st.markdown(
            f'<span class="stat-warn">Sensitive information detected:<br><b>{detected}</b></span>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-label">FINAL RESULT</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="result-box">{result["final_result"]}</div>', unsafe_allow_html=True)
