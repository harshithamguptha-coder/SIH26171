"""
agent/screenshot.py
===================
Local Screenshot Component for SIH26171.
Problem Statement: On-device Visual Perception for Lightweight Browser Agents

Key Guarantees:
1. Captures visible browser page using Playwright.
2. Saves strictly to local disk (screenshots/ directory).
3. 100% On-device — Never uploads or transmits screenshots to cloud APIs.
4. Uses timestamped filenames (e.g. search_20260920_114500.png).
5. Returns the local filepath for downstream visual processing (OCR, privacy masking).
"""

import os
import sys
import time
from datetime import datetime
from typing import Any

# Ensure project root is in sys.path so utils can be imported when run directly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PIL import Image
from utils.helpers import get_screenshots_dir

# Safe import for Playwright Page type
try:
    from playwright.sync_api import Page
except ImportError:
    Page = Any


class ScreenshotManager:
    """
    Manages local screenshot capture, timestamped file naming,
    and image loading for visual perception modules.
    """

    def __init__(self, output_dir: str = None):
        """
        Parameters:
            output_dir (str, optional): Directory to store screenshots.
                                        Defaults to project 'screenshots/' folder.
        """
        self.output_dir = output_dir or get_screenshots_dir()
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_filename(self, prefix: str = "screenshot") -> str:
        """
        Generates a timestamped filename.
        Format: <prefix>_YYYYMMDD_HHMMSS.png
        Example: search_results_20260920_114210.png
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_prefix = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in prefix)
        return f"{clean_prefix}_{timestamp}.png"

    def capture_page(self, page: Page, prefix: str = "browser_page") -> str:
        """
        Captures the currently visible browser viewport from Playwright
        and saves it directly to local disk.

        Parameters:
            page (Page): Active Playwright Page instance.
            prefix (str): Label/prefix for the screenshot (e.g. 'search_results').

        Returns:
            str: Absolute path of the locally saved screenshot.
        """
        if not page:
            raise ValueError("Playwright Page instance is required to capture a screenshot.")

        filename = self.generate_filename(prefix=prefix)
        filepath = os.path.join(self.output_dir, filename)

        # Capture the visible page viewport locally
        page.screenshot(path=filepath, full_page=False)

        print(f"[ScreenshotManager] Screenshot captured locally -> {filepath}")
        print("[ScreenshotManager] Privacy check: NO cloud upload performed (100% on-device).")

        return filepath

    def capture(self, page: Page, name_prefix: str = "step") -> str:
        return self.capture_page(page, prefix=name_prefix)

    def load_as_pil(self, filepath: str) -> Image.Image:
        """Loads a locally saved screenshot into a Pillow Image object."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Screenshot file does not exist: {filepath}")
        return Image.open(filepath)


def capture_google_search_demo(
    query: str = "Artificial Intelligence",
    visible: bool = True,
    engine: str = "Bing"
) -> str:
    """
    Demo function that:
    1. Opens Chromium (visible by default).
    2. Navigates to the selected search engine (Bing or Google).
    3. Searches for the query (e.g. 'Artificial Intelligence').
    4. Uses ScreenshotManager to capture and save the results locally.
    5. Returns the local screenshot path.
    """
    from agent.browser import BrowserController

    engine_clean = engine.lower()
    if "bing" in engine_clean:
        target_url = "https://www.bing.com"
        engine_label = "Bing"
    else:
        target_url = "https://www.google.com"
        engine_label = "Google"

    print(f"\n[Demo] Starting {engine_label} search screenshot demo for: '{query}'...")
    screenshot_mgr = ScreenshotManager()

    with BrowserController(headless=not visible, slow_mo=60) as browser:
        # Step 1: Open Search Engine
        browser.navigate(target_url)
        time.sleep(1.5)
        browser.handle_consent_popups()

        # Check if Google served a CAPTCHA rate limit on this IP
        if engine_label == "Google" and browser.is_captcha_page():
            print("[Warning] Google rate-limited this IP with a reCAPTCHA.")
            print("[Notice] Automatically switching to Bing for real search results...")
            browser.navigate("https://www.bing.com")
            time.sleep(1.5)
            engine_label = "Bing"

        # Step 2: Locate search box, type query, and submit
        browser.locate_and_click_search_box()
        browser.type_and_search(query=query)
        browser.wait_for_results(timeout_sec=6)
        time.sleep(2)

        if engine_label == "Google" and browser.is_captcha_page():
            print("[Warning] Google showed a reCAPTCHA after search submission.")
            print("[Notice] Switching to Bing so the judge demo can continue with real results.")
            browser.navigate("https://www.bing.com")
            time.sleep(1.5)
            browser.handle_consent_popups()
            browser.locate_and_click_search_box()
            browser.type_and_search(query=query)
            browser.wait_for_results(timeout_sec=6)
            time.sleep(2)
            engine_label = "Bing"

        # Step 3: Capture screenshot locally
        prefix = f"{engine_label.lower()}_{query.lower().replace(' ', '_')}"
        screenshot_path = screenshot_mgr.capture_page(browser.page, prefix=prefix)

        print(f"[Demo] Screenshot successfully captured and saved: {screenshot_path}")
        return screenshot_path


if __name__ == "__main__":
    print("Testing ScreenshotManager locally with Bing...")
    path = capture_google_search_demo(query="Artificial Intelligence", visible=True, engine="Bing")
    print(f"Done! Result saved at: {path}")
