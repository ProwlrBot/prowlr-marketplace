# Marketplace REST API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI REST API that serves marketplace listing data with search, filtering, pagination, download tracking, and auto-generated OpenAPI docs.

**Architecture:** FastAPI app in `api/` reads `index.json` into memory on startup, serves it via REST endpoints with weighted full-text search and faceted filtering. SQLite stores download events with per-IP deduplication. Rate limiting via slowapi.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, uvicorn, slowapi, sqlite3 (stdlib), pytest + httpx (testing)

**Spec:** `docs/superpowers/specs/2026-03-17-marketplace-api-design.md`

---

## File Structure

```
api/
├── __init__.py      # Empty, makes api/ a package
├── main.py          # FastAPI app, CORS, lifespan, root router mount
├── config.py        # Settings via env vars (CORS, rate limits, paths)
├── models.py        # Pydantic response models (ListingSummary, ListingDetail, etc.)
├── search.py        # In-memory search engine (full-text, faceted, fuzzy)
├── db.py            # SQLite init, download recording, stats queries
├── routers/
│   ├── __init__.py
│   ├── listings.py  # GET /v1/listings, GET /v1/listings/{id}
│   ├── categories.py # GET /v1/categories
│   └── stats.py     # POST /v1/listings/{id}/download, GET /v1/listings/{id}/stats, GET /v1/health
tests/
├── test_api.py      # All API endpoint tests (TestClient)
├── test_search.py   # Search engine unit tests
├── conftest.py      # Add API fixtures (client, sample index)
```

---

### Task 1: Config + Pydantic Models

**Files:**
- Create: `api/__init__.py`
- Create: `api/config.py`
- Create: `api/models.py`

- [ ] **Step 1: Create api package**

```bash
mkdir -p api/routers
```

- [ ] **Step 2: Write config.py**

```python
# api/config.py
from __future__ import annotations
import os
import json
import pathlib

REPO_ROOT = pathlib.Path(__file__).parent.parent
INDEX_PATH = REPO_ROOT / "index.json"
DB_PATH = REPO_ROOT / "api" / "marketplace.db"

CORS_ORIGINS: list[str] = json.loads(
    os.environ.get("CORS_ORIGINS", '["http://localhost:8080","http://127.0.0.1:8080","http://localhost:3000"]')
)
RATE_LIMIT = os.environ.get("RATE_LIMIT", "100/minute")
```

- [ ] **Step 3: Write models.py with all Pydantic response models**

```python
# api/models.py
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
```

- [ ] **Step 4: Create empty __init__.py files**

Create `api/__init__.py` and `api/routers/__init__.py` (both empty).

- [ ] **Step 5: Commit**

```bash
git add api/
git commit -m "feat(api): add config and Pydantic response models"
```

---

### Task 2: SQLite Database Layer

**Files:**
- Create: `api/db.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: Write failing test for DB init and download recording**

```python
# tests/test_db.py
import sqlite3
import tempfile
import pathlib
import pytest
from api.db import init_db, record_download, get_stats

@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    init_db(path)
    return path

class TestDatabase:
    def test_init_creates_tables(self, db_path):
        conn = sqlite3.connect(db_path)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = {t[0] for t in tables}
        assert "downloads" in table_names
        assert "download_counts" in table_names
        conn.close()

    def test_record_download(self, db_path):
        result = record_download(db_path, "skill-test", "abc123")
        assert result is True  # New download recorded

    def test_record_download_dedup_same_day(self, db_path):
        record_download(db_path, "skill-test", "abc123")
        result = record_download(db_path, "skill-test", "abc123")
        assert result is False  # Duplicate, not counted

    def test_record_download_different_listing(self, db_path):
        record_download(db_path, "skill-test", "abc123")
        result = record_download(db_path, "skill-other", "abc123")
        assert result is True  # Different listing, counted

    def test_get_stats_empty(self, db_path):
        stats = get_stats(db_path, "skill-test")
        assert stats["total_downloads"] == 0
        assert stats["downloads_last_7_days"] == 0
        assert stats["downloads_last_30_days"] == 0

    def test_get_stats_after_download(self, db_path):
        record_download(db_path, "skill-test", "abc123")
        record_download(db_path, "skill-test", "def456")
        stats = get_stats(db_path, "skill-test")
        assert stats["total_downloads"] == 2
        assert stats["downloads_last_7_days"] == 2
        assert stats["downloads_last_30_days"] == 2
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_db.py -v
```

Expected: ImportError — `api.db` does not exist yet.

- [ ] **Step 3: Write db.py implementation**

```python
# api/db.py
from __future__ import annotations
import hashlib
import sqlite3
import pathlib
from datetime import date, datetime, timezone, timedelta

