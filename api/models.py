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


class ReviewSubmission(BaseModel):
    rating: int
    display_name: str = "Anonymous"
    title: str = ""
    body: str = ""


class ReviewItem(BaseModel):
    id: int
    rating: int
    display_name: str
    title: str
    body: str
    created_at: str


class PaginatedReviews(BaseModel):
    listing_id: str
    reviews: list[ReviewItem]
    total: int
    page: int
    per_page: int
    pages: int


class RatingSummary(BaseModel):
    listing_id: str
    average_rating: float = 0
    total_reviews: int = 0
    distribution: dict[int, int] = {}


# --- Trust Score (F15) ---

class TrustBreakdown(BaseModel):
    security: float = 0
    community: float = 0
    popularity: float = 0
    author: float = 0
    freshness: float = 0
    metadata: float = 0


class TrustScoreResponse(BaseModel):
    listing_id: str
    total_score: float = 0
    level: str = "minimal"
    breakdown: TrustBreakdown
    max_possible: int = 100


class AuthorReputation(BaseModel):
    author: str
    listing_count: int = 0
    average_rating: float = 0


# --- Signing (F16) ---

class KeyRegistration(BaseModel):
    key_id: str
    author: str
    public_key: str


class SigningRequest(BaseModel):
    key_id: str
    signature: str
    manifest_data: dict


class VerificationResponse(BaseModel):
    listing_id: str
    verified: bool
    status: str
    reason: str = ""
    key_id: str = ""
    fingerprint: str = ""
    signed_at: str = ""
    author: str = ""


class SignatureInfo(BaseModel):
    listing_id: str
    key_id: str
    manifest_hash: str
    signed_at: str
    author: str
    fingerprint: str
    key_revoked: bool = False


# --- Auth ---

class CreatorRegistration(BaseModel):
    display_name: str
    email: str


class CreatorProfile(BaseModel):
    creator_id: str
    display_name: str
    email: str
    stripe_account_id: str | None = None
    created_at: str = ""
    is_active: bool = True


# --- Payments (F13) ---

class PricingUpdate(BaseModel):
    tier: str


class PricingInfo(BaseModel):
    listing_id: str
    tier: str = "free"
    price_cents: int = 0
    currency: str = "usd"
    creator_payout_cents: int = 0
    marketplace_fee_cents: int = 0


class PurchaseRequest(BaseModel):
    stripe_payment_id: str = ""


class PurchaseResponse(BaseModel):
    purchase_id: str = ""
    listing_id: str
    amount_cents: int = 0
    marketplace_fee_cents: int = 0
    creator_payout_cents: int = 0
    status: str = ""


class EarningsSummary(BaseModel):
    creator_id: str
    total_sales: int = 0
    total_revenue_cents: int = 0
    total_earnings_cents: int = 0
    total_paid_out_cents: int = 0
    balance_cents: int = 0


# --- Dashboard (F14) ---

class DashboardStats(BaseModel):
    creator_id: str
    total_listings: int = 0
    total_downloads: int = 0
    total_reviews: int = 0
    average_rating: float = 0
    total_earnings_cents: int = 0
    balance_cents: int = 0
