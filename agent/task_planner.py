"""
agent/task_planner.py
=====================
Lightweight deterministic task planner for SIH26171 Level 2.
Decomposes natural language instructions into ordered sub-goals and actions.
Zero cloud API calls — 100% on-device planning logic.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, List, Optional

from utils.helpers import get_project_root


@dataclass
class PlanStep:
    """Detailed definition of a single step in a plan."""
    step_number: int
    action: str  # NAVIGATE, CLICK, TYPE, PRESS_KEY, SCROLL, WAIT, VERIFY, STOP
    target: str
    description: str
    expected_verification: Optional[str] = None
    input_value: Optional[str] = None
    fallback_selector: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_number": self.step_number,
            "action": self.action,
            "target": self.target,
            "description": self.description,
            "expected_verification": self.expected_verification,
            "input_value": self.input_value,
            "fallback_selector": self.fallback_selector,
        }


@dataclass
class TaskPlan:
    """Complete decomposed plan representation."""
    task: str
    goal: str
    workflow_type: str
    steps: List[str]  # Human-readable step summaries
    step_definitions: List[PlanStep] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "goal": self.goal,
            "workflow_type": self.workflow_type,
            "steps": self.steps,
            "step_definitions": [s.to_dict() for s in self.step_definitions],
        }


class TaskPlanner:
    """
    Translates user natural language instructions into structured multi-step plans.
    Specializes in controlled hackathon demonstration workflows with safety stops.
    """

    def __init__(self):
        self.project_root = get_project_root()

    def get_demo_form_url(self) -> str:
        """Returns the local file URI for the bundled demo form."""
        form_path = os.path.join(self.project_root, "demo_pages", "demo_form.html")
        return f"file:///{form_path.replace(os.sep, '/')}"

    def create_plan(self, instruction: str) -> TaskPlan:
        """
        Decomposes an instruction into an ordered TaskPlan.
        """
        text = instruction.strip().lower()

        # Workflow 1: GitHub Login (Primary SIH Demo)
        if "github" in text and ("login" in text or "sign in" in text or "signin" in text):
            return self._plan_github_login(instruction)

        # Workflow 2: Demo Form Fill & Submit (Secondary Demo)
        if "demo form" in text or "mock form" in text or ("form" in text and ("submit" in text or "enter my name" in text or "name" in text)):
            return self._plan_demo_form(instruction)

        # Workflow 3: Search Engine Query (Demo 3)
        if "search" in text or "google" in text or "bing" in text:
            return self._plan_search_query(instruction)

        # Fallback / General Plan
        return self._plan_generic(instruction)

    def _plan_github_login(self, instruction: str) -> TaskPlan:
        steps_text = [
            "Open GitHub",
            "Find Sign in",
            "Click Sign in",
            "Verify login page",
        ]
        step_defs = [
            PlanStep(
                step_number=1,
                action="NAVIGATE",
                target="https://github.com",
                description="Open GitHub homepage",
                expected_verification="github_homepage",
            ),
            PlanStep(
                step_number=2,
                action="CLICK",
                target="Sign in",
                description="Find and click 'Sign in' navigation element",
                expected_verification=None,
                fallback_selector="a[href*='/login'], a:has-text('Sign in')",
            ),
            PlanStep(
                step_number=3,
                action="VERIFY",
                target="GitHub Login Page",
                description="Verify login page has been reached and pause for user authentication",
                expected_verification="login_page",
            ),
        ]
        return TaskPlan(
            task=instruction,
            goal="Navigate to GitHub Login page and pause for user authentication",
            workflow_type="github_login",
            steps=steps_text,
            step_definitions=step_defs,
        )

    def _plan_demo_form(self, instruction: str) -> TaskPlan:
        # Extract dummy name if user provided one, otherwise default to "Aarav Sharma"
        name = "Aarav Sharma"
        name_match = re.search(r"enter (?:my )?name(?: as)? ['\"]?([a-zA-Z\s]+?)['\"]?(?: and|,|$)", instruction, re.IGNORECASE)
        if name_match:
            extracted = name_match.group(1).strip()
            if extracted and len(extracted) > 1:
                name = extracted

        form_url = self.get_demo_form_url()
        steps_text = [
            "Open demo form",
            "Find name field",
            "Click name field",
            f"Type name '{name}'",
            "Find Submit button",
            "Click Submit",
            "Verify success message",
        ]
        step_defs = [
            PlanStep(
                step_number=1,
                action="NAVIGATE",
                target=form_url,
                description="Open local demo form",
                expected_verification="form_loaded",
            ),
            PlanStep(
                step_number=2,
                action="CLICK",
                target="name",
                description="Locate and focus 'Full Name' input field",
                expected_verification=None,
                fallback_selector="input#full_name, input[name='name'], input[type='text']",
            ),
            PlanStep(
                step_number=3,
                action="TYPE",
                target="name",
                input_value=name,
                description=f"Type dummy name '{name}' into name field",
                expected_verification=None,
            ),
            PlanStep(
                step_number=4,
                action="CLICK",
                target="Submit",
                description="Locate and click 'Submit' button",
                expected_verification=None,
                fallback_selector="button[type='submit'], #submit-btn, button:has-text('Submit')",
            ),
            PlanStep(
                step_number=5,
                action="VERIFY",
                target="Submission Confirmation",
                description="Verify form submission success banner is visible",
                expected_verification="form_submitted",
            ),
        ]
        return TaskPlan(
            task=instruction,
            goal="Fill demo form with dummy credentials and submit",
            workflow_type="demo_form",
            steps=steps_text,
            step_definitions=step_defs,
        )

    def _plan_search_query(self, instruction: str) -> TaskPlan:
        query = "Artificial Intelligence"
        query_match = re.search(
            r"search(?:\s+for)?\s+[\"']?([^\"']+?)[\"']?(?:\s+on\s+([a-zA-Z0-9.-]+))?$",
            instruction,
            re.IGNORECASE,
        )
        engine_url = "https://www.google.com"
        engine_name = "Google"

        if query_match:
            extracted_query = query_match.group(1).strip()
            if extracted_query:
                query = extracted_query
            site = query_match.group(2)
            if site and "bing" in site.lower():
                engine_url = "https://www.bing.com"
                engine_name = "Bing"
        elif "bing" in instruction.lower():
            engine_url = "https://www.bing.com"
            engine_name = "Bing"

        steps_text = [
            f"Open {engine_name}",
            "Find search box",
            "Click search box",
            f"Type query '{query}'",
            "Press Enter",
            "Verify search results",
        ]
        step_defs = [
            PlanStep(
                step_number=1,
                action="NAVIGATE",
                target=engine_url,
                description=f"Open {engine_name} homepage",
                expected_verification="search_homepage",
            ),
            PlanStep(
                step_number=2,
                action="CLICK",
                target="search_box",
                description=f"Locate and focus {engine_name} search box",
                expected_verification=None,
                fallback_selector="textarea[name='q'], input[name='q']",
            ),
            PlanStep(
                step_number=3,
                action="TYPE",
                target="search_box",
                input_value=query,
                description=f"Type '{query}' with observable keystrokes",
                expected_verification=None,
            ),
            PlanStep(
                step_number=4,
                action="PRESS_KEY",
                target="Enter",
                description="Press Enter to submit search",
                expected_verification=None,
            ),
            PlanStep(
                step_number=5,
                action="VERIFY",
                target="Search Results",
                description="Verify search results loaded on page",
                expected_verification="search_results",
            ),
        ]
        return TaskPlan(
            task=instruction,
            goal=f"Search for '{query}' on {engine_name}",
            workflow_type="search_query",
            steps=steps_text,
            step_definitions=step_defs,
        )

    def _plan_generic(self, instruction: str) -> TaskPlan:
        # Check if URL in instruction
        url_match = re.search(r"https?://[^\s]+", instruction)
        target_url = url_match.group(0) if url_match else "https://www.google.com"

        steps_text = [
            f"Navigate to {target_url}",
            "Observe screen",
            "Analyze page content",
            "Complete task",
        ]
        step_defs = [
            PlanStep(
                step_number=1,
                action="NAVIGATE",
                target=target_url,
                description=f"Navigate to {target_url}",
                expected_verification="page_loaded",
            ),
            PlanStep(
                step_number=2,
                action="VERIFY",
                target="Page Content",
                description="Observe page content and complete task",
                expected_verification="page_loaded",
            ),
        ]
        return TaskPlan(
            task=instruction,
            goal=f"Navigate to {target_url} and inspect screen",
            workflow_type="generic",
            steps=steps_text,
            step_definitions=step_defs,
        )

