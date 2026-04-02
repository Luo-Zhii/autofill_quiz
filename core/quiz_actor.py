"""
core/quiz_actor.py

Provides the QuizActor class, which encapsulates all DOM interactions
needed to answer quiz questions and navigate between pages.
"""

import random
import time
from playwright.sync_api import Page

# Mapping from human-readable answer letter to the radio button's value attribute.
ANSWER_MAP: dict[str, str] = {
    "A": "0",
    "B": "1",
    "C": "2",
    "D": "3",
}

# CSS selector for the "Next page" submit button.
NEXT_BUTTON_SELECTOR = "#mod_quiz-next-nav"


class QuizActor:
    """
    Handles all DOM interactions on the quiz page:
      - Selecting radio-button answers by question index and letter.
      - Filling all questions on the page randomly.
      - Clicking the 'Next page' navigation button.
    """

    def __init__(self, page: Page) -> None:
        """
        Parameters
        ----------
        page : Page
            The Playwright Page object pointing to the active quiz tab.
        """
        self._page = page

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_all_question_groups(self) -> list[str]:
        """
        Query all radio buttons on the current page and extract unique group names.

        Returns
        -------
        list[str]
            A list of unique 'name' attributes (preserving DOM order).
        """
        all_radios = self._page.query_selector_all(
            "input[type='radio'].form-check-input"
        )
        seen: set[str] = set()
        group_names: list[str] = []
        for radio in all_radios:
            name = radio.get_attribute("name")
            if name and name not in seen:
                seen.add(name)
                group_names.append(name)
        return group_names

    def fill_all_questions_randomly(self) -> None:
        """
        Identify all question groups on the page, sort them visually (left column first, 
        top to bottom), and select a random answer for each.

        Sorting logic:
          1. Primarily by x-coordinate (using round(x / 50) as a column bucket).
          2. Secondarily by y-coordinate.
        """
        group_names = self.get_all_question_groups()
        if not group_names:
            print("[QuizActor] No question groups found.")
            return

        # 1. Collect visual coordinates for each group
        visual_groups = []
        for name in group_names:
            # We take the first radio button in each group to determine its position.
            first_radio_selector = f"input[name='{name}']"
            element = self._page.query_selector(first_radio_selector)
            if element:
                box = element.bounding_box()
                if box:
                    visual_groups.append({
                        "name": name,
                        "x": box["x"],
                        "y": box["y"]
                    })
                else:
                    print(f"[QuizActor] WARNING: Could not get bounding_box for group '{name}'.")
            else:
                print(f"[QuizActor] WARNING: Could not find radio for group '{name}'.")

        # 2. Sort visually: Left-to-right columns (bucketed), then top-to-bottom.
        # We round X / 50 to ensure that items in slightly different X positions 
        # (due to padding/tables) are treated as being in the same column.
        sorted_groups = sorted(
            visual_groups, 
            key=lambda g: (round(g["x"] / 50), g["y"])
        )

        print(f"[QuizActor] Visually sorted {len(sorted_groups)} questions.")

        # 3. Iterate and fill
        for group in sorted_groups:
            name = group["name"]
            # Pick a random answer letter (A, B, or C) as requested
            letter = random.choice(["A", "B", "C"])
            value = ANSWER_MAP[letter]

            selector = (
                f"input[type='radio'].form-check-input"
                f"[name='{name}'][value='{value}']"
            )
            radio_element = self._page.query_selector(selector)
            
            if radio_element:
                radio_element.click()
                print(
                    f"[QuizActor] Visually processed '{name}' at (x={group['x']:.1f}, "
                    f"y={group['y']:.1f}) -> Selected '{letter}' (value={value})."
                )
                # Random human-like delay 0.5 to 1.0s
                time.sleep(random.uniform(0.5, 1.0))
            else:
                print(f"[QuizActor] WARNING: Could not find radio for group '{name}' value='{value}'.")

    def select_answer(self, question_index: int, answer_letter: str) -> None:
        """
        Select a radio-button answer for a given question.

        The quiz groups radio buttons by a shared ``name`` attribute.
        We collect all distinct radio-group names on the page (preserving
        DOM order), pick the one at ``question_index``, then click the
        radio whose value matches ``answer_letter``.

        Parameters
        ----------
        question_index : int
            Zero-based index of the question on the current page
            (0 = first question, 1 = second question, …).
        answer_letter : str
            One of 'A', 'B', 'C', or 'D' (case-insensitive).

        Raises
        ------
        ValueError
            If the answer letter is not recognised or the question index
            is out of range.
        RuntimeError
            If the target radio button cannot be found in the DOM.
        """
        letter = answer_letter.upper()
        if letter not in ANSWER_MAP:
            raise ValueError(
                f"Invalid answer letter '{answer_letter}'. "
                f"Must be one of: {', '.join(ANSWER_MAP)}."
            )

        value = ANSWER_MAP[letter]

        group_names = self.get_all_question_groups()
        if not group_names:
            raise RuntimeError(
                "No radio buttons with class 'form-check-input' found on the page."
            )

        if question_index >= len(group_names):
            raise ValueError(
                f"question_index {question_index} is out of range. "
                f"Only {len(group_names)} question(s) found on this page."
            )

        target_group = group_names[question_index]

        # Find the specific radio with the matching value within the group.
        selector = (
            f"input[type='radio'].form-check-input"
            f"[name='{target_group}'][value='{value}']"
        )
        radio_element = self._page.query_selector(selector)

        if radio_element is None:
            raise RuntimeError(
                f"Could not find radio button for question {question_index} "
                f"(group='{target_group}'), answer '{answer_letter}' (value='{value}')."
            )

        radio_element.click()
        print(
            f"[QuizActor] Selected answer '{answer_letter}' (value={value}) "
            f"for question index {question_index} (group='{target_group}')."
        )

    def has_next_page(self) -> bool:
        """
        Check if the 'Next page' button is currently visible on the page.

        Returns
        -------
        bool
            True if the button exists and is visible, False otherwise.
        """
        try:
            # Use is_visible() for a quick, non-blocking check.
            return self._page.is_visible(NEXT_BUTTON_SELECTOR)
        except Exception:
            return False

    def click_next_page(self) -> None:
        """
        Wait for the 'Next page' button, click it, and wait for the next page to load.

        Uses a robust strategy:
          1. expect_navigation with wait_until='domcontentloaded'.
          2. Fallback wait_for_timeout(2000) if navigation is AJAX-based or slow.

        Raises
        ------
        RuntimeError
            If the next-page button is not found or click fails.
        """
        print(f"[QuizActor] Waiting for next-page button ({NEXT_BUTTON_SELECTOR})…")
        try:
            self._page.wait_for_selector(NEXT_BUTTON_SELECTOR, timeout=10_000, state="visible")
        except Exception as exc:
            raise RuntimeError(
                f"Next-page button '{NEXT_BUTTON_SELECTOR}' did not appear within 10 s."
            ) from exc

        print("[QuizActor] Clicking 'Next page' button…")
        try:
            # Use expect_navigation to handle full page loads robustly
            with self._page.expect_navigation(wait_until="domcontentloaded", timeout=15_000):
                self._page.click(NEXT_BUTTON_SELECTOR)
        except Exception as exc:
            # If it's a TimeoutError, it might be an AJAX update that doesn't 
            # trigger full navigation. We log it and rely on the settle delay.
            print(f"[QuizActor] WARNING: Navigation event not detected ({exc}). Proceeding with settle delay…")
        
        # Give the page 2 seconds to settle visually (handle AJAX updates, timers, etc.)
        self._page.wait_for_timeout(2000)
        print("[QuizActor] Navigation / Settle complete.")
