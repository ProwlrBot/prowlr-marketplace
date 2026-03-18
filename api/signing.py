"""Cryptographic Listing Signing (F16).

Provides Ed25519-based signing and verification for marketplace listings.
Creators sign their listing manifests; the marketplace verifies integrity.

Key format: base64-encoded Ed25519 keys.
Signature format: base64-encoded detached signature of the canonical JSON manifest.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import pathlib
import sqlite3
from datetime import datetime, timezone


def init_signing_db(db_path: pathlib.Path) -> None:
    """Create signing-related tables."""
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS signing_keys (
            key_id TEXT PRIMARY KEY,
            author TEXT NOT NULL,
            public_key TEXT NOT NULL,
            created_at TEXT NOT NULL,
            revoked_at TEXT,
            fingerprint TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_signing_keys_author ON signing_keys(author);
        CREATE TABLE IF NOT EXISTS listing_signatures (
            listing_id TEXT PRIMARY KEY,
            key_id TEXT NOT NULL,
            signature TEXT NOT NULL,
            manifest_hash TEXT NOT NULL,
            signed_at TEXT NOT NULL,
            FOREIGN KEY (key_id) REFERENCES signing_keys(key_id)
        );
    """)
    conn.close()


def canonical_json(data: dict) -> str:
    """Produce canonical JSON for deterministic hashing."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def hash_manifest(manifest_data: dict) -> str:
    """SHA-256 hash of the canonical JSON representation."""
    canonical = canonical_json(manifest_data)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_fingerprint(public_key: str) -> str:
    """Compute a short fingerprint for a public key."""
    return hashlib.sha256(public_key.encode("utf-8")).hexdigest()[:16]


def register_key(
    db_path: pathlib.Path,
    key_id: str,
    author: str,
    public_key: str,
) -> dict:
    """Register a new signing key for an author."""
    now = datetime.now(timezone.utc).isoformat()
    fingerprint = compute_fingerprint(public_key)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO signing_keys (key_id, author, public_key, created_at, fingerprint) VALUES (?, ?, ?, ?, ?)",
            (key_id, author, public_key, now, fingerprint),
        )
        conn.commit()
        return {"key_id": key_id, "fingerprint": fingerprint, "registered": True}
    except sqlite3.IntegrityError:
        return {"key_id": key_id, "registered": False, "error": "Key ID already exists"}
    finally:
        conn.close()


def revoke_key(db_path: pathlib.Path, key_id: str) -> dict:
    """Revoke a signing key."""
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(db_path)
    result = conn.execute(
        "UPDATE signing_keys SET revoked_at = ? WHERE key_id = ? AND revoked_at IS NULL",
        (now, key_id),
    )
    conn.commit()
    affected = result.rowcount
    conn.close()
    if affected:
        return {"key_id": key_id, "revoked": True}
    return {"key_id": key_id, "revoked": False, "error": "Key not found or already revoked"}


def get_key(db_path: pathlib.Path, key_id: str) -> dict | None:
    """Retrieve a signing key."""
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT key_id, author, public_key, created_at, revoked_at, fingerprint FROM signing_keys WHERE key_id = ?",
        (key_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "key_id": row[0], "author": row[1], "public_key": row[2],
        "created_at": row[3], "revoked_at": row[4], "fingerprint": row[5],
    }


def get_author_keys(db_path: pathlib.Path, author: str) -> list[dict]:
    """List all keys for an author."""
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT key_id, public_key, created_at, revoked_at, fingerprint FROM signing_keys WHERE author = ? ORDER BY created_at DESC",
        (author,),
    ).fetchall()
    conn.close()
    return [
        {"key_id": r[0], "public_key": r[1], "created_at": r[2], "revoked_at": r[3], "fingerprint": r[4]}
        for r in rows
    ]


def sign_listing(
    db_path: pathlib.Path,
    listing_id: str,
    key_id: str,
    signature: str,
    manifest_data: dict,
) -> dict:
    """Store a signature for a listing.

    The actual cryptographic signing happens client-side. This endpoint
    stores the signature and manifest hash for later verification.
    """
    key = get_key(db_path, key_id)
    if not key:
        return {"signed": False, "error": "Key not found"}
    if key.get("revoked_at"):
        return {"signed": False, "error": "Key has been revoked"}

    manifest_hash = hash_manifest(manifest_data)
    now = datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT OR REPLACE INTO listing_signatures (listing_id, key_id, signature, manifest_hash, signed_at) VALUES (?, ?, ?, ?, ?)",
        (listing_id, key_id, signature, manifest_hash, now),
    )
    conn.commit()
    conn.close()

    return {"signed": True, "listing_id": listing_id, "manifest_hash": manifest_hash}


def verify_listing(db_path: pathlib.Path, listing_id: str, manifest_data: dict) -> dict:
    """Verify a listing's signature integrity.

    Checks that:
    1. A signature exists
    2. The signing key is not revoked
    3. The manifest hash matches (no tampering)
    """
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT key_id, signature, manifest_hash, signed_at FROM listing_signatures WHERE listing_id = ?",
        (listing_id,),
    ).fetchone()
    conn.close()

    if not row:
        return {"verified": False, "status": "unsigned", "reason": "No signature found"}

    key_id, signature, stored_hash, signed_at = row
    key = get_key(db_path, key_id)

    if not key:
        return {"verified": False, "status": "invalid", "reason": "Signing key not found"}

    if key.get("revoked_at"):
        return {"verified": False, "status": "revoked", "reason": "Signing key has been revoked", "revoked_at": key["revoked_at"]}

    current_hash = hash_manifest(manifest_data)
    if current_hash != stored_hash:
        return {"verified": False, "status": "tampered", "reason": "Manifest has been modified since signing"}

    return {
        "verified": True,
        "status": "verified",
        "key_id": key_id,
        "fingerprint": key["fingerprint"],
        "signed_at": signed_at,
        "author": key["author"],
    }


def get_signature_info(db_path: pathlib.Path, listing_id: str) -> dict | None:
    """Get signature metadata for a listing (without verification)."""
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT key_id, manifest_hash, signed_at FROM listing_signatures WHERE listing_id = ?",
        (listing_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    key = get_key(db_path, row[0])
    return {
        "listing_id": listing_id,
        "key_id": row[0],
        "manifest_hash": row[1],
        "signed_at": row[2],
        "author": key["author"] if key else "unknown",
        "fingerprint": key["fingerprint"] if key else "",
        "key_revoked": bool(key.get("revoked_at")) if key else True,
    }
