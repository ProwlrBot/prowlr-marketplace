import sqlite3
import pytest
from api.db import init_db, submit_review, get_reviews, get_rating_summary, get_all_rating_summaries


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    init_db(path)
    return path


class TestReviewDatabase:
    def test_init_creates_review_tables(self, db_path):
        conn = sqlite3.connect(db_path)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = {t[0] for t in tables}
        assert "reviews" in table_names
        assert "rating_summaries" in table_names
        conn.close()

    def test_submit_review(self, db_path):
        result = submit_review(db_path, "skill-test", "user1", 5, "Alice", "Great!", "Loved it")
        assert result["created"] is True

    def test_submit_review_updates_on_duplicate(self, db_path):
        submit_review(db_path, "skill-test", "user1", 5, "Alice", "Great!", "Loved it")
        result = submit_review(db_path, "skill-test", "user1", 3, "Alice", "OK", "Changed my mind")
        assert result.get("updated") is True

    def test_get_reviews_empty(self, db_path):
        data = get_reviews(db_path, "skill-test")
        assert data["total"] == 0
        assert data["reviews"] == []

    def test_get_reviews_after_submit(self, db_path):
        submit_review(db_path, "skill-test", "user1", 5, "Alice", "Great!", "Loved it")
        submit_review(db_path, "skill-test", "user2", 4, "Bob", "Good", "Nice tool")
        data = get_reviews(db_path, "skill-test")
        assert data["total"] == 2
        assert len(data["reviews"]) == 2

    def test_get_reviews_pagination(self, db_path):
        for i in range(15):
            submit_review(db_path, "skill-test", f"user{i}", (i % 5) + 1, f"User {i}")
        data = get_reviews(db_path, "skill-test", page=1, per_page=5)
        assert data["total"] == 15
        assert len(data["reviews"]) == 5
        assert data["pages"] == 3

    def test_rating_summary_empty(self, db_path):
        summary = get_rating_summary(db_path, "skill-test")
        assert summary["average_rating"] == 0
        assert summary["total_reviews"] == 0

    def test_rating_summary_after_reviews(self, db_path):
        submit_review(db_path, "skill-test", "user1", 5)
        submit_review(db_path, "skill-test", "user2", 3)
        summary = get_rating_summary(db_path, "skill-test")
        assert summary["average_rating"] == 4.0
        assert summary["total_reviews"] == 2
        assert summary["distribution"][5] == 1
        assert summary["distribution"][3] == 1

    def test_get_all_rating_summaries(self, db_path):
        submit_review(db_path, "skill-a", "user1", 5)
        submit_review(db_path, "skill-b", "user1", 3)
        summaries = get_all_rating_summaries(db_path)
        assert "skill-a" in summaries
        assert "skill-b" in summaries
        assert summaries["skill-a"]["average_rating"] == 5.0


class TestReviewAPI:
    def test_submit_review(self, client):
        resp = client.get("/v1/listings?per_page=1")
        listing_id = resp.json()["listings"][0]["id"]
        resp = client.post(f"/v1/listings/{listing_id}/reviews", json={
            "rating": 5, "display_name": "Tester", "title": "Excellent", "body": "Works great"
        })
        assert resp.status_code == 200
        assert resp.json()["created"] is True

    def test_submit_review_invalid_rating(self, client):
        resp = client.get("/v1/listings?per_page=1")
        listing_id = resp.json()["listings"][0]["id"]
        resp = client.post(f"/v1/listings/{listing_id}/reviews", json={"rating": 0})
        assert resp.status_code == 400

    def test_submit_review_nonexistent_listing(self, client):
        resp = client.post("/v1/listings/nonexistent-xyz/reviews", json={"rating": 5})
        assert resp.status_code == 404

    def test_get_reviews_empty(self, client):
        resp = client.get("/v1/listings?per_page=1")
        listing_id = resp.json()["listings"][0]["id"]
        resp = client.get(f"/v1/listings/{listing_id}/reviews")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    def test_get_reviews_after_submit(self, client):
        resp = client.get("/v1/listings?per_page=1")
        listing_id = resp.json()["listings"][0]["id"]
        client.post(f"/v1/listings/{listing_id}/reviews", json={
            "rating": 4, "display_name": "Alice", "title": "Good", "body": "Nice"
        })
        resp = client.get(f"/v1/listings/{listing_id}/reviews")
        data = resp.json()
        assert data["total"] == 1
        assert data["reviews"][0]["rating"] == 4
        assert data["reviews"][0]["display_name"] == "Alice"

    def test_get_rating_summary(self, client):
        resp = client.get("/v1/listings?per_page=1")
        listing_id = resp.json()["listings"][0]["id"]
        resp = client.get(f"/v1/listings/{listing_id}/rating")
        assert resp.status_code == 200
        data = resp.json()
        assert "average_rating" in data
        assert "total_reviews" in data
        assert "distribution" in data

    def test_rating_nonexistent_listing(self, client):
        resp = client.get("/v1/listings/nonexistent-xyz/rating")
        assert resp.status_code == 404

    def test_reviews_nonexistent_listing(self, client):
        resp = client.get("/v1/listings/nonexistent-xyz/reviews")
        assert resp.status_code == 404

    def test_bulk_ratings_endpoint(self, client):
        resp = client.get("/v1/ratings/all")
        assert resp.status_code == 200
        assert "ratings" in resp.json()

    def test_review_per_page_limit(self, client):
        resp = client.get("/v1/listings?per_page=1")
        listing_id = resp.json()["listings"][0]["id"]
        resp = client.get(f"/v1/listings/{listing_id}/reviews?per_page=51")
        assert resp.status_code == 400

    def test_review_body_length_limit(self, client):
        resp = client.get("/v1/listings?per_page=1")
        listing_id = resp.json()["listings"][0]["id"]
        resp = client.post(f"/v1/listings/{listing_id}/reviews", json={
            "rating": 5, "body": "x" * 2001
        })
        assert resp.status_code == 400
