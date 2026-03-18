"""Stripe Connect Payment Integration (F13).

Implements the 70/30 revenue split:
  - 70% goes to the creator
  - 30% is the marketplace fee

Pricing tiers: Free, $5, $15, $29

In production, Stripe API calls would be real. This module provides
the data layer and business logic; the actual Stripe integration
is stubbed with clear extension points.
"""

from __future__ import annotations

import sqlite3
import pathlib
import secrets
from datetime import datetime, timezone


MARKETPLACE_FEE_RATE = 0.30  # 30% marketplace fee
PRICING_TIERS = {
    "free": 0,
    "$5": 500,      # cents
    "$15": 1500,
    "$29": 2900,
}


def init_payments_db(db_path: pathlib.Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS listing_pricing (
            listing_id TEXT PRIMARY KEY,
            creator_id TEXT NOT NULL,
            price_cents INTEGER NOT NULL DEFAULT 0,
            tier TEXT NOT NULL DEFAULT 'free',
            currency TEXT NOT NULL DEFAULT 'usd',
            is_active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS purchases (
            purchase_id TEXT PRIMARY KEY,
            listing_id TEXT NOT NULL,
            buyer_ip_hash TEXT NOT NULL,
            creator_id TEXT NOT NULL,
            amount_cents INTEGER NOT NULL,
            marketplace_fee_cents INTEGER NOT NULL,
            creator_payout_cents INTEGER NOT NULL,
            currency TEXT NOT NULL DEFAULT 'usd',
            status TEXT NOT NULL DEFAULT 'completed',
            stripe_payment_id TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(listing_id, buyer_ip_hash)
        );
        CREATE INDEX IF NOT EXISTS idx_purchases_listing ON purchases(listing_id);
        CREATE INDEX IF NOT EXISTS idx_purchases_creator ON purchases(creator_id);
        CREATE TABLE IF NOT EXISTS payouts (
            payout_id TEXT PRIMARY KEY,
            creator_id TEXT NOT NULL,
            amount_cents INTEGER NOT NULL,
            currency TEXT NOT NULL DEFAULT 'usd',
            status TEXT NOT NULL DEFAULT 'pending',
            stripe_payout_id TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_payouts_creator ON payouts(creator_id);
    """)
    conn.close()


def set_listing_price(
    db_path: pathlib.Path,
    listing_id: str,
    creator_id: str,
    tier: str,
) -> dict:
    """Set or update pricing for a listing."""
    if tier not in PRICING_TIERS:
        return {"error": f"Invalid tier '{tier}'. Valid: {', '.join(PRICING_TIERS.keys())}"}
    price_cents = PRICING_TIERS[tier]

    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT OR REPLACE INTO listing_pricing (listing_id, creator_id, price_cents, tier) VALUES (?, ?, ?, ?)",
        (listing_id, creator_id, price_cents, tier),
    )
    conn.commit()
    conn.close()

    return {
        "listing_id": listing_id,
        "tier": tier,
        "price_cents": price_cents,
        "creator_payout_cents": int(price_cents * (1 - MARKETPLACE_FEE_RATE)),
        "marketplace_fee_cents": int(price_cents * MARKETPLACE_FEE_RATE),
    }


def get_listing_price(db_path: pathlib.Path, listing_id: str) -> dict:
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT listing_id, creator_id, price_cents, tier, currency, is_active FROM listing_pricing WHERE listing_id = ?",
        (listing_id,),
    ).fetchone()
    conn.close()
    if not row:
        return {"listing_id": listing_id, "tier": "free", "price_cents": 0, "currency": "usd"}
    return {
        "listing_id": row[0], "creator_id": row[1], "price_cents": row[2],
        "tier": row[3], "currency": row[4], "is_active": bool(row[5]),
    }


def process_purchase(
    db_path: pathlib.Path,
    listing_id: str,
    buyer_ip_hash: str,
    stripe_payment_id: str = "",
) -> dict:
    """Process a purchase. Calculates the 70/30 split."""
    pricing = get_listing_price(db_path, listing_id)
    if pricing["price_cents"] == 0:
        return {"error": "This listing is free"}

    creator_id = pricing.get("creator_id", "")
    amount = pricing["price_cents"]
    fee = int(amount * MARKETPLACE_FEE_RATE)
    payout = amount - fee

    purchase_id = "pur_" + secrets.token_hex(12)
    now = datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO purchases (purchase_id, listing_id, buyer_ip_hash, creator_id, amount_cents, marketplace_fee_cents, creator_payout_cents, currency, stripe_payment_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (purchase_id, listing_id, buyer_ip_hash, creator_id, amount, fee, payout, pricing.get("currency", "usd"), stripe_payment_id, now),
        )
        conn.commit()
        return {
            "purchase_id": purchase_id,
            "listing_id": listing_id,
            "amount_cents": amount,
            "marketplace_fee_cents": fee,
            "creator_payout_cents": payout,
            "status": "completed",
        }
    except sqlite3.IntegrityError:
        return {"error": "Already purchased"}
    finally:
        conn.close()


def get_creator_earnings(db_path: pathlib.Path, creator_id: str) -> dict:
    """Get earnings summary for a creator."""
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(creator_payout_cents), 0), COALESCE(SUM(amount_cents), 0) FROM purchases WHERE creator_id = ? AND status = 'completed'",
        (creator_id,),
    ).fetchone()
    # Payouts
    payout_row = conn.execute(
        "SELECT COALESCE(SUM(amount_cents), 0) FROM payouts WHERE creator_id = ? AND status = 'completed'",
        (creator_id,),
    ).fetchone()
    conn.close()

    total_sales = row[0] or 0
    total_earnings = row[1] or 0
    total_revenue = row[2] or 0
    total_paid_out = payout_row[0] or 0

    return {
        "creator_id": creator_id,
        "total_sales": total_sales,
        "total_revenue_cents": total_revenue,
        "total_earnings_cents": total_earnings,
        "total_paid_out_cents": total_paid_out,
        "balance_cents": total_earnings - total_paid_out,
    }


def get_creator_purchases(db_path: pathlib.Path, creator_id: str, page: int = 1, per_page: int = 20) -> dict:
    """Get paginated purchase history for a creator."""
    import math
    conn = sqlite3.connect(db_path)
    total = conn.execute(
        "SELECT COUNT(*) FROM purchases WHERE creator_id = ?", (creator_id,),
    ).fetchone()[0]
    offset = (page - 1) * per_page
    rows = conn.execute(
        "SELECT purchase_id, listing_id, amount_cents, marketplace_fee_cents, creator_payout_cents, status, created_at FROM purchases WHERE creator_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (creator_id, per_page, offset),
    ).fetchall()
    conn.close()

    purchases = [
        {
            "purchase_id": r[0], "listing_id": r[1], "amount_cents": r[2],
            "marketplace_fee_cents": r[3], "creator_payout_cents": r[4],
            "status": r[5], "created_at": r[6],
        }
        for r in rows
    ]
    return {
        "purchases": purchases, "total": total, "page": page,
        "per_page": per_page, "pages": max(1, math.ceil(total / per_page)),
    }


def has_purchased(db_path: pathlib.Path, listing_id: str, buyer_ip_hash: str) -> bool:
    """Check if a buyer has already purchased a listing."""
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT 1 FROM purchases WHERE listing_id = ? AND buyer_ip_hash = ?",
        (listing_id, buyer_ip_hash),
    ).fetchone()
    conn.close()
    return row is not None
