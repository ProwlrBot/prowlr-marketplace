import pytest
from api.db import init_db
from api.auth import init_auth_db, register_creator
from api.payments import init_payments_db


class TestCreatorRegistration:
    def test_register_creator(self, client):
        resp = client.post("/v1/creators/register", json={
            "display_name": "DashCreator", "email": "dash@example.com"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["registered"] is True
        assert "api_key" in data
        assert data["api_key"].startswith("pmk_")

    def test_register_duplicate_email(self, client):
        client.post("/v1/creators/register", json={
            "display_name": "A", "email": "dup@example.com"
        })
        resp = client.post("/v1/creators/register", json={
            "display_name": "B", "email": "dup@example.com"
        })
        assert resp.status_code == 409

    def test_register_invalid_email(self, client):
        resp = client.post("/v1/creators/register", json={
            "display_name": "Bad", "email": "notemail"
        })
        assert resp.status_code == 400


class TestCreatorProfile:
    def _register(self, client, name="TestBot", email="bot@test.com"):
        resp = client.post("/v1/creators/register", json={
            "display_name": name, "email": email
        })
        return resp.json()["api_key"]

    def test_get_profile(self, client):
        key = self._register(client)
        resp = client.get("/v1/creators/me", headers={"X-API-Key": key})
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "TestBot"
        assert data["is_active"] is True

    def test_profile_requires_auth(self, client):
        resp = client.get("/v1/creators/me")
        assert resp.status_code == 401

    def test_profile_invalid_key(self, client):
        resp = client.get("/v1/creators/me", headers={"X-API-Key": "bad_key"})
        assert resp.status_code == 401


class TestDashboard:
    def _register(self, client):
        resp = client.post("/v1/creators/register", json={
            "display_name": "ProwlrBot", "email": "prowlr@test.com"
        })
        return resp.json()["api_key"]

    def test_dashboard_stats(self, client):
        key = self._register(client)
        resp = client.get("/v1/creators/me/dashboard", headers={"X-API-Key": key})
        assert resp.status_code == 200
        data = resp.json()
        assert "total_listings" in data
        assert "total_downloads" in data
        assert "total_reviews" in data
        assert "average_rating" in data
        assert "total_earnings_cents" in data
        assert "balance_cents" in data
        # ProwlrBot has listings in the index
        assert data["total_listings"] > 0

    def test_my_listings(self, client):
        key = self._register(client)
        resp = client.get("/v1/creators/me/listings", headers={"X-API-Key": key})
        assert resp.status_code == 200
        data = resp.json()
        assert "listings" in data
        assert data["total"] > 0
        listing = data["listings"][0]
        assert "id" in listing
        assert "title" in listing
        assert "downloads" in listing
        assert "tier" in listing

    def test_link_stripe(self, client):
        key = self._register(client)
        resp = client.put(
            "/v1/creators/me/stripe",
            json={"stripe_account_id": "acct_test123"},
            headers={"X-API-Key": key},
        )
        assert resp.status_code == 200
        assert resp.json()["linked"] is True
        # Verify in profile
        resp = client.get("/v1/creators/me", headers={"X-API-Key": key})
        assert resp.json()["stripe_account_id"] == "acct_test123"
