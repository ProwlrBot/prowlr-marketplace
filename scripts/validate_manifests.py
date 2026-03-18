#!/usr/bin/env python3
"""Validate all manifest.json files against the formal JSON Schema.

Run manually:  python3 scripts/validate_manifests.py
Run by CI:     python3 scripts/validate_manifests.py --strict  (exit 1 on any failure)
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:
    print(
        "ERROR: jsonschema is required. Install it with:\n"
        "  pip install jsonschema",
        file=sys.stderr,
    )
    sys.exit(2)

REPO_ROOT = pathlib.Path(__file__).parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "manifest.schema.json"

# Directories that contain template/example manifests (skip validation)
SKIP_DIRS = {"templates", "scripts", "docs", ".github", ".auto-claude", "defaults"}


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def find_manifests() -> list[pathlib.Path]:
    manifests = []
    for p in sorted(REPO_ROOT.rglob("manifest.json")):
        parts = p.relative_to(REPO_ROOT).parts
        if parts[0] in SKIP_DIRS:
            continue
        # Skip node_modules, .git, etc.
        if any(part.startswith(".") for part in parts):
            continue
        manifests.append(p)
    return manifests


def validate_manifest(
    manifest_path: pathlib.Path,
    validator: Draft202012Validator,
) -> list[str]:
    """Validate a single manifest. Returns list of error messages."""
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Invalid JSON: {exc}"]
    except OSError as exc:
        return [f"Cannot read file: {exc}"]

    errors = []
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"  {path}: {error.message}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate marketplace manifests")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 on any validation failure",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show passing manifests too",
    )
    args = parser.parse_args()

    schema = load_schema()
    validator = Draft202012Validator(schema)

    manifests = find_manifests()
    total = len(manifests)
    failed = 0
    passed = 0

    print(f"Validating {total} manifests against {SCHEMA_PATH.name}...\n")

    for manifest_path in manifests:
        rel = manifest_path.relative_to(REPO_ROOT)
        errors = validate_manifest(manifest_path, validator)

        if errors:
            failed += 1
            print(f"FAIL {rel}")
            for e in errors:
                print(e)
            print()
        else:
            passed += 1
            if args.verbose:
                print(f"OK   {rel}")

    print(f"\nResults: {passed} passed, {failed} failed out of {total} manifests")

    if failed and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
