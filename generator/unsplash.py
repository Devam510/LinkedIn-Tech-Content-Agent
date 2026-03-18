"""
generator/unsplash.py — Fetch a high-quality topic-relevant photo from Unsplash.
Free API: 50 requests/hour. Register at https://unsplash.com/developers
Add UNSPLASH_ACCESS_KEY to .env

Unsplash License: photos are free for commercial use. No attribution required in posts,
but crediting the photographer is good practice.
"""
import os
import requests
from pathlib import Path
from utils.logger import log

UNSPLASH_API = "https://api.unsplash.com/photos/random"

# Map topic keywords → focused Unsplash search queries for better relevance
TOPIC_QUERY_MAP: dict[str, str] = {
    "AI":          "artificial intelligence technology",
    "LLM":         "machine learning data science",
    "agent":       "robot automation technology",
    "open source": "developers collaboration coding",
    "startup":     "startup office innovation",
    "funding":     "investment growth business",
    "cloud":       "cloud server technology",
    "Python":      "programming coding developer",
    "Rust":        "systems programming technology",
    "security":    "cybersecurity protection technology",
    "database":    "data storage technology",
    "research":    "science research laboratory",
    "GitHub":      "open source code collaboration",
    "model":       "neural network deep learning",
}

DEFAULT_QUERY = "technology innovation"


def _build_query(item: dict) -> str:
    """Pick the best Unsplash search query based on the article title."""
    title = item.get("title", "").lower()
    for keyword, query in TOPIC_QUERY_MAP.items():
        if keyword.lower() in title:
            return query
    return DEFAULT_QUERY


def fetch_unsplash_photo(item: dict, output_path: str = "data/post_image.png") -> str:
    """
    Download a random relevant photo from Unsplash.
    Returns path to saved image on success, raises on failure.
    """
    access_key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
    if not access_key:
        raise ValueError("UNSPLASH_ACCESS_KEY not set in .env")

    query = _build_query(item)
    log.info(f"[Unsplash] Searching: '{query}' …")

    resp = requests.get(
        UNSPLASH_API,
        params={
            "query":       query,
            "orientation": "landscape",
            "content_filter": "high",
        },
        headers={"Authorization": f"Client-ID {access_key}"},
        timeout=12,
    )
    resp.raise_for_status()
    data = resp.json()

    # Get 1280px wide version (good for LinkedIn 1200×627 target)
    img_url = data["urls"].get("regular", data["urls"]["full"])
    photographer = data.get("user", {}).get("name", "unknown")
    log.info(f"[Unsplash] Photo by {photographer} — downloading …")

    img_resp = requests.get(img_url, timeout=30)
    img_resp.raise_for_status()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(img_resp.content)

    log.info(f"[Unsplash] Photo saved → {output_path}  (by {photographer})")
    return output_path
