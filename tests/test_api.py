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
