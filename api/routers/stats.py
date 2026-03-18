from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException
from api.db import record_download, get_stats, hash_ip
from api.models import StatsResponse, HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health(request: Request):
    return HealthResponse(
        status="ok",
        total_listings=len(request.app.state.listings),
        version=request.app.state.index_meta.get("version", "1"),
    )

@router.post("/listings/{listing_id}/download")
async def record_listing_download(listing_id: str, request: Request):
    listing = next((l for l in request.app.state.listings if l["id"] == listing_id), None)
    if not listing:
        raise HTTPException(status_code=404, detail=f"Listing '{listing_id}' not found")
    ip = request.client.host if request.client else "unknown"
    ip_hashed = hash_ip(ip)
    recorded = record_download(request.app.state.db_path, listing_id, ip_hashed)
    return {"recorded": recorded, "listing_id": listing_id}

@router.get("/listings/{listing_id}/stats", response_model=StatsResponse)
async def listing_stats(listing_id: str, request: Request):
    listing = next((l for l in request.app.state.listings if l["id"] == listing_id), None)
    if not listing:
        raise HTTPException(status_code=404, detail=f"Listing '{listing_id}' not found")
    stats = get_stats(request.app.state.db_path, listing_id)
    return StatsResponse(listing_id=listing_id, **stats)
