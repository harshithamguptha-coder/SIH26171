"""
agent/actions.py
================
Action coordination and demo execution for SIH26171.

Implements:
1. `run_google_search_demo()`:
   Exact first working component demo:
   - Launches visible Chromium
   - Opens https://www.google.com
   - Locates Google search box
   - Clicks it
   - Types query (e.g. "Artificial Intelligence")
   - Presses Enter
   - Waits for search results
   - Saves screenshot locally in screenshots/ folder
2. `BrowserAgent`:
   Modular coordinator for full perception -> privacy -> action pipelines.

Zero cloud APIs used — 100% on-device.
"""

import os
import time
import re
from .browser import BrowserController
from .screenshot import ScreenshotManager
from .ocr import VisualPerception
from .privacy import PrivacyGuard
from utils.helpers import get_screenshots_dir, draw_bounding_boxes


def run_google_search_demo(query: str = "Artificial Intelligence", visible: bool = True) -> str:
    """
    Executes the first working component demo:
    1. Launch Chromium (visible to judges).
    2. Open https://www.google.com/
    3. Locate Google search box.
    4. Click it.
    5. Type query ('Artificial Intelligence').
    6. Press Enter.
    7. Wait for search results page.
    8. Take a screenshot and save it locally in screenshots/ folder.

    Parameters:
        query (str): The search phrase to type. Default is 'Artificial Intelligence'.
        visible (bool): If True, leaves browser window visible on screen.

    Returns:
        str: Path to the saved search results screenshot.
    """
    print("\n========================================================")
    print("  SIH26171: First Working Component Demo Starting")
    print("========================================================")
    print(f"Target URL : https://www.google.com")
    print(f"Search Term: '{query}'")
    print(f"Mode       : {'Visible (Judges Demo)' if visible else 'Headless'}")
    print("--------------------------------------------------------\n")

    # Initialize the browser controller with visible window and slow_mo for smooth observation
    browser = BrowserController(headless=not visible, slow_mo=60)

    try:
        # Step 1: Launch Chromium
        print("[Step 1/6] Launching Chromium browser locally...")
        browser.start()

        # Step 2: Open Google
        print("[Step 2/6] Navigating to https://www.google.com...")
        browser.navigate("https://www.google.com")
        time.sleep(1.5)  # Allow page layout to settle

        # Handle any regional cookie consent popups
        browser.handle_consent_popups()

        # Step 3: Locate the search box and click it
        print("[Step 3/6] Locating and clicking the Google search box...")
        clicked = browser.locate_and_click_search_box()
        if not clicked:
            print("[Step 3/6] Warning: Fallback click used. Continuing...")
        time.sleep(0.5)

        # Step 4 & 5: Type query and press Enter
        print(f"[Step 4/6] Typing '{query}' with visible keystroke pacing...")
        print("[Step 5/6] Submitting search (pressing Enter)...")
        browser.type_and_search(query=query, delay_ms=80)

        # Step 6: Wait for search results and take screenshot
        print("[Step 6/6] Waiting for search results to load...")
        browser.wait_for_results(timeout_sec=8)
        time.sleep(2)  # Extra moment for visual confirmation

        # Save screenshot locally
        screenshot_filename = f"google_search_{query.lower().replace(' ', '_')}.png"
        saved_path = browser.take_screenshot(filename=screenshot_filename)

        print("\n========================================================")
        print("  Demo Completed Successfully!")
        print(f"  Screenshot saved locally at:\n  {saved_path}")
        print("========================================================\n")

        # Keep browser open for 3 seconds so judges can see the final state
        if visible:
            print("[Notice] Keeping browser open for 3 seconds for visual review...")
            time.sleep(3)

        return saved_path

    except Exception as error:
        print(f"\n[ERROR] An error occurred during demo execution: {error}")
        raise error

    finally:
        # Always clean up browser resources
        browser.close()


class BrowserAgent:
    """
    Modular coordinator integrating perception, privacy, and browser action.
    Used by the Streamlit application for end-to-end demonstration.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.screenshot_mgr = ScreenshotManager()
        self.perception = VisualPerception()
        self.privacy_guard = PrivacyGuard(redact_mode="blackout")

    def parse_command(self, command: str) -> dict:
        """Parses simple natural language commands into target site and query."""
        command = command.strip()
        result = {
            "action": "search",
            "url": "https://www.google.com",
            "query": "Smart India Hackathon 2026",
            "raw_command": command,
        }

        search_match = re.search(
            r"search(?:\s+for)?\s+[\"']?([^\"']+?)[\"']?(?:\s+on\s+([a-zA-Z0-9.-]+))?$",
            command,
            re.IGNORECASE,
        )
        if search_match:
            query = search_match.group(1).strip()
            site = search_match.group(2)
            result["query"] = query
            if site:
                site_lower = site.lower()
                if "bing" in site_lower:
                    result["url"] = "https://www.bing.com"
                elif "duckduckgo" in site_lower:
                    result["url"] = "https://duckduckgo.com"
                else:
                    result["url"] = f"https://www.{site_lower}.com"
            return result

        if command:
            result["query"] = command

        return result

    def execute(self, user_command: str, progress_callback=None) -> dict:
        """Executes full on-device visual agent pipeline."""
        logs = []

        def log(msg: str):
            print(f"[BrowserAgent] {msg}")
            logs.append(msg)
            if progress_callback:
                progress_callback(msg)

        log(f"Received user command: '{user_command}'")
        parsed = self.parse_command(user_command)

        browser = BrowserController(headless=self.headless, slow_mo=30)
        results = {
            "command": user_command,
            "parsed": parsed,
            "logs": logs,
            "raw_screenshot": None,
            "annotated_screenshot": None,
            "masked_screenshot": None,
            "final_screenshot": None,
            "detected_elements": [],
            "redacted_count": 0,
        }

        try:
            log("Step 1: Launching local Chromium browser via Playwright...")
            browser.start()

            log(f"Step 2: Navigating to {parsed['url']}...")
            browser.navigate(parsed["url"])
            time.sleep(2)
            browser.handle_consent_popups()

            # Step 2: Capture raw screenshot locally
            log("Step 2: Capturing raw browser screenshot locally...")
            raw_shot = self.screenshot_mgr.capture(browser.page, name_prefix="01_raw")
            results["raw_screenshot"] = raw_shot

            # Step 3: On-device visual perception (OCR + contour element detection)
            log("Step 3: Running on-device visual perception...")
            elements = self.perception.extract_elements(raw_shot)
            results["detected_elements"] = elements
            log(f"Detected {len(elements)} visual element(s) locally.")

            annotated_shot = draw_bounding_boxes(raw_shot, elements)
            results["annotated_screenshot"] = annotated_shot

            # Step 4: On-device privacy layer & masking
            log("Step 4: Running on-device privacy guard...")
            sensitive = self.privacy_guard.find_sensitive_elements(elements)
            masked_shot, count = self.privacy_guard.mask_screenshot(raw_shot, sensitive)
            results["masked_screenshot"] = masked_shot
            results["redacted_count"] = count

            # Step 5: Perform action
            log(f"Step 5: Locating search box and typing '{parsed['query']}'...")
            browser.locate_and_click_search_box()
            browser.type_and_search(parsed["query"])
            browser.wait_for_results()
            time.sleep(2)

            # Step 6: Capture final state
            log("Step 6: Capturing final browser screenshot after action execution...")
            final_shot = self.screenshot_mgr.capture(browser.page, name_prefix="02_final")
            results["final_screenshot"] = final_shot
            log("Pipeline execution finished successfully!")

        finally:
            browser.close()

        return results
