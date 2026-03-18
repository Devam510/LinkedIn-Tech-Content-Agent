"""
scraper/hacker_news.py — Fetch top stories from Hacker News Firebase API.
Free, no auth required, ~10k req/day limit.
"""
from datetime import datetime
from scraper.base import fetch_json
from utils.logger import log

HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"


def fetch_hn_top(limit: int = 30) -> list[dict]:
    """
    Fetch top `limit` HN stories.
    Returns list of dicts: title, url, score, source, published_at.
    """
    log.info(f"[HackerNews] Fetching top {limit} stories …")
    ids: list[int] = fetch_json(HN_TOP_URL)[:limit]

    items = []
    for item_id in ids:
        try:
            data = fetch_json(HN_ITEM_URL.format(item_id))
            if not data or data.get("type") != "story":
                continue
            url = data.get("url", "")
            if not url:
                # Self-post (Ask HN / Show HN) — skip as they have no external link
                continue
            items.append({
                "title": data.get("title", "").strip(),
                "url": url,
                "score": data.get("score", 0),
                "source": "HackerNews",
                "published_at": datetime.utcfromtimestamp(data["time"]).isoformat() if data.get("time") else None,
            })
        except Exception as e:
            log.warning(f"[HackerNews] Skipping item {item_id}: {e}")

    log.info(f"[HackerNews] Fetched {len(items)} stories.")
    return items
