from __future__ import annotations
import hashlib
import sqlite3
import pathlib
from datetime import datetime, timezone, timedelta

def init_db(db_path: pathlib.Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id TEXT NOT NULL,
            ip_hash TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            download_date TEXT NOT NULL,
            UNIQUE(listing_id, ip_hash, download_date)
        );
        CREATE TABLE IF NOT EXISTS download_counts (
            listing_id TEXT PRIMARY KEY,
            total_count INTEGER DEFAULT 0,
            last_7_days INTEGER DEFAULT 0,
            last_30_days INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_downloads_listing ON downloads(listing_id);
        CREATE INDEX IF NOT EXISTS idx_downloads_date ON downloads(download_date);
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id TEXT NOT NULL,
            ip_hash TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            display_name TEXT NOT NULL DEFAULT 'Anonymous',
            title TEXT NOT NULL DEFAULT '',
            body TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            UNIQUE(listing_id, ip_hash)
        );
        CREATE INDEX IF NOT EXISTS idx_reviews_listing ON reviews(listing_id);
        CREATE TABLE IF NOT EXISTS rating_summaries (
            listing_id TEXT PRIMARY KEY,
            average_rating REAL DEFAULT 0,
            total_reviews INTEGER DEFAULT 0,
            rating_1 INTEGER DEFAULT 0,
            rating_2 INTEGER DEFAULT 0,
            rating_3 INTEGER DEFAULT 0,
            rating_4 INTEGER DEFAULT 0,
            rating_5 INTEGER DEFAULT 0
        );
    """)
    conn.close()

def hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()[:16]

def record_download(db_path: pathlib.Path, listing_id: str, ip_hash: str) -> bool:
    now = datetime.now(timezone.utc)
    today = now.date().isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO downloads (listing_id, ip_hash, timestamp, download_date) VALUES (?, ?, ?, ?)",
            (listing_id, ip_hash, now.isoformat(), today),
        )
        _refresh_counts(conn, listing_id)
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def _refresh_counts(conn: sqlite3.Connection, listing_id: str) -> None:
    today = datetime.now(timezone.utc).date()
    d7 = (today - timedelta(days=7)).isoformat()
    d30 = (today - timedelta(days=30)).isoformat()
    total = conn.execute(
        "SELECT COUNT(*) FROM downloads WHERE listing_id = ?", (listing_id,)
    ).fetchone()[0]
    last_7 = conn.execute(
        "SELECT COUNT(*) FROM downloads WHERE listing_id = ? AND download_date >= ?",
        (listing_id, d7),
    ).fetchone()[0]
    last_30 = conn.execute(
        "SELECT COUNT(*) FROM downloads WHERE listing_id = ? AND download_date >= ?",
        (listing_id, d30),
    ).fetchone()[0]
    conn.execute(
        "INSERT OR REPLACE INTO download_counts (listing_id, total_count, last_7_days, last_30_days) VALUES (?, ?, ?, ?)",
        (listing_id, total, last_7, last_30),
    )

def get_stats(db_path: pathlib.Path, listing_id: str) -> dict:
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT total_count, last_7_days, last_30_days FROM download_counts WHERE listing_id = ?",
        (listing_id,),
    ).fetchone()
    conn.close()
    if row:
        return {"total_downloads": row[0], "downloads_last_7_days": row[1], "downloads_last_30_days": row[2]}
    return {"total_downloads": 0, "downloads_last_7_days": 0, "downloads_last_30_days": 0}

def get_download_counts(db_path: pathlib.Path) -> dict[str, int]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT listing_id, total_count FROM download_counts").fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}


# --- Reviews ---

def submit_review(
    db_path: pathlib.Path,
    listing_id: str,
    ip_hash: str,
    rating: int,
    display_name: str = "Anonymous",
    title: str = "",
    body: str = "",
) -> dict:
    now = datetime.now(timezone.utc)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO reviews (listing_id, ip_hash, rating, display_name, title, body, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (listing_id, ip_hash, rating, display_name, title, body, now.isoformat()),
        )
        _refresh_rating_summary(conn, listing_id)
        conn.commit()
        return {"created": True}
    except sqlite3.IntegrityError:
        # User already reviewed — update instead
        conn.execute(
            "UPDATE reviews SET rating = ?, display_name = ?, title = ?, body = ?, created_at = ? WHERE listing_id = ? AND ip_hash = ?",
            (rating, display_name, title, body, now.isoformat(), listing_id, ip_hash),
        )
        _refresh_rating_summary(conn, listing_id)
        conn.commit()
        return {"created": False, "updated": True}
    finally:
        conn.close()


def _refresh_rating_summary(conn: sqlite3.Connection, listing_id: str) -> None:
    row = conn.execute(
        "SELECT COUNT(*), AVG(rating) FROM reviews WHERE listing_id = ?",
        (listing_id,),
    ).fetchone()
    total = row[0] or 0
    avg = round(row[1] or 0, 2)
    buckets = {}
    for i in range(1, 6):
        cnt = conn.execute(
            "SELECT COUNT(*) FROM reviews WHERE listing_id = ? AND rating = ?",
            (listing_id, i),
        ).fetchone()[0]
        buckets[i] = cnt
    conn.execute(
        "INSERT OR REPLACE INTO rating_summaries (listing_id, average_rating, total_reviews, rating_1, rating_2, rating_3, rating_4, rating_5) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (listing_id, avg, total, buckets[1], buckets[2], buckets[3], buckets[4], buckets[5]),
    )


def get_reviews(db_path: pathlib.Path, listing_id: str, page: int = 1, per_page: int = 10) -> dict:
    conn = sqlite3.connect(db_path)
    total = conn.execute(
        "SELECT COUNT(*) FROM reviews WHERE listing_id = ?", (listing_id,)
    ).fetchone()[0]
    offset = (page - 1) * per_page
    rows = conn.execute(
        "SELECT id, rating, display_name, title, body, created_at FROM reviews WHERE listing_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (listing_id, per_page, offset),
    ).fetchall()
    conn.close()
    reviews = [
        {"id": r[0], "rating": r[1], "display_name": r[2], "title": r[3], "body": r[4], "created_at": r[5]}
        for r in rows
    ]
    import math
    return {"reviews": reviews, "total": total, "page": page, "per_page": per_page, "pages": max(1, math.ceil(total / per_page))}


def get_rating_summary(db_path: pathlib.Path, listing_id: str) -> dict:
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT average_rating, total_reviews, rating_1, rating_2, rating_3, rating_4, rating_5 FROM rating_summaries WHERE listing_id = ?",
        (listing_id,),
    ).fetchone()
    conn.close()
    if row:
        return {
            "average_rating": row[0], "total_reviews": row[1],
            "distribution": {1: row[2], 2: row[3], 3: row[4], 4: row[5], 5: row[6]},
        }
    return {"average_rating": 0, "total_reviews": 0, "distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}}


def get_all_rating_summaries(db_path: pathlib.Path) -> dict[str, dict]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT listing_id, average_rating, total_reviews FROM rating_summaries").fetchall()
    conn.close()
    return {r[0]: {"average_rating": r[1], "total_reviews": r[2]} for r in rows}
