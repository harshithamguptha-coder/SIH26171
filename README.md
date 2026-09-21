# On-Device Visual Perception for Lightweight Browser Agents

A privacy-first, autonomous on-device browser agent that controls a web browser, visually perceives the user interface locally, masks sensitive information to protect user privacy, and executes multi-step natural language workflows — **without sending any screenshots to external cloud APIs**.

---

## Key Features

### Level 1: On-Device Perception & Privacy Foundation
1. **Local Visual Perception**: Extracts text and interactive UI elements using local OCR (`pytesseract`) and OpenCV contour detection on your device.
2. **On-Device Privacy Protection**: Automatically detects Personally Identifiable Information (PII) like emails, phone numbers, API keys, and passwords, masking/redacting them locally before any agent or human review.
3. **Zero Cloud Leaks**: 100% of perception, screenshot processing, and masking happens strictly on your machine — 0 bytes uploaded to external vision LLMs or cloud APIs.
4. **Local Browser Control**: Powered by Playwright Chromium running on your local machine with support for system Chrome/Edge.

### Level 2: Multi-Step Autonomous Agent
1. **Closed-Loop Controller**: Implements the continuous `OBSERVE → PRIVACY MASK → PERCEIVE → ACT → VERIFY → REPEAT` lifecycle.
2. **Deterministic Task Planner**: Decomposes natural language instructions into ordered sub-goals and actions.
3. **Structured Screen State**: Captures URL, page title, detected UI elements with bounding boxes and confidence scores, and privacy masking metrics.
4. **Visual Perception Preferred with Safe Fallback**: Uses visual coordinate clicks from local OCR and contour detection; safely falls back to Playwright locators when visual confidence is low, logging each method explicitly.
5. **Safety & Authentication Barrier**: Strictly prevents automated password entry. Detects login/authentication forms and pauses with `"User authentication required — waiting for user."`
6. **Max Action Limit & Safety**: Capped at `MAX_STEPS = 10` to avoid infinite loops, with interactive **STOP AGENT** support.

---

## Project Structure

```text
SIH26171/
│
├── app.py                  # Streamlit web dashboard (Light mode, Live Agent & Inspector tabs)
├── requirements.txt        # Python library dependencies
├── README.md               # Setup, testing, and usage guide
├── test_agent.py           # Level 1 verification test script (Privacy & OCR)
├── test_vision.py          # Level 1 visual perception test script
├── test_level2.py          # Level 2 automated test suite (Planner, Verifier, Loops)
│
├── agent/                  # Core browser agent modules
│   ├── __init__.py         # Package exports for all components
│   ├── browser.py          # Playwright browser controller (navigation, clicks, typing)
│   ├── screenshot.py       # Screenshot capture & local storage manager
│   ├── ocr.py              # On-device visual OCR & element detector (Tesseract)
│   ├── privacy.py          # On-device sensitive data (PII) masking layer
│   ├── vision.py           # On-device UI element detection & text matching
│   ├── actions.py          # Level 1 action coordinator
│   ├── state.py            # Level 2 structured ScreenState & UIElement models
│   ├── task_planner.py     # Level 2 deterministic task decomposition
│   ├── verifier.py         # Level 2 action verification & auth detection
│   └── controller.py       # Level 2 multi-step autonomous controller loop
│
├── demo_pages/             # Standalone local mock pages for testing
│   └── demo_form.html      # Safe registration form for multi-step Demo 2
│
├── utils/                  # Helper utilities
│   ├── __init__.py
│   └── helpers.py          # Path helpers, bounding box drawing, logging
│
└── screenshots/            # Local directory where screenshots are saved (gitignored)
```

---

## Supported Workflows & Demos

### Demo 1 — Primary Workflow (GitHub Login)
- **Command**: `"Open GitHub and navigate to the login page"`
- **Workflow**:
  1. Open GitHub homepage (`https://github.com`)
  2. Capture screen locally & apply on-device privacy filter
  3. Visually detect the "Sign in" navigation link
  4. Click "Sign in" using visual coordinates (`Visual perception → action`)
  5. Capture new screen & apply privacy masking
  6. Detect login page landmarks (Username, Password fields)
  7. **Safety Stop**: Automatically pause and display:
     `TASK PAUSED — USER INPUT REQUIRED: User authentication required — waiting for user.`

