import pytest
from api.db import init_db, submit_review, record_download
from api.trust import compute_trust_score, compute_author_stats


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    init_db(path)
    return path


class TestTrustScoreComputation:
    def test_minimal_score_empty_listing(self, db_path):
        listing = {"id": "test-listing", "author": "TestBot", "version": "0.1.0"}
        result = compute_trust_score(listing, db_path)
        assert result["total_score"] >= 0
        assert result["level"] in ("minimal", "low", "fair", "good", "excellent")
        assert result["max_possible"] == 100
        assert "breakdown" in result

    def test_security_score_passed(self, db_path):
        listing = {"id": "test", "author": "Bot", "version": "1.0.0", "security_status": "passed"}
        result = compute_trust_score(listing, db_path)
        assert result["breakdown"]["security"] == 20

    def test_security_score_verified(self, db_path):
        listing = {"id": "test", "author": "Bot", "version": "1.0.0", "security_status": "passed", "verified": True}
        result = compute_trust_score(listing, db_path)
        assert result["breakdown"]["security"] == 25

    def test_community_score_with_reviews(self, db_path):
        listing = {"id": "test", "author": "Bot", "version": "1.0.0"}
        submit_review(db_path, "test", "u1", 5)
        submit_review(db_path, "test", "u2", 5)
        result = compute_trust_score(listing, db_path)
        assert result["breakdown"]["community"] > 0

    def test_popularity_score_with_downloads(self, db_path):
        listing = {"id": "test", "author": "Bot", "version": "1.0.0"}
        for i in range(15):
            record_download(db_path, "test", f"ip{i}")
        result = compute_trust_score(listing, db_path)
        assert result["breakdown"]["popularity"] == 8  # 10-99 range

    def test_metadata_quality(self, db_path):
        listing = {
            "id": "test", "author": "Bot", "version": "1.0.0",
            "description": "A really great listing for testing purposes.",
            "tags": ["test", "quality"],
            "license": "MIT",
            "persona_tags": ["developer"],
            "min_prowlrbot_version": "0.1.0",
        }
        result = compute_trust_score(listing, db_path)
        assert result["breakdown"]["metadata"] == 10

    def test_trust_level_excellent(self, db_path):
        listing = {
            "id": "test", "author": "Bot", "version": "2.0.0",
            "security_status": "passed", "verified": True,
            "description": "A really great listing for testing purposes.",
            "tags": ["test", "quality"],
            "license": "MIT",
            "persona_tags": ["developer"],
            "min_prowlrbot_version": "0.1.0",
        }
        # Add reviews and downloads
        for i in range(12):
            submit_review(db_path, "test", f"u{i}", 5)
            record_download(db_path, "test", f"ip{i}")
        result = compute_trust_score(
            listing, db_path, author_listing_count=5, author_avg_rating=4.5,
        )
        assert result["level"] == "excellent"
        assert result["total_score"] >= 80

    def test_author_score_multiple_listings(self, db_path):
        listing = {"id": "test", "author": "Bot", "version": "1.0.0"}
        result = compute_trust_score(listing, db_path, author_listing_count=5, author_avg_rating=4.5)
        assert result["breakdown"]["author"] == 15

    def test_freshness_major_version(self, db_path):
        listing = {"id": "test", "author": "Bot", "version": "2.3.1"}
        result = compute_trust_score(listing, db_path)
        assert result["breakdown"]["freshness"] == 10


class TestAuthorStats:
    def test_author_with_no_listings(self, db_path):
        stats = compute_author_stats([], db_path, "Nobody")
        assert stats["listing_count"] == 0
        assert stats["average_rating"] == 0

    def test_author_with_listings(self, db_path):
        listings = [
            {"id": "a", "author": "Bot"},
            {"id": "b", "author": "Bot"},
            {"id": "c", "author": "Other"},
        ]
        submit_review(db_path, "a", "u1", 5)
        submit_review(db_path, "b", "u1", 3)
        stats = compute_author_stats(listings, db_path, "Bot")
        assert stats["listing_count"] == 2
        assert stats["average_rating"] == 4.0


class TestTrustAPI:
    def test_listing_trust_score(self, client):
        resp = client.get("/v1/listings?per_page=1")
        listing_id = resp.json()["listings"][0]["id"]
        resp = client.get(f"/v1/listings/{listing_id}/trust")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_score" in data
        assert "level" in data
        assert "breakdown" in data

    def test_trust_nonexistent_listing(self, client):
        resp = client.get("/v1/listings/nonexistent-xyz/trust")
        assert resp.status_code == 404

    def test_bulk_trust_scores(self, client):
        resp = client.get("/v1/trust/all")
        assert resp.status_code == 200
        data = resp.json()
        assert "trust_scores" in data
        assert isinstance(data["trust_scores"], dict)

    def test_author_reputation(self, client):
        resp = client.get("/v1/authors/ProwlrBot/reputation")
        assert resp.status_code == 200
        data = resp.json()
        assert data["author"] == "ProwlrBot"
        assert data["listing_count"] > 0

    def test_author_reputation_not_found(self, client):
        resp = client.get("/v1/authors/NonexistentAuthor999/reputation")
        assert resp.status_code == 404
