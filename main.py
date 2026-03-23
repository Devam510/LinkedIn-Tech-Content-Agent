"""
main.py — Autonomous LinkedIn Agent Orchestrator.

Pipeline:
  FESTIVAL DAY  → Exit immediately. No post.
  REGULAR DAY   → Scrape → Deduplicate → Rank → Generate → Image → Post → Record

Runs once daily at 9 AM via GitHub Actions cron.
"""
import json
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from utils.logger import log
from utils.db import init_db, insert_item, record_post

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

    init_db()

    # ── Festival Gate: skip the entire run on festival days ───────────────────
    festival = get_today_festival()
    if festival:
        log.info(f"[Main] Today is {festival}. No post scheduled — taking the day off. 🎉")
        return

    # ── Scrape ────────────────────────────────────────────────────────────────
    raw_items = scrape_all()
    if not raw_items:
        log.error("[Main] No items scraped from any source. Aborting.")
        return

    # ── Deduplicate + Rank ────────────────────────────────────────────────────
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

    # ── Generate Post ─────────────────────────────────────────────────────────
    try:
        raw_post = generate_post(top_item)
    except Exception as e:
        log.error(f"[Main] Post generation failed after all retries: {e}")
        save_draft("", item=top_item, reason=f"generation_failed: {e}")
        return

    # ── Generate Image ────────────────────────────────────────────────────────
    image_path = get_post_image(top_item)

    # ── Format + Publish ──────────────────────────────────────────────────────
    post_text = format_post(raw_post)
    log.info(f"[Main] Final post ({len(post_text)} chars):\n{'-'*40}\n{post_text}\n{'-'*40}")

    success = post_to_linkedin(post_text, image_path=image_path, item=top_item)

    # ── Record ────────────────────────────────────────────────────────────────
    status = "success" if success else "failed"
    if item_id:
        record_post(item_id, post_text, image_path, status=status)

    log.info(f"[Main] Run complete — status: {status.upper()}")
    log.info("=" * 60)


if __name__ == "__main__":
    run()
