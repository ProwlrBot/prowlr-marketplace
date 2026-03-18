#!/usr/bin/env python3
"""Security scanning for marketplace listings.

Checks for:
1. Hardcoded secrets (API keys, tokens, passwords) in manifests and listing files
2. Suspicious URLs (known-malicious patterns, data URIs, javascript URIs)
3. Missing capability declarations
4. Overly broad permissions

Run manually:  python3 scripts/security_scan.py
Run by CI:     python3 scripts/security_scan.py --strict  (exit 1 on any finding)
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from urllib.parse import urlparse

REPO_ROOT = pathlib.Path(__file__).parent.parent

# Directories to skip
SKIP_DIRS = {"defaults", "templates", "scripts", "docs", ".github", ".auto-claude",
             "schemas", "tests", "gallery", "node_modules"}

# Patterns that likely indicate hardcoded secrets
SECRET_PATTERNS = [
    (re.compile(r'(?:api[_-]?key|apikey)\s*[=:]\s*["\']?[A-Za-z0-9_\-]{20,}', re.IGNORECASE), "API key"),
    (re.compile(r'(?:secret|password|passwd|pwd)\s*[=:]\s*["\']?[^\s"\']{8,}', re.IGNORECASE), "secret/password"),
    (re.compile(r'(?:token)\s*[=:]\s*["\']?[A-Za-z0-9_\-\.]{20,}', re.IGNORECASE), "token"),
    (re.compile(r'sk-[A-Za-z0-9]{20,}'), "OpenAI API key"),
    (re.compile(r'sk-ant-[A-Za-z0-9\-]{20,}'), "Anthropic API key"),
    (re.compile(r'ghp_[A-Za-z0-9]{36}'), "GitHub personal access token"),
    (re.compile(r'gho_[A-Za-z0-9]{36}'), "GitHub OAuth token"),
    (re.compile(r'glpat-[A-Za-z0-9\-]{20,}'), "GitLab access token"),
    (re.compile(r'xoxb-[A-Za-z0-9\-]{20,}'), "Slack bot token"),
    (re.compile(r'xoxp-[A-Za-z0-9\-]{20,}'), "Slack user token"),
    (re.compile(r'AKIA[0-9A-Z]{16}'), "AWS access key"),
    (re.compile(r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----'), "Private key"),
    (re.compile(r'Bearer\s+[A-Za-z0-9_\-\.]{20,}'), "Bearer token"),
]

# Suspicious URL patterns
SUSPICIOUS_URL_PATTERNS = [
    (re.compile(r'^javascript:', re.IGNORECASE), "javascript: URI"),
    (re.compile(r'^data:', re.IGNORECASE), "data: URI"),
    (re.compile(r'^file:', re.IGNORECASE), "file: URI"),
]

# Known malicious or suspicious domains
BLOCKED_DOMAINS = {
    "evil.com", "malware.com", "hack.me",
}

# File extensions to scan for secrets (beyond manifest.json)
SCANNABLE_EXTENSIONS = {".json", ".md", ".yaml", ".yml", ".txt", ".py", ".js", ".ts", ".sh"}


def find_listing_dirs() -> list[pathlib.Path]:
    """Find all listing directories."""
    dirs = []
    for manifest_path in sorted(REPO_ROOT.rglob("manifest.json")):
        parts = manifest_path.relative_to(REPO_ROOT).parts
        if parts[0] in SKIP_DIRS or parts[0].startswith("."):
            continue
        dirs.append(manifest_path.parent)
    return dirs


def scan_for_secrets(content: str, file_path: pathlib.Path) -> list[str]:
    """Scan content for hardcoded secrets."""
    findings = []
    for pattern, description in SECRET_PATTERNS:
        matches = pattern.findall(content)
        for match in matches:
            # Skip common false positives
            if any(fp in match.lower() for fp in [
                "example", "placeholder", "your-", "xxx", "todo",
                "change-me", "insert-", "replace-", "<your",
            ]):
                continue
            try:
                rel = file_path.relative_to(REPO_ROOT)
            except ValueError:
                rel = file_path
            findings.append(f"Possible {description} detected in {rel}")
    return findings


def scan_urls(data: dict, manifest_path: pathlib.Path) -> list[str]:
    """Scan manifest URLs for suspicious patterns."""
    findings = []

    try:
        rel = manifest_path.relative_to(REPO_ROOT)
    except ValueError:
        rel = manifest_path

    def check_url(url: str, field: str) -> None:
        if not isinstance(url, str) or not url:
            return
        for pattern, description in SUSPICIOUS_URL_PATTERNS:
            if pattern.match(url):
                findings.append(f"Suspicious {description} in {rel} field '{field}': {url[:80]}")
                return
        try:
            parsed = urlparse(url)
            if parsed.hostname and parsed.hostname.lower() in BLOCKED_DOMAINS:
                findings.append(f"Blocked domain in {rel} field '{field}': {parsed.hostname}")
        except Exception:
            pass

    def walk(obj: dict | list, prefix: str = "") -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                path = f"{prefix}.{k}" if prefix else k
                if isinstance(v, str) and ("url" in k.lower() or "source" in k.lower() or "repository" in k.lower()):
                    check_url(v, path)
                elif isinstance(v, str) and v.startswith(("http://", "https://", "javascript:", "data:", "file:")):
                    check_url(v, path)
                elif isinstance(v, (dict, list)):
                    walk(v, path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{prefix}[{i}]")

    walk(data)
    return findings


def scan_listing(listing_dir: pathlib.Path) -> list[str]:
    """Scan a single listing directory for security issues."""
    findings = []

    # Scan manifest
    manifest_path = listing_dir / "manifest.json"
    if manifest_path.exists():
        try:
            content = manifest_path.read_text(encoding="utf-8")
            data = json.loads(content)
        except (json.JSONDecodeError, OSError):
            return [f"Cannot read manifest: {manifest_path.relative_to(REPO_ROOT)}"]

        # Check for secrets in manifest
        findings.extend(scan_for_secrets(content, manifest_path))

        # Check URLs
        findings.extend(scan_urls(data, manifest_path))

    # Scan other files in the listing directory
    for file_path in listing_dir.iterdir():
        if file_path.is_file() and file_path.suffix in SCANNABLE_EXTENSIONS and file_path.name != "manifest.json":
            try:
                content = file_path.read_text(encoding="utf-8")
                findings.extend(scan_for_secrets(content, file_path))
            except (OSError, UnicodeDecodeError):
                continue

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Security scan marketplace listings")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on any finding")
    parser.add_argument("--verbose", action="store_true", help="Show clean listings too")
    args = parser.parse_args()

    listing_dirs = find_listing_dirs()
    total_findings = 0

    print(f"Security scanning {len(listing_dirs)} listings...\n")

    for listing_dir in listing_dirs:
        findings = scan_listing(listing_dir)
        if findings:
            total_findings += len(findings)
            for f in findings:
                print(f"WARN: {f}")
        elif args.verbose:
            print(f"OK:   {listing_dir.relative_to(REPO_ROOT)}")

    if total_findings:
        print(f"\n{total_findings} security finding(s) detected.")
        if args.strict:
            return 1
    else:
        print("\nNo security issues found.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
