"""Lightweight authentication layer for creator features (F13/F14).

Uses API key-based auth. In production this would be replaced by
a full OAuth2/JWT system (F19), but the interface is the same.

Creators register with a display name and receive an API key.
The API key is passed via X-API-Key header.
"""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
import pathlib
from datetime import datetime, timezone


def init_auth_db(db_path: pathlib.Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS creators (
            creator_id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            email TEXT UNIQUE,
            api_key_hash TEXT NOT NULL,
            stripe_account_id TEXT,
            created_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        );
        CREATE INDEX IF NOT EXISTS idx_creators_email ON creators(email);
        CREATE INDEX IF NOT EXISTS idx_creators_api_key ON creators(api_key_hash);
    """)
    conn.close()


def _hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def register_creator(
    db_path: pathlib.Path,
    display_name: str,
    email: str,
) -> dict:
    """Register a new creator. Returns the API key (shown once)."""
    creator_id = "creator-" + secrets.token_hex(8)
    api_key = "pmk_" + secrets.token_urlsafe(32)
    key_hash = _hash_key(api_key)
    now = datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO creators (creator_id, display_name, email, api_key_hash, created_at) VALUES (?, ?, ?, ?, ?)",
            (creator_id, display_name, email, key_hash, now),
        )
        conn.commit()
        return {"creator_id": creator_id, "api_key": api_key, "registered": True}
    except sqlite3.IntegrityError:
        return {"registered": False, "error": "Email already registered"}
    finally:
        conn.close()


def authenticate(db_path: pathlib.Path, api_key: str) -> dict | None:
    """Authenticate a creator by API key. Returns creator info or None."""
    key_hash = _hash_key(api_key)
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT creator_id, display_name, email, stripe_account_id, is_active FROM creators WHERE api_key_hash = ?",
        (key_hash,),
    ).fetchone()
    conn.close()
    if not row or not row[4]:  # not active
        return None
    return {
        "creator_id": row[0],
        "display_name": row[1],
        "email": row[2],
        "stripe_account_id": row[3],
    }


def get_creator(db_path: pathlib.Path, creator_id: str) -> dict | None:
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT creator_id, display_name, email, stripe_account_id, created_at, is_active FROM creators WHERE creator_id = ?",
        (creator_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "creator_id": row[0], "display_name": row[1], "email": row[2],
        "stripe_account_id": row[3], "created_at": row[4], "is_active": bool(row[5]),
    }


def update_stripe_account(db_path: pathlib.Path, creator_id: str, stripe_account_id: str) -> bool:
    conn = sqlite3.connect(db_path)
    result = conn.execute(
        "UPDATE creators SET stripe_account_id = ? WHERE creator_id = ?",
        (stripe_account_id, creator_id),
    )
    conn.commit()
    affected = result.rowcount
    conn.close()
    return affected > 0
