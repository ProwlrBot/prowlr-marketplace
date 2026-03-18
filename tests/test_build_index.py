"""Tests for build_index.py — marketplace index generation."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).parent.parent
PYTHON = sys.executable


class TestBuildIndexOutput:
    """Test the generated index.json structure and content."""

    @pytest.fixture(autouse=True)
    def load_index(self):
        """Load the current index.json."""
        index_path = REPO_ROOT / "index.json"
        self.index = json.loads(index_path.read_text(encoding="utf-8"))

    def test_index_has_required_keys(self):
        assert "version" in self.index
        assert "generated_at" in self.index
        assert "total" in self.index
        assert "categories" in self.index
        assert "listings" in self.index

    def test_total_matches_listings_count(self):
        assert self.index["total"] == len(self.index["listings"])

    def test_categories_sum_matches_total(self):
        cat_sum = sum(self.index["categories"].values())
        assert cat_sum == self.index["total"]

    def test_no_external_pseudo_category(self):
        """External listings should be categorized properly, not as 'external'."""
        assert "external" not in self.index["categories"]

    def test_no_consumer_pseudo_category(self):
        """Consumer listings should use their real category, not 'consumer'."""
        assert "consumer" not in self.index["categories"]

    def test_consumer_listings_are_indexed(self):
        """Consumer directory listings should appear in the index."""
        consumer_listings = [l for l in self.index["listings"] if "consumer" in l["path"]]
        assert len(consumer_listings) >= 10, f"Expected >=10 consumer listings, got {len(consumer_listings)}"

    def test_external_listings_are_indexed(self):
        """External directory listings should appear in the index."""
        external_listings = [l for l in self.index["listings"] if "external" in l["path"]]
        assert len(external_listings) >= 16, f"Expected >=16 external listings, got {len(external_listings)}"

    def test_listing_has_required_fields(self):
        """Each listing entry should have all required index fields."""
        required = {"id", "slug", "category", "title", "description", "version",
                    "author", "pricing_model", "license", "tags", "path", "manifest"}
        for listing in self.index["listings"]:
            missing = required - set(listing.keys())
            assert missing == set(), f"Listing {listing.get('id', '?')} missing: {missing}"

    def test_valid_categories_only(self):
        """All listings should have a recognized category."""
        valid = {"skills", "agents", "prompts", "mcp-servers", "themes", "workflows", "specs"}
        for listing in self.index["listings"]:
            assert listing["category"] in valid, f"{listing['id']} has invalid category: {listing['category']}"

    def test_all_listings_have_title(self):
        """Every listing should have a non-empty title."""
        for listing in self.index["listings"]:
            assert listing["title"], f"Listing {listing['id']} has empty title"

    def test_no_duplicate_ids(self):
        """All listing IDs should be unique."""
        ids = [l["id"] for l in self.index["listings"]]
        dupes = [id_ for id_ in ids if ids.count(id_) > 1]
        assert dupes == [], f"Duplicate IDs: {set(dupes)}"

    def test_description_truncated_to_200(self):
        """Descriptions should be truncated to 200 characters."""
        for listing in self.index["listings"]:
            assert len(listing["description"]) <= 200


class TestBuildIndexCheckMode:
    """Test the --check flag for CI."""

    def test_check_passes_when_index_is_current(self):
        """--check should exit 0 when index is up to date."""
        result = subprocess.run(
            [PYTHON, "scripts/build_index.py", "--check"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"--check failed: {result.stdout}\n{result.stderr}"


class TestBuildIndexExcludedDirs:
    """Test that excluded directories are not indexed."""

    @pytest.fixture(autouse=True)
    def load_index(self):
        index_path = REPO_ROOT / "index.json"
        self.index = json.loads(index_path.read_text(encoding="utf-8"))

    def test_templates_not_indexed(self):
        for listing in self.index["listings"]:
            assert "templates" not in listing["path"], f"Template found in index: {listing['path']}"

    def test_defaults_not_indexed(self):
        for listing in self.index["listings"]:
            assert "defaults" not in listing["path"], f"Defaults found in index: {listing['path']}"

    def test_scripts_not_indexed(self):
        for listing in self.index["listings"]:
            assert listing["path"].split("\\")[0] != "scripts"
            assert listing["path"].split("/")[0] != "scripts"

    def test_hidden_dirs_not_indexed(self):
        for listing in self.index["listings"]:
            parts = listing["path"].replace("\\", "/").split("/")
            for part in parts:
                assert not part.startswith("."), f"Hidden dir in index: {listing['path']}"
