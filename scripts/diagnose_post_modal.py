"""
scripts/diagnose_post_modal.py — Diagnose textbox selectors inside LinkedIn post dialog.
Opens a post dialog (with an image upload), then reports available textbox selectors.
Usage: venv\\Scripts\\python scripts/diagnose_post_modal.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from playwright.sync_api import sync_playwright
from utils.auth import load_session
from utils.logger import log

TEST_IMAGE = Path("data/post_image.png")


def diagnose():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 800},
        )
        load_session(ctx)
        page = ctx.new_page()

        print("Loading LinkedIn feed …")
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(5000)

        if "login" in page.url.lower():
            print("ERROR: Session expired — run: venv\\Scripts\\python -m utils.auth")
            browser.close()
            return

        # Click Start a post
        print("Clicking 'Start a post' …")
        page.locator("text=Start a post").first.wait_for(state="visible", timeout=15000)
        page.locator("text=Start a post").first.click()
        time.sleep(3)

        # Upload image if available
        if TEST_IMAGE.exists():
            print("Uploading image …")
            for sel in ['[aria-label*="photo"]', '[aria-label*="media"]', 'button:has-text("Photo")']:
                try:
                    btn = page.locator(sel).first
                    btn.wait_for(state="visible", timeout=6000)
                    btn.click()
                    time.sleep(2)
                    with page.expect_file_chooser(timeout=8000) as fc:
                        try:
                            page.get_by_text("Upload from computer").click(timeout=4000)
                        except Exception:
                            page.locator('input[type="file"]').first.click(timeout=4000)
                    fc.value.set_files(str(TEST_IMAGE))
                    time.sleep(4)
                    print("Image uploaded.")
                    break
                except Exception as e:
                    print(f"  Media btn {sel} failed: {e}")
        else:
            print("No test image — testing without upload.")

        # Now probe textbox selectors
        print("\n── Textbox selectors after upload ──")
        selectors = [
            '[aria-label*="creating content"]',
            '[aria-label*="Text editor for creating"]',
            '[aria-label*="share"]',
            '[aria-label*="Add a comment"]',
            '[aria-label*="write"]',
            '[aria-label*="post"]',
            '.ql-editor',
            'div[role="textbox"]',
            'div[contenteditable="true"]',
            '[data-placeholder]',
        ]
        for sel in selectors:
            try:
                count = page.locator(sel).count()
                visible = 0
                for i in range(count):
                    try:
                        if page.locator(sel).nth(i).is_visible():
                            visible += 1
                    except Exception:
                        pass
                status = f"FOUND {count} total, {visible} visible"
            except Exception as e:
                status = f"ERROR: {e}"
            print(f"  [{status:35s}] {sel}")

        # Save HTML after upload for inspection
        html_path = Path("data/linkedin_post_modal.html")
        html_path.write_text(page.content(), encoding="utf-8")
        print(f"\nPost modal HTML saved → {html_path}")
        browser.close()


if __name__ == "__main__":
    diagnose()
