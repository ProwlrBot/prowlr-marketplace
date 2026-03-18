from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException, Query
from api.db import hash_ip, submit_review, get_reviews, get_rating_summary, get_all_rating_summaries
from api.models import ReviewSubmission, PaginatedReviews, ReviewItem, RatingSummary

router = APIRouter()


def _find_listing(request: Request, listing_id: str):
    listing = next((l for l in request.app.state.listings if l["id"] == listing_id), None)
    if not listing:
        raise HTTPException(status_code=404, detail=f"Listing '{listing_id}' not found")
    return listing


@router.post("/listings/{listing_id}/reviews")
async def create_review(listing_id: str, review: ReviewSubmission, request: Request):
    _find_listing(request, listing_id)
    if review.rating < 1 or review.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    if len(review.display_name) > 50:
        raise HTTPException(status_code=400, detail="Display name must be 50 characters or less")
    if len(review.title) > 100:
        raise HTTPException(status_code=400, detail="Title must be 100 characters or less")
    if len(review.body) > 2000:
        raise HTTPException(status_code=400, detail="Body must be 2000 characters or less")
    ip = request.client.host if request.client else "unknown"
    ip_hashed = hash_ip(ip)
    result = submit_review(
        request.app.state.db_path, listing_id, ip_hashed,
        review.rating, review.display_name, review.title, review.body,
    )
    return {"listing_id": listing_id, **result}


@router.get("/listings/{listing_id}/reviews", response_model=PaginatedReviews)
async def list_reviews(
    listing_id: str,
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1),
):
    _find_listing(request, listing_id)
    if per_page > 50:
        raise HTTPException(status_code=400, detail="per_page must be <= 50")
    data = get_reviews(request.app.state.db_path, listing_id, page, per_page)
    return PaginatedReviews(
        listing_id=listing_id,
        reviews=[ReviewItem(**r) for r in data["reviews"]],
        total=data["total"], page=data["page"],
        per_page=data["per_page"], pages=data["pages"],
    )


@router.get("/ratings/all")
async def all_ratings(request: Request):
    summaries = get_all_rating_summaries(request.app.state.db_path)
    return {"ratings": summaries}


@router.get("/listings/{listing_id}/rating", response_model=RatingSummary)
async def listing_rating(listing_id: str, request: Request):
    _find_listing(request, listing_id)
    summary = get_rating_summary(request.app.state.db_path, listing_id)
    return RatingSummary(listing_id=listing_id, **summary)
