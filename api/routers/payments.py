from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException, Depends
from api.models import (
    PricingUpdate, PricingInfo, PurchaseRequest, PurchaseResponse, EarningsSummary,
)
from api.payments import (
    set_listing_price, get_listing_price, process_purchase,
    get_creator_earnings, get_creator_purchases, has_purchased,
    PRICING_TIERS, MARKETPLACE_FEE_RATE,
)
from api.auth import authenticate
from api.db import hash_ip

router = APIRouter()


def _get_creator(request: Request):
    """Extract and validate creator from API key header."""
    api_key = request.headers.get("X-API-Key", "")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    creator = authenticate(request.app.state.db_path, api_key)
    if not creator:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return creator


def _find_listing(request: Request, listing_id: str):
    listing = next((l for l in request.app.state.listings if l["id"] == listing_id), None)
    if not listing:
        raise HTTPException(status_code=404, detail=f"Listing '{listing_id}' not found")
    return listing


@router.get("/pricing/tiers")
async def list_pricing_tiers():
    return {
        "tiers": {k: {"price_cents": v, "price_display": k} for k, v in PRICING_TIERS.items()},
        "marketplace_fee_rate": MARKETPLACE_FEE_RATE,
    }


@router.put("/listings/{listing_id}/pricing")
async def update_listing_pricing(listing_id: str, pricing: PricingUpdate, request: Request):
    _find_listing(request, listing_id)
    creator = _get_creator(request)
    result = set_listing_price(request.app.state.db_path, listing_id, creator["creator_id"], pricing.tier)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/listings/{listing_id}/pricing")
async def get_pricing(listing_id: str, request: Request):
    _find_listing(request, listing_id)
    pricing = get_listing_price(request.app.state.db_path, listing_id)
    return pricing


@router.post("/listings/{listing_id}/purchase")
async def purchase_listing(listing_id: str, purchase: PurchaseRequest, request: Request):
    _find_listing(request, listing_id)
    ip = request.client.host if request.client else "unknown"
    ip_hashed = hash_ip(ip)

    if has_purchased(request.app.state.db_path, listing_id, ip_hashed):
        raise HTTPException(status_code=409, detail="Already purchased")

    result = process_purchase(
        request.app.state.db_path, listing_id, ip_hashed, purchase.stripe_payment_id,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/listings/{listing_id}/purchased")
async def check_purchased(listing_id: str, request: Request):
    _find_listing(request, listing_id)
    ip = request.client.host if request.client else "unknown"
    ip_hashed = hash_ip(ip)
    purchased = has_purchased(request.app.state.db_path, listing_id, ip_hashed)
    return {"listing_id": listing_id, "purchased": purchased}


@router.get("/creators/me/earnings", response_model=EarningsSummary)
async def my_earnings(request: Request):
    creator = _get_creator(request)
    earnings = get_creator_earnings(request.app.state.db_path, creator["creator_id"])
    return EarningsSummary(**earnings)


@router.get("/creators/me/purchases")
async def my_purchases(request: Request, page: int = 1, per_page: int = 20):
    creator = _get_creator(request)
    if per_page > 50:
        raise HTTPException(status_code=400, detail="per_page must be <= 50")
    data = get_creator_purchases(request.app.state.db_path, creator["creator_id"], page, per_page)
    return data
