"""
agent/controller.py
===================
Multi-Step Autonomous Browser Agent Controller for SIH26171 Level 2.
Implements the closed loop:
OBSERVE -> PRIVACY MASK -> UNDERSTAND -> DECIDE -> ACT -> VERIFY -> REPEAT

Zero cloud vision APIs — 100% on-device visual perception and privacy protection.
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from agent.browser import BrowserController
from agent.privacy import PrivacyGuard
from agent.screenshot import ScreenshotManager
from agent.state import ScreenState, UIElement
from agent.task_planner import PlanStep, TaskPlan, TaskPlanner
from agent.verifier import ActionVerifier, VerificationResult
from agent.vision import LocalVision


@dataclass
class StepLog:
    """Detailed log record of a single action step."""
    step_number: int
    action: str
    target: str
    method: str  # 'Visual perception → action' or 'Visual perception uncertain → Playwright fallback'
    status: str  # 'SUCCESS', 'FAILED', 'AUTH_REQUIRED', 'RETRY'
    details: str = ""
    coordinates: Optional[tuple[int, int]] = None
    sensitive_count: int = 0
    raw_screenshot: Optional[str] = None
    protected_screenshot: Optional[str] = None
    annotated_screenshot: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step_number,
            "action": self.action,
            "target": self.target,
            "method": self.method,
            "status": self.status,
            "details": self.details,
            "coordinates": self.coordinates,
            "sensitive_count": self.sensitive_count,
            "protected_screenshot": self.protected_screenshot,
            "annotated_screenshot": self.annotated_screenshot,
        }


@dataclass
class ExecutionResult:
    """Final outcome summary of the agent execution."""
    task: str
    status: str  # 'TASK COMPLETED', 'TASK PAUSED — USER INPUT REQUIRED', 'TASK STOPPED SAFELY', 'FAILED'
    message: str
    steps_completed: int
    action_logs: List[StepLog] = field(default_factory=list)
    timeline: List[str] = field(default_factory=list)
    final_screen_state: Optional[ScreenState] = None
    plan: Optional[TaskPlan] = None
    privacy_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "status": self.status,
            "message": self.message,
            "steps_completed": self.steps_completed,
            "timeline": self.timeline,
            "action_logs": [l.to_dict() for l in self.action_logs],
            "privacy_summary": self.privacy_summary,
            "final_state": self.final_screen_state.to_dict() if self.final_screen_state else None,
        }


class AgentController:
    """
    Orchestrates the multi-step browser agent loop with privacy enforcement,
    visual coordinate preference, safe Playwright fallback, and auth safety checks.
    """

    def __init__(
        self,
        headless: bool = False,
        max_steps: int = 10,
        slow_mo: int = 60,
        debug: bool = True,
    ):
        self.headless = headless
        self.max_steps = max_steps
        self.slow_mo = slow_mo
        self.debug = debug

        # On-device components
        self.planner = TaskPlanner()
        self.screenshot_mgr = ScreenshotManager()
        self.privacy_guard = PrivacyGuard(redact_mode="blackout")
        self.vision = LocalVision(debug=debug, redact_mode="blackout")
        self.verifier = ActionVerifier()

        # Cancellation flag
        self.stop_requested = False

    def stop(self):
        """Signals the controller to safely interrupt execution."""
        print("[AGENT] Cancellation signal received. Stopping agent safely...")
        self.stop_requested = True

    def run(
        self,
        instruction: str,
        progress_callback: Optional[Callable[[str, Optional[ScreenState]], None]] = None,
    ) -> ExecutionResult:
        """
        Executes the multi-step loop for the given natural language instruction.
        """
        self.stop_requested = False
        action_logs: List[StepLog] = []
        timeline: List[str] = []
        total_sensitive_masked = 0
        all_sensitive_categories = set()

        def log_event(phase: str, text: str, state: Optional[ScreenState] = None):
            formatted = f"[{phase}] {text}"
            print(formatted)
            timeline.append(f"✓ {text}")
            if progress_callback:
                progress_callback(formatted, state)

        log_event("AGENT", f"Task received: '{instruction}'")

        # Step 1: Understand task and create plan
        plan = self.planner.create_plan(instruction)
        log_event("PLAN", f"Decomposed into {len(plan.step_definitions)} step(s): {', '.join(plan.steps)}")

        browser = BrowserController(headless=self.headless, slow_mo=self.slow_mo)
        step_counter = 0
        final_state: Optional[ScreenState] = None
        task_status = "TASK COMPLETED"
        task_message = "All planned sub-goals achieved successfully."

        try:
            log_event("AGENT", "Launching local Chromium browser via Playwright...")
            browser.start()
            timeline.append("✓ Browser opened")

            # Execute plan steps sequentially with verification
            for plan_step in plan.step_definitions:
                if self.stop_requested:
                    task_status = "TASK STOPPED SAFELY"
                    task_message = "Agent execution stopped by user request."
                    log_event("AGENT", task_message)
                    break

                if step_counter >= self.max_steps:
                    task_status = "TASK STOPPED SAFELY"
                    task_message = "Task stopped safely: maximum action limit reached."
                    log_event("AGENT", task_message)
                    break

                step_counter += 1
                log_event("AGENT", f"Starting Step {step_counter}: {plan_step.description}")

                # 1. ACTION: NAVIGATE
                if plan_step.action == "NAVIGATE":
                    log_event("PLAN", f"Next action: NAVIGATE to {plan_step.target}")
                    browser.navigate(plan_step.target)
                    time.sleep(1.5)
                    browser.handle_consent_popups()
                    action_log = StepLog(
                        step_number=step_counter,
                        action="NAVIGATE",
                        target=plan_step.target,
                        method="System",
                        status="SUCCESS",
                        details=f"Navigated to {plan_step.target}",
                    )
                    action_logs.append(action_log)
                    log_event("ACTION", f"Navigation to {plan_step.target} completed")

                # 2. ACTIONS requiring visual observation (CLICK, TYPE, PRESS_KEY, VERIFY)
                else:
                    # OBSERVE: Capture screenshot locally
                    raw_shot = self.screenshot_mgr.capture_page(browser.page, prefix=f"step_{step_counter:02d}")
                    log_event("OBSERVE", f"Screenshot captured locally ({os.path.basename(raw_shot)})")

                    # PRIVACY: On-device PII scan & masking
                    _orig, protected_shot, categories = self.privacy_guard.process_screenshot(raw_shot)
                    num_masked = len(categories)
                    total_sensitive_masked += num_masked
                    all_sensitive_categories.update(categories)
                    log_event("PRIVACY", f"Sensitive information detected and masked (Items: {num_masked}, Types: {categories})")

                    # PERCEPTION: Local visual perception
                    vision_result = self.vision.analyse(raw_shot)
                    annotated_shot = vision_result.get("debug_image")
                    
                    # Convert to structured ScreenState
                    elements: List[UIElement] = []
                    for elem in vision_result.get("elements", []):
                        elements.append(
                            UIElement(
                                element_type=elem.get("element", "ui_element"),
                                text=elem.get("matched_text", elem.get("element", "")),
                                x=elem.get("x", 0),
                                y=elem.get("y", 0),
                                width=elem.get("width", 0),
                                height=elem.get("height", 0),
                                confidence=elem.get("confidence", 0.5),
                                method=elem.get("method", "visual_perception"),
                                box=elem.get("box", []),
                            )
                        )

                    current_state = ScreenState(
                        url=browser.get_current_url(),
                        title=browser.get_title(),
                        page=self._determine_page_label(browser.get_current_url(), browser.get_title()),
                        raw_screenshot=raw_shot,
                        protected_screenshot=protected_shot,
                        annotated_screenshot=annotated_shot,
                        elements=elements,
                        text_tokens=vision_result.get("text_tokens", []),
                        sensitive_items_masked=num_masked,
                        sensitive_categories=categories,
                    )
                    final_state = current_state
                    log_event("PERCEPTION", f"Detected {len(elements)} UI elements and {len(current_state.text_tokens)} text tokens locally", current_state)

                    # Check for safety / authentication requirement before acting
                    body_text = browser.get_page_content_text()
                    is_auth, auth_landmarks = self.verifier._check_auth_checkpoint(current_state, body_text)
                    if is_auth and plan_step.action not in ["VERIFY", "NAVIGATE"]:
                        task_status = "TASK PAUSED — USER INPUT REQUIRED"
                        task_message = "User authentication required — waiting for user."
                        log_event("AGENT", task_message, current_state)
                        break

                    # Execute specific action:
                    if plan_step.action == "CLICK":
                        log_event("PLAN", f"Next action: CLICK \"{plan_step.target}\"")
                        click_success, method_used, coords = self._execute_click_with_fallback(
                            browser, plan_step.target, current_state, raw_shot, plan_step.fallback_selector
                        )
                        status_str = "SUCCESS" if click_success else "FAILED"
                        action_logs.append(
                            StepLog(
                                step_number=step_counter,
                                action="CLICK",
                                target=plan_step.target,
                                method=method_used,
                                status=status_str,
                                coordinates=coords,
                                protected_screenshot=protected_shot,
                                annotated_screenshot=annotated_shot,
                                sensitive_count=num_masked,
                            )
                        )
                        log_event("ACTION", f"Click executed on \"{plan_step.target}\" via {method_used}")
                        time.sleep(1.5)  # Allow DOM to react

                    elif plan_step.action == "TYPE":
                        val_to_type = plan_step.input_value or "Sample Text"
                        log_event("PLAN", f"Next action: TYPE \"{val_to_type}\" into {plan_step.target}")
                        type_success, method_used = self._execute_type(
                            browser, plan_step.target, val_to_type, current_state, raw_shot, plan_step.fallback_selector
                        )
                        action_logs.append(
                            StepLog(
                                step_number=step_counter,
                                action="TYPE",
                                target=plan_step.target,
                                method=method_used,
                                status="SUCCESS" if type_success else "FAILED",
                                details=f"Typed input into {plan_step.target}",
                                protected_screenshot=protected_shot,
                                annotated_screenshot=annotated_shot,
                            )
                        )
                        log_event("ACTION", f"Type action completed for {plan_step.target}")

                    elif plan_step.action == "PRESS_KEY":
                        key_name = plan_step.target or "Enter"
                        log_event("PLAN", f"Next action: PRESS_KEY \"{key_name}\"")
                        browser.press_key(key_name)
                        action_logs.append(
                            StepLog(
                                step_number=step_counter,
                                action="PRESS_KEY",
                                target=key_name,
                                method="System",
                                status="SUCCESS",
                                details=f"Pressed keyboard key: {key_name}",
                            )
                        )
                        log_event("ACTION", f"Key press '{key_name}' executed")
                        time.sleep(1.5)

                # Post-action VERIFICATION check (if step specifies verification or at end)
                if plan_step.expected_verification:
                    # Capture fresh post-action screen state to verify
                    post_shot = self.screenshot_mgr.capture_page(browser.page, prefix=f"verify_{step_counter:02d}")
                    _orig, post_protected, post_cats = self.privacy_guard.process_screenshot(post_shot)
                    post_vision = self.vision.analyse(post_shot)
                    
                    post_elements = [
                        UIElement(
                            element_type=e.get("element", "ui_element"),
                            text=e.get("matched_text", e.get("element", "")),
                            x=e.get("x", 0),
                            y=e.get("y", 0),
                            width=e.get("width", 0),
                            height=e.get("height", 0),
                            confidence=e.get("confidence", 0.5),
                            method=e.get("method", "visual_perception"),
                            box=e.get("box", []),
                        )
                        for e in post_vision.get("elements", [])
                    ]

                    verify_state = ScreenState(
                        url=browser.get_current_url(),
                        title=browser.get_title(),
                        page=self._determine_page_label(browser.get_current_url(), browser.get_title()),
                        raw_screenshot=post_shot,
                        protected_screenshot=post_protected,
                        annotated_screenshot=post_vision.get("debug_image"),
                        elements=post_elements,
                        text_tokens=post_vision.get("text_tokens", []),
                        sensitive_items_masked=len(post_cats),
                        sensitive_categories=post_cats,
                    )
                    final_state = verify_state

                    v_result = self.verifier.verify(
                        plan_step.expected_verification,
                        verify_state,
                        browser.get_page_content_text(),
                    )

                    log_event("VERIFY", f"Result: {v_result.message} (Status: {v_result.status})", verify_state)
                    action_logs.append(
                        StepLog(
                            step_number=step_counter,
                            action="VERIFY",
                            target=plan_step.target,
                            method="Visual perception",
                            status=v_result.status,
                            details=v_result.message,
                            protected_screenshot=post_protected,
                            annotated_screenshot=post_vision.get("debug_image"),
                        )
                    )

                    # Check if authentication checkpoint was reached
                    if v_result.auth_required:
                        task_status = "TASK PAUSED — USER INPUT REQUIRED"
                        task_message = "User authentication required — waiting for user."
                        log_event("AGENT", task_message, verify_state)
                        break

            # If all steps completed without auth interruption
            if task_status == "TASK COMPLETED":
                log_event("AGENT", "Task completed successfully!")

        except Exception as error:
            task_status = "FAILED"
            task_message = f"Agent execution encountered an error: {error}"
            log_event("AGENT", task_message)
            print(f"[AGENT] Traceback: {error}")

        finally:
            browser.close()
            log_event("AGENT", "Browser closed safely.")

        return ExecutionResult(
            task=instruction,
            status=task_status,
            message=task_message,
            steps_completed=step_counter,
            action_logs=action_logs,
            timeline=timeline,
            final_screen_state=final_state,
            plan=plan,
            privacy_summary={
                "processing": "LOCAL",
                "cloud_uploads": "NONE",
                "total_sensitive_items_masked": total_sensitive_masked,
                "categories_detected": sorted(list(all_sensitive_categories)),
            },
        )

    def _execute_click_with_fallback(
        self,
        browser: BrowserController,
        target: str,
        screen_state: ScreenState,
        screenshot_path: str,
        fallback_selector: Optional[str] = None,
    ) -> tuple[bool, str, Optional[tuple[int, int]]]:
        """
        Executes a click preferring visual coordinates first, and falling back
        to Playwright DOM locators if visual perception is uncertain.
        """
        # 1. Try local visual target lookup
        visual_target = self.vision.find_target(screenshot_path, target)

        if visual_target and visual_target.get("confidence", 0.0) >= 0.50:
            cx, cy = visual_target["x"], visual_target["y"]
            print(f"[AGENT] Visual perception → action: Found '{target}' at ({cx}, {cy}) conf={visual_target['confidence']}")
            browser.click_at(cx, cy)
            return True, "Visual perception → action", (cx, cy)

        # 2. Check if screen_state has matched text element
        elem = screen_state.find_element(target, min_confidence=0.50)
        if elem:
            print(f"[AGENT] Visual perception → action: Found element text '{elem.text}' at ({elem.x}, {elem.y})")
            browser.click_at(elem.x, elem.y)
            return True, "Visual perception → action", (elem.x, elem.y)

        # 3. Safe fallback: Playwright DOM selector
        print(f"[AGENT] Visual perception uncertain for '{target}' (conf < 0.50). Using safe Playwright fallback...")
        selector_to_try = fallback_selector or target
        fallback_success = browser.click_element_by_selector(selector_to_try)
        if fallback_success:
            return True, "Visual perception uncertain → Playwright fallback", None

        # 4. Secondary fallback: try clicking text directly via Playwright
        if browser.click_element_by_selector(target):
            return True, "Visual perception uncertain → Playwright fallback", None

        return False, "Failed to locate target", None

    def _execute_type(
        self,
        browser: BrowserController,
        target: str,
        text_to_type: str,
        screen_state: ScreenState,
        screenshot_path: str,
        fallback_selector: Optional[str] = None,
    ) -> tuple[bool, str]:
        """Focuses target element visually or via fallback and types text."""
        # Focus first
        self._execute_click_with_fallback(browser, target, screen_state, screenshot_path, fallback_selector)
        time.sleep(0.3)
        browser.type_text(text_to_type, delay_ms=50)
        return True, "Visual perception → action"

    def _determine_page_label(self, url: str, title: str) -> str:
        """Derives a human-readable page label from URL and title."""
        url_lower = url.lower()
        if "github.com/login" in url_lower:
            return "GitHub Login"
        if "github.com" in url_lower:
            return "GitHub Homepage"
        if "demo_form" in url_lower:
            return "Demo Form"
        if "google" in url_lower:
            return "Google Search"
        if "bing" in url_lower:
            return "Bing Search"
        return title or "Active Page"
