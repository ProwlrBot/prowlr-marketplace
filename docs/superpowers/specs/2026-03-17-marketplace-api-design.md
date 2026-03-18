# Marketplace REST API — Design Spec

**Date:** 2026-03-17
**Feature:** Feature 7 (Phase 2: Discovery & Web Presence)
**Status:** Approved

## Overview

A FastAPI-based REST API that serves marketplace data from the git-based registry. Reads static listing data from `index.json` into memory on startup, stores dynamic data (download counts) in SQLite. Provides search, filtering, pagination, and auto-generated OpenAPI documentation.

## Architecture

```
api/
├── main.py          # FastAPI app, CORS, lifespan (loads index.json)
├── routers/
│   ├── listings.py  # /listings, /listings/{id}
│   ├── categories.py # /categories
│   └── stats.py     # /stats (download tracking, health)
├── search.py        # Search engine (full-text, faceted, fuzzy)
├── db.py            # SQLite connection + schema (ratings, downloads)
├── models.py        # Pydantic response models
└── config.py        # Settings (CORS origins, rate limits, DB path)
```

### Data Flow

1. On startup, load `index.json` into memory (~50KB, 76 listings)
2. Static listing data served from memory — sub-millisecond response
3. Dynamic data (download counts) read/written to `api/marketplace.db` (SQLite)
4. `index.json` reloaded on process restart (no live reload endpoint in v1)
5. CORS configured via `CORS_ORIGINS` env var (default: `["http://localhost:8080", "http://127.0.0.1:8080"]`)

## API Endpoints

| Method | Path | Description | Query Params |
|--------|------|-------------|-------------|
| `GET` | `/v1/listings` | Paginated listing search | `q`, `category`, `tags`, `persona`, `difficulty`, `pricing`, `sort`, `page`, `per_page` |
| `GET` | `/v1/listings/{id}` | Full listing detail + manifest | — |
| `GET` | `/v1/categories` | Categories with listing counts | — |
| `GET` | `/v1/health` | Health check | — |
| `POST` | `/v1/listings/{id}/download` | Record download event | — |
| `GET` | `/v1/listings/{id}/stats` | Download count + trends | — |

### Search & Filtering

**Full-text search (`q` param):**
- Tokenize query into words, match against title (3x weight), description (1x), tags (2x)
- Case-insensitive, prefix matching ("contain" matches "container")
- Fuzzy: Levenshtein distance <= 2 for typo tolerance

**Faceted filtering:**
- Pre-built indexes on startup: `by_category`, `by_tag`, `by_persona`, `by_difficulty`, `by_pricing`
- Filters narrow via set intersection before scoring
- Combined: `?q=review&category=skills&difficulty=beginner`

**Sorting:**
- `relevance`: text match score (default when `q` present)
- `title`: alphabetical (default when `q` absent)
- `popular`: by download count from SQLite, tie-break by title alphabetical

Note: `newest` sort deferred from v1 — requires adding `created_at` timestamps to index entries (not currently present).

**Pagination:**
- Default: `page=1`, `per_page=20`, max 100
- `per_page` > 100 returns 400 Bad Request
- Response includes `total`, `page`, `per_page`, `pages`

### Response Format

**Listing summary (in search results):**
```json
{
  "listings": [
    {
      "id": "skill-api-tester",
      "slug": "api-tester",
      "title": "API Tester",
      "category": "skills",
      "description": "...",
      "version": "1.0.0",
      "author": "ProwlrBot",
      "tags": ["api-testing", "load-testing"],
      "persona_tags": ["developer"],
      "pricing_model": "free",
      "difficulty": "intermediate",
      "verified": true,
      "registry": null,
      "source": null,
      "risk_level": null,
      "path": "skills/api-tester",
      "manifest": "skills/api-tester/manifest.json"
    }
  ],
  "total": 76,
  "page": 1,
  "per_page": 20,
  "pages": 4
}
```

**Listing detail (`/v1/listings/{id}`):**
Returns all fields from the search response plus the full manifest data as a nested `manifest_data` object.

