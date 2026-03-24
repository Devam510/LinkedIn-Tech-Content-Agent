"""
filter/scorer.py — Scoring and ranking engine.
score = (engagement * 0.40) + (keyword_match * 0.35) + (recency * 0.25)
"""
import time
from datetime import datetime
from filter.config import HIGH_SIGNAL_KEYWORDS, NOISE_KEYWORDS, MIN_SCORE_THRESHOLD, TOP_N_ITEMS
from utils.logger import log
from utils.db import get_recent_sources


def _normalize_engagement(score: int, max_val: int = 500) -> float:
    """Normalize raw engagement score (upvotes/stars) to 0–10."""
    return min(score / max_val, 1.0) * 10


def _keyword_score(title: str) -> float:
    """Count HIGH_SIGNAL_KEYWORDS matches in the title (capped at 10)."""
    title_lower = title.lower()
    hits = sum(1 for kw in HIGH_SIGNAL_KEYWORDS if kw.lower() in title_lower)
    return min(hits, 10)


def _recency_score(published_at: str | None) -> float:
    """
    Score based on article age:
      < 6h  → 10
      < 12h → 7
      < 24h → 4
      older → 0
    """
    if not published_at:
        return 3.0  # unknown age — neutral
    try:
        pub = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        age_hours = (datetime.now(pub.tzinfo) - pub).total_seconds() / 3600
    except Exception:
        return 3.0
    if age_hours < 6:
        return 10.0
    if age_hours < 12:
        return 7.0
    if age_hours < 24:
        return 4.0
    return 0.0


def _is_noise(title: str) -> bool:
    """Return True if the title contains any noise keyword."""
    title_lower = title.lower()
    return any(nw.lower() in title_lower for nw in NOISE_KEYWORDS)


def score_item(item: dict, recent_sources: list[str]) -> float:
    """Compute composite score for a single item, including source diversity penalty."""
    if _is_noise(item.get("title", "")):
        return 0.0
    eng   = _normalize_engagement(item.get("score", 0))
    kw    = _keyword_score(item.get("title", ""))
    rec   = _recency_score(item.get("published_at"))
    
    total = (eng * 0.40) + (kw * 0.35) + (rec * 0.25)

    # ── Source Diversity Penalty ──
    # If this source was used heavily in the last few posts, penalize it heavily so we rotate.
    source = item.get("source", "unknown")
    penalty = 0.0
    for past_source in recent_sources:
        if source == past_source:
            penalty -= 3.0  # Massive penalty for back-to-back same sources

    return round(max(total + penalty, 0.0), 4)


def rank_items(raw_items: list[dict]) -> list[dict]:
    """
    Score all items, filter noise, apply diversity penalties, sort descending, return top N.
    """
    log.info(f"[Filter] Scoring {len(raw_items)} items …")
    
    recent_sources = get_recent_sources(limit=4)
    if recent_sources:
        log.info(f"[Filter] Recent sources to avoid repeating: {recent_sources}")

    for item in raw_items:
        item["rank_score"] = score_item(item, recent_sources)

    filtered = [i for i in raw_items if i["rank_score"] >= MIN_SCORE_THRESHOLD]
    ranked   = sorted(filtered, key=lambda x: x["rank_score"], reverse=True)
    top      = ranked[:TOP_N_ITEMS]

    log.info(f"[Filter] {len(filtered)} passed threshold → top {len(top)} selected.")
    for i, item in enumerate(top, 1):
        log.debug(f"  #{i} score={item['rank_score']:.2f} | {item['title'][:80]}")

    return top