### Demo 2 — Secondary Workflow (Local Demo Form)
- **Command**: `"Open the demo form, enter my name, and submit the form"`
- **Workflow**:
  1. Open local `demo_pages/demo_form.html`
  2. Observe screen & mask PII (email field)
  3. Identify "Full Name" input visually & click it
  4. Type dummy name (`"Aarav Sharma"`)
  5. Identify "Submit Application" button visually & click it
  6. Re-perceive screen and verify submission success banner
  7. Display `TASK COMPLETED`

### Demo 3 — Optional Workflow (Search Query)
- **Command**: `"Open Google and search for Artificial Intelligence"`
- **Workflow**:
  1. Open search engine (`https://www.google.com`)
  2. Locate search input visually & click it
  3. Type query with visible keystrokes
  4. Press Enter
  5. Verify search results populated on screen

---

## Setup Instructions

Follow these steps in your terminal (**PowerShell** or **Command Prompt**):

### Step 1: Open the Project Folder
Ensure your terminal is in the project directory:
```powershell
cd "c:\Users\KRUPA G\SIH26171"
```

### Step 2: Install Python Dependencies
Install required libraries from `requirements.txt`:
```powershell
pip install -r requirements.txt
```

### Step 3: Install Playwright Browser Binaries
Playwright requires local browser binaries (Chromium) to operate:
```powershell
playwright install chromium
```
*(The browser controller also automatically detects your system's Google Chrome or Microsoft Edge on Windows).*

### Step 4: Verify Tesseract OCR (Optional / Recommended)
Install Tesseract OCR to `C:\Program Files\Tesseract-OCR\` if not already installed. The project automatically detects it at that path and falls back gracefully to local OpenCV contour analysis if unavailable.

---

## Run Automated Tests

### 1. Test Level 1 Privacy & Vision Modules
```powershell
python test_agent.py
python test_vision.py
```

### 2. Test Level 2 Multi-Step Agent & Closed Loop
```powershell
python test_level2.py
```
This runs:
- **Test 1**: TaskPlanner decomposition for all 3 demo workflows.
- **Test 2**: Structured ScreenState parsing & ActionVerifier landmarks.
- **Test 3**: Local Demo Form (Demo 2) end-to-end multi-step loop.
- **Test 4**: GitHub Login (Demo 1) end-to-end with safety authentication pause.

---

## Launch the Streamlit Demo App

To start the interactive UI dashboard, run:
```powershell
streamlit run app.py
```

Streamlit will launch in your browser at `http://localhost:8501`.

### Using the Dashboard:
1. **Choose a Scenario**: Click one of the preset scenario buttons (**Demo 1: GitHub Login**, **Demo 2: Submit Demo Form**, or **Demo 3: Google Search**) or type your own custom instruction.
2. **Display Mode**: Toggle between **Visible Browser** (watch Chromium perform live clicks and typing) or **Headless** (fast background execution).
3. **Execute**: Click **▶ RUN AGENT** to start the autonomous loop.
4. **Inspect Tabs**:
   - **AGENT**: Live agent status, execution banner, and step-by-step action history.
   - **PRIVACY**: Privacy metrics (cloud upload = 0 bytes, PII items masked) and privacy-protected screenshot preview.
   - **PERCEPTION**: Visual perception annotations, bounding boxes, and detected UI element metrics.
   - **ACTIVITY**: Live terminal audit log and sub-goal execution timeline.
   - **LEVEL 1 INSPECTOR**: Granular inspection of raw screenshot, OCR bounding boxes, and masked PII regions.
5. **Safety Control**: Click **■ STOP** at any time to safely halt execution.

---

## Privacy & Compliance

| Requirement | Implementation in this Project |
| :--- | :--- |
| **On-device Processing** | All image analysis (OpenCV & OCR) executes locally on CPU/local GPU. |
| **Zero Cloud Leaks** | No screenshots, tokens, or DOM trees sent to external cloud APIs (0 bytes). |
| **Sensitive Data Masking** | PII is identified via regex and blacked out/blurred locally before visual perception. |
| **Safety Barrier** | Credential forms automatically pause agent execution. Passwords are never entered by the agent. |
| **Action Limit & Safety** | Capped at 10 steps to prevent infinite loops; user can click STOP AGENT anytime. |
| **Safe Fallback** | Prefers visual coordinates (`Visual perception → action`); uses Playwright fallback only when uncertain. |
