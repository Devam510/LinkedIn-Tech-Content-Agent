"""
main.py — Autonomous LinkedIn Agent Orchestrator.

Pipeline:
  FESTIVAL DAY:
    1. Check festivals.json for today's date
    2. If festival found AND not already posted today → generate & post festival greeting, then exit.
    3. If festival found BUT already posted today → exit gracefully (no tech news).

  REGULAR DAY:
    1. Scrape all sources
    2. Deduplicate + rank
    3. Generate post text via LLM (random template)
    4. Generate image
    5. Format post
    6. Publish to LinkedIn via Playwright
    7. Record to DB

Run daily via GitHub Actions cron or local cron job.
"""
import json
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from utils.logger import log
from utils.db import init_db, insert_item, record_post, already_posted, check_festival_posted

from scraper.hacker_news import fetch_hn_top
from scraper.rss_feeds import fetch_rss_items
from scraper.reddit import fetch_reddit_top
from scraper.github_trending import fetch_github_trending
from scraper.product_hunt import fetch_product_hunt

from filter.deduplicator import deduplicate
from filter.scorer import rank_items

from generator.generator import generate_post
from generator.festival_generator import generate_festival_post
from generator.image_generator import get_post_image
from formatter.formatter import format_post
from poster.linkedin_poster import post_to_linkedin
from poster.draft_saver import save_draft

FESTIVALS_PATH = Path("data/festivals.json")


def get_today_festival() -> str | None:
    """Return the festival name for today (MM-DD), or None if it's a regular day."""
    if not FESTIVALS_PATH.exists():
        return None
    try:
        festivals = json.loads(FESTIVALS_PATH.read_text(encoding="utf-8"))
        today_key = date.today().strftime("%m-%d")
        return festivals.get(today_key)
    except Exception as e:
        log.warning(f"[Main] Could not read festivals.json: {e}")
        return None


def run_festival(festival_name: str) -> None:
    """Full pipeline for a festival post."""
    today_str = date.today().isoformat()  # YYYY-MM-DD

    if check_festival_posted(today_str):
        log.info(f"[Main] Festival post for '{festival_name}' already published today. Skipping all posts.")
        return

    log.info(f"[Main] 🎉 Today is {festival_name}. Generating a special festival post …")

    # Build a fake "item" so we can reuse the DB and image pipeline unchanged
    festival_item = {
        "title":    f"Happy {festival_name}!",
        "url":      f"festival://{today_str}",
        "source":   "Festival Calendar",
        "score":    0,
    }

    item_id = insert_item(festival_item)

    # Generate text
    try:
        raw_post = generate_festival_post(festival_name)
    except Exception as e:
        log.error(f"[Main] Festival post generation failed: {e}")
        save_draft("", item=festival_item, reason=f"festival_generation_failed: {e}")
        return

    # Generate image — pass the item so the image pipeline works normally
    image_path = get_post_image(festival_item)

    # Format + publish
    post_text = format_post(raw_post)
    log.info(f"[Main] Festival post ({len(post_text)} chars):\n{'-'*40}\n{post_text}\n{'-'*40}")

    success = post_to_linkedin(post_text, image_path=image_path, item=festival_item)

    status = "success" if success else "failed"
    if item_id:
        record_post(item_id, post_text, image_path, status=status)

    log.info(f"[Main] Festival run complete — status: {status.upper()}")


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


def run_regular() -> None:
    """Standard tech-news post pipeline."""
    raw_items = scrape_all()
    if not raw_items:
        log.error("[Main] No items scraped from any source. Aborting.")
        return

    fresh_items = deduplicate(raw_items)
    if not fresh_items:
        log.warning("[Main] All items already seen. Nothing new to post today.")
        return

    ranked = rank_items(fresh_items)
    if not ranked:
        log.warning("[Main] No items passed the relevance threshold.")
        return

    top_item = ranked[0]
    log.info(f"[Main] Selected item: {top_item['title'][:80]}")
    log.info(f"[Main] Source: {top_item['source']}  |  Score: {top_item['rank_score']}")

    item_id = insert_item(top_item)

    try:
        raw_post = generate_post(top_item)
    except Exception as e:
        log.error(f"[Main] Post generation failed after all retries: {e}")
        save_draft("", item=top_item, reason=f"generation_failed: {e}")
        return

    image_path = get_post_image(top_item)
    post_text  = format_post(raw_post)
    log.info(f"[Main] Final post ({len(post_text)} chars):\n{'-'*40}\n{post_text}\n{'-'*40}")

    success = post_to_linkedin(post_text, image_path=image_path, item=top_item)

    status = "success" if success else "failed"
    if item_id:
        record_post(item_id, post_text, image_path, status=status)

    log.info(f"[Main] Run complete — status: {status.upper()}")
    log.info("=" * 60)


def run() -> None:
    load_dotenv()
    log.info("=" * 60)
    log.info("LinkedIn Agent — Daily Run Starting")
    log.info("=" * 60)

    init_db()

    # ── Festival Gate ─────────────────────────────────────────────────────────
    festival = get_today_festival()
    if festival:
        run_festival(festival)
        return  # ← NEVER fall through to tech news on a festival day

    # ── Regular Tech News Post ────────────────────────────────────────────────
    run_regular()


if __name__ == "__main__":
    run()

