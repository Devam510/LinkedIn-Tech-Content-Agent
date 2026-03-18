"""
utils/db.py — SQLite helpers for the LinkedIn agent.
Handles schema creation, raw_item insertion, and posted_history tracking.
"""
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from utils.logger import log

DB_PATH = Path("data/agent.db")


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't already exist."""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS raw_items (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            title         TEXT    NOT NULL,
            url           TEXT    NOT NULL,
            url_hash      TEXT    UNIQUE,
            title_hash    TEXT    UNIQUE,
            source        TEXT,
            score         INTEGER DEFAULT 0,
            published_at  DATETIME,
            fetched_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
            rank_score    REAL    DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS posted_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id     INTEGER REFERENCES raw_items(id),
            post_text   TEXT    NOT NULL,
            image_path  TEXT,
            posted_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            status      TEXT    DEFAULT 'success'
        );
    """)
    conn.commit()
    conn.close()
    log.info("Database initialised.")


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def is_duplicate(url: str, title: str) -> bool:
    """Return True if this URL or title has been seen before."""
    conn = get_conn()
    row = conn.execute(
        "SELECT 1 FROM raw_items WHERE url_hash = ? OR title_hash = ?",
        (_hash(url), _hash(title)),
    ).fetchone()
    conn.close()
    return row is not None


def insert_item(item: dict) -> int | None:
    """Insert a raw scraped item. Returns new row id, or None if duplicate."""
    if is_duplicate(item["url"], item["title"]):
        return None
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO raw_items (title, url, url_hash, title_hash, source, score, published_at, rank_score)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            item["title"],
            item["url"],
            _hash(item["url"]),
            _hash(item["title"]),
            item.get("source", "unknown"),
            item.get("score", 0),
            item.get("published_at"),
            item.get("rank_score", 0.0),
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def already_posted(url: str) -> bool:
    """Return True if this URL has already been published to LinkedIn."""
    conn = get_conn()
    row = conn.execute(
        """SELECT 1 FROM posted_history ph
           JOIN raw_items ri ON ph.item_id = ri.id
           WHERE ri.url = ? AND ph.status = 'success'""",
        (url,),
    ).fetchone()
    conn.close()
    return row is not None


def record_post(item_id: int, post_text: str, image_path: str | None, status: str = "success") -> None:
    """Save a published (or failed) post to history."""
    conn = get_conn()
    conn.execute(
        "INSERT INTO posted_history (item_id, post_text, image_path, status) VALUES (?, ?, ?, ?)",
        (item_id, post_text, image_path, status),
    )
    conn.commit()
    conn.close()
    log.info(f"Post recorded — status={status}, item_id={item_id}")