def init_db(db_path: pathlib.Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id TEXT NOT NULL,
            ip_hash TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            download_date TEXT NOT NULL,
            UNIQUE(listing_id, ip_hash, download_date)
        );
        CREATE TABLE IF NOT EXISTS download_counts (
            listing_id TEXT PRIMARY KEY,
            total_count INTEGER DEFAULT 0,
            last_7_days INTEGER DEFAULT 0,
            last_30_days INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_downloads_listing ON downloads(listing_id);
        CREATE INDEX IF NOT EXISTS idx_downloads_date ON downloads(download_date);
    """)
    conn.close()

def hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()[:16]

def record_download(db_path: pathlib.Path, listing_id: str, ip_hash: str) -> bool:
    now = datetime.now(timezone.utc)
    today = now.date().isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO downloads (listing_id, ip_hash, timestamp, download_date) VALUES (?, ?, ?, ?)",
            (listing_id, ip_hash, now.isoformat(), today),
        )
        # Update materialized counts
        _refresh_counts(conn, listing_id)
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Duplicate for this listing+ip+date
        return False
    finally:
        conn.close()

def _refresh_counts(conn: sqlite3.Connection, listing_id: str) -> None:
    today = datetime.now(timezone.utc).date()
    d7 = (today - timedelta(days=7)).isoformat()
    d30 = (today - timedelta(days=30)).isoformat()
    total = conn.execute(
        "SELECT COUNT(*) FROM downloads WHERE listing_id = ?", (listing_id,)
    ).fetchone()[0]
    last_7 = conn.execute(
        "SELECT COUNT(*) FROM downloads WHERE listing_id = ? AND download_date >= ?",
        (listing_id, d7),
    ).fetchone()[0]
    last_30 = conn.execute(
        "SELECT COUNT(*) FROM downloads WHERE listing_id = ? AND download_date >= ?",
        (listing_id, d30),
    ).fetchone()[0]
    conn.execute(
        "INSERT OR REPLACE INTO download_counts (listing_id, total_count, last_7_days, last_30_days) VALUES (?, ?, ?, ?)",
        (listing_id, total, last_7, last_30),
    )

def get_stats(db_path: pathlib.Path, listing_id: str) -> dict:
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT total_count, last_7_days, last_30_days FROM download_counts WHERE listing_id = ?",
        (listing_id,),
    ).fetchone()
    conn.close()
    if row:
        return {"total_downloads": row[0], "downloads_last_7_days": row[1], "downloads_last_30_days": row[2]}
    return {"total_downloads": 0, "downloads_last_7_days": 0, "downloads_last_30_days": 0}

def get_download_counts(db_path: pathlib.Path) -> dict[str, int]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT listing_id, total_count FROM download_counts").fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_db.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add api/db.py tests/test_db.py
git commit -m "feat(api): add SQLite database layer with download tracking and dedup"
```

---

### Task 3: Search Engine

**Files:**
- Create: `api/search.py`
- Create: `tests/test_search.py`

- [ ] **Step 1: Write failing tests for search engine**

```python
# tests/test_search.py
import pytest
from api.search import SearchEngine

SAMPLE_LISTINGS = [
    {"id": "skill-api-tester", "slug": "api-tester", "title": "API Tester", "category": "skills",
     "description": "API endpoint testing and validation", "tags": ["api-testing", "validation"],
     "persona_tags": ["developer"], "difficulty": "intermediate", "pricing_model": "free",
     "version": "1.0.0", "author": "ProwlrBot", "license": "Apache-2.0",
     "path": "skills/api-tester", "manifest": "skills/api-tester/manifest.json"},
    {"id": "agent-prowlr-writer", "slug": "prowlr-writer", "title": "Prowlr Writer", "category": "agents",
     "description": "Content writing and documentation generation", "tags": ["writing", "docs"],
     "persona_tags": ["developer", "business"], "difficulty": "beginner", "pricing_model": "free",
     "version": "1.0.0", "author": "ProwlrBot", "license": "Apache-2.0",
     "path": "agents/prowlr-writer", "manifest": "agents/prowlr-writer/manifest.json"},
    {"id": "workflow-deploy-review", "slug": "deploy-review", "title": "Deploy Review Pipeline", "category": "workflows",
     "description": "Automated code review to deployment pipeline", "tags": ["ci-cd", "deployment"],
     "persona_tags": [], "difficulty": "advanced", "pricing_model": "free",
     "version": "1.0.0", "author": "ProwlrBot", "license": "Apache-2.0",
     "path": "workflows/deploy-review", "manifest": "workflows/deploy-review/manifest.json"},
]

@pytest.fixture
def engine():
    return SearchEngine(SAMPLE_LISTINGS)

class TestFullTextSearch:
    def test_search_by_title(self, engine):
        results = engine.search(q="API Tester")
        assert results[0]["id"] == "skill-api-tester"

    def test_search_by_description(self, engine):
        results = engine.search(q="documentation")
        assert any(r["id"] == "agent-prowlr-writer" for r in results)

    def test_search_by_tag(self, engine):
        results = engine.search(q="ci-cd")
        assert results[0]["id"] == "workflow-deploy-review"

    def test_search_case_insensitive(self, engine):
        results = engine.search(q="api tester")
        assert results[0]["id"] == "skill-api-tester"

    def test_search_prefix_match(self, engine):
        results = engine.search(q="deploy")
        assert any(r["id"] == "workflow-deploy-review" for r in results)

    def test_search_no_results(self, engine):
        results = engine.search(q="nonexistent-xyz-term")
        assert len(results) == 0

class TestFacetedFiltering:
    def test_filter_by_category(self, engine):
        results = engine.search(category="skills")
        assert all(r["category"] == "skills" for r in results)

    def test_filter_by_difficulty(self, engine):
        results = engine.search(difficulty="beginner")
        assert all(r["difficulty"] == "beginner" for r in results)

    def test_filter_by_persona(self, engine):
        results = engine.search(persona="business")
        assert all("business" in r["persona_tags"] for r in results)

    def test_filter_by_tag(self, engine):
        results = engine.search(tags="api-testing")
        assert all("api-testing" in r["tags"] for r in results)

    def test_combined_search_and_filter(self, engine):
        results = engine.search(q="testing", category="skills")
        assert len(results) == 1
        assert results[0]["id"] == "skill-api-tester"

class TestSorting:
    def test_default_sort_alphabetical(self, engine):
        results = engine.search()
        titles = [r["title"] for r in results]
        assert titles == sorted(titles)

    def test_sort_by_title(self, engine):
        results = engine.search(sort="title")
        titles = [r["title"] for r in results]
        assert titles == sorted(titles)

class TestFuzzySearch:
    def test_fuzzy_match_typo(self, engine):
        results = engine.search(q="testor")  # typo for "tester"
        assert any(r["id"] == "skill-api-tester" for r in results)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_search.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write search.py implementation**

```python
# api/search.py
from __future__ import annotations

class SearchEngine:
    def __init__(self, listings: list[dict]) -> None:
        self.listings = listings
        self._build_indexes()

    def _build_indexes(self) -> None:
        self.by_category: dict[str, set[int]] = {}
        self.by_tag: dict[str, set[int]] = {}
        self.by_persona: dict[str, set[int]] = {}
        self.by_difficulty: dict[str, set[int]] = {}
        self.by_pricing: dict[str, set[int]] = {}

        for i, listing in enumerate(self.listings):
            cat = listing.get("category", "")
            self.by_category.setdefault(cat, set()).add(i)

            for tag in listing.get("tags", []):
                self.by_tag.setdefault(tag.lower(), set()).add(i)

            for persona in listing.get("persona_tags", []):
                self.by_persona.setdefault(persona.lower(), set()).add(i)

            diff = listing.get("difficulty", "intermediate")
            self.by_difficulty.setdefault(diff, set()).add(i)

            pricing = listing.get("pricing_model", "free")
            self.by_pricing.setdefault(pricing, set()).add(i)

    def search(
        self,
        q: str | None = None,
        category: str | None = None,
        tags: str | None = None,
        persona: str | None = None,
        difficulty: str | None = None,
        pricing: str | None = None,
        sort: str | None = None,
        download_counts: dict[str, int] | None = None,
    ) -> list[dict]:
        # Start with all indices
        candidates = set(range(len(self.listings)))

        # Apply facet filters
        if category:
            candidates &= self.by_category.get(category, set())
        if tags:
            for tag in tags.split(","):
                candidates &= self.by_tag.get(tag.strip().lower(), set())
        if persona:
            candidates &= self.by_persona.get(persona.lower(), set())
        if difficulty:
            candidates &= self.by_difficulty.get(difficulty, set())
        if pricing:
            candidates &= self.by_pricing.get(pricing, set())

        # Score and filter by text search
        if q:
            scored = []
            for i in candidates:
                score = self._score(self.listings[i], q)
                if score > 0:
                    scored.append((i, score))
            # Sort by score descending if relevance sort
            effective_sort = sort or "relevance"
            if effective_sort == "relevance":
                scored.sort(key=lambda x: (-x[1], self.listings[x[0]]["title"]))
                return [self.listings[i] for i, _ in scored]
            results = [self.listings[i] for i, _ in scored]
        else:
            results = [self.listings[i] for i in candidates]

        # Apply sorting
        effective_sort = sort or "title"
        if q and not sort:
            # Already sorted by relevance above
            pass
        elif effective_sort == "title":
            results.sort(key=lambda x: x["title"].lower())
        elif effective_sort == "popular":
            counts = download_counts or {}
            results.sort(key=lambda x: (-counts.get(x["id"], 0), x["title"].lower()))

        return results

    def _score(self, listing: dict, query: str) -> float:
        query_lower = query.lower()
        tokens = query_lower.split()
        score = 0.0

        title_lower = listing.get("title", "").lower()
        desc_lower = listing.get("description", "").lower()
        tags = [t.lower() for t in listing.get("tags", [])]

        for token in tokens:
            # Exact and prefix matching
            if token in title_lower:
                score += 3.0
            elif self._fuzzy_match(token, title_lower.split()):
                score += 1.5

            if token in desc_lower:
                score += 1.0

            for tag in tags:
                if token in tag:
                    score += 2.0
                    break
            else:
                # Fuzzy match on tags
                if self._fuzzy_match(token, tags):
                    score += 1.0

        return score

    def _fuzzy_match(self, token: str, words: list[str]) -> bool:
        for word in words:
            if self._levenshtein(token, word) <= 2:
                return True
        return False

    @staticmethod
    def _levenshtein(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return SearchEngine._levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        prev_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row
        return prev_row[-1]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_search.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add api/search.py tests/test_search.py
git commit -m "feat(api): add in-memory search engine with full-text, faceted, and fuzzy search"
```

---

### Task 4: FastAPI App + Health Endpoint

**Files:**
- Create: `api/main.py`
- Create: `api/routers/__init__.py`
- Create: `api/routers/stats.py`

- [ ] **Step 1: Add API fixtures to conftest.py**

Add to `tests/conftest.py`:

```python
from fastapi.testclient import TestClient
from api.main import create_app

@pytest.fixture
def api_app(tmp_path):
    """Create a FastAPI app loaded with real index.json data."""
    app = create_app(index_path=REPO_ROOT / "index.json", db_path=tmp_path / "test.db")
    return app

@pytest.fixture
def client(api_app):
    """TestClient for API endpoint tests."""
    return TestClient(api_app)
```

- [ ] **Step 2: Write failing tests for health, download, and stats endpoints**

```python
# tests/test_api.py (start of file)
import pytest

class TestHealth:
    def test_health_returns_200(self, client):
        resp = client.get("/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["total_listings"] >= 0

class TestDownloads:
    def test_record_download(self, client):
        resp = client.get("/v1/listings?per_page=1")
        listing_id = resp.json()["listings"][0]["id"]
        resp = client.post(f"/v1/listings/{listing_id}/download")
        assert resp.status_code == 200
        assert resp.json()["recorded"] is True

    def test_download_nonexistent_listing(self, client):
        resp = client.post("/v1/listings/nonexistent-xyz/download")
        assert resp.status_code == 404

    def test_download_dedup(self, client):
        resp = client.get("/v1/listings?per_page=1")
        listing_id = resp.json()["listings"][0]["id"]
        client.post(f"/v1/listings/{listing_id}/download")
        resp = client.post(f"/v1/listings/{listing_id}/download")
        assert resp.json()["recorded"] is False

class TestStats:
    def test_stats_empty(self, client):
        resp = client.get("/v1/listings?per_page=1")
        listing_id = resp.json()["listings"][0]["id"]
        resp = client.get(f"/v1/listings/{listing_id}/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_downloads"] == 0

    def test_stats_after_download(self, client):
        resp = client.get("/v1/listings?per_page=1")
        listing_id = resp.json()["listings"][0]["id"]
        client.post(f"/v1/listings/{listing_id}/download")
        resp = client.get(f"/v1/listings/{listing_id}/stats")
        data = resp.json()
        assert data["total_downloads"] == 1
        assert data["downloads_last_7_days"] == 1

    def test_stats_nonexistent_listing(self, client):
        resp = client.get("/v1/listings/nonexistent-xyz/stats")
        assert resp.status_code == 404
```

Note: TestDownloads and TestStats tests will initially fail (404 on /listings endpoint needed to get IDs). They will pass once Task 6 (listings router) is implemented. This is acceptable — they verify the stats router endpoints from Task 4.

- [ ] **Step 3: Run test to verify it fails**

```bash
pytest tests/test_api.py::TestHealth -v
```

- [ ] **Step 4: Write main.py with app factory and lifespan**

```python
# api/main.py
from __future__ import annotations

import json
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.config import INDEX_PATH, DB_PATH, CORS_ORIGINS, RATE_LIMIT
from api.db import init_db
from api.search import SearchEngine
from api.routers import listings, categories, stats

limiter = Limiter(key_func=get_remote_address, default_limits=[RATE_LIMIT])

def load_index(index_path: pathlib.Path) -> dict:
    data = json.loads(index_path.read_text(encoding="utf-8"))
    return data

def create_app(
    index_path: pathlib.Path | None = None,
    db_path: pathlib.Path | None = None,
) -> FastAPI:
    idx_path = index_path or INDEX_PATH
    database_path = db_path or DB_PATH

    app = FastAPI(
        title="ProwlrBot Marketplace API",
        description="REST API for the ProwlrBot marketplace registry",
        version="1.0.0",
    )

    # State
    if idx_path and idx_path.exists():
        index_data = load_index(idx_path)
        app.state.listings = index_data.get("listings", [])
        app.state.index_meta = {
            "version": index_data.get("version", "1"),
            "total": index_data.get("total", 0),
            "categories": index_data.get("categories", {}),
        }
    else:
        app.state.listings = []
        app.state.index_meta = {"version": "1", "total": 0, "categories": {}}

    app.state.search_engine = SearchEngine(app.state.listings)
    app.state.db_path = database_path

    # Init DB
    init_db(database_path)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Routers
    app.include_router(listings.router, prefix="/v1")
    app.include_router(categories.router, prefix="/v1")
    app.include_router(stats.router, prefix="/v1")

    return app

# Default app instance for uvicorn
app = create_app()
```

- [ ] **Step 5: Write stats router with health endpoint**

```python
# api/routers/stats.py
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
    # Verify listing exists
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
```

- [ ] **Step 6: Create empty routers for listings and categories (stubs)**

```python
# api/routers/listings.py
from fastapi import APIRouter
router = APIRouter()

# api/routers/categories.py
from fastapi import APIRouter
router = APIRouter()
```

- [ ] **Step 7: Run test to verify it passes**

```bash
pytest tests/test_api.py::TestHealth -v
```

- [ ] **Step 8: Commit**

```bash
git add api/ tests/test_api.py
git commit -m "feat(api): add FastAPI app with health endpoint, CORS, and rate limiting"
```

---

### Task 5: Categories Endpoint

**Files:**
- Modify: `api/routers/categories.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_api.py`:

```python
class TestCategories:
    def test_categories_returns_list(self, client):
        resp = client.get("/v1/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)

    def test_categories_have_counts(self, client):
        resp = client.get("/v1/categories")
        data = resp.json()
        for cat in data["categories"]:
            assert "id" in cat
            assert "name" in cat
            assert "count" in cat
            assert isinstance(cat["count"], int)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_api.py::TestCategories -v
```

- [ ] **Step 3: Implement categories router**

```python
# api/routers/categories.py
from __future__ import annotations
from fastapi import APIRouter, Request
from api.models import CategoriesResponse, CategoryCount

router = APIRouter()

CATEGORY_NAMES = {
    "skills": "Skills",
    "agents": "Agents",
    "prompts": "Prompts",
    "mcp-servers": "MCP Servers",
    "themes": "Themes",
    "workflows": "Workflows",
    "specs": "Specs",
}

@router.get("/categories", response_model=CategoriesResponse)
async def list_categories(request: Request):
    counts = request.app.state.index_meta.get("categories", {})
    categories = [
        CategoryCount(id=cat_id, name=CATEGORY_NAMES.get(cat_id, cat_id), count=count)
        for cat_id, count in sorted(counts.items())
    ]
    return CategoriesResponse(categories=categories)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_api.py::TestCategories -v
```

- [ ] **Step 5: Commit**

```bash
git add api/routers/categories.py tests/test_api.py
git commit -m "feat(api): add categories endpoint with listing counts"
```

---

### Task 6: Listings Search Endpoint

**Files:**
- Modify: `api/routers/listings.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Write failing tests for listings endpoint**

Add to `tests/test_api.py`:

```python
class TestListings:
    def test_listings_returns_paginated(self, client):
        resp = client.get("/v1/listings")
        assert resp.status_code == 200
        data = resp.json()
        assert "listings" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "pages" in data

    def test_listings_default_pagination(self, client):
        resp = client.get("/v1/listings")
        data = resp.json()
        assert data["page"] == 1
        assert data["per_page"] == 20
        assert len(data["listings"]) <= 20

    def test_listings_custom_page_size(self, client):
        resp = client.get("/v1/listings?per_page=5")
        data = resp.json()
        assert data["per_page"] == 5
        assert len(data["listings"]) <= 5

    def test_listings_per_page_over_100_returns_400(self, client):
        resp = client.get("/v1/listings?per_page=101")
        assert resp.status_code == 400

    def test_listings_filter_by_category(self, client):
        resp = client.get("/v1/listings?category=skills")
        data = resp.json()
        for listing in data["listings"]:
            assert listing["category"] == "skills"

    def test_listings_search_by_query(self, client):
        resp = client.get("/v1/listings?q=API")
        data = resp.json()
        assert data["total"] > 0

    def test_listings_default_sort_title(self, client):
        resp = client.get("/v1/listings?per_page=100")
        data = resp.json()
        titles = [l["title"] for l in data["listings"]]
        assert titles == sorted(titles, key=str.lower)

    def test_listings_sort_popular(self, client):
        resp = client.get("/v1/listings?sort=popular")
        assert resp.status_code == 200

    def test_listings_includes_all_fields(self, client):
        resp = client.get("/v1/listings?per_page=1")
        data = resp.json()
        listing = data["listings"][0]
        assert "id" in listing
        assert "slug" in listing
        assert "title" in listing
        assert "category" in listing
        assert "path" in listing
        assert "manifest" in listing

    def test_listings_invalid_sort_returns_400(self, client):
        resp = client.get("/v1/listings?sort=invalid")
        assert resp.status_code == 400

class TestListingDetail:
    def test_get_existing_listing(self, client):
        resp = client.get("/v1/listings?per_page=1")
        listing_id = resp.json()["listings"][0]["id"]
        resp = client.get(f"/v1/listings/{listing_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == listing_id
        assert "manifest_data" in data

    def test_get_nonexistent_listing(self, client):
        resp = client.get("/v1/listings/nonexistent-listing-xyz")
        assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_api.py::TestListings -v
```

- [ ] **Step 3: Implement listings router**

```python
# api/routers/listings.py
from __future__ import annotations

import json
import pathlib

from fastapi import APIRouter, Request, HTTPException, Query
from api.models import ListingSummary, ListingDetail, PaginatedListings
from api.db import get_download_counts
import math

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
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )

@router.get("/listings/{listing_id}", response_model=ListingDetail)
async def get_listing(listing_id: str, request: Request):
    listing = next((l for l in request.app.state.listings if l["id"] == listing_id), None)
    if not listing:
        raise HTTPException(status_code=404, detail=f"Listing '{listing_id}' not found")

    # Load full manifest data
    manifest_data = {}
    from api.config import REPO_ROOT
    manifest_path = REPO_ROOT / listing.get("manifest", "")
    if manifest_path.exists():
        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    return ListingDetail(**listing, manifest_data=manifest_data)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_api.py::TestListings -v
```

- [ ] **Step 5: Commit**

```bash
git add api/routers/listings.py tests/test_api.py
git commit -m "feat(api): add listings search endpoint with pagination, filtering, and sorting"
```

---

### Task 7: CORS Test + CI Integration

**Files:**
- Modify: `tests/test_api.py`
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Add CORS test with httpx**

Add to `tests/test_api.py`:

```python
import httpx

class TestCORS:
    def test_cors_allows_configured_origin(self, api_app):
        # TestClient bypasses CORS, so use httpx ASGI transport
        transport = httpx.ASGITransport(app=api_app)
        with httpx.Client(transport=transport, base_url="http://test") as c:
            resp = c.get("/v1/health", headers={"Origin": "http://localhost:8080"})
            assert resp.headers.get("access-control-allow-origin") == "http://localhost:8080"

    def test_cors_blocks_unknown_origin(self, api_app):
        transport = httpx.ASGITransport(app=api_app)
        with httpx.Client(transport=transport, base_url="http://test") as c:
            resp = c.get("/v1/health", headers={"Origin": "http://evil.com"})
            assert "access-control-allow-origin" not in resp.headers
```

- [ ] **Step 2: Update CI to install API dependencies and run all tests**

In `.github/workflows/ci.yml`, update the test job's install step:

```yaml
      - name: Install dependencies
        run: pip install jsonschema pytest pytest-cov fastapi uvicorn slowapi httpx

      - name: Run tests
        run: pytest tests/ -v --cov=scripts --cov=api --cov-report=term-missing
```

- [ ] **Step 3: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests PASS (Phase 1 tests + API tests).

- [ ] **Step 4: Commit**

```bash
git add tests/test_api.py .github/workflows/ci.yml
git commit -m "test(api): add CORS tests and update CI with API dependencies"
```

---

### Task 8: Requirements File + Run Script

**Files:**
- Create: `requirements.txt`
- Modify: `api/main.py` (add `if __name__` block)

- [ ] **Step 1: Create requirements.txt**

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
slowapi>=0.1.9
jsonschema>=4.20.0
pytest>=8.0.0
pytest-cov>=5.0.0
httpx>=0.27.0
```

- [ ] **Step 2: Add run block to main.py**

Append to `api/main.py`:

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
```

- [ ] **Step 3: Verify server starts**

```bash
python api/main.py &
sleep 2
curl http://localhost:8000/v1/health
curl http://localhost:8000/docs
kill %1
```

Expected: Health returns `{"status": "ok", ...}` and /docs returns OpenAPI HTML.

- [ ] **Step 4: Add marketplace.db to .gitignore**

Append to `.gitignore`:

```
api/marketplace.db
```

- [ ] **Step 5: Commit**

```bash
git add requirements.txt api/main.py .gitignore
git commit -m "feat(api): add requirements.txt, run script, and gitignore for DB"
```

---

## Summary

| Task | Component | Tests | Commit |
|------|-----------|-------|--------|
| 1 | Config + Models | — | `feat(api): add config and Pydantic response models` |
| 2 | SQLite DB Layer | 6 | `feat(api): add SQLite database layer` |
| 3 | Search Engine | 13 | `feat(api): add in-memory search engine` |
| 4 | FastAPI App + Health + Stats | 8 | `feat(api): add FastAPI app with health, download, stats endpoints` |
| 5 | Categories | 2 | `feat(api): add categories endpoint` |
| 6 | Listings Search + Detail | 12 | `feat(api): add listings search and detail endpoints` |
| 7 | CORS + CI | 2 | `test(api): add CORS tests and CI update` |
| 8 | Requirements + Run | — | `feat(api): add requirements.txt and run script` |

**Total: 8 tasks, ~43 tests, 8 commits**

## Deferred from automated testing

- **Rate limit 429 response**: Requires mocking the limiter or sending 100+ requests. Verified manually or via integration test.
- **200ms response time**: Verified manually via `time curl`. At 76 listings, in-memory search is sub-millisecond.
