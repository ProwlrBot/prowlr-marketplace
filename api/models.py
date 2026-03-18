from __future__ import annotations
from pydantic import BaseModel

class ListingSummary(BaseModel):
    id: str
    slug: str
    title: str
    category: str
    description: str
    version: str
    author: str
    tags: list[str] = []
    persona_tags: list[str] = []
    pricing_model: str = "free"
    difficulty: str = "intermediate"
    license: str = "Apache-2.0"
    min_prowlrbot_version: str = "0.1.0"
    verified: bool | None = None
    registry: str | None = None
    source: str | None = None
    risk_level: str | None = None
    path: str
    manifest: str

class ListingDetail(ListingSummary):
    manifest_data: dict = {}

class PaginatedListings(BaseModel):
    listings: list[ListingSummary]
    total: int
    page: int
    per_page: int
    pages: int

class CategoryCount(BaseModel):
    id: str
    name: str
    count: int

class CategoriesResponse(BaseModel):
    categories: list[CategoryCount]

class StatsResponse(BaseModel):
    listing_id: str
    total_downloads: int = 0
    downloads_last_7_days: int = 0
    downloads_last_30_days: int = 0

class HealthResponse(BaseModel):
    status: str = "ok"
    total_listings: int = 0
    version: str = "1"
