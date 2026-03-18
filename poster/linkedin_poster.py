"""
poster/linkedin_poster.py — Playwright-based LinkedIn post automation.
Features:
  - Cookie-based session (no password required after first run)
  - Optional image upload before typing text
  - Human-like character-by-character typing with random delays
  - Retry × 2 with draft fallback on total failure
"""
import os
import time
import random
from pathlib import Path

from utils.auth import load_session, save_session
from utils.logger import log
from poster.draft_saver import save_draft

MAX_RETRIES = 2

# Typing speed bounds (seconds per character)
TYPE_MIN = 0.02
TYPE_MAX = 0.07


def _human_delay(lo: float = 2.0, hi: float = 5.0) -> None:
    time.sleep(random.uniform(lo, hi))


def _click_start_post(page) -> None:
    """
    Click the 'Start a post' button.
    Waits for the element to be visible before clicking (confirmed working selectors from diagnostic).
    """
    # Confirmed by diagnose_linkedin.py: 'Start a post' text = 1 element, aria-label *post = 6 elements
    SELECTORS = [
        "text=Start a post",
        '[aria-label*="post"]',
        "button:has-text('post')",
        "text=start a post",
    ]
    for i, selector in enumerate(SELECTORS):
        try:
            el = page.locator(selector).first
            el.wait_for(state="visible", timeout=15000)
            el.click()
            log.debug(f"[Poster] 'Start a post' clicked via selector #{i + 1}: {selector}")
            return
        except Exception as e:
            log.debug(f"[Poster] Selector #{i + 1} failed ({selector}): {e}")
            continue
    raise RuntimeError("Could not find 'Start a post' button — all selectors failed. LinkedIn UI may have changed.")


