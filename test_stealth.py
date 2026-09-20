import os
import sys
import time
from playwright.sync_api import sync_playwright

def test_search():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel='chrome',
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
            ]
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Test Google with stealth
        print("Testing Google with stealth...")
        page.goto('https://www.google.com')
        time.sleep(1)

        # Check for consent
        for btn_text in ["Accept all", "I agree", "Reject all", "Accept"]:
            try:
                btn = page.get_by_role("button", name=btn_text)
                if btn.is_visible(timeout=500):
                    btn.click()
                    break
            except Exception:
                pass

        page.locator('textarea[name="q"], input[name="q"]').first.fill('Artificial Intelligence')
        page.keyboard.press('Enter')
        time.sleep(3)
        page.screenshot(path='screenshots/stealth_google_search.png')
        print("Google screenshot saved: screenshots/stealth_google_search.png")

        # Test Bing as rock-solid backup
        print("Testing Bing...")
        page.goto('https://www.bing.com')
        time.sleep(1)
        page.locator('textarea[name="q"], input[name="q"]').first.fill('Artificial Intelligence')
        page.keyboard.press('Enter')
        time.sleep(3)
        page.screenshot(path='screenshots/stealth_bing_search.png')
        print("Bing screenshot saved: screenshots/stealth_bing_search.png")

        browser.close()

if __name__ == '__main__':
    test_search()

