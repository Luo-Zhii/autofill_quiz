"""
core/browser.py

Manages connection to an existing Brave/Chrome browser session
via Chrome DevTools Protocol (CDP) using Playwright's sync API.
"""

from playwright.sync_api import sync_playwright, Page, Browser, Playwright

CDP_ENDPOINT = "http://localhost:9222"
TARGET_URL_SUBSTRING = "elearning.thanglong.edu.vn"


class BrowserManager:
    """
    Connects to a running browser instance exposed on a remote debugging port
    and retrieves a specific Page by URL substring.
    """

    def __init__(
        self,
        cdp_endpoint: str = CDP_ENDPOINT,
        url_substring: str = TARGET_URL_SUBSTRING,
    ) -> None:
        self._cdp_endpoint = cdp_endpoint
        self._url_substring = url_substring
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    # ------------------------------------------------------------------
    # Context-manager support (optional but convenient)
    # ------------------------------------------------------------------
    def __enter__(self) -> "BrowserManager":
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        # Intentionally NOT closing the browser — we only borrowed the session.
        self.disconnect_playwright()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def connect(self) -> None:
        """Start Playwright and attach to the running browser via CDP."""
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.connect_over_cdp(self._cdp_endpoint)
        print(f"[BrowserManager] Connected to CDP endpoint: {self._cdp_endpoint}")

    def disconnect_playwright(self) -> None:
        """Stop the Playwright engine (does NOT close the external browser)."""
        if self._playwright:
            self._playwright.stop()
            print("[BrowserManager] Playwright engine stopped (browser left open).")

    def get_quiz_page(self) -> Page:
        """
        Iterate through all open pages in the first browser context and
        return the one whose URL contains the configured substring.

        Raises
        ------
        RuntimeError
            If no matching page is found.
        """
        if self._browser is None:
            raise RuntimeError(
                "Browser is not connected. Call connect() before get_quiz_page()."
            )

        contexts = self._browser.contexts
        if not contexts:
            raise RuntimeError("No browser contexts found in the connected browser.")

        for page in contexts[0].pages:
            if self._url_substring in page.url:
                print(f"[BrowserManager] Found quiz page: {page.url}")
                return page

        raise RuntimeError(
            f"No page with URL containing '{self._url_substring}' was found. "
            "Make sure the quiz tab is open in the browser."
        )
