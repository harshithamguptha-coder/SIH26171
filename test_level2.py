"""
test_level2.py
==============
Automated test suite verifying SIH26171 Level 2 components:
1. TaskPlanner decomposition
2. ScreenState structured representation
3. ActionVerifier landmarks & authentication detection
4. End-to-end AgentController multi-step loop on local demo form
"""

import os
import sys

# Ensure root directory is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from agent.task_planner import TaskPlanner
from agent.state import ScreenState, UIElement
from agent.verifier import ActionVerifier
from agent.controller import AgentController


def test_task_planner():
    print("\n--- Test 1: TaskPlanner Decomposition ---")
    planner = TaskPlanner()

    # Test Primary Demo 1: GitHub Login
    plan_gh = planner.create_plan("Open GitHub and navigate to the login page")
    assert plan_gh.workflow_type == "github_login", f"Expected github_login, got {plan_gh.workflow_type}"
    assert len(plan_gh.step_definitions) >= 3
    assert plan_gh.step_definitions[0].action == "NAVIGATE"
    assert "github.com" in plan_gh.step_definitions[0].target
    assert plan_gh.step_definitions[1].action == "CLICK"
    assert "Sign in" in plan_gh.step_definitions[1].target
    print("[OK] GitHub Login plan decomposed correctly into:")
    for i, s in enumerate(plan_gh.steps, 1):
        print(f"     Step {i}: {s}")

    # Test Secondary Demo 2: Demo Form
    plan_form = planner.create_plan("Open the demo form, enter my name, and submit the form")
    assert plan_form.workflow_type == "demo_form"
    assert any(s.action == "TYPE" for s in plan_form.step_definitions)
    assert any(s.action == "CLICK" and "Submit" in s.target for s in plan_form.step_definitions)
    print("[OK] Demo Form plan decomposed correctly into:")
    for i, s in enumerate(plan_form.steps, 1):
        print(f"     Step {i}: {s}")

    # Test Demo 3: Search Query
    plan_search = planner.create_plan("Open Google and search for Artificial Intelligence")
    assert plan_search.workflow_type == "search_query"
    assert any(s.action == "TYPE" and s.input_value == "Artificial Intelligence" for s in plan_search.step_definitions)
    print("[OK] Search Query plan decomposed correctly.")


def test_screen_state_and_verifier():
    print("\n--- Test 2: ScreenState & ActionVerifier ---")
    verifier = ActionVerifier()

    # Mock a GitHub Login screen state
    gh_login_state = ScreenState(
        url="https://github.com/login",
        title="Sign in to GitHub · GitHub",
        page="GitHub Login",
        elements=[
            UIElement("button", "Sign in", x=640, y=360, width=200, height=40, confidence=0.92),
            UIElement("input", "Username or email address", x=640, y=240, width=300, height=36, confidence=0.88),
            UIElement("input", "Password", x=640, y=300, width=300, height=36, confidence=0.89),
        ],
        text_tokens=[
            {"text": "Sign", "x": 600, "y": 180, "width": 40, "height": 20, "confidence": 95},
            {"text": "in", "x": 645, "y": 180, "width": 20, "height": 20, "confidence": 95},
            {"text": "to", "x": 670, "y": 180, "width": 20, "height": 20, "confidence": 95},
            {"text": "GitHub", "x": 695, "y": 180, "width": 60, "height": 20, "confidence": 95},
        ],
    )

    elem = gh_login_state.find_element("Sign in")
    assert elem is not None
    assert elem.x == 640
    print("[OK] ScreenState element lookup succeeded for 'Sign in'.")

    # Verify that login page triggers AUTH_REQUIRED status
    v_result = verifier.verify("login_page", gh_login_state, page_body_text="Sign in to GitHub Username or email address Password")
    assert v_result.auth_required is True, "Login page must trigger auth_required=True"
    assert v_result.status == "AUTH_REQUIRED"
    assert "User authentication required — waiting for user." in v_result.message
    print(f"[OK] ActionVerifier correctly enforced auth pause: '{v_result.message}'")


def test_controller_local_form_loop():
    print("\n--- Test 3: End-to-End Controller Multi-Step Loop (Local Demo Form) ---")
    controller = AgentController(headless=True, slow_mo=30)
    result = controller.run("Open the demo form, enter my name as Aarav Sharma, and submit the form")

    print(f"Final Task Status: {result.status}")
    print(f"Final Message    : {result.message}")
    print(f"Steps Completed  : {result.steps_completed}")
    print(f"Action Logs Count: {len(result.action_logs)}")

    assert result.status == "TASK COMPLETED", f"Expected TASK COMPLETED, got {result.status}"
    assert result.steps_completed >= 4, f"Expected at least 4 steps, got {result.steps_completed}"
    assert any(log.action == "TYPE" for log in result.action_logs)
    assert any(log.action == "VERIFY" and log.status == "SUCCESS" for log in result.action_logs)
def test_controller_github_login():
    print("\n--- Test 4: Primary Demo 1 (GitHub Login Navigation & Auth Pause) ---")
    controller = AgentController(headless=True, slow_mo=30)
    result = controller.run("Open GitHub and navigate to the login page")
    print(f"Final Task Status: {result.status}")
    print(f"Final Message    : {result.message}")
    assert result.status in ["TASK PAUSED — USER INPUT REQUIRED", "TASK COMPLETED"]
    assert "User authentication required" in result.message or "Login page" in result.message
    print("[OK] GitHub Login workflow passed with safety authentication pause!")


if __name__ == "__main__":
    test_task_planner()
    test_screen_state_and_verifier()
    test_controller_local_form_loop()
    test_controller_github_login()
    print("\n========================================================")
    print("  ALL LEVEL 2 AUTOMATED TESTS PASSED SUCCESSFULLY!       ")
    print("========================================================\n")
