"""
agent/browser.py
================
Playwright Browser Controller for SIH26171.
Provides beginner-friendly, modular methods to:
1. Launch a visible or headless Chromium browser instance.
2. Navigate to web pages (e.g. https://www.google.com).
3. Handle cookie consent banners if they appear.
4. Locate input elements (like the Google search box) and click them.
5. Type text with visible typing speed so judges can watch in real time.
6. Submit searches and wait for result elements to load.
7. Capture and save screenshots locally.
8. Safely close browser resources.

Zero cloud APIs are involved — 100% local execution.
"""

import os
import sys
import time
from typing import Any

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.helpers import get_screenshots_dir

# Safe import of Playwright to provide clear error message if not yet installed
try:
    from playwright.sync_api import sync_playwright, Browser, Page, Playwright
except ImportError:
    sync_playwright = None
    Browser = Any
    Page = Any
    Playwright = Any


class BrowserController:
    """
    Controls Chromium browser actions using Python Playwright.
    Designed for interactive demos with visible UI and human-like typing speed.
    """

    def __init__(self, headless: bool = False, slow_mo: int = 50, viewport: dict = None):
        """
        Parameters:
            headless (bool): If False (default), the browser window is visible to the judges.
                             If True, it runs in the background.
            slow_mo (int): Slows down Playwright actions by X milliseconds
                           so human observers can follow each click and keystroke.
            viewport (dict): Window size (width and height).
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.viewport = viewport or {"width": 1280, "height": 800}

        # Internal state tracking
        self.playwright: Playwright = None
        self.browser: Browser = None
        self.page: Page = None

    def start(self):
        """
        Launches Playwright Chromium.
        First tries installed system Chrome/Edge (instant on Windows),
        then falls back to Playwright's bundled Chromium.
        """
        if sync_playwright is None:
            raise ImportError(
                "Playwright is not installed in this Python environment.\n"
                "Please run: pip install playwright && playwright install chromium"
            )

        if self.browser is not None:
            return  # Already started

        # On Windows, Playwright requires WindowsProactorEventLoopPolicy to spawn subprocesses.
        # Frameworks like Streamlit or Tornado override this to SelectorEventLoop, which causes NotImplementedError.
        if sys.platform == "win32":
            import asyncio
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            except Exception:
                pass

        print(f"[Browser] Initializing Playwright (visible={not self.headless}, slow_mo={self.slow_mo}ms)...")
        self.playwright = sync_playwright().start()

        # Stealth flags to avoid bot detection and reCAPTCHAs
        stealth_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars",
            "--disable-dev-shm-usage",
        ]

        # Priority list for browser engines:
        launch_candidates = [
            ("System Google Chrome", {"channel": "chrome", "headless": self.headless, "slow_mo": self.slow_mo, "args": stealth_args}),
            ("System Microsoft Edge", {"channel": "msedge", "headless": self.headless, "slow_mo": self.slow_mo, "args": stealth_args}),
            ("Bundled Chromium", {"headless": self.headless, "slow_mo": self.slow_mo, "args": stealth_args}),
        ]

        last_error = None
        for name, options in launch_candidates:
            try:
                self.browser = self.playwright.chromium.launch(**options)
                print(f"[Browser] Successfully launched via {name}.")
                break
            except Exception as err:
                last_error = err

        if self.browser is None:
            raise RuntimeError(
                f"Failed to launch any Chromium browser. Error: {last_error}\n"
                "Tip: Run 'playwright install chromium' or ensure Chrome/Edge is installed."
            )

        # Standard desktop browser user agent
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
        self.context = self.browser.new_context(
            viewport=self.viewport,
            user_agent=user_agent
        )
        self.page = self.context.new_page()

        # Remove navigator.webdriver so websites do not flag the browser as an automated bot
        try:
            self.page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception:
            pass

    def is_captcha_page(self) -> bool:
        """Checks if current page is blocked by a robot/reCAPTCHA verification interstitial."""
        if not self.page:
            return False
        try:
            url = self.page.url.lower()
            if "sorry/index" in url or "recaptcha" in url:
                return True
            title = self.page.title().lower()
            if "unusual traffic" in title or "robot" in title:
                return True
            body = self.page.inner_text("body").lower()
            return "unusual traffic from your computer network" in body or "i'm not a robot" in body
        except Exception:
            return False

    def navigate(self, url: str, timeout_ms: int = 30000):
        """
        Navigates the browser to the specified web address.

        Parameters:
            url (str): Target web address (e.g. 'https://www.google.com')
            timeout_ms (int): Maximum wait time in milliseconds.
        """
        if not self.page:
            raise RuntimeError("Browser is not running. Please call .start() first.")

        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        print(f"[Browser] Navigating to: {url}")
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            print("[Browser] Page loaded successfully.")
        except Exception as e:
            raise RuntimeError(f"Failed to navigate to {url}: {e}")

    def handle_consent_popups(self):
        """
        Dismisses Google cookie or privacy consent dialogs if they appear.
        Common in European and certain regional network configurations.
        """
        if not self.page:
            return

        consent_buttons = ["Accept all", "I agree", "Reject all", "Accept", "Agree"]
        for text in consent_buttons:
            try:
                btn = self.page.get_by_role("button", name=text)
                if btn.is_visible(timeout=800):
                    print(f"[Browser] Dismissing cookie consent dialog: '{text}'...")
                    btn.click()
                    time.sleep(1)
                    break
            except Exception:
                continue

    def locate_and_click_search_box(self) -> bool:
        """
        Locates the Google search input area (textarea or input with name='q')
        and performs a visible mouse click to focus it.

        Returns:
            bool: True if located and clicked successfully.
        """
        if not self.page:
            raise RuntimeError("Browser is not running.")

        print("[Browser] Locating the Google search box...")

        # Selectors covering modern and classic Google search inputs:
        # Modern Google uses textarea[name="q"], older layouts use input[name="q"]
        selectors = [
            'textarea[name="q"]',
            'input[name="q"]',
            'input[title="Search"]',
            'input[aria-label="Search"]',
            'textarea[aria-label="Search"]',
            'input[type="search"]',
        ]

        for sel in selectors:
            try:
                locator = self.page.locator(sel).first
                if locator.is_visible(timeout=1500):
                    print(f"[Browser] Found search box matching selector: '{sel}'")
                    locator.click()
                    print("[Browser] Clicked search box (focused).")
                    return True
            except Exception:
                continue

        # If selector lookup failed, try clicking by visual center coordinates
        print("[Browser] Standard selector not found, attempting coordinate-based click at center...")
        self.page.mouse.click(640, 360)
        return False

    def type_and_search(self, query: str, delay_ms: int = 70):
        """
        Types the search query character-by-character with a slight delay
        so viewers can observe typing, then presses Enter.

        Parameters:
            query (str): The search text (e.g. 'Artificial Intelligence')
            delay_ms (int): Keystroke delay in milliseconds.
        """
        if not self.page:
            raise RuntimeError("Browser is not running.")

        print(f"[Browser] Typing query: '{query}'...")
        self.page.keyboard.type(query, delay=delay_ms)
        time.sleep(0.5)

        print("[Browser] Pressing Enter to submit search...")
        self.page.keyboard.press("Enter")

    def wait_for_results(self, timeout_sec: int = 10):
        """
        Waits for the search results page to populate.
        """
        if not self.page:
            raise RuntimeError("Browser is not running.")

        print("[Browser] Waiting for search results to load...")
        try:
            # Common Google search results container elements
            self.page.wait_for_selector("#search, #rso, div[id='center_col']", timeout=timeout_sec * 1000)
            print("[Browser] Search results detected on page!")
        except Exception:
            # Fallback: wait for general DOM stability
            print("[Browser] Waiting for DOM network settle...")
            time.sleep(3)

    def take_screenshot(self, filename: str = None) -> str:
        """
        Captures the browser screenshot and saves it locally in the screenshots folder.

        Parameters:
            filename (str, optional): Custom filename (e.g. 'google_ai_search.png').

        Returns:
            str: Absolute path of the saved screenshot.
        """
        if not self.page:
            raise RuntimeError("Browser is not running.")

        screenshots_dir = get_screenshots_dir()
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"google_search_{timestamp}.png"

        filepath = os.path.join(screenshots_dir, filename)
        self.page.screenshot(path=filepath, full_page=False)
        print(f"[Browser] Screenshot saved locally -> {filepath}")
        return filepath

    def click_at(self, x: int, y: int):
        """Clicks at specific screen pixel coordinates."""
        if not self.page:
            raise RuntimeError("Browser is not running.")
        self.page.mouse.click(x, y)

    def close(self):
        """Safely closes browser pages and stops Playwright."""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            print(f"[Browser] Warning during close: {e}")
        finally:
            self.page = None
            self.browser = None
            self.playwright = None
            print("[Browser] Browser shut down safely.")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
