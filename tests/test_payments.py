import pytest
from api.db import init_db
from api.auth import init_auth_db, register_creator
from api.payments import (
    init_payments_db, set_listing_price, get_listing_price,
    process_purchase, get_creator_earnings, get_creator_purchases,
    has_purchased, PRICING_TIERS, MARKETPLACE_FEE_RATE,
)


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    init_db(path)
    init_auth_db(path)
    init_payments_db(path)
    return path


class TestPricingTiers:
    def test_valid_tiers(self):
        assert "free" in PRICING_TIERS
        assert "$5" in PRICING_TIERS
        assert "$15" in PRICING_TIERS
        assert "$29" in PRICING_TIERS

    def test_fee_rate(self):
        assert MARKETPLACE_FEE_RATE == 0.30


class TestListingPricing:
    def test_set_price(self, db_path):
        result = set_listing_price(db_path, "test-listing", "creator-1", "$5")
        assert result["tier"] == "$5"
        assert result["price_cents"] == 500
        assert result["creator_payout_cents"] == 350
        assert result["marketplace_fee_cents"] == 150

    def test_set_price_invalid_tier(self, db_path):
        result = set_listing_price(db_path, "test", "creator-1", "$99")
        assert "error" in result

    def test_get_price_default_free(self, db_path):
        price = get_listing_price(db_path, "nonexistent")
        assert price["tier"] == "free"
        assert price["price_cents"] == 0

    def test_get_price_after_set(self, db_path):
        set_listing_price(db_path, "test", "creator-1", "$15")
        price = get_listing_price(db_path, "test")
        assert price["tier"] == "$15"
        assert price["price_cents"] == 1500

    def test_update_price(self, db_path):
        set_listing_price(db_path, "test", "creator-1", "$5")
        set_listing_price(db_path, "test", "creator-1", "$29")
        price = get_listing_price(db_path, "test")
        assert price["tier"] == "$29"


class TestPurchases:
    def test_process_purchase(self, db_path):
        set_listing_price(db_path, "test", "creator-1", "$5")
        result = process_purchase(db_path, "test", "buyer-hash-1")
        assert "purchase_id" in result
        assert result["amount_cents"] == 500
        assert result["creator_payout_cents"] == 350
        assert result["marketplace_fee_cents"] == 150

    def test_purchase_free_listing_error(self, db_path):
        set_listing_price(db_path, "test", "creator-1", "free")
        result = process_purchase(db_path, "test", "buyer-1")
        assert "error" in result

    def test_duplicate_purchase_error(self, db_path):
        set_listing_price(db_path, "test", "creator-1", "$5")
        process_purchase(db_path, "test", "buyer-1")
        result = process_purchase(db_path, "test", "buyer-1")
        assert "error" in result

    def test_has_purchased(self, db_path):
        set_listing_price(db_path, "test", "creator-1", "$5")
        assert has_purchased(db_path, "test", "buyer-1") is False
        process_purchase(db_path, "test", "buyer-1")
        assert has_purchased(db_path, "test", "buyer-1") is True


class TestEarnings:
    def test_empty_earnings(self, db_path):
        earnings = get_creator_earnings(db_path, "creator-1")
        assert earnings["total_sales"] == 0
        assert earnings["total_earnings_cents"] == 0
        assert earnings["balance_cents"] == 0

    def test_earnings_after_sales(self, db_path):
        set_listing_price(db_path, "test", "creator-1", "$5")
        process_purchase(db_path, "test", "buyer-1")
        process_purchase(db_path, "test", "buyer-2")  # Different buyer, succeeds
        earnings = get_creator_earnings(db_path, "creator-1")
        assert earnings["total_sales"] == 2
        assert earnings["total_earnings_cents"] == 700  # 350 * 2
        assert earnings["balance_cents"] == 700

    def test_purchases_list(self, db_path):
        set_listing_price(db_path, "l1", "creator-1", "$5")
        set_listing_price(db_path, "l2", "creator-1", "$15")
        process_purchase(db_path, "l1", "buyer-1")
        process_purchase(db_path, "l2", "buyer-2")
        data = get_creator_purchases(db_path, "creator-1")
        assert data["total"] == 2
        assert len(data["purchases"]) == 2


class TestPaymentsAPI:
    def _register_and_get_key(self, client):
        resp = client.post("/v1/creators/register", json={
            "display_name": "TestCreator", "email": "test@example.com"
        })
        return resp.json()["api_key"]

    def test_pricing_tiers_endpoint(self, client):
        resp = client.get("/v1/pricing/tiers")
        assert resp.status_code == 200
        data = resp.json()
        assert "tiers" in data
        assert "free" in data["tiers"]
        assert data["marketplace_fee_rate"] == 0.30

    def test_set_pricing_requires_auth(self, client):
        resp = client.get("/v1/listings?per_page=1")
        lid = resp.json()["listings"][0]["id"]
        resp = client.put(f"/v1/listings/{lid}/pricing", json={"tier": "$5"})
        assert resp.status_code == 401

    def test_set_and_get_pricing(self, client):
        api_key = self._register_and_get_key(client)
        resp = client.get("/v1/listings?per_page=1")
        lid = resp.json()["listings"][0]["id"]
        resp = client.put(
            f"/v1/listings/{lid}/pricing",
            json={"tier": "$5"},
            headers={"X-API-Key": api_key},
        )
        assert resp.status_code == 200
        resp = client.get(f"/v1/listings/{lid}/pricing")
        assert resp.json()["tier"] == "$5"

    def test_purchase_listing(self, client):
        api_key = self._register_and_get_key(client)
        resp = client.get("/v1/listings?per_page=1")
        lid = resp.json()["listings"][0]["id"]
        client.put(
            f"/v1/listings/{lid}/pricing",
            json={"tier": "$5"},
            headers={"X-API-Key": api_key},
        )
        resp = client.post(f"/v1/listings/{lid}/purchase", json={})
        assert resp.status_code == 200
        assert resp.json()["amount_cents"] == 500

    def test_purchase_duplicate(self, client):
        api_key = self._register_and_get_key(client)
        resp = client.get("/v1/listings?per_page=1")
        lid = resp.json()["listings"][0]["id"]
        client.put(
            f"/v1/listings/{lid}/pricing",
            json={"tier": "$5"},
            headers={"X-API-Key": api_key},
        )
        client.post(f"/v1/listings/{lid}/purchase", json={})
        resp = client.post(f"/v1/listings/{lid}/purchase", json={})
        assert resp.status_code == 409

    def test_check_purchased(self, client):
        resp = client.get("/v1/listings?per_page=1")
        lid = resp.json()["listings"][0]["id"]
        resp = client.get(f"/v1/listings/{lid}/purchased")
        assert resp.status_code == 200
        assert resp.json()["purchased"] is False

    def test_my_earnings(self, client):
        api_key = self._register_and_get_key(client)
        resp = client.get("/v1/creators/me/earnings", headers={"X-API-Key": api_key})
        assert resp.status_code == 200
        assert resp.json()["total_sales"] == 0
