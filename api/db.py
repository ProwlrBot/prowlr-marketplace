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
