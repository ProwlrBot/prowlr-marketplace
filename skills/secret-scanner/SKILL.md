---
name: secret-scanner
description: Use this skill when the user wants to scan code for secrets, find leaked credentials, check for hardcoded API keys, audit git history for sensitive data, or set up secret detection.
---

# Secret Scanner

## Overview

Scans codebases, files, and git history for accidentally committed secrets: API keys, tokens, passwords, private keys, and credentials. Produces severity-tagged reports without logging the secrets themselves.

## Pattern-Based Scanner

```python
import re
from pathlib import Path
from dataclasses import dataclass

@dataclass
class SecretFinding:
    file: str
    line: int
    type_: str
    severity: str
    preview: str  # first 6 chars + *** (never log full secret)

# Common secret patterns
PATTERNS = {
    "aws-access-key":      (r"AKIA[0-9A-Z]{16}", "CRITICAL"),
    "aws-secret-key":      (r"(?i)aws.{0,20}secret.{0,20}['\"][0-9a-zA-Z/+]{40}['\"]", "CRITICAL"),
    "github-token":        (r"gh[pousr]_[A-Za-z0-9_]{36,}", "HIGH"),
    "github-app-token":    (r"ghs_[A-Za-z0-9_]{36}", "HIGH"),
    "stripe-key":          (r"sk_(live|test)_[0-9a-zA-Z]{24,}", "CRITICAL"),
    "stripe-restricted":   (r"rk_(live|test)_[0-9a-zA-Z]{24,}", "HIGH"),
    "openai-key":          (r"sk-[A-Za-z0-9]{20,}T3BlbkFJ[A-Za-z0-9]{20,}", "CRITICAL"),
    "anthropic-key":       (r"sk-ant-[A-Za-z0-9\-_]{90,}", "CRITICAL"),
    "slack-token":         (r"xox[baprs]-([0-9a-zA-Z]{10,48})", "HIGH"),
    "private-key-header":  (r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY( BLOCK)?-----", "CRITICAL"),
    "generic-api-key":     (r"(?i)(api_key|apikey)\s*[=:]\s*['\"][A-Za-z0-9+/=_\-]{20,}['\"]", "HIGH"),
    "generic-password":    (r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]{8,}['\"]", "MEDIUM"),
    "jwt-token":           (r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "MEDIUM"),
    "connection-string":   (r"(?i)(mongodb|postgres|mysql|redis)://[^:]+:[^@]+@", "HIGH"),
    "env-file-cred":       (r"(?m)^[A-Z_]+(KEY|SECRET|TOKEN|PASSWORD)\s*=\s*[^\s$]", "MEDIUM"),
}

SKIP_EXTENSIONS = {".pyc", ".png", ".jpg", ".gif", ".svg", ".ico", ".lock"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

def scan_file(file_path: Path) -> list[SecretFinding]:
    if file_path.suffix in SKIP_EXTENSIONS:
        return []
    try:
        text = file_path.read_text(errors="ignore")
    except OSError:
        return []

    findings = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        for secret_type, (pattern, severity) in PATTERNS.items():
            if re.search(pattern, line):
                # Extract first match, show only prefix
                m = re.search(pattern, line)
                raw = m.group() if m else ""
                preview = raw[:6] + "***" if len(raw) > 6 else "***"
                findings.append(SecretFinding(
                    file=str(file_path),
                    line=i,
                    type_=secret_type,
                    severity=severity,
                    preview=preview,
                ))
    return findings

def scan_directory(directory: str = ".") -> list[SecretFinding]:
    root = Path(directory)
    all_findings = []
    for path in root.rglob("*"):
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        if path.is_file():
            all_findings.extend(scan_file(path))
    return all_findings
```

## Git History Scanner

```python
import subprocess

def scan_git_history(repo_path: str = ".", depth: int = 100) -> list[dict]:
    """Scan recent git commits for secrets in diffs."""
    log = subprocess.run(
        ["git", "log", f"-{depth}", "--oneline"],
        cwd=repo_path, capture_output=True, text=True
    ).stdout.strip().splitlines()

    findings = []
    for line in log:
        commit_hash = line.split()[0]
        diff = subprocess.run(
            ["git", "show", commit_hash, "--unified=0"],
            cwd=repo_path, capture_output=True, text=True
        ).stdout

        for secret_type, (pattern, severity) in PATTERNS.items():
            matches = re.findall(pattern, diff)
            if matches:
                findings.append({
                    "commit": commit_hash,
                    "type": secret_type,
                    "severity": severity,
                    "count": len(matches),
                })
    return findings
```

## Gitleaks Integration

```bash
# Install gitleaks
brew install gitleaks  # macOS
# or download from https://github.com/gitleaks/gitleaks/releases

# Scan current repo
gitleaks detect --source . --report-format json --report-path findings.json

# Scan git history
gitleaks detect --source . --log-opts="-n 500" --report-format json

# Pre-commit hook
gitleaks protect --staged  # scan staged files only
```

## Report Formatter

```python
def format_report(findings: list[SecretFinding]) -> str:
    if not findings:
        return "No secrets detected."

    by_severity = {"CRITICAL": [], "HIGH": [], "MEDIUM": []}
    for f in findings:
        by_severity.setdefault(f.severity, []).append(f)

    lines = [f"Secret Scan Report — {len(findings)} finding(s)\n"]
    for severity in ("CRITICAL", "HIGH", "MEDIUM"):
        group = by_severity.get(severity, [])
        if group:
            lines.append(f"\n{severity} ({len(group)})")
            for f in group:
                lines.append(f"  {f.file}:{f.line}  [{f.type_}]  {f.preview}")
    return "\n".join(lines)
```

## Pre-commit Hook Setup

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

## Quick Reference

| Task | Tool | Notes |
|------|------|-------|
| Scan directory | Custom regex | 15+ pattern types |
| Scan git history | gitleaks | Checks all commits |
| Pre-commit check | gitleaks protect | Blocks staged secrets |
| CI integration | gitleaks detect | Exit 1 on findings |
| False positives | `.gitleaksignore` | Allowlist specific lines |
