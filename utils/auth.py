"""
utils/auth.py — LinkedIn session persistence via Playwright cookies.
Run save_session_interactive() once manually (headful) to capture cookies.
All subsequent runs load cookies and skip manual login.
"""
import json
from pathlib import Path
from utils.logger import log

COOKIES_FILE = Path("data/linkedin_cookies.json")


def save_session(context) -> None:
    """Persist current Playwright browser context cookies to disk."""
    COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    cookies = context.cookies()
    with open(COOKIES_FILE, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=2)
    log.info(f"Session cookies saved → {COOKIES_FILE}")


def load_session(context) -> bool:
    """
    Load saved cookies into a Playwright browser context.
    Returns True if cookies were loaded, False if file missing.
    """
    if not COOKIES_FILE.exists():
        log.warning("No saved cookies found. Run interactive login first.")
        return False
    with open(COOKIES_FILE, encoding="utf-8") as f:
        cookies = json.load(f)
    context.add_cookies(cookies)
    log.info(f"Session cookies loaded ({len(cookies)} cookies).")
    return True


def save_session_interactive() -> None:
    """
    One-time interactive login to LinkedIn.
    Run this script directly: python -m utils.auth
    Handles 2FA / CAPTCHA manually, then saves cookies for future headless runs.
    """
    import os
    from playwright.sync_api import sync_playwright

    email = os.environ.get("LINKEDIN_EMAIL", "")
    password = os.environ.get("LINKEDIN_PASSWORD", "")

    if not email or not password:
        raise ValueError("Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in your .env file.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headed for manual steps
        context = browser.new_context()
        page = context.new_page()

        log.info("Opening LinkedIn login page …")
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        page.fill("#username", email)
        page.fill("#password", password)
        page.click('[data-litms-control-urn="login-submit"]')

        log.info("Waiting 30s for 2FA / CAPTCHA — complete it in the browser window.")
        page.wait_for_timeout(30_000)  # 30 seconds for manual 2FA

        save_session(context)
        browser.close()
        log.info("Interactive login complete. Cookies saved.")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    save_session_interactive()
