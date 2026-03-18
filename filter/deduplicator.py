"""
filter/deduplicator.py — Cross-session deduplication using SQLite.
Ensures we never re-post the same story even across days.
"""
from utils.db import is_duplicate, already_posted
from utils.logger import log


def deduplicate(items: list[dict]) -> list[dict]:
    """
    Remove items already seen (by URL or title hash) OR already posted.
    Returns a filtered list of fresh items.
    """
    fresh = []
    for item in items:
        url   = item.get("url", "")
        title = item.get("title", "")

        if already_posted(url):
            log.debug(f"[Dedup] Already posted — skipping: {title[:60]}")
            continue
        if is_duplicate(url, title):
            log.debug(f"[Dedup] Seen before — skipping: {title[:60]}")
            continue
        fresh.append(item)

    log.info(f"[Dedup] {len(items)} in → {len(fresh)} fresh items out.")
    return fresh
