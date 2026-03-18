"""
scraper/reddit.py — Fetch top posts from tech subreddits.
Uses the unauthenticated JSON endpoint — no API key required.
"""
from datetime import datetime
from scraper.base import fetch_json
from utils.logger import log

SUBREDDITS = [
    "programming",
    "MachineLearning",
    "artificial",
    "technology",
    "OpenAI",
]

REDDIT_TOP_URL = "https://www.reddit.com/r/{subreddit}/top.json"


def fetch_reddit_top(limit_per_sub: int = 10) -> list[dict]:
    """
    Fetch top posts (past 24h) from configured subreddits.
    Returns list of dicts: title, url, score, source, published_at.
    """
    all_items: list[dict] = []

    for sub in SUBREDDITS:
        try:
            log.info(f"[Reddit] Fetching r/{sub} top posts …")
            data = fetch_json(
                REDDIT_TOP_URL.format(subreddit=sub),
                params={"t": "day", "limit": limit_per_sub},
            )
            posts = data.get("data", {}).get("children", [])
            count = 0
            for post in posts:
                p = post.get("data", {})
                url = p.get("url", "")
                title = p.get("title", "").strip()

                # Skip self-posts and media-only posts
                if not url or p.get("is_self") or url.endswith((".gif", ".mp4")):
                    continue

                all_items.append({
                    "title": title,
                    "url": url,
                    "score": p.get("score", 0),
                    "source": f"Reddit/r/{sub}",
                    "published_at": datetime.utcfromtimestamp(p["created_utc"]).isoformat()
                    if p.get("created_utc")
                    else None,
                })
                count += 1

            log.info(f"[Reddit] r/{sub}: {count} items.")
        except Exception as e:
            log.error(f"[Reddit] r/{sub} failed: {e}")

    log.info(f"[Reddit] Total items: {len(all_items)}")
    return all_items
