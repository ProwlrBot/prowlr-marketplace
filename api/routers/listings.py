from __future__ import annotations
import json
import math
from fastapi import APIRouter, Request, HTTPException, Query
from api.models import ListingSummary, ListingDetail, PaginatedListings
from api.db import get_download_counts

router = APIRouter()

VALID_SORTS = {"relevance", "title", "popular"}

@router.get("/listings", response_model=PaginatedListings)
async def list_listings(
    request: Request,
    q: str | None = None,
    category: str | None = None,
    tags: str | None = None,
    persona: str | None = None,
    difficulty: str | None = None,
    pricing: str | None = None,
    sort: str | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1),
):
    if per_page > 100:
        raise HTTPException(status_code=400, detail="per_page must be <= 100")
    if sort and sort not in VALID_SORTS:
        raise HTTPException(status_code=400, detail=f"Invalid sort: '{sort}'. Valid options: {', '.join(VALID_SORTS)}")

    download_counts = get_download_counts(request.app.state.db_path)
    results = request.app.state.search_engine.search(
        q=q, category=category, tags=tags, persona=persona,
        difficulty=difficulty, pricing=pricing, sort=sort,
        download_counts=download_counts,
    )

    total = len(results)
    pages = max(1, math.ceil(total / per_page))
    start = (page - 1) * per_page
    end = start + per_page
    page_results = results[start:end]

    return PaginatedListings(
        listings=[ListingSummary(**r) for r in page_results],
        total=total, page=page, per_page=per_page, pages=pages,
    )

@router.get("/listings/{listing_id}", response_model=ListingDetail)
async def get_listing(listing_id: str, request: Request):
    listing = next((l for l in request.app.state.listings if l["id"] == listing_id), None)
    if not listing:
        raise HTTPException(status_code=404, detail=f"Listing '{listing_id}' not found")
    manifest_data = {}
    from api.config import REPO_ROOT
    manifest_path = REPO_ROOT / listing.get("manifest", "")
    if manifest_path.exists():
        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return ListingDetail(**listing, manifest_data=manifest_data)
