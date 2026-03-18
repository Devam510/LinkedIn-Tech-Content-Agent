"""
scraper/github_trending.py — Scrape GitHub Trending page for today's top repos.
No API key needed. Runs once per day.
"""
from bs4 import BeautifulSoup
from scraper.base import fetch_html
from utils.logger import log

GITHUB_TRENDING_URL = "https://github.com/trending"
GITHUB_BASE = "https://github.com"


def fetch_github_trending(limit: int = 15) -> list[dict]:
    """
    Scrape GitHub Trending page and return top repos.
    Returns list of dicts: title, url, score (stars today), source, published_at.
    """
    log.info("[GitHub] Scraping trending repositories …")
    try:
        html = fetch_html(GITHUB_TRENDING_URL)
        soup = BeautifulSoup(html, "html.parser")
        articles = soup.select("article.Box-row")[:limit]

        items = []
        for article in articles:
            # Repo name
            h2 = article.select_one("h2 a")
            if not h2:
                continue
            repo_path = h2.get("href", "").strip()
            repo_name = repo_path.lstrip("/").replace("/", " / ")
            url = GITHUB_BASE + repo_path

            # Description
            desc_tag = article.select_one("p")
            description = desc_tag.get_text(strip=True) if desc_tag else ""

            # Stars today
            stars_today_tag = article.select_one("span.d-inline-block.float-sm-right")
            stars_text = stars_today_tag.get_text(strip=True) if stars_today_tag else "0"
            stars_today = int(stars_text.replace(",", "").replace("stars today", "").strip() or 0)

            title = f"{repo_name}" + (f" — {description}" if description else "")

            items.append({
                "title": title[:200],       # guard against very long titles
                "url": url,
                "score": stars_today,
                "source": "GitHubTrending",
                "published_at": None,       # trending page has no timestamps
            })

        log.info(f"[GitHub] Scraped {len(items)} trending repos.")
        return items

    except Exception as e:
        log.error(f"[GitHub] Scraping failed: {e}")
        return []
