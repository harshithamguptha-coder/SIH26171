# On-device Visual Perception for Lightweight Browser Agents

A beginner-friendly, modular proof-of-concept.
This project implements an autonomous on-device browser agent that controls a web browser, visually perceives the user interface locally, masks sensitive information to protect privacy, and executes natural language commands — **without sending any screenshots to external cloud APIs**.
This project implements an autonomous on-device browser agent that controls a web browser, visually perceives the user interface locally, masks sensitive information to protect privacy, and executes multi-step natural language workflows — **without sending any screenshots to external cloud APIs**.

---

## 🌟 Key Features

1. **Natural Language Browser Command**: Accepts human instructions such as `"Search for Smart India Hackathon on Google"`.
2. **Local Browser Control**: Powered by Playwright Chromium running on your local machine.
3. **Local Visual Perception**: Extracts text and interactive UI elements using local OCR (`pytesseract`) and OpenCV contour detection.
4. **On-Device Privacy Protection**: Automatically detects Personally Identifiable Information (emails, phone numbers, API keys, passwords) and masks/redacts them locally before any human or agent review.
5. **Autonomous Action Execution**: Locates the visual target, clicks, types, and submits queries automatically.
6. **Zero Cloud Leak**: 100% of perception, screenshot processing, and masking happens entirely on your machine.
7. **Interactive Streamlit UI**: A clean visual dashboard showing raw screenshots, OCR detections, privacy masks, and final results step-by-step.
### Level 1 (Single-Action Foundation)
1. **Local Browser Control**: Powered by Playwright Chromium running on your local machine.
2. **Local Visual Perception**: Extracts text and interactive UI elements using local OCR (`pytesseract`) and OpenCV contour detection.
3. **On-Device Privacy Protection**: Automatically detects Personally Identifiable Information (emails, phone numbers, credit cards, passwords) and masks/redacts them locally before any visual processing.
4. **Zero Cloud Leak**: 100% of perception, screenshot processing, and masking happens entirely on your local machine.

### Level 2 (Multi-Step Autonomous Agent)
1. **Closed-Loop Controller**: Implements the continuous `OBSERVE → PRIVACY MASK → PERCEIVE → ACT → VERIFY → REPEAT` lifecycle.
2. **Deterministic Task Planner**: Decomposes natural language instructions into ordered sub-goals and actions.
3. **Structured Screen State**: Captures URL, page title, detected UI elements with bounding boxes and confidence scores, and privacy masking metrics.
4. **Visual Perception Preferred with Safe Fallback**: Uses visual coordinate clicks from local OCR and contour detection; safely falls back to Playwright locators when visual confidence is low, logging each method explicitly.
5. **Safety & Authentication Barrier**: Strictly prevents automated password entry. Detects login/authentication forms and pauses with `"User authentication required — waiting for user."`
6. **Max Action Limit**: Capped at `MAX_STEPS = 10` to avoid infinite loops, with interactive **STOP AGENT** support.

---

## 📁 Project Structure

