"""
poster/draft_saver.py — Persist failed/skipped posts to disk for manual review.
"""
import json
from datetime import datetime
from pathlib import Path
from utils.logger import log

DRAFTS_DIR = Path("data/drafts")


def save_draft(post_text: str, item: dict | None = None, reason: str = "unknown") -> str:
    """
    Save a post draft to data/drafts/<timestamp>.json.
    Returns the path to the saved draft file.
    """
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = DRAFTS_DIR / f"draft_{timestamp}.json"

    payload = {
        "saved_at": datetime.now().isoformat(),
        "reason": reason,
        "post_text": post_text,
        "source_item": item or {},
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    log.warning(f"[DraftSaver] Draft saved → {filename}  (reason: {reason})")
    return str(filename)
