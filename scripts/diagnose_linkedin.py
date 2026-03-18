"""
scripts/diagnose_linkedin.py — Diagnostic script to capture LinkedIn feed HTML.
Run this to find what selectors are actually available on the feed page.
Usage: venv\\Scripts\\python scripts/diagnose_linkedin.py
"""
import sys
from pathlib import Path

# Ensure project root is in path so 'utils' package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from dotenv import load_dotenv

load_dotenv()

from playwright.sync_api import sync_playwright
from utils.auth import load_session

OUTPUT_HTML = Path("data/linkedin_feed_dump.html")
OUTPUT_SELECTORS = Path("data/linkedin_selector_report.txt")


def diagnose():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )

        if not load_session(ctx):
            print("ERROR: No session cookies. Run: venv\\Scripts\\python -m utils.auth")
            browser.close()
            return

        page = ctx.new_page()
        print("Loading LinkedIn feed…")
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=45000)
        import time; time.sleep(5)

        # Check session
        if "login" in page.url.lower():
            print("ERROR: Session expired. Re-run utils.auth")
            browser.close()
            return

        print(f"Page URL: {page.url}")
        print(f"Page title: {page.title()}")

        # Save full HTML for inspection
        html = page.content()
        OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_HTML.write_text(html, encoding="utf-8")
        print(f"Full HTML → {OUTPUT_HTML}")

        # Test each selector
        selectors_to_test = [
            ("get_by_text 'Start a post'",     lambda: page.get_by_text("Start a post", exact=False).count()),
            ("get_by_text 'start a post'",     lambda: page.get_by_text("start a post", exact=False).count()),
            ("placeholder *post",              lambda: page.locator('[placeholder*="post"]').count()),
            ("placeholder *Post",              lambda: page.locator('[placeholder*="Post"]').count()),
            (".share-box-feed-entry__trigger", lambda: page.locator(".share-box-feed-entry__trigger").count()),
            ("aria-label *post",               lambda: page.locator('[aria-label*="post"]').count()),
            ("aria-label *Post",               lambda: page.locator('[aria-label*="Post"]').count()),
            ("data-control-name share",        lambda: page.locator('[data-control-name*="share"]').count()),
            ("button + 'post' text",           lambda: page.locator("button:has-text('post')").count()),
            (".share-creation-state__content", lambda: page.locator(".share-creation-state__content").count()),
        ]

        report = []
        for name, fn in selectors_to_test:
            try:
                count = fn()
                status = f"FOUND ({count} elements)" if count > 0 else "NOT FOUND (0 elements)"
            except Exception as e:
                status = f"ERROR: {e}"
            line = f"  [{status:40s}] {name}"
            print(line)
            report.append(line)

        OUTPUT_SELECTORS.write_text("\n".join(report), encoding="utf-8")
        print(f"\nSelector report → {OUTPUT_SELECTORS}")
        browser.close()


if __name__ == "__main__":
    diagnose()
