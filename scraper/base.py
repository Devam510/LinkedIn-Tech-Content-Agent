"""
scraper/base.py — Base HTTP fetch with retry logic for all scrapers.
"""
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from utils.logger import log

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.RequestException, ValueError)),
    reraise=True,
)
def fetch_json(url: str, headers: dict = None, params: dict = None) -> dict | list:
    """Fetch a URL and return parsed JSON. Retries up to 3 times."""
    merged_headers = {**HEADERS, **(headers or {})}
    resp = requests.get(url, headers=merged_headers, params=params, timeout=12)
    resp.raise_for_status()
    return resp.json()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.RequestException,)),
    reraise=True,
)
def fetch_html(url: str, headers: dict = None) -> str:
    """Fetch a URL and return raw HTML text. Retries up to 3 times."""
    merged_headers = {**HEADERS, **(headers or {})}
    resp = requests.get(url, headers=merged_headers, timeout=12)
    resp.raise_for_status()
    return resp.text
