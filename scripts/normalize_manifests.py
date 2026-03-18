#!/usr/bin/env python3
"""Normalize all manifest.json files to use consistent field names and formats.

This migration script:
1. Renames 'name' -> 'title' where 'title' is missing
2. Adds missing 'category' field based on directory structure
3. Adds missing 'pricing_model' field (defaults to 'free')
4. Normalizes tags to lowercase-hyphenated format
5. Reports all changes made

Run: python3 scripts/normalize_manifests.py
Dry run: python3 scripts/normalize_manifests.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).parent.parent

# Skip these directories
SKIP_DIRS = {"defaults", "templates", "scripts", "docs", ".github", ".auto-claude",
             "schemas", "tests", "gallery", "node_modules"}

# Map top-level directories to default categories for external listings
DIR_CATEGORY_DEFAULTS = {
    "skills": "skills",
    "agents": "agents",
    "prompts": "prompts",
    "mcp-servers": "mcp-servers",
    "themes": "themes",
    "workflows": "workflows",
    "consumer": None,   # Use manifest data
    "external": "skills",  # Default for external listings without category
}


def normalize_tag(tag: str) -> str:
    """Normalize a tag to lowercase-hyphenated format."""
    return tag.lower().strip().replace(" ", "-").replace("_", "-")


def infer_category(manifest_path: pathlib.Path, data: dict) -> str | None:
    """Infer the correct category for a manifest."""
    parts = manifest_path.relative_to(REPO_ROOT).parts
    top_dir = parts[0]

    # If the manifest already has a valid category, keep it
    valid_categories = {"skills", "agents", "prompts", "mcp-servers", "themes", "workflows", "specs"}
    if data.get("category") in valid_categories:
        return data["category"]

    # For consumer dir, infer from content
    if top_dir == "consumer":
        # Consumer listings are typically workflows or agents
        if data.get("setup_steps") or data.get("before_after"):
            return "workflows"
        return "agents"

    # Use directory default
    return DIR_CATEGORY_DEFAULTS.get(top_dir, top_dir)


def normalize_manifest(manifest_path: pathlib.Path, dry_run: bool) -> list[str]:
    """Normalize a single manifest. Returns list of changes made."""
    try:
        raw = manifest_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError) as exc:
        return [f"ERROR: {exc}"]

    changes = []

    # 1. Rename 'name' -> 'title'
    if "title" not in data and "name" in data:
        data["title"] = data.pop("name")
        changes.append(f"renamed 'name' -> 'title' (value: {data['title']})")

    # 2. Add missing 'category'
    if "category" not in data or data["category"] not in {
        "skills", "agents", "prompts", "mcp-servers", "themes", "workflows", "specs"
    }:
        new_cat = infer_category(manifest_path, data)
        if new_cat:
            old = data.get("category")
            data["category"] = new_cat
            if old:
                changes.append(f"fixed category: '{old}' -> '{new_cat}'")
            else:
                changes.append(f"added category: '{new_cat}'")

    # 3. Add missing 'pricing_model'
    if "pricing_model" not in data:
        data["pricing_model"] = "free"
        changes.append("added pricing_model: 'free'")

    # 4. Normalize tags
    if "tags" in data:
        normalized = [normalize_tag(t) for t in data["tags"]]
        if normalized != data["tags"]:
            changes.append("normalized tags to lowercase-hyphenated")
            data["tags"] = normalized

    # 5. Normalize persona_tags
    if "persona_tags" in data:
        normalized = [normalize_tag(t) for t in data["persona_tags"]]
        if normalized != data["persona_tags"]:
            changes.append("normalized persona_tags to lowercase-hyphenated")
            data["persona_tags"] = normalized

    # Write back if changes were made
    if changes and not dry_run:
        new_content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        manifest_path.write_text(new_content, encoding="utf-8")

    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize marketplace manifests")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    manifests = []
    for p in sorted(REPO_ROOT.rglob("manifest.json")):
        parts = p.relative_to(REPO_ROOT).parts
        if parts[0] in SKIP_DIRS or parts[0].startswith("."):
            continue
        manifests.append(p)

    total_changes = 0
    files_changed = 0

    mode = "DRY RUN" if args.dry_run else "NORMALIZING"
    print(f"{mode}: Processing {len(manifests)} manifests...\n")

    for manifest_path in manifests:
        rel = manifest_path.relative_to(REPO_ROOT)
        changes = normalize_manifest(manifest_path, args.dry_run)
        if changes:
            files_changed += 1
            total_changes += len(changes)
            print(f"{'WOULD CHANGE' if args.dry_run else 'CHANGED'} {rel}:")
            for c in changes:
                print(f"  - {c}")
            print()

    print(f"\nSummary: {total_changes} changes across {files_changed} files")
    if args.dry_run:
        print("(dry run — no files were modified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
