import json
import pathlib
import pytest
from jsonschema import validate


REPO_ROOT = pathlib.Path(__file__).parent.parent


@pytest.fixture
def schema():
    schema_path = REPO_ROOT / "schemas" / "manifest.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


class TestScreenshotSchema:
    def test_valid_screenshots_field(self, schema):
        manifest = {
            "id": "test-gallery",
            "title": "Test Gallery",
            "description": "A listing with screenshots for testing.",
            "version": "1.0.0",
            "author": "TestBot",
            "category": "skills",
            "tags": ["test"],
            "screenshots": [
                {"src": "screenshots/main.png", "alt": "Main view"},
                {"src": "screenshots/config.png", "alt": "Config panel", "caption": "Configuration options"},
            ],
        }
        validate(instance=manifest, schema=schema)

    def test_screenshots_requires_src_and_alt(self, schema):
        manifest = {
            "id": "test-gallery",
            "title": "Test Gallery",
            "description": "A listing with screenshots for testing.",
            "version": "1.0.0",
            "author": "TestBot",
            "category": "skills",
            "tags": ["test"],
            "screenshots": [
                {"src": "img.png"},  # missing alt
            ],
        }
        with pytest.raises(Exception):
            validate(instance=manifest, schema=schema)

    def test_screenshots_empty_array_valid(self, schema):
        manifest = {
            "id": "test-gallery",
            "title": "Test Gallery",
            "description": "A listing with screenshots for testing.",
            "version": "1.0.0",
            "author": "TestBot",
            "category": "skills",
            "tags": ["test"],
            "screenshots": [],
        }
        validate(instance=manifest, schema=schema)

    def test_screenshots_max_items(self, schema):
        manifest = {
            "id": "test-gallery",
            "title": "Test Gallery",
            "description": "A listing with screenshots for testing.",
            "version": "1.0.0",
            "author": "TestBot",
            "category": "skills",
            "tags": ["test"],
            "screenshots": [
                {"src": f"img{i}.png", "alt": f"Image {i}"} for i in range(11)
            ],
        }
        with pytest.raises(Exception):
            validate(instance=manifest, schema=schema)

    def test_screenshots_with_url_src(self, schema):
        manifest = {
            "id": "test-gallery",
            "title": "Test Gallery",
            "description": "A listing with screenshots for testing.",
            "version": "1.0.0",
            "author": "TestBot",
            "category": "skills",
            "tags": ["test"],
            "screenshots": [
                {"src": "https://example.com/screenshot.png", "alt": "External screenshot"},
            ],
        }
        validate(instance=manifest, schema=schema)


class TestDownloadStatsAPI:
    def test_stats_returns_all_fields(self, client):
        resp = client.get("/v1/listings?per_page=1")
        listing_id = resp.json()["listings"][0]["id"]
        resp = client.get(f"/v1/listings/{listing_id}/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_downloads" in data
        assert "downloads_last_7_days" in data
        assert "downloads_last_30_days" in data

    def test_stats_increment_after_download(self, client):
        resp = client.get("/v1/listings?per_page=1")
        listing_id = resp.json()["listings"][0]["id"]
        # Record a download
        client.post(f"/v1/listings/{listing_id}/download")
        resp = client.get(f"/v1/listings/{listing_id}/stats")
        data = resp.json()
        assert data["total_downloads"] >= 1
        assert data["downloads_last_7_days"] >= 1
        assert data["downloads_last_30_days"] >= 1
