"""
agent
=====
Package containing core modules for the on-device visual browser agent:
- browser.py: Playwright browser automation controller
- screenshot.py: Local screenshot capture and storage
- ocr.py: On-device visual OCR & element detection
- privacy.py: On-device sensitive information masking (PII redaction)
- vision.py: On-device UI element detection (search box, button, text)
- actions.py: End-to-end action coordinator
"""

from .browser import BrowserController
from .screenshot import ScreenshotManager
from .ocr import VisualPerception
from .privacy import PrivacyGuard
from .vision import VisionAgent, detect_ui_elements
from .actions import BrowserAgent

__all__ = [
    "BrowserController",
    "ScreenshotManager",
    "VisualPerception",
    "PrivacyGuard",
    "VisionAgent",
    "detect_ui_elements",
    "BrowserAgent",
]