def _post_attempt(post_text: str, image_path: str | None) -> None:
    """Single attempt to post to LinkedIn via Playwright."""
    from playwright.sync_api import sync_playwright

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
            browser.close()
            raise RuntimeError(
                "No LinkedIn session found. Run: python -m utils.auth  (first-time login)"
            )

        page = ctx.new_page()
        log.info("[Poster] Loading LinkedIn feed …")
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(5000)  # extra wait for React components to render
        _human_delay(2, 4)

        # Check we're actually logged in
        if "login" in page.url.lower():
            browser.close()
            raise RuntimeError("LinkedIn session expired. Re-run: python -m utils.auth")

        # Open post dialog — try multiple selectors (LinkedIn changes UI frequently)
        _click_start_post(page)
        _human_delay(1.5, 3)

        # ── Step 1: Type text FIRST (textbox always visible in basic modal) ──
        # (Confirmed by diagnostic: 'Start a post' modal always has 1 textbox)
        TEXTBOX_SELECTORS = [
            "text=Start a post",           # clicking the share box acts as textbox
            '[aria-label*="creating content"]',
            '[aria-label*="Text editor for creating"]',
            '.ql-editor',
            'div[role="textbox"]',
            'div[contenteditable="true"]',
        ]
        textbox = None
        for sel in TEXTBOX_SELECTORS:
            try:
                el = page.locator(sel).first
                el.wait_for(state="visible", timeout=8000)
                el.click()
                textbox = el
                log.debug(f"[Poster] Textbox focused via: {sel}")
                break
            except Exception:
                continue

        if textbox is None:
            screenshot_path = "data/debug_screenshot.png"
            try:
                page.screenshot(path=screenshot_path, full_page=False)
                log.warning(f"[Poster] Screenshot saved → {screenshot_path}")
            except Exception:
                pass
            raise RuntimeError("Could not find post textbox — all selectors failed. Check data/debug_screenshot.png")

        log.info("[Poster] Typing post …")
        # Wait 2 seconds before typing to let Quill bind its event listeners
        # to prevent the first few characters from being dropped.
        page.wait_for_timeout(2000)
        
        # Use .type() with delay so React registers the input events.
        # insert_text bypasses DOM events causing the post to submit empty.
        page.keyboard.type(post_text, delay=10)
        _human_delay(1, 2)

        # ── Step 2: Upload image AFTER typing (text persists in composer) ───
        if image_path and Path(image_path).exists():
            log.info(f"[Poster] Uploading image: {image_path}")
            try:
                MEDIA_BTN_SELECTORS = [
                    '[aria-label*="Add a photo"]',
                    '[aria-label*="photo"]',
                    '[aria-label*="media"]',
                    '[aria-label*="image"]',
                    'button:has-text("Photo")',
                ]
                media_opened = False
                for sel in MEDIA_BTN_SELECTORS:
                    try:
                        btn = page.locator(sel).first
                        btn.wait_for(state="visible", timeout=6000)
                        btn.click()
                        media_opened = True
                        log.debug(f"[Poster] Media button clicked via: {sel}")
                        break
                    except Exception:
                        continue

                if media_opened:
                    _human_delay(1, 2)
                    with page.expect_file_chooser(timeout=10000) as fc_info:
                        try:
                            page.get_by_text("Upload from computer", exact=False).click(timeout=5000)
                        except Exception:
                            page.locator('input[type="file"]').first.click(timeout=5000)
                    fc_info.value.set_files(image_path)
                    _human_delay(3, 5)
                    
                    # We must click "Next" or "Done" in the media preview modal to attach it
                    clicked_next = False
                    for sel in ['button:has-text("Next")', 'button:has-text("Done")', 'button.share-box-footer__primary-btn']:
                        try:
                            btn = page.locator(sel).last
                            if btn.is_visible():
                                btn.click(timeout=5000)
                                clicked_next = True
                                log.debug(f"[Poster] Clicked media preview button: {sel}")
                                break
                        except Exception:
                            continue
                    
                    if not clicked_next:
                        log.warning("[Poster] Could not find Next/Done on image preview. Things might break.")
                        
                    _human_delay(2, 4)
                    log.info("[Poster] Image uploaded successfully.")
                else:
                    log.warning("[Poster] Could not find media button — posting without image.")
            except Exception as e:
                log.warning(f"[Poster] Image upload failed ({e}) — posting without image.")
        _human_delay(2, 4)

        # ── Step 3: Submit the post ───────────────────────────────────────
        # Root cause analysis:
        #   - Ctrl+Enter in a contenteditable div inserts a newline, does NOT submit
        #   - div[role="dialog"] matches LinkedIn's video player, not the composer
        #   - The post composer hides itself after posting (class share-box-v2)
        #   - LinkedIn shows a toast "Your post was sent" on success
        #
        # Strategy: find the Post button globally (not scoped to wrong container),
        # wait for it to be enabled, click it, then verify via success toast.
        log.info("[Poster] Finding Post button ...")
        submitted = False

        def is_post_composer_visible():
            """Check if the post composer is still on screen."""
            try:
                el = page.locator(
                    '.share-box-v2, [id*="share-box"], .share-creation-state__main'
                ).first
                return el.is_visible()
            except Exception:
                return False

        # Wait up to 15s for Post button to appear and become enabled
        try:
            post_btn = None
            # Try multiple selectors for the Post button
            POST_BTN_SELECTORS = [
                'button[aria-label="Post"]',
                'button.share-actions__primary-action',
                'button.artdeco-button--primary:has-text("Post")',
            ]
            for sel in POST_BTN_SELECTORS:
                try:
                    el = page.locator(sel).last
                    el.wait_for(state="visible", timeout=5000)
                    post_btn = el
                    log.debug(f"[Poster] Found Post button via: {sel}")
                    break
                except Exception:
                    continue

            # Fallback: use Playwright role selector
            if post_btn is None:
                post_btn = page.get_by_role("button", name="Post", exact=True).last
                post_btn.wait_for(state="visible", timeout=5000)

            # Wait for Post button to be enabled (LinkedIn disables it during image processing)
            for _ in range(20):
                try:
                    is_disabled = post_btn.get_attribute("disabled")
                    if is_disabled is None:  # None means attribute not present = enabled
                        break
                except Exception:
                    pass
                time.sleep(0.5)

            # Click it
            log.info("[Poster] Clicking Post button ...")
            post_btn.click(timeout=5000)

            # Confirm success via toast or composer disappearing (up to 10s)
            for _ in range(10):
                time.sleep(1)
                # Check for success toast
                try:
                    toast = page.locator(
                        'text="Your post was sent",'
                        ' .artdeco-toast-item--visible,'
                        ' [data-control-name="toasts_sharing_success"]'
                    ).first
                    if toast.is_visible():
                        submitted = True
                        log.info("[Poster] Success toast detected ✓")
                        break
                except Exception:
                    pass
                # Also check if composer disappeared
                if not is_post_composer_visible():
                    submitted = True
                    log.info("[Poster] Post composer closed ✓")
                    break

        except Exception as e:
            log.warning(f"[Poster] Post button attempt failed: {e}")

        if not submitted:
            # Save HTML dump for debugging
            try:
                os.makedirs("data", exist_ok=True)
                html_content = page.content()
                with open("data/post_submit_failed.html", "w", encoding="utf-8") as f:
                    # Save only buttons section for quick diagnosis
                    import re
                    buttons = re.findall(r'<button[^>]*>.*?</button>', html_content, re.DOTALL)
                    f.write("\n\n".join(buttons[:30]))
                log.error("[Poster] Saved button HTML dump to data/post_submit_failed.html")
            except Exception as e:
                log.error(f"[Poster] Could not save failure HTML: {e}")
            raise RuntimeError("Post submission failed. See data/post_submit_failed.html")

        _human_delay(4, 7)

        # Save refreshed cookies
        save_session(ctx)
        browser.close()
        log.info("[Poster] Post published successfully! ✓")


def post_to_linkedin(post_text: str, image_path: str | None = None, item: dict | None = None) -> bool:
    """
    Attempt to post to LinkedIn with retries.
    On total failure: saves draft and returns False.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info(f"[Poster] Attempt {attempt}/{MAX_RETRIES} …")
            _post_attempt(post_text, image_path)
            return True
        except Exception as e:
            log.warning(f"[Poster] Attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                log.info("[Poster] Waiting 30s before retry …")
                time.sleep(30)

    log.error("[Poster] All attempts failed — saving draft.")
    save_draft(post_text, item=item, reason="all_posting_attempts_failed")
    return False
