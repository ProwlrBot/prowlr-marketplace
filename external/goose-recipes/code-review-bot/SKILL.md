---
name: code-review-bot
description: Use this skill when you want to automatically review GitHub pull requests and post line-level comments with findings, suggestions, and approval recommendations.
source: https://github.com/block/goose/tree/main/docs/recipes
---

# Code Review Bot

## Overview

Automated GitHub PR reviewer. Fetches the diff, runs it through Claude for analysis, and posts line-level review comments back to the PR. Produces structured findings with severity and suggested fixes.

## Setup

```bash
pip install PyGithub anthropic
export GITHUB_TOKEN=ghp_...
```

## PR Review Engine

```python
import anthropic
import json
from github import Github
import os

client = anthropic.Anthropic()
gh = Github(os.environ["GITHUB_TOKEN"])

def review_pr(repo_name: str, pr_number: int) -> dict:
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    # Get the diff
    files_changed = []
    for file in pr.get_files():
        if file.patch:  # has diff content
            files_changed.append({
                "filename": file.filename,
                "status": file.status,  # added/modified/deleted
                "patch": file.patch,
                "additions": file.additions,
                "deletions": file.deletions,
            })

    # Review each changed file
    all_findings = []
    for file_info in files_changed:
        findings = review_file(file_info)
        all_findings.extend(findings)

    # Post review
    post_review(pr, all_findings)
    return {"files": len(files_changed), "findings": len(all_findings)}

def review_file(file_info: dict) -> list[dict]:
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        tools=[{
            "name": "report_findings",
            "description": "Report code review findings",
            "input_schema": {
                "type": "object",
                "properties": {
                    "findings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "line": {"type": "integer", "description": "Line number in the diff"},
                                "severity": {"type": "string", "enum": ["critical", "high", "medium", "low", "info"]},
                                "category": {"type": "string", "enum": ["security", "bug", "performance", "style", "docs"]},
                                "message": {"type": "string"},
                                "suggestion": {"type": "string"}
                            },
                            "required": ["severity", "category", "message"]
                        }
                    },
                    "summary": {"type": "string"},
                    "recommendation": {"type": "string", "enum": ["approve", "request_changes", "comment"]}
                },
                "required": ["findings", "summary", "recommendation"]
            }
        }],
        tool_choice={"type": "tool", "name": "report_findings"},
        messages=[{
            "role": "user",
            "content": f"""Review this code change for: bugs, security issues, performance problems, and style issues.

File: {file_info['filename']} ({file_info['status']})

Diff:
{file_info['patch'][:3000]}"""  # truncate large diffs
        }],
    )

    for block in response.content:
        if block.type == "tool_use":
            findings = block.input.get("findings", [])
            for f in findings:
                f["filename"] = file_info["filename"]
            return findings
    return []

def post_review(pr, findings: list[dict]) -> None:
    # Group by severity for summary
    critical = [f for f in findings if f["severity"] == "critical"]
    high = [f for f in findings if f["severity"] == "high"]

    body = f"""## ProwlrBot Code Review

Found **{len(findings)} findings** ({len(critical)} critical, {len(high)} high priority)

| Severity | Count |
|----------|-------|
| Critical | {len(critical)} |
| High | {len(high)} |
| Medium | {len([f for f in findings if f['severity'] == 'medium'])} |
| Low/Info | {len([f for f in findings if f['severity'] in ['low', 'info']])} |

*Review by ProwlrBot — automated code analysis*"""

    event = "REQUEST_CHANGES" if critical or high else "COMMENT"
    pr.create_review(body=body, event=event)
```

## Quick Reference

| Finding Type | Examples |
|-------------|---------|
| security | SQL injection, hardcoded secrets, SSRF |
| bug | Off-by-one, null dereference, race condition |
| performance | N+1 query, unbounded loop, missing index |
| style | Naming, dead code, missing type hints |
| docs | Missing docstring, incorrect comment |
