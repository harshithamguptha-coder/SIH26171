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
- actions.py: Level 1 action coordinator
- state.py: Level 2 structured screen and browser state
- task_planner.py: Level 2 natural language task decomposition
- verifier.py: Level 2 action verification and safety auth checks
- controller.py: Level 2 multi-step closed loop agent controller
"""

from .browser import BrowserController
from .screenshot import ScreenshotManager
from .ocr import VisualPerception
from .privacy import PrivacyGuard
from .vision import VisionAgent, detect_ui_elements
from .actions import BrowserAgent
from .privacy import PrivacyGuard, protect_screenshot
from .vision import VisionAgent, LocalVision, detect_ui_elements, locate_ui_element
from .actions import BrowserAgent, run_google_search_demo
from .state import ScreenState, UIElement
from .task_planner import TaskPlanner, TaskPlan, PlanStep
from .verifier import ActionVerifier, VerificationResult
from .controller import AgentController, StepLog, ExecutionResult

__all__ = [
    "BrowserController",
    "ScreenshotManager",
    "VisualPerception",
    "PrivacyGuard",
    "protect_screenshot",
    "VisionAgent",
    "LocalVision",
    "detect_ui_elements",
    "locate_ui_element",
    "BrowserAgent",
    "run_google_search_demo",
    "ScreenState",
    "UIElement",
    "TaskPlanner",
    "TaskPlan",
    "PlanStep",
    "ActionVerifier",
    "VerificationResult",
    "AgentController",
    "StepLog",
    "ExecutionResult",
]