```text
SIH26171/
│
├── app.py                  # Streamlit web interface for demoing the agent
├── requirements.txt        # Python library dependencies
├── README.md               # Setup and usage guide
├── test_agent.py           # Quick verification test script
├── app.py                      # Upgraded Streamlit dashboard (Level 1 & Level 2 tabs)
├── requirements.txt            # Python library dependencies
├── README.md                   # Setup, testing, and usage guide
├── test_agent.py               # Level 1 verification test script
├── test_vision.py              # Level 1 visual perception test script
├── test_level2.py              # Level 2 automated test suite (Planner, Verifier, Loops)
│
├── agent/                  # Core browser agent modules
│   ├── __init__.py         # Package exports
│   ├── browser.py          # Playwright controller (launch, navigate, click, type)
│   ├── screenshot.py       # Screenshot capture & local storage manager
│   ├── ocr.py              # On-device visual perception & element detector
│   ├── privacy.py          # On-device sensitive data (PII) masking layer
│   └── actions.py          # End-to-end coordinator (perceive -> mask -> act)
├── agent/                      # Core browser agent modules
│   ├── __init__.py             # Package exports for all components
│   ├── browser.py              # Playwright browser controller (navigation, clicks, typing)
│   ├── screenshot.py           # Screenshot capture & local storage manager
│   ├── ocr.py                  # On-device visual OCR & element detector (Tesseract)
│   ├── privacy.py              # On-device sensitive data (PII) masking layer
│   ├── vision.py               # On-device UI element detection & text matching
│   ├── actions.py              # Level 1 action coordinator
│   ├── state.py                # Level 2 structured ScreenState & UIElement models
│   ├── task_planner.py         # Level 2 deterministic task decomposition
│   ├── verifier.py             # Level 2 action verification & auth detection
│   └── controller.py           # Level 2 multi-step autonomous controller loop
│
├── utils/                  # Helper utilities
├── demo_pages/                 # Standalone local mock pages for testing
│   └── demo_form.html          # Safe registration form for multi-step Demo 2
│
├── utils/                      # Helper utilities
│   ├── __init__.py
│   └── helpers.py          # Path helpers, bounding box drawing, logging
│   └── helpers.py              # Path helpers, bounding box drawing, logging
│
└── screenshots/            # Local directory where screenshots are saved
└── screenshots/                # Local directory where screenshots are saved
```

---

## 🚀 Step-by-Step Setup Instructions
## 🎯 Supported Workflows & Demos

Follow these exact steps in your **VS Code Terminal** (`PowerShell` or `Command Prompt`).
### Demo 1 — Primary Workflow (GitHub Login)
- **Command**: `"Open GitHub and navigate to the login page"`
- **Workflow**:
  1. Open GitHub homepage (`https://github.com`)
  2. Capture screen locally & apply on-device privacy filter
  3. Visually detect the "Sign in" navigation link
  4. Click "Sign in" using visual coordinates (`Visual perception → action`)
  5. Capture new screen & apply privacy masking
  6. Detect login page landmarks (Username, Password fields)
  7. **Safety Stop**: Automatically pause and show:
     `TASK PAUSED — USER INPUT REQUIRED: User authentication required — waiting for user.`

### Step 1: Open the Project Folder in VS Code
Ensure your terminal is in the project directory:
```powershell
cd c:\Users\Harshitha\OneDrive\Desktop\SIH26171
```
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

### Step 2: Create a Python Virtual Environment
Creating a virtual environment ensures a clean installation:
```powershell
python -m venv venv
```
### Demo 3 — Optional Workflow (Search Query)
- **Command**: `"Open Google and search for Artificial Intelligence"`
- **Workflow**:
  1. Open search engine (`https://www.google.com` or `https://www.bing.com`)
  2. Locate search input visually & click it
  3. Type query with visible keystrokes
  4. Press Enter
  5. Verify search results populated on screen

### Step 3: Activate the Virtual Environment
- **On PowerShell**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
  *(If PowerShell shows an execution policy warning, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then re-run the activate command)*
---

- **On Command Prompt (cmd)**:
  ```cmd
  venv\Scripts\activate.bat
  ```
## 🚀 Setup Instructions

### Step 4: Install Dependencies
Install all required libraries from `requirements.txt`:
### Step 1: Open the Project Folder
Ensure your terminal is in the project root:
```powershell
cd "c:\Users\KRUPA G\SIH26171"
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 5: Install Playwright Browser Binaries
Playwright requires local browser binaries (Chromium) to operate:
### Step 3: Install Playwright Browser Binaries
```powershell
playwright install chromium
```
*(The browser controller automatically detects your system's Google Chrome or Microsoft Edge on Windows as well).*

### Step 6: (Optional) Install Tesseract OCR for Enhanced Text Recognition
The project includes a built-in **OpenCV visual perception fallback** that works immediately without Tesseract. However, for full text OCR recognition:
1. Download the Windows installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
2. Install it to the default path: `C:\Program Files\Tesseract-OCR\`.
3. The project will automatically detect it!
### Step 4: Verify Tesseract OCR
Install Tesseract OCR to `C:\Program Files\Tesseract-OCR\` if not already installed. The project automatically detects it.

---

## 🧪 Run Verification Test
## 🧪 Run Automated Tests

Run the included test script to verify that on-device perception and privacy masking work:
### 1. Test Level 1 Privacy & Vision Modules
```powershell
python test_agent.py
python test_vision.py
```
Expected output:
```text
[OK] Created synthetic test image...
[OK] PrivacyGuard detected 2 sensitive item(s):
     - Type: email -> Text: 'Contact: admin@sih.gov.in'
     - Type: api_key_or_secret -> Text: 'Secret Key: sk_test_987654321'
