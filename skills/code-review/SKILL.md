---
name: code-review
description: Use this skill when the user wants to review code, audit a pull request, check code quality, find bugs, or get feedback on implementation.
---

# Code Review

## Overview

Systematic code review covering correctness, security, performance, readability, and test coverage. Works on files, diffs, or GitHub PRs. Produces structured markdown reports.

## Review Structure

Always structure a review as:
1. **Summary** — what the code does, overall verdict
2. **Critical** — bugs, security issues (must fix)
3. **Major** — design problems, significant issues (should fix)
4. **Minor** — style, naming, small improvements (nice to have)
5. **Positive** — what's done well

## Reviewing a Diff

```python
import subprocess

def get_staged_diff() -> str:
    return subprocess.run(
        ["git", "diff", "--staged", "--unified=5"],
        capture_output=True, text=True
    ).stdout

def get_pr_diff(base: str = "main") -> str:
    return subprocess.run(
        ["git", "diff", f"{base}...HEAD", "--unified=5"],
        capture_output=True, text=True
    ).stdout
```

## Static Analysis Integration

### pylint (Python)
```python
import subprocess, json

def run_pylint(file_path: str) -> list[dict]:
    result = subprocess.run(
        ["python", "-m", "pylint", "--output-format=json", file_path],
        capture_output=True, text=True
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
```

### AST complexity check
```python
import ast

def check_complexity(source: str) -> list[str]:
    """Flag functions with too many branches or too long."""
    issues = []
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lines = node.end_lineno - node.lineno
            branches = sum(1 for n in ast.walk(node)
                          if isinstance(n, (ast.If, ast.For, ast.While, ast.Try)))
            if lines > 50:
                issues.append(f"{node.name}: {lines} lines (consider splitting)")
            if branches > 10:
                issues.append(f"{node.name}: cyclomatic complexity ~{branches}")
    return issues
```

## Security Checklist

When reviewing code, always check:

```
□ SQL injection: string formatting in queries? Use parameterized queries.
□ Command injection: user input in subprocess/shell calls?
□ Path traversal: user-controlled file paths? Validate with Path.resolve()
□ Hardcoded secrets: API keys, passwords in source?
□ Insecure deserialization: loading untrusted binary data?
□ Open redirects: user-controlled redirect URLs?
□ Missing auth: endpoints without authentication checks?
□ Race conditions: shared mutable state without locks?
□ Dependency versions: known CVEs in requirements?
```

## GitHub PR Review via PyGithub

```python
from github import Github

def review_pr(token: str, repo: str, pr_number: int, review_body: str,
              event: str = "COMMENT") -> None:
    """Submit a review to a GitHub PR. event: COMMENT|APPROVE|REQUEST_CHANGES"""
    g = Github(token)
    pr = g.get_repo(repo).get_pull(pr_number)
    pr.create_review(body=review_body, event=event)
```

## Review Report Template

```markdown
## Code Review — {filename}

**Verdict:** APPROVE | REQUEST_CHANGES | BLOCK

### Summary
{2-3 sentence description of what the code does and overall quality}

### Critical Issues
- [ ] {issue} (`{file}:{line}`)

### Major Issues
- [ ] {issue description}

### Minor / Style
- {suggestion}

### What's Good
- {positive observations}
```

## Quick Reference

| Check | Tool | Command |
|-------|------|---------|
| Linting | pylint | `python -m pylint --output-format=json` |
| Type checking | mypy | `python -m mypy --strict` |
| Security | bandit | `python -m bandit -r src/` |
| Complexity | radon | `python -m radon cc -s src/` |
| Dead code | vulture | `python -m vulture src/` |
| Deps audit | pip-audit | `pip-audit` |
