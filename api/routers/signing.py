from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException
from api.models import (
    KeyRegistration, SigningRequest, VerificationResponse, SignatureInfo,
)
from api.signing import (
    register_key, revoke_key, get_key, get_author_keys,
    sign_listing, verify_listing, get_signature_info,
)

router = APIRouter()


def _find_listing(request: Request, listing_id: str):
    listing = next((l for l in request.app.state.listings if l["id"] == listing_id), None)
    if not listing:
        raise HTTPException(status_code=404, detail=f"Listing '{listing_id}' not found")
    return listing


@router.post("/signing/keys")
async def register_signing_key(reg: KeyRegistration, request: Request):
    if len(reg.key_id) > 64:
        raise HTTPException(status_code=400, detail="Key ID must be 64 characters or less")
    if len(reg.public_key) > 500:
        raise HTTPException(status_code=400, detail="Public key too large")
    result = register_key(request.app.state.db_path, reg.key_id, reg.author, reg.public_key)
    if not result.get("registered"):
        raise HTTPException(status_code=409, detail=result.get("error", "Registration failed"))
    return result


@router.delete("/signing/keys/{key_id}")
async def revoke_signing_key(key_id: str, request: Request):
    result = revoke_key(request.app.state.db_path, key_id)
    if not result.get("revoked"):
        raise HTTPException(status_code=404, detail=result.get("error", "Key not found"))
    return result


@router.get("/signing/keys/{key_id}")
async def get_signing_key(key_id: str, request: Request):
    key = get_key(request.app.state.db_path, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    return key


@router.get("/signing/authors/{author}/keys")
async def list_author_keys(author: str, request: Request):
    keys = get_author_keys(request.app.state.db_path, author)
    return {"author": author, "keys": keys}


@router.post("/listings/{listing_id}/sign")
async def sign_listing_endpoint(listing_id: str, req: SigningRequest, request: Request):
    _find_listing(request, listing_id)
    result = sign_listing(
        request.app.state.db_path, listing_id,
        req.key_id, req.signature, req.manifest_data,
    )
    if not result.get("signed"):
        raise HTTPException(status_code=400, detail=result.get("error", "Signing failed"))
    return result


@router.get("/listings/{listing_id}/verify")
async def verify_listing_endpoint(listing_id: str, request: Request):
    listing = _find_listing(request, listing_id)
    # Load manifest for verification
    from api.config import REPO_ROOT
    import json
    manifest_data = {}
    manifest_path = REPO_ROOT / listing.get("manifest", "")
    if manifest_path.exists():
        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    result = verify_listing(request.app.state.db_path, listing_id, manifest_data)
    return VerificationResponse(listing_id=listing_id, **result)


@router.get("/listings/{listing_id}/signature")
async def get_listing_signature(listing_id: str, request: Request):
    _find_listing(request, listing_id)
    info = get_signature_info(request.app.state.db_path, listing_id)
    if not info:
        raise HTTPException(status_code=404, detail="No signature found for this listing")
    return SignatureInfo(**info)
