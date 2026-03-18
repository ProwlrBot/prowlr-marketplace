"""Tests for JSON Schema validation of marketplace manifests."""

from __future__ import annotations

import json
import pathlib

import jsonschema
import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = pathlib.Path(__file__).parent.parent


class TestSchemaStructure:
    """Test the schema itself is valid and well-formed."""

    def test_schema_is_valid_json(self, schema):
        assert isinstance(schema, dict)

    def test_schema_has_required_fields(self, schema):
        assert "required" in schema
        required = schema["required"]
        assert "id" in required
        assert "title" in required
        assert "description" in required
        assert "version" in required
        assert "author" in required
        assert "category" in required

    def test_schema_defines_category_enum(self, schema):
        cat_enum = schema["properties"]["category"]["enum"]
        expected = ["skills", "agents", "prompts", "mcp-servers", "themes", "workflows", "specs"]
        assert cat_enum == expected

    def test_schema_defines_pricing_enum(self, schema):
        pricing_enum = schema["properties"]["pricing_model"]["enum"]
        assert "free" in pricing_enum
        assert "paid" in pricing_enum

    def test_schema_defines_difficulty_enum(self, schema):
        diff_enum = schema["properties"]["difficulty"]["enum"]
        assert set(diff_enum) == {"beginner", "intermediate", "advanced"}


class TestValidManifests:
    """Test that valid manifests pass schema validation."""

    @pytest.fixture
    def validator(self, schema):
        return Draft202012Validator(schema)

    def test_valid_skill(self, validator, valid_skill_manifest):
        errors = list(validator.iter_errors(valid_skill_manifest))
        assert errors == [], f"Valid skill failed: {[e.message for e in errors]}"

    def test_valid_agent(self, validator, valid_agent_manifest):
        errors = list(validator.iter_errors(valid_agent_manifest))
        assert errors == [], f"Valid agent failed: {[e.message for e in errors]}"

    def test_valid_consumer(self, validator, valid_consumer_manifest):
        errors = list(validator.iter_errors(valid_consumer_manifest))
        assert errors == [], f"Valid consumer failed: {[e.message for e in errors]}"

    def test_valid_mcp_server(self, validator, valid_mcp_manifest):
        errors = list(validator.iter_errors(valid_mcp_manifest))
        assert errors == [], f"Valid MCP failed: {[e.message for e in errors]}"

    def test_valid_external(self, validator, valid_external_manifest):
        errors = list(validator.iter_errors(valid_external_manifest))
        assert errors == [], f"Valid external failed: {[e.message for e in errors]}"


