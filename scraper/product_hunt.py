"""
scraper/product_hunt.py — Fetch top launches from Product Hunt GraphQL API.
Requires a free API token from https://www.producthunt.com/v2/oauth/applications
Set PRODUCT_HUNT_TOKEN in .env (optional — skipped gracefully if not set).
"""
import os
import requests
from utils.logger import log

PH_GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql"

PH_QUERY = """
{
  posts(order: VOTES, postedAfter: "%s") {
    edges {
      node {
        name
        tagline
        url
        votesCount
        createdAt
      }
    }
  }
}
"""


def fetch_product_hunt(limit: int = 10) -> list[dict]:
    """
    Fetch today's top Product Hunt launches.
    Returns list of dicts or empty list if token not configured.
    """
    token = os.environ.get("PRODUCT_HUNT_TOKEN", "")
    if not token:
        log.warning("[ProductHunt] PRODUCT_HUNT_TOKEN not set — skipping.")
        return []

    from datetime import datetime, timedelta
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        log.info("[ProductHunt] Fetching top launches …")
        resp = requests.post(
            PH_GRAPHQL_URL,
            json={"query": PH_QUERY % yesterday},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=12,
        )
        resp.raise_for_status()
        edges = resp.json().get("data", {}).get("posts", {}).get("edges", [])

        items = []
        for edge in edges[:limit]:
            node = edge.get("node", {})
            name = node.get("name", "")
            tagline = node.get("tagline", "")
            title = f"{name} — {tagline}" if tagline else name
            items.append({
                "title": title[:200],
                "url": node.get("url", ""),
                "score": node.get("votesCount", 0),
                "source": "ProductHunt",
                "published_at": node.get("createdAt"),
            })

        log.info(f"[ProductHunt] Fetched {len(items)} launches.")
        return items

    except Exception as e:
        log.error(f"[ProductHunt] Failed: {e}")
        return []
