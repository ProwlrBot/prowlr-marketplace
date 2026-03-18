"""Trust Score Engine (F15).

Computes a transparent trust score (0-100) for each listing based on:
  - Security scan status (0-25 pts)
  - Community ratings    (0-25 pts)
  - Download popularity  (0-15 pts)
  - Author reputation    (0-15 pts)
  - Listing freshness    (0-10 pts)
  - Metadata quality     (0-10 pts)

The algorithm is fully transparent — no hidden weights.
"""

from __future__ import annotations

import pathlib
from datetime import datetime, timezone

from api.db import get_rating_summary, get_stats


def compute_trust_score(
    listing: dict,
    db_path: pathlib.Path,
    author_listing_count: int = 1,
    author_avg_rating: float = 0,
) -> dict:
    """Compute a trust score breakdown for a single listing."""
    scores = {}

    # 1. Security (0-25): based on security_status and verified flag
    sec_status = listing.get("security_status", "unscanned")
    verified = listing.get("verified", False)
    sec_score = 0
    if sec_status == "passed":
        sec_score = 20
    elif sec_status == "issues":
        sec_score = 5
    # unscanned = 0
    if verified:
        sec_score += 5
    scores["security"] = min(25, sec_score)

    # 2. Community ratings (0-25): based on avg rating and review count
    rating_data = get_rating_summary(db_path, listing["id"])
    avg = rating_data.get("average_rating", 0)
    total_reviews = rating_data.get("total_reviews", 0)
    # Scale: avg/5 * 20 + min(review_count, 10)/10 * 5
    rating_score = (avg / 5) * 20 if avg > 0 else 0
    review_bonus = min(total_reviews, 10) / 10 * 5
    scores["community"] = round(min(25, rating_score + review_bonus), 1)

    # 3. Download popularity (0-15): log-scaled downloads
    stats = get_stats(db_path, listing["id"])
    downloads = stats.get("total_downloads", 0)
    if downloads >= 1000:
        dl_score = 15
    elif downloads >= 100:
        dl_score = 12
    elif downloads >= 10:
        dl_score = 8
    elif downloads >= 1:
        dl_score = 4
    else:
        dl_score = 0
    scores["popularity"] = dl_score

    # 4. Author reputation (0-15): based on how many listings they have and their avg rating
    author_score = 0
    if author_listing_count >= 5:
        author_score += 8
    elif author_listing_count >= 3:
        author_score += 5
    elif author_listing_count >= 1:
        author_score += 2
    if author_avg_rating >= 4.0:
        author_score += 7
    elif author_avg_rating >= 3.0:
        author_score += 4
    elif author_avg_rating >= 2.0:
        author_score += 2
    scores["author"] = min(15, author_score)

    # 5. Listing freshness (0-10): based on version number
    version = listing.get("version", "0.0.0")
    parts = version.split(".")
    try:
        major = int(parts[0])
    except (ValueError, IndexError):
        major = 0
    if major >= 2:
        freshness = 10
    elif major >= 1:
        freshness = 7
    else:
        freshness = 3
    scores["freshness"] = freshness

    # 6. Metadata quality (0-10): completeness of listing fields
    quality = 0
    if listing.get("description") and len(listing["description"]) >= 20:
        quality += 2
    if listing.get("tags") and len(listing["tags"]) >= 2:
        quality += 2
    if listing.get("license"):
        quality += 2
    if listing.get("persona_tags") and len(listing["persona_tags"]) >= 1:
        quality += 2
    if listing.get("min_prowlrbot_version"):
        quality += 2
    scores["metadata"] = min(10, quality)

    total = sum(scores.values())
    level = _trust_level(total)

    return {
        "total_score": round(total, 1),
        "level": level,
        "breakdown": scores,
        "max_possible": 100,
    }


def _trust_level(score: float) -> str:
    if score >= 80:
        return "excellent"
    if score >= 60:
        return "good"
    if score >= 40:
        return "fair"
    if score >= 20:
        return "low"
    return "minimal"


def compute_author_stats(
    listings: list[dict],
    db_path: pathlib.Path,
    author: str,
) -> dict:
    """Compute aggregate stats for an author across all their listings."""
    author_listings = [l for l in listings if l.get("author") == author]
    count = len(author_listings)

    total_rating = 0
    rated_count = 0
    for l in author_listings:
        rd = get_rating_summary(db_path, l["id"])
        if rd.get("total_reviews", 0) > 0:
            total_rating += rd["average_rating"]
            rated_count += 1

    avg_rating = total_rating / rated_count if rated_count > 0 else 0

    return {
        "author": author,
        "listing_count": count,
        "average_rating": round(avg_rating, 2),
    }
