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

import json
import re
import os
from core.browser import BrowserManager
from core.quiz_actor import QuizActor


def main() -> None:
    browser_manager = BrowserManager()

    try:
        # ── 1. Connect to the existing browser session ────────────────────
        browser_manager.connect()

        # ── 2. Locate the quiz tab ────────────────────────────────────────
        page = browser_manager.get_quiz_page()

        # ── 3. Dynamic Context Routing ──────────────────────────────────
        print("[main] Detecting test context from page title...")
        
        try:
            # Search inside itemprop="name", .breadcrumb, or h1 tags to ensure we don't catch sidebar links
            title_locator = page.locator("span[itemprop='name'], .breadcrumb, h1").locator("text=/PRACTICE TEST \\d+ - (LISTENING|READING)/i").first
            # Wait briefly for the element to be present
            title_text = title_locator.inner_text(timeout=5000).strip()
            print(f"[main] Found Title: \"{title_text}\"")
        except Exception:
            print("[main] ERROR: Could not find the test title on the page.")
            return

        # Regex to extract Test Number and Skill from the captured text
        match = re.search(r"PRACTICE TEST\s+(\d+)\s*-\s*(\w+)", title_text, re.IGNORECASE)
        
        if not match:
            print(f"[main] ERROR: Could not parse test number and skill from \"{title_text}\".")
            return

        test_num_raw = match.group(1)
        skill_raw = match.group(2)

        # Format variables
        test_num = test_num_raw.zfill(2)  # 6 -> 06
        skill = skill_raw.lower()         # LISTENING -> listening
        
        db_path = os.path.join("data", "tests", f"test_{test_num}", f"{skill}.json")
        print(f"[main] Derived Path: {db_path}")

        # Load test data
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                full_data = json.load(f)
                test_key = f"TEST_{test_num}"
                test_data = full_data.get(test_key, [])
            print(f"[main] SUCCESS: Loaded {len(test_data)} questions from {db_path}.")
        except FileNotFoundError:
            print(f"[main] ERROR: Database file not found: {db_path}")
            return
        except Exception as e:
            print(f"[main] ERROR loading JSON: {e}")
            return

        # ── 4. Initialise the actor ───────────────────────────────────────
        actor = QuizActor(page, test_data, source_file=db_path)

        # ── 4. Loop through all quiz pages ────────────────────────────────
        print("[main] Starting multi-page quiz automation…")
        page_count = 1
        
        while True:
            print(f"\n[main] Processing Page {page_count}…")
            
            # fill all questions on the current page intelligently
            actor.fill_all_questions_intelligently()

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
