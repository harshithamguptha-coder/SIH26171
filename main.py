"""
main.py
=======
Main Entry Point for SIH26171 — First Working Component Demo.

This script demonstrates the first core milestone of our Hackathon project:
1. Launches Chromium browser locally using Playwright (in visible/headed mode).
2. Opens https://www.google.com.
3. Automatically locates and clicks the Google search box.
4. Types "Artificial Intelligence" with human-observable pacing.
5. Presses Enter to submit the search.
6. Waits for Google search results to appear.
7. Captures a screenshot and saves it locally into the 'screenshots/' folder.
8. Ensures 100% on-device execution — NO cloud APIs, NO data leaks.

Run with:
    python main.py
"""

import sys
import os

# Ensure the root project directory is in Python's module search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.actions import run_google_search_demo


def main():
    """
    Main function to run the visible browser demo.
    """
    print("\n========================================================")
    print("  SIH 2026 - Problem Statement: SIH26171")
    print("  On-device Visual Perception for Lightweight Browser Agents")
    print("  Component #1: Playwright Local Browser Controller")
    print("========================================================\n")

    # Target query as specified in problem statement demo requirements
    SEARCH_QUERY = "Artificial Intelligence"

    try:
        # Run the demo with visible browser window (headless=False)
        # so evaluators and judges can see every action happening live!
        screenshot_path = run_google_search_demo(
            query=SEARCH_QUERY,
            visible=True  # Keeps Chromium visible on screen
        )

        print("[SUCCESS] Demo completed without errors.")
        print(f"[SUCCESS] Check your local screenshot: {screenshot_path}\n")

    except KeyboardInterrupt:
        print("\n[ABORTED] Demo interrupted by user (Ctrl+C).")
        sys.exit(0)

    except Exception as err:
        print(f"\n[FAILURE] Demo encountered an error:\n{err}")
        print("\nTroubleshooting tips:")
        print("1. Ensure Playwright is installed: pip install playwright")
        print("2. Ensure browser binaries exist: playwright install chromium")
        print("3. Ensure you have an active internet connection to load Google.")
        sys.exit(1)


if __name__ == "__main__":
    main()

