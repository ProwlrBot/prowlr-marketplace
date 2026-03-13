---
name: jira-sync
description: Use this skill when you want to sync GitHub activity with Jira — create tickets from issues, link PRs to tickets, update status from commits, or generate sprint summaries.
source: https://github.com/block/goose/tree/main/docs/recipes
---

# Jira Sync

## Overview

Bidirectional sync between GitHub and Jira: create Jira tickets from GitHub issues, link PRs to tickets, auto-update status from branch names/commits, and generate AI-powered sprint summaries.

## Setup

```bash
pip install jira PyGithub anthropic
export JIRA_URL=https://yourorg.atlassian.net
export JIRA_EMAIL=you@yourorg.com
export JIRA_API_TOKEN=...   # from id.atlassian.com/manage-profile/security/api-tokens
export GITHUB_TOKEN=ghp_...
```

## Jira Client

```python
from jira import JIRA
import os

jira = JIRA(
    server=os.environ["JIRA_URL"],
    basic_auth=(os.environ["JIRA_EMAIL"], os.environ["JIRA_API_TOKEN"])
)

def create_ticket(project_key: str, summary: str, description: str,
                  issue_type: str = "Bug", priority: str = "Medium") -> str:
    issue = jira.create_issue(
        project=project_key,
        summary=summary,
        description=description,
        issuetype={"name": issue_type},
        priority={"name": priority},
    )
    return issue.key  # e.g., "PROJ-123"

def transition_ticket(ticket_key: str, status: str) -> None:
    """Move ticket to a new status."""
    issue = jira.issue(ticket_key)
    transitions = jira.transitions(issue)
    target = next((t for t in transitions if t["name"].lower() == status.lower()), None)
    if target:
        jira.transition_issue(issue, target["id"])
```

## GitHub Issue → Jira Ticket

```python
from github import Github
import anthropic

gh = Github(os.environ["GITHUB_TOKEN"])
client = anthropic.Anthropic()

def sync_github_issue_to_jira(repo_name: str, issue_number: int,
                                project_key: str) -> str:
    repo = gh.get_repo(repo_name)
    issue = repo.get_issue(issue_number)

    # Use Claude to write a better Jira description
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=512,
        system="Convert GitHub issues to Jira tickets. Use Jira markdown. Include: Summary, Steps to Reproduce (if bug), Expected vs Actual, Environment.",
        messages=[{"role": "user", "content": f"Title: {issue.title}\n\n{issue.body or ''}"}]
    )
    jira_description = response.content[0].text

    # Determine issue type from labels
    labels = [l.name for l in issue.labels]
    issue_type = "Bug" if "bug" in labels else "Story" if "feature" in labels else "Task"

    # Create Jira ticket
    ticket_key = create_ticket(project_key, issue.title, jira_description, issue_type)

    # Link back to GitHub issue
    issue.create_comment(f"Jira ticket created: [{ticket_key}]({os.environ['JIRA_URL']}/browse/{ticket_key})")

    return ticket_key
```

## Sprint Summary Generator

```python
def generate_sprint_summary(project_key: str, sprint_name: str) -> str:
    # Get completed issues this sprint
    issues = jira.search_issues(
        f'project={project_key} AND sprint="{sprint_name}" AND status=Done',
        maxResults=100
    )

    issue_list = "\n".join([f"- [{i.key}] {i.fields.summary}" for i in issues])

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=512,
        system="Write sprint summaries for engineering teams. Be specific about what shipped. Group by theme.",
        messages=[{"role": "user", "content": f"Sprint: {sprint_name}\n\nCompleted:\n{issue_list}"}]
    )
    return response.content[0].text
```

## Quick Reference

| Feature | Description |
|---------|-------------|
| Create ticket | GitHub issue → Jira ticket |
| Transition | Move ticket through workflow |
| Sprint summary | AI-generated what-shipped summary |
| PR linking | Commit message `PROJ-123` → auto-link |