**Stats response (`/v1/listings/{id}/stats`):**
```json
{
  "listing_id": "skill-api-tester",
  "total_downloads": 142,
  "downloads_last_7_days": 18,
  "downloads_last_30_days": 61
}
```

### Error Handling

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Bad query parameters (e.g., `per_page=101`, invalid `sort` value) |
| 404 | Listing not found |
| 429 | Rate limited |
| 500 | Internal error |

All errors return: `{"detail": "human-readable message"}`

Startup fails fast if `index.json` missing or malformed.

### Rate Limiting

100 requests/minute per IP via `slowapi`.

### Download Event Deduplication

`POST /v1/listings/{id}/download` enforces a per-listing-per-IP cooldown of 24 hours. If the same IP records a download for the same listing within 24 hours, the request succeeds (200) but does not increment the count. This prevents trivial inflation while keeping the endpoint simple.

The `downloads` table stores: `listing_id`, `timestamp`, `ip_hash`, with a unique constraint on `(listing_id, ip_hash, date)`.

## Data Storage

### Static Data (index.json)
- Loaded into memory on startup
- Contains all 76 listings with normalized fields (including `slug`, `verified`, `registry`, `source`, `risk_level` where present)
- Reloaded on process restart

### Dynamic Data (SQLite)
- `api/marketplace.db`
- Tables:
  - `downloads`: listing_id, timestamp, ip_hash, date (unique on listing_id + ip_hash + date)
  - `download_counts`: listing_id, total_count, last_7_days, last_30_days (materialized view, refreshed on write)
- No ORM — raw `sqlite3` stdlib module

## Dependencies

- `fastapi` — API framework (includes `pydantic` v2)
- `uvicorn[standard]` — ASGI server
- `slowapi` — rate limiting
- `sqlite3` — stdlib, no install needed

## Testing

- `tests/test_api.py` using FastAPI `TestClient`
- 20+ tests covering: all endpoints, search, pagination edge cases, faceted filtering, 404s, download dedup
- CORS tested via `httpx` with explicit `Origin` header (TestClient bypasses CORS middleware)
- Reuses existing `conftest.py` fixtures
- Runs in CI alongside Phase 1 tests

## Not in v1

- `sort=newest` (requires `created_at` field in index entries)
- `GET /v1/tags` endpoint (clients can derive from listing data)
- `POST /admin/reload` (reload via process restart; admin endpoints deferred until auth exists)
- Ratings/reviews write endpoints (Phase 3)
- User authentication (Phase 4)
- Admin dashboard
- WebSocket real-time updates
- Caching layer (not needed at current scale)
- Fuzzy search will need review if catalog grows past ~1,000 listings (Levenshtein is O(n*m*k))

## Acceptance Criteria

- [ ] GET /v1/listings returns paginated results with total count
- [ ] GET /v1/listings?q=search&category=skills filters correctly
- [ ] GET /v1/listings/{id} returns full listing detail including manifest_data
- [ ] GET /v1/categories returns categories with counts
- [ ] GET /v1/health returns 200
- [ ] POST /v1/listings/{id}/download records event with 24h per-IP dedup
- [ ] GET /v1/listings/{id}/stats returns total, 7-day, and 30-day download counts
- [ ] Full-text search finds listings by title, description, tags with weighted scoring
- [ ] Faceted filtering works for category, tags, persona, difficulty, pricing
- [ ] Fuzzy matching handles typos (Levenshtein distance <= 2)
- [ ] Pagination with configurable page size (max 100)
- [ ] GET /v1/listings?per_page=101 returns 400
- [ ] Default sort is `title` (alphabetical) when `q` absent, `relevance` when `q` present
- [ ] `sort=popular` tie-breaks by title alphabetical when counts are equal
- [ ] Rate limiting at 100 req/min per IP
- [ ] Auto-generated OpenAPI docs at /docs
- [ ] CORS allows configured origins (tested with explicit Origin header)
- [ ] Response includes slug, verified, registry, source, risk_level fields
- [ ] 20+ passing tests
- [ ] API responds within 200ms for search queries
