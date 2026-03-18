"""
scraper/rss_feeds.py — Parse multiple RSS feeds using feedparser.
No API key required. Fetches recent tech articles from curated sources.
"""
import time
import feedparser
from utils.logger import log

RSS_FEEDS = [
    {"name": "TechCrunch",      "url": "https://techcrunch.com/feed/"},
    {"name": "The Verge",       "url": "https://www.theverge.com/rss/index.xml"},
    {"name": "ArsTechnica",     "url": "https://feeds.arstechnica.com/arstechnica/technology-lab"},
    {"name": "Wired",           "url": "https://www.wired.com/feed/rss"},
    {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/feed/"},
]


def _parse_time(entry) -> str | None:
    """Convert feedparser time struct to ISO string."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return time.strftime("%Y-%m-%dT%H:%M:%S", entry.published_parsed)
    return None


def fetch_rss_items(max_per_feed: int = 10) -> list[dict]:
    """
    Parse all configured RSS feeds.
    Returns list of dicts: title, url, score, source, published_at.
    """
    all_items: list[dict] = []

    for feed_cfg in RSS_FEEDS:
        try:
            log.info(f"[RSS] Parsing {feed_cfg['name']} …")
            feed = feedparser.parse(feed_cfg["url"])

            if feed.bozo:
                log.warning(f"[RSS] {feed_cfg['name']} returned bozo feed (malformed): {feed.bozo_exception}")

            count = 0
            for entry in feed.entries[:max_per_feed]:
                url = entry.get("link", "")
                title = entry.get("title", "").strip()
                if not url or not title:
                    continue
                all_items.append({
                    "title": title,
                    "url": url,
                    "score": 0,           # RSS has no engagement score
                    "source": feed_cfg["name"],
                    "published_at": _parse_time(entry),
                })
                count += 1

            log.info(f"[RSS] {feed_cfg['name']}: {count} items.")
        except Exception as e:
            log.error(f"[RSS] Failed to parse {feed_cfg['name']}: {e}")

    log.info(f"[RSS] Total items across all feeds: {len(all_items)}")
    return all_items
