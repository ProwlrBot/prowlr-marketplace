from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException
from api.models import TrustScoreResponse, TrustBreakdown, AuthorReputation
from api.trust import compute_trust_score, compute_author_stats

router = APIRouter()


def _find_listing(request: Request, listing_id: str):
    listing = next((l for l in request.app.state.listings if l["id"] == listing_id), None)
    if not listing:
        raise HTTPException(status_code=404, detail=f"Listing '{listing_id}' not found")
    return listing


@router.get("/listings/{listing_id}/trust", response_model=TrustScoreResponse)
async def listing_trust_score(listing_id: str, request: Request):
    listing = _find_listing(request, listing_id)
    author = listing.get("author", "")
    author_stats = compute_author_stats(
        request.app.state.listings, request.app.state.db_path, author,
    )
    result = compute_trust_score(
        listing, request.app.state.db_path,
        author_listing_count=author_stats["listing_count"],
        author_avg_rating=author_stats["average_rating"],
    )
    return TrustScoreResponse(
        listing_id=listing_id,
        total_score=result["total_score"],
        level=result["level"],
        breakdown=TrustBreakdown(**result["breakdown"]),
    )


@router.get("/trust/all")
async def all_trust_scores(request: Request):
    """Bulk trust scores for all listings (for card badges)."""
    results = {}
    # Pre-compute author stats
    author_cache: dict[str, dict] = {}
    for listing in request.app.state.listings:
        author = listing.get("author", "")
        if author not in author_cache:
            author_cache[author] = compute_author_stats(
                request.app.state.listings, request.app.state.db_path, author,
            )
        author_stats = author_cache[author]
        score = compute_trust_score(
            listing, request.app.state.db_path,
            author_listing_count=author_stats["listing_count"],
            author_avg_rating=author_stats["average_rating"],
        )
        results[listing["id"]] = {
            "total_score": score["total_score"],
            "level": score["level"],
        }
    return {"trust_scores": results}


@router.get("/authors/{author}/reputation", response_model=AuthorReputation)
async def author_reputation(author: str, request: Request):
    author_listings = [l for l in request.app.state.listings if l.get("author") == author]
    if not author_listings:
        raise HTTPException(status_code=404, detail=f"Author '{author}' not found")
    stats = compute_author_stats(
        request.app.state.listings, request.app.state.db_path, author,
    )
    return AuthorReputation(**stats)
