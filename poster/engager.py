"""
poster/engager.py — Automated feed engagement (Likes and Comments) via Playwright.

Scrolls the user's feed, likes 5-10 posts, and drops highly contextual, 
LLM-generated comments on 1-3 high-value posts.
"""
import random
import time
from playwright.sync_api import Page
from utils.logger import log
from generator.comment_generator import generate_comment

MAX_LIKES = 8
MAX_COMMENTS = 2


def _human_delay(min_sec: float = 2.0, max_sec: float = 5.0) -> None:
    time.sleep(random.uniform(min_sec, max_sec))


def run_auto_engagement(page: Page) -> None:
    """
    Navigate to the feed, like a few posts, and comment intelligently on a couple.
    """
    log.info("=" * 60)
    log.info("[Engager] Starting feed engagement (Algorithm Booster) ...")
    
    page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
    _human_delay(3, 6)

    # Scroll a few times to load posts
    log.info("[Engager] Scrolling to load feed ...")
    for _ in range(3):
        page.mouse.wheel(0, 800)
        _human_delay(1, 3)

    # Find all posts in the feed
    # LinkedIn organic posts usually have the data-urn attribute on a div
    post_locators = page.locator('div[data-urn^="urn:li:activity:"]').all()
    log.info(f"[Engager] Found {len(post_locators)} posts in the feed.")

    likes_done = 0
    comments_done = 0

    for i, post in enumerate(post_locators):
        if likes_done >= MAX_LIKES and comments_done >= MAX_COMMENTS:
            break

        # Skip if post isn't visible
        try:
            if not post.is_visible():
                continue
            post.scroll_into_view_if_needed()
            _human_delay(1, 2)
        except Exception:
            continue

        # ── 1. Liking logic ──────────────────────────────────────────────────
        if likes_done < MAX_LIKES:
            # 60% chance to like this post to make it look organic
            if random.random() < 0.60:
                try:
                    # Find the generic 'Like' button for this specific post
                    like_btn = post.locator('button[aria-label^="React Like"]').first
                    if like_btn.is_visible():
                        # Check if already liked (aria-pressed is true)
                        is_liked = like_btn.get_attribute("aria-pressed") == "true"
                        if not is_liked:
                            like_btn.click()
                            likes_done += 1
                            log.info(f"[Engager] 👍 Liked post #{i+1} ({likes_done}/{MAX_LIKES})")
                            _human_delay(2, 4)
                except Exception as e:
                    log.debug(f"[Engager] Could not like post #{i+1}: {e}")

        # ── 2. Commenting logic ──────────────────────────────────────────────
        if comments_done < MAX_COMMENTS:
            # Only comment on ~15% of posts we see
            if random.random() < 0.15:
                try:
                    # Extract author name
                    author_el = post.locator('span.update-components-actor__name, span[dir="ltr"]').first
                    author = author_el.inner_text().strip() if author_el.count() > 0 else "Connection"
                    
                    # Avoid commenting on huge brand pages or promoted posts if possible
                    if "Promoted" in post.inner_text():
                        continue

                    # Extract post text
                    # Usually in a span with break-words class
                    text_el = post.locator('div.update-components-text span[dir="ltr"]').first
                    if text_el.count() == 0:
                        continue
                    
                    post_text = text_el.inner_text().strip()
                    if len(post_text) < 40:
                        # Skip posts that are just an image/video with minimal text
                        continue

                    log.info(f"[Engager] Found good post by {author}. Generating comment...")
                    comment_text = generate_comment(author, post_text)

                    # Click the comment button to open the text box
                    comment_btn = post.locator('button[aria-label^="Comment on"]').first
                    if comment_btn.is_visible():
                        comment_btn.click()
                        _human_delay(1, 2)

                        # Find the contenteditable paragraph inside the post
                        editor = post.locator('div[role="textbox"], div.ql-editor').first
                        if editor.is_visible():
                            editor.fill(comment_text)
                            _human_delay(1, 2)

                            # Click the actual post/submit button
                            submit_btn = post.locator('button.comments-comment-box__submit-button').first
                            if submit_btn.is_visible() and not submit_btn.is_disabled():
                                submit_btn.click()
                                comments_done += 1
                                log.info(f"[Engager] ✅ Commented on {author}'s post: {comment_text[:50]}...")
                                _human_delay(3, 6)

                except Exception as e:
                    log.debug(f"[Engager] Could not comment on post #{i+1}: {e}")

    log.info(f"[Engager] Finished! Liked {likes_done} posts, commented {comments_done} times.")
    log.info("=" * 60)
