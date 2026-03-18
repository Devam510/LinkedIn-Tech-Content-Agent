"""
main.py — Autonomous LinkedIn Agent Orchestrator.

Pipeline:
  1. Scrape all sources
  2. Deduplicate + rank
  3. Generate post text via LLM
  4. Generate image (Imagen 3 → Pillow fallback)
  5. Format post
  6. Publish to LinkedIn via Playwright
  7. Record to DB

Run daily via GitHub Actions cron or local cron job.
"""
import os
from dotenv import load_dotenv
from utils.logger import log
from utils.db import init_db, insert_item, record_post, already_posted

from scraper.hacker_news import fetch_hn_top
from scraper.rss_feeds import fetch_rss_items
from scraper.reddit import fetch_reddit_top
from scraper.github_trending import fetch_github_trending
from scraper.product_hunt import fetch_product_hunt

from filter.deduplicator import deduplicate
from filter.scorer import rank_items

from generator.generator import generate_post
from generator.image_generator import get_post_image
from formatter.formatter import format_post
from poster.linkedin_poster import post_to_linkedin
from poster.draft_saver import save_draft


def scrape_all() -> list[dict]:
    """Fetch items from all sources and combine into one list."""
    items = []
    items += fetch_hn_top(limit=30)
    items += fetch_rss_items(max_per_feed=10)
    items += fetch_reddit_top(limit_per_sub=10)
    items += fetch_github_trending(limit=15)
    items += fetch_product_hunt(limit=10)
    log.info(f"[Main] Total raw items collected: {len(items)}")
    return items


def run() -> None:
    load_dotenv()
    log.info("=" * 60)
    log.info("LinkedIn Agent — Daily Run Starting")
    log.info("=" * 60)

    # ── Step 1: Init DB ────────────────────────────────────────────────
    init_db()

    # ── Step 2: Scrape ─────────────────────────────────────────────────
    raw_items = scrape_all()
    if not raw_items:
        log.error("[Main] No items scraped from any source. Aborting.")
        return

    # ── Step 3: Deduplicate + Rank ─────────────────────────────────────
    fresh_items = deduplicate(raw_items)
    if not fresh_items:
        log.warning("[Main] All items already seen. Nothing new to post today.")
        return

    ranked = rank_items(fresh_items)
    if not ranked:
        log.warning("[Main] No items passed the relevance threshold.")
        return

    # Pick the top item
    top_item = ranked[0]
    log.info(f"[Main] Selected item: {top_item['title'][:80]}")
    log.info(f"[Main] Source: {top_item['source']}  |  Score: {top_item['rank_score']}")

    # Store item in DB (for deduplication in future runs)
    item_id = insert_item(top_item)

    # ── Step 4: Generate Post Text ─────────────────────────────────────
    try:
        raw_post = generate_post(top_item)
    except Exception as e:
        log.error(f"[Main] Post generation failed after all retries: {e}")
        save_draft("", item=top_item, reason=f"generation_failed: {e}")
        return

    # ── Step 5: Generate Image ─────────────────────────────────────────
    image_path = get_post_image(top_item)

    # ── Step 6: Format ─────────────────────────────────────────────────
    post_text = format_post(raw_post)
    log.info(f"[Main] Final post ({len(post_text)} chars):\n{'-'*40}\n{post_text}\n{'-'*40}")

    # ── Step 7: Publish ────────────────────────────────────────────────
    success = post_to_linkedin(post_text, image_path=image_path, item=top_item)

    # ── Step 8: Record ─────────────────────────────────────────────────
    status = "success" if success else "failed"
    if item_id:
        record_post(item_id, post_text, image_path, status=status)

    log.info(f"[Main] Run complete — status: {status.upper()}")
    log.info("=" * 60)


if __name__ == "__main__":
    run()
