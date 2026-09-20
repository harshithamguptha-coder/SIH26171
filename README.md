# SIH26171 — On-device Visual Perception for Lightweight Browser Agents

A beginner-friendly, modular proof-of-concept for the **Smart India Hackathon 2026** problem statement **SIH26171**.

This project implements an autonomous on-device browser agent that controls a web browser, visually perceives the user interface locally, masks sensitive information to protect privacy, and executes natural language commands — **without sending any screenshots to external cloud APIs**.

---

## 🌟 Key Features

1. **Natural Language Browser Command**: Accepts human instructions such as `"Search for Smart India Hackathon on Google"`.
2. **Local Browser Control**: Powered by Playwright Chromium running on your local machine.
3. **Local Visual Perception**: Extracts text and interactive UI elements using local OCR (`pytesseract`) and OpenCV contour detection.
4. **On-Device Privacy Protection**: Automatically detects Personally Identifiable Information (emails, phone numbers, API keys, passwords) and masks/redacts them locally before any human or agent review.
5. **Autonomous Action Execution**: Locates the visual target, clicks, types, and submits queries automatically.
6. **Zero Cloud Leak**: 100% of perception, screenshot processing, and masking happens entirely on your machine.
7. **Interactive Streamlit UI**: A clean visual dashboard showing raw screenshots, OCR detections, privacy masks, and final results step-by-step.

---

## 📁 Project Structure

```text
SIH26171/
│
├── app.py                  # Streamlit web interface for demoing the agent
├── requirements.txt        # Python library dependencies
├── README.md               # Setup and usage guide
├── test_agent.py           # Quick verification test script
│
├── agent/                  # Core browser agent modules
│   ├── __init__.py         # Package exports
│   ├── browser.py          # Playwright controller (launch, navigate, click, type)
│   ├── screenshot.py       # Screenshot capture & local storage manager
│   ├── ocr.py              # On-device visual perception & element detector
│   ├── privacy.py          # On-device sensitive data (PII) masking layer
│   └── actions.py          # End-to-end coordinator (perceive -> mask -> act)
│
├── utils/                  # Helper utilities
│   ├── __init__.py
│   └── helpers.py          # Path helpers, bounding box drawing, logging
│
└── screenshots/            # Local directory where screenshots are saved
```

---

## 🚀 Step-by-Step Setup Instructions

Follow these exact steps in your **VS Code Terminal** (`PowerShell` or `Command Prompt`).

### Step 1: Open the Project Folder in VS Code
Ensure your terminal is in the project directory:
```powershell
cd c:\Users\Harshitha\OneDrive\Desktop\SIH26171
```

### Step 2: Create a Python Virtual Environment
Creating a virtual environment ensures a clean installation:
```powershell
python -m venv venv
```

### Step 3: Activate the Virtual Environment
- **On PowerShell**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
  *(If PowerShell shows an execution policy warning, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then re-run the activate command)*

- **On Command Prompt (cmd)**:
  ```cmd
  venv\Scripts\activate.bat
  ```

### Step 4: Install Dependencies
Install all required libraries from `requirements.txt`:
```powershell
pip install -r requirements.txt
```

### Step 5: Install Playwright Browser Binaries
Playwright requires local browser binaries (Chromium) to operate:
```powershell
playwright install chromium
```

### Step 6: (Optional) Install Tesseract OCR for Enhanced Text Recognition
The project includes a built-in **OpenCV visual perception fallback** that works immediately without Tesseract. However, for full text OCR recognition:
1. Download the Windows installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
2. Install it to the default path: `C:\Program Files\Tesseract-OCR\`.
3. The project will automatically detect it!

---

## 🧪 Run Verification Test

Run the included test script to verify that on-device perception and privacy masking work:
```powershell
python test_agent.py
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
```

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

---

## 🛡️ Privacy & SIH Compliance

| Requirement | Implementation in this Project |
| :--- | :--- |
| **On-device Processing** | All image analysis (OpenCV & OCR) executes on the CPU/local GPU. |
| **Zero Cloud Leaks** | No HTTP calls to external vision LLMs (OpenAI, Gemini, Claude, etc.). |
| **Sensitive Data Masking** | PII is identified via regex and blacked out or blurred locally. |
| **Lightweight Design** | Modular Python without heavy multi-agent frameworks or vector DBs. |

