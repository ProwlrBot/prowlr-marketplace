---
name: github-issue-triage
description: Use this skill when you want to automatically triage GitHub issues — classify type, add labels, route to teams, and draft initial responses.
source: https://github.com/block/goose/tree/main/docs/recipes
---

# GitHub Issue Triage

## Overview

Automatically processes incoming GitHub issues: classifies them (bug/feature/question/docs), adds appropriate labels, identifies the responsible team, and drafts an initial response. Adapted from Block's Goose automation recipes.

## Setup

```bash
pip install PyGithub anthropic
export GITHUB_TOKEN=ghp_...
export ANTHROPIC_API_KEY=sk-ant-...
```

## Issue Classifier

```python
import anthropic
import json
from github import Github
from pathlib import Path

client = anthropic.Anthropic()
gh = Github(os.environ["GITHUB_TOKEN"])

TEAM_ROUTING = {
    "bug": ["engineering"],
    "feature": ["product", "engineering"],
    "docs": ["docs-team"],
    "question": ["support"],
    "security": ["security-team"],
}

LABEL_COLORS = {
    "bug": "d73a4a",
    "feature": "a2eeef",
    "docs": "0075ca",
    "question": "d876e3",
    "security": "e4e669",
}

def classify_issue(title: str, body: str) -> dict:
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=512,
        tools=[{
            "name": "classify_issue",
            "description": "Classify a GitHub issue",
            "input_schema": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["bug", "feature", "question", "docs", "security", "other"]
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low"]
                    },
                    "component": {
                        "type": "string",
                        "description": "Affected component/area"
                    },
                    "needs_more_info": {"type": "boolean"},
                    "initial_response": {
                        "type": "string",
                        "description": "Friendly initial response acknowledging the issue"
                    }
                },
                "required": ["type", "priority", "initial_response"]
            }
        }],
        tool_choice={"type": "tool", "name": "classify_issue"},
        messages=[{
            "role": "user",
            "content": f"Classify this GitHub issue:\n\nTitle: {title}\n\nBody:\n{body}"
        }],
    )
    for block in response.content:
        if block.type == "tool_use":
            return block.input
    return {}
```

## Issue Processor

```python
def process_issue(repo_name: str, issue_number: int) -> dict:
    repo = gh.get_repo(repo_name)
    issue = repo.get_issue(issue_number)

    # Classify
    classification = classify_issue(issue.title, issue.body or "")
    issue_type = classification.get("type", "other")
    priority = classification.get("priority", "medium")

    # Apply labels
    labels_to_add = [issue_type, f"priority:{priority}"]
    for label_name in labels_to_add:
        try:
            label = repo.get_label(label_name)
        except Exception:
            color = LABEL_COLORS.get(label_name, "ededed")
            label = repo.create_label(label_name, color)
        issue.add_to_labels(label)

    # Post response
    if classification.get("initial_response"):
        issue.create_comment(
            f"{classification['initial_response']}\n\n"
            f"*Classified as: {issue_type} (Priority: {priority}) by ProwlrBot*"
        )

    # Request more info if needed
    if classification.get("needs_more_info"):
        issue.create_comment(
            "Could you provide more information? Please include:\n"
            "- Steps to reproduce (for bugs)\n"
            "- Expected vs actual behavior\n"
            "- Environment details (OS, version)"
        )

    return classification
```

## GitHub Webhook Handler

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook/github")
async def handle_github_webhook(request: Request):
    payload = await request.json()
    action = payload.get("action")
    if action == "opened" and "issue" in payload:
        issue = payload["issue"]
        repo_name = payload["repository"]["full_name"]
        result = process_issue(repo_name, issue["number"])
        return {"classified": result}
    return {"skipped": action}
```

## Quick Reference

| Feature | Description |
|---------|-------------|
| Classification | bug/feature/question/docs/security |
| Priority | critical/high/medium/low |
| Auto-label | Creates labels if missing |
| Auto-response | Friendly acknowledgment |
| Info request | Asks for repro steps if vague |
