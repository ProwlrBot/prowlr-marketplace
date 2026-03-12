#!/usr/bin/env python3
"""Generate index.json from all manifest.json files in the marketplace.

Run manually:  python3 scripts/build_index.py
Run by CI:     python3 scripts/build_index.py --check  (exit 1 if index is stale)
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).parent.parent
INDEX_PATH = REPO_ROOT / "index.json"

# Directories to exclude from the index
EXCLUDE_DIRS = {"defaults", "templates", "scripts", "docs", ".github"}


def load_manifests() -> list[dict]:
    entries: list[dict] = []
    for manifest_path in sorted(REPO_ROOT.rglob("manifest.json")):
        parts = manifest_path.relative_to(REPO_ROOT).parts
        # Skip excluded top-level dirs
        if parts[0] in EXCLUDE_DIRS:
            continue
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"WARNING: could not parse {manifest_path}: {exc}", file=sys.stderr)
            continue

        category = parts[0]
        slug = parts[1] if len(parts) > 1 else manifest_path.parent.name
        rel_path = str(manifest_path.parent.relative_to(REPO_ROOT))

        # Strip dynamic fields that belong in the backend, not static JSON
        # downloads and rating must NOT be hardcoded — they come from the API
        entry = {
            "id": data.get("id") or f"{category}-{slug}",
            "slug": slug,
            "category": category,
            "title": data.get("title") or data.get("name") or slug,
            "description": (data.get("description") or "")[:200],
            "version": data.get("version", "1.0.0"),
            "author": data.get("author", "ProwlrBot"),
            "pricing_model": data.get("pricing_model", "free"),
            "license": data.get("license", "Apache-2.0"),
            "tags": data.get("tags") or [],
            "persona_tags": data.get("persona_tags") or [],
            "difficulty": data.get("difficulty", "intermediate"),
            "min_prowlrbot_version": data.get("min_prowlrbot_version", "0.1.0"),
            "path": rel_path,
            "manifest": f"{rel_path}/manifest.json",
        }
        entries.append(entry)

    return entries


def build_index(entries: list[dict]) -> dict:
    categories: dict[str, int] = {}
    for e in entries:
        categories[e["category"]] = categories.get(e["category"], 0) + 1

    return {
        "version": "1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(entries),
        "categories": categories,
        "listings": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build marketplace index.json")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with code 1 if index.json is stale (use in CI)",
    )
    args = parser.parse_args()

    entries = load_manifests()
    index = build_index(entries)
    new_content = json.dumps(index, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not INDEX_PATH.exists():
            print("ERROR: index.json does not exist. Run build_index.py to generate it.")
            return 1
        existing = INDEX_PATH.read_text(encoding="utf-8")
        # Compare listings only (ignore generated_at timestamp)
        existing_data = json.loads(existing)
        new_data = json.loads(new_content)
        existing_data.pop("generated_at", None)
        new_data.pop("generated_at", None)
        if existing_data != new_data:
            print("ERROR: index.json is stale. Run scripts/build_index.py and commit the result.")
            return 1
        print(f"OK: index.json is up to date ({len(entries)} listings)")
        return 0

    INDEX_PATH.write_text(new_content, encoding="utf-8")
    print(f"Generated index.json — {len(entries)} listings across {len(index['categories'])} categories:")
    for cat, count in sorted(index["categories"].items()):
        print(f"  {cat}: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
