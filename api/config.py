from __future__ import annotations
import os
import json
import pathlib

REPO_ROOT = pathlib.Path(__file__).parent.parent
INDEX_PATH = REPO_ROOT / "index.json"
DB_PATH = REPO_ROOT / "api" / "marketplace.db"

CORS_ORIGINS: list[str] = json.loads(
    os.environ.get("CORS_ORIGINS", '["http://localhost:8080","http://127.0.0.1:8080","http://localhost:3000"]')
)
RATE_LIMIT = os.environ.get("RATE_LIMIT", "100/minute")
