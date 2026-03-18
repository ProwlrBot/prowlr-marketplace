"""Shared test fixtures for the marketplace test suite."""

from __future__ import annotations

import json
import pathlib
import shutil
import tempfile

import pytest

REPO_ROOT = pathlib.Path(__file__).parent.parent

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


@pytest.fixture
def repo_root():
    """Return the repo root path."""
    return REPO_ROOT


@pytest.fixture
def schema():
    """Load the manifest JSON Schema."""
    schema_path = REPO_ROOT / "schemas" / "manifest.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


@pytest.fixture
def tmp_marketplace(tmp_path):
    """Create a temporary marketplace directory structure for testing."""
    # Create minimal structure
    (tmp_path / "skills" / "test-skill").mkdir(parents=True)
    (tmp_path / "agents" / "test-agent").mkdir(parents=True)
    (tmp_path / "consumer" / "test-consumer").mkdir(parents=True)
    (tmp_path / "external" / "test-registry" / "test-external").mkdir(parents=True)
    (tmp_path / "templates").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "schemas").mkdir()
    (tmp_path / "docs").mkdir()

    return tmp_path


@pytest.fixture
def valid_skill_manifest():
    """Return a valid skill manifest dict."""
    return {
        "id": "skill-test",
        "title": "Test Skill",
        "description": "A test skill for validation testing purposes.",
        "version": "1.0.0",
        "author": "TestBot",
        "category": "skills",
        "tags": ["test", "validation"],
        "pricing_model": "free",
        "license": "Apache-2.0",
    }


@pytest.fixture
def valid_agent_manifest():
    """Return a valid agent manifest dict."""
    return {
        "id": "agent-test",
        "title": "Test Agent",
        "description": "A test agent for validation testing purposes.",
        "version": "1.0.0",
        "author": "TestBot",
        "category": "agents",
        "tags": ["test"],
        "pricing_model": "free",
        "license": "Apache-2.0",
    }


@pytest.fixture
def valid_consumer_manifest():
    """Return a valid consumer manifest dict."""
    return {
        "id": "test-consumer",
        "title": "Test Consumer Workflow",
        "description": "A test consumer workflow for testing purposes.",
        "version": "1.0.0",
        "author": "TestBot",
        "category": "workflows",
        "tags": ["test"],
        "pricing_model": "free",
        "license": "Apache-2.0",
        "persona_tags": ["developer"],
        "difficulty": "beginner",
        "setup_time_minutes": 5,
        "before_after": {
            "before": "Before state",
            "after": "After state",
            "time_saved": "1 hr/week",
        },
    }


@pytest.fixture
def valid_mcp_manifest():
    """Return a valid MCP server manifest dict."""
    return {
        "id": "mcp-test",
        "title": "Test MCP Server",
        "description": "A test MCP server for validation testing.",
        "version": "1.0.0",
        "author": "TestBot",
        "category": "mcp-servers",
        "tags": ["test", "mcp"],
        "pricing_model": "free",
        "license": "Apache-2.0",
        "transport": ["stdio"],
        "tools": ["test_tool"],
    }


@pytest.fixture
def valid_external_manifest():
    """Return a valid external manifest dict."""
    return {
        "id": "ext-test",
        "title": "Test External",
        "description": "An external listing for testing purposes.",
        "version": "1.0.0",
        "author": "ExternalBot",
        "category": "skills",
        "tags": ["test"],
        "pricing_model": "free",
        "license": "MIT",
        "registry": "test-registry",
        "source": "https://github.com/example/repo",
        "verified": True,
        "risk_level": "clean",
    }
