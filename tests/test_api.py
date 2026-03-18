import pytest
import httpx


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


class TestCORS:
    @pytest.mark.asyncio
    async def test_cors_allows_configured_origin(self, api_app):
        transport = httpx.ASGITransport(app=api_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/v1/health", headers={"Origin": "http://localhost:8080"})
            assert resp.headers.get("access-control-allow-origin") == "http://localhost:8080"

    @pytest.mark.asyncio
    async def test_cors_blocks_unknown_origin(self, api_app):
        transport = httpx.ASGITransport(app=api_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/v1/health", headers={"Origin": "http://evil.com"})
            assert "access-control-allow-origin" not in resp.headers
