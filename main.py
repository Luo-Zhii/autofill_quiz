"""
main.py

Entry point for the quiz automation script.

Usage
-----
    python main.py

Prerequisites
-------------
1. Brave / Chrome must be running with --remote-debugging-port=9222.
2. The quiz tab (URL containing 'elearning.thanglong') must already be open.
3. Install dependencies:  pip install playwright && playwright install chromium
"""

from core.browser import BrowserManager
from core.quiz_actor import QuizActor


def main() -> None:
    browser_manager = BrowserManager()

    try:
        # ── 1. Connect to the existing browser session ────────────────────
        browser_manager.connect()

        # ── 2. Locate the quiz tab ────────────────────────────────────────
        page = browser_manager.get_quiz_page()

        # ── 3. Initialise the actor ───────────────────────────────────────
        actor = QuizActor(page)

        # ── 4. Loop through all quiz pages ────────────────────────────────
        print("[main] Starting multi-page quiz automation…")
        page_count = 1
        
        while True:
            print(f"\n[main] Processing Page {page_count}…")
            
            # fill all questions on the current page
            actor.fill_all_questions_randomly()

            # Check if there is a next page
            if actor.has_next_page():
                print(f"[main] Page {page_count} finished. Navigating to Page {page_count + 1}…")
                actor.click_next_page()
                page_count += 1
            else:
                print(f"[main] Page {page_count} was the last page.")
                break

        print("\n[main] SUCCESS: Reached the end of the quiz!")
        print("[main] Done — browser left open as requested.")

    except Exception as exc:
        print(f"[main] ERROR: {exc}")
        raise

    finally:
        # Stop Playwright engine; the external browser is NOT closed.
        browser_manager.disconnect_playwright()


if __name__ == "__main__":
    main()
