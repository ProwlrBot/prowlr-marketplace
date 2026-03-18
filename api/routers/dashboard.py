from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException
from api.models import DashboardStats, CreatorRegistration, CreatorProfile
from api.auth import authenticate, register_creator, get_creator, update_stripe_account
from api.db import get_stats, get_rating_summary
from api.payments import get_creator_earnings, get_listing_price

router = APIRouter()


def _get_creator(request: Request):
    api_key = request.headers.get("X-API-Key", "")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    creator = authenticate(request.app.state.db_path, api_key)
    if not creator:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return creator


@router.post("/creators/register")
async def register(reg: CreatorRegistration, request: Request):
    if not reg.email or "@" not in reg.email:
        raise HTTPException(status_code=400, detail="Valid email required")
    if not reg.display_name or len(reg.display_name) > 50:
        raise HTTPException(status_code=400, detail="Display name required (max 50 chars)")
    result = register_creator(request.app.state.db_path, reg.display_name, reg.email)
    if not result.get("registered"):
        raise HTTPException(status_code=409, detail=result.get("error", "Registration failed"))
    return result


@router.get("/creators/me", response_model=CreatorProfile)
async def my_profile(request: Request):
    creator = _get_creator(request)
    full = get_creator(request.app.state.db_path, creator["creator_id"])
    if not full:
        raise HTTPException(status_code=404, detail="Creator not found")
    return CreatorProfile(**full)


@router.put("/creators/me/stripe")
async def link_stripe(request: Request):
    creator = _get_creator(request)
    body = await request.json()
    stripe_id = body.get("stripe_account_id", "")
    if not stripe_id:
        raise HTTPException(status_code=400, detail="stripe_account_id required")
    updated = update_stripe_account(request.app.state.db_path, creator["creator_id"], stripe_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Creator not found")
    return {"linked": True, "stripe_account_id": stripe_id}


@router.get("/creators/me/dashboard", response_model=DashboardStats)
async def dashboard(request: Request):
    creator = _get_creator(request)
    creator_id = creator["creator_id"]
    author_name = creator["display_name"]

    # Find listings by this author
    my_listings = [l for l in request.app.state.listings if l.get("author") == author_name]

    total_downloads = 0
    total_reviews = 0
    rating_sum = 0
    rated_count = 0

    for l in my_listings:
        stats = get_stats(request.app.state.db_path, l["id"])
        total_downloads += stats.get("total_downloads", 0)
        rd = get_rating_summary(request.app.state.db_path, l["id"])
        total_reviews += rd.get("total_reviews", 0)
        if rd.get("total_reviews", 0) > 0:
            rating_sum += rd["average_rating"]
            rated_count += 1

    avg_rating = round(rating_sum / rated_count, 2) if rated_count > 0 else 0

    earnings = get_creator_earnings(request.app.state.db_path, creator_id)

    return DashboardStats(
        creator_id=creator_id,
        total_listings=len(my_listings),
        total_downloads=total_downloads,
        total_reviews=total_reviews,
        average_rating=avg_rating,
        total_earnings_cents=earnings["total_earnings_cents"],
        balance_cents=earnings["balance_cents"],
    )


@router.get("/creators/me/listings")
async def my_listings(request: Request):
    creator = _get_creator(request)
    author_name = creator["display_name"]
    listings = [l for l in request.app.state.listings if l.get("author") == author_name]

    enriched = []
    for l in listings:
        stats = get_stats(request.app.state.db_path, l["id"])
        rd = get_rating_summary(request.app.state.db_path, l["id"])
        pricing = get_listing_price(request.app.state.db_path, l["id"])
        enriched.append({
            "id": l["id"],
            "title": l.get("title", ""),
            "category": l.get("category", ""),
            "version": l.get("version", ""),
            "downloads": stats.get("total_downloads", 0),
            "reviews": rd.get("total_reviews", 0),
            "average_rating": rd.get("average_rating", 0),
            "tier": pricing.get("tier", "free"),
            "price_cents": pricing.get("price_cents", 0),
        })

    return {"listings": enriched, "total": len(enriched)}