[OK] Redacted 2 regions into: ...
[OK] Annotated image generated: ...
All unit tests passed successfully!

### 2. Test Level 2 Multi-Step Agent & Closed Loop
```powershell
python test_level2.py
```
This runs:
- Test 1: TaskPlanner decomposition for all 3 demo workflows.
- Test 2: Structured ScreenState parsing & ActionVerifier landmarks.
- Test 3: Local Demo Form (Demo 2) end-to-end multi-step loop.
- Test 4: GitHub Login (Demo 1) end-to-end with safety authentication pause.

---

## 🖥️ Launch the Streamlit Demo App

To start the interactive UI dashboard, run:
```powershell
streamlit run app.py
```

Streamlit will open in your default browser at `http://localhost:8501`.
- Choose a preset command (e.g. `"Search for Smart India Hackathon 2026 on Google"`).
- Toggle between Headless (background) or Headed (visible browser) mode.
- Click **🚀 Run Browser Agent**.
- Inspect the four tabs:
  1. **Raw Screenshot**
  2. **On-Device OCR & UI Elements**
  3. **Privacy Masking** (shows masked PII)
  4. **Final Action Result**
Streamlit will launch in your browser at `http://localhost:8501`.

### Using the Level 2 Multi-Step Agent UI:
1. Click one of the preset workflow buttons (**Demo 1: GitHub Login**, **Demo 2: Submit Demo Form**, or **Demo 3: Google Search**) or type your own instruction.
2. Select **Visible Browser** if you wish to watch Chromium perform the clicks and keystrokes on your desktop live!
3. Click **🚀 START AGENT**.
4. Watch the:
   - **Live Agent Status Timeline** (real-time step updates)
   - **Task Result** (`TASK COMPLETED` or `TASK PAUSED — USER INPUT REQUIRED`)
   - **Privacy Panel** (100% Local, 0 bytes cloud upload, PII masked count)
   - **Current Screen Tabs** (Privacy-Protected, Visual Perception Annotations, Raw Screen)
   - **Screen Analysis** (Table of detected UI elements, bounding boxes, confidence, methods)
   - **Action Log** (Step-by-step audit with Action, Target, Coordinates, and Method)
5. Use the **🛑 STOP AGENT** button at any time to safely halt execution.

---

## 🛡️ Privacy & SIH Compliance

| Requirement | Implementation in this Project |
| :--- | :--- |
| **On-device Processing** | All image analysis (OpenCV & OCR) executes on the CPU/local GPU. |
| **Zero Cloud Leaks** | No HTTP calls to external vision LLMs (OpenAI, Gemini, Claude, etc.). |
| **Sensitive Data Masking** | PII is identified via regex and blacked out or blurred locally. |
| **Lightweight Design** | Modular Python without heavy multi-agent frameworks or vector DBs. |

| **On-device Processing** | All image analysis (OpenCV & OCR) executes on CPU/local GPU. |
| **Zero Cloud Leaks** | No screenshots, tokens, or DOM trees sent to external cloud APIs. |
| **Sensitive Data Masking** | PII is identified via regex and blacked out/blurred locally before perception. |
| **Safety Barrier** | Credential forms automatically pause agent execution. Real passwords are never typed. |
| **Action Limit & Safety** | Capped at 10 steps to prevent loops; user can click STOP AGENT anytime. |
| **Safe Fallback** | Prefers visual coordinates (`Visual perception → action`); uses Playwright fallback only when uncertain. |