class TestInvalidManifests:
    """Test that invalid manifests are rejected."""

    @pytest.fixture
    def validator(self, schema):
        return Draft202012Validator(schema)

    def test_missing_id(self, validator, valid_skill_manifest):
        del valid_skill_manifest["id"]
        errors = list(validator.iter_errors(valid_skill_manifest))
        assert any("'id' is a required property" in e.message for e in errors)

    def test_missing_title(self, validator, valid_skill_manifest):
        del valid_skill_manifest["title"]
        errors = list(validator.iter_errors(valid_skill_manifest))
        assert any("'title' is a required property" in e.message for e in errors)

    def test_missing_description(self, validator, valid_skill_manifest):
        del valid_skill_manifest["description"]
        errors = list(validator.iter_errors(valid_skill_manifest))
        assert any("'description' is a required property" in e.message for e in errors)

    def test_missing_version(self, validator, valid_skill_manifest):
        del valid_skill_manifest["version"]
        errors = list(validator.iter_errors(valid_skill_manifest))
        assert any("'version' is a required property" in e.message for e in errors)

    def test_missing_category(self, validator, valid_skill_manifest):
        del valid_skill_manifest["category"]
        errors = list(validator.iter_errors(valid_skill_manifest))
        assert any("'category' is a required property" in e.message for e in errors)

    def test_invalid_category(self, validator, valid_skill_manifest):
        valid_skill_manifest["category"] = "invalid-category"
        errors = list(validator.iter_errors(valid_skill_manifest))
        assert len(errors) > 0

    def test_invalid_version_format(self, validator, valid_skill_manifest):
        valid_skill_manifest["version"] = "not-a-version"
        errors = list(validator.iter_errors(valid_skill_manifest))
        assert len(errors) > 0

    def test_invalid_id_format(self, validator, valid_skill_manifest):
        valid_skill_manifest["id"] = "UPPERCASE_BAD"
        errors = list(validator.iter_errors(valid_skill_manifest))
        assert len(errors) > 0

    def test_description_too_short(self, validator, valid_skill_manifest):
        valid_skill_manifest["description"] = "Short"
        errors = list(validator.iter_errors(valid_skill_manifest))
        assert len(errors) > 0

    def test_invalid_pricing_model(self, validator, valid_skill_manifest):
        valid_skill_manifest["pricing_model"] = "invalid"
        errors = list(validator.iter_errors(valid_skill_manifest))
        assert len(errors) > 0

    def test_invalid_difficulty(self, validator, valid_skill_manifest):
        valid_skill_manifest["difficulty"] = "expert"
        errors = list(validator.iter_errors(valid_skill_manifest))
        assert len(errors) > 0

    def test_invalid_tag_format(self, validator, valid_skill_manifest):
        valid_skill_manifest["tags"] = ["UPPERCASE", "has spaces"]
        errors = list(validator.iter_errors(valid_skill_manifest))
        assert len(errors) > 0

    def test_invalid_risk_level(self, validator, valid_skill_manifest):
        valid_skill_manifest["risk_level"] = "critical"
        errors = list(validator.iter_errors(valid_skill_manifest))
        assert len(errors) > 0

    def test_invalid_skill_scan_value(self, validator, valid_consumer_manifest):
        valid_consumer_manifest["skill_scan"] = {"automation": 15}  # > 10
        errors = list(validator.iter_errors(valid_consumer_manifest))
        assert len(errors) > 0


class TestAllExistingManifests:
    """Test that ALL existing manifests in the repo pass validation."""

    SKIP_DIRS = {"defaults", "templates", "scripts", "docs", ".github", ".auto-claude",
                 "schemas", "tests", "gallery", "node_modules"}

    @pytest.fixture
    def validator(self, schema):
        return Draft202012Validator(schema)

    def _find_manifests(self):
        manifests = []
        for p in sorted(REPO_ROOT.rglob("manifest.json")):
            parts = p.relative_to(REPO_ROOT).parts
            if parts[0] in self.SKIP_DIRS or parts[0].startswith("."):
                continue
            manifests.append(p)
        return manifests

    def test_all_manifests_pass_schema(self, validator):
        manifests = self._find_manifests()
        assert len(manifests) > 0, "No manifests found"

        failures = []
        for manifest_path in manifests:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            errors = list(validator.iter_errors(data))
            if errors:
                rel = manifest_path.relative_to(REPO_ROOT)
                failure_msgs = [e.message for e in errors]
                failures.append(f"{rel}: {failure_msgs}")

        assert failures == [], f"Manifests with validation errors:\n" + "\n".join(failures)

    def test_all_manifests_have_title_not_name(self):
        """Verify normalization: no manifest should use 'name' without 'title'."""
        manifests = self._find_manifests()
        name_only = []
        for manifest_path in manifests:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            if "name" in data and "title" not in data:
                name_only.append(str(manifest_path.relative_to(REPO_ROOT)))

        assert name_only == [], f"Manifests using 'name' without 'title':\n" + "\n".join(name_only)

    def test_all_manifests_have_valid_category(self):
        """Verify all manifests have a recognized category."""
        valid_cats = {"skills", "agents", "prompts", "mcp-servers", "themes", "workflows", "specs"}
        manifests = self._find_manifests()
        bad = []
        for manifest_path in manifests:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            cat = data.get("category")
            if cat not in valid_cats:
                bad.append(f"{manifest_path.relative_to(REPO_ROOT)}: category={cat}")

        assert bad == [], f"Manifests with invalid category:\n" + "\n".join(bad)

    def test_manifest_count_minimum(self):
        """Ensure we have a healthy number of listings."""
        manifests = self._find_manifests()
        assert len(manifests) >= 60, f"Expected at least 60 manifests, found {len(manifests)}"
