---
name: git-workflow
description: Use this skill when the user wants to automate git operations, manage branches, generate commit messages, handle PRs, set up git hooks, or implement a git workflow.
---

# Git Workflow

## Overview

Automates git workflows: branch naming, commit message generation, PR checklists, merge strategies, and hook setup. Uses GitPython for programmatic operations and the GitHub API for PR management.

## Branch Naming Conventions

```
feature/TICKET-123-short-description
fix/TICKET-456-bug-description
chore/update-dependencies
hotfix/critical-login-issue
release/v1.2.0
docs/update-api-reference
refactor/extract-auth-service
```

```python
import re

def create_branch_name(type_: str, ticket: str | None, description: str) -> str:
    slug = re.sub(r"[^a-z0-9-]", "-", description.lower()).strip("-")
    slug = re.sub(r"-+", "-", slug)[:40]
    parts = [type_]
    if ticket:
        parts.append(ticket.upper())
    parts.append(slug)
    return "/".join(parts)

# create_branch_name("feature", "PROJ-123", "Add user authentication")
# → "feature/PROJ-123-add-user-authentication"
```

## GitPython Operations

```python
from git import Repo

def get_repo(path: str = ".") -> Repo:
    return Repo(path, search_parent_directories=True)

def create_and_checkout(repo: Repo, branch: str, from_branch: str = "main") -> None:
    repo.git.fetch("origin")
    repo.git.checkout(f"origin/{from_branch}", b=branch)

def stage_and_commit(repo: Repo, message: str, paths: list[str] | None = None) -> str:
    if paths:
        repo.index.add(paths)
    else:
        repo.git.add(A=True)
    commit = repo.index.commit(message)
    return commit.hexsha[:8]

def get_changed_files(repo: Repo) -> dict[str, list[str]]:
    return {
        "staged": [d.a_path for d in repo.index.diff("HEAD")],
        "unstaged": [d.a_path for d in repo.index.diff(None)],
        "untracked": repo.untracked_files,
    }
```

## Conventional Commit Message Generator

```python
def generate_commit_message(diff: str, context: str = "") -> str:
    """
    Use this as a guide when writing commit messages from a diff.

    Format: <type>(<scope>): <subject>

    Types:
      feat     — new feature
      fix      — bug fix
      docs     — documentation only
      style    — formatting, no logic change
      refactor — code restructure, no feature/fix
      test     — adding/updating tests
      chore    — build, deps, tooling
      perf     — performance improvement
      ci       — CI/CD changes

    Rules:
      - Subject: imperative mood, ≤50 chars, no period at end
      - Body: explain WHY, not what (the diff shows what)
      - Footer: BREAKING CHANGE: or Closes #123

    Examples:
      feat(auth): add JWT refresh token rotation
      fix(api): handle empty response body in retry logic
      chore(deps): upgrade SQLAlchemy to 2.0
    """
    pass

# When generating commit messages, analyze the diff for:
# 1. What files changed (determines scope)
# 2. What type of change (feat/fix/refactor/etc.)
# 3. The core reason for the change (the subject)
# 4. Any breaking changes
```

## PR Checklist Generator

```python
PR_CHECKLIST = """
## PR Checklist

### Code Quality
- [ ] Code follows project style guide
- [ ] No debug prints or commented-out code left in
- [ ] Complex logic has comments explaining WHY
- [ ] No hardcoded values that should be config

### Testing
- [ ] Unit tests added/updated for new behavior
- [ ] All existing tests pass
- [ ] Edge cases covered
- [ ] Manual testing done (describe below)

### Security
- [ ] No secrets or credentials in code
- [ ] User input is validated
- [ ] Auth/permissions checked where needed

### Documentation
- [ ] README updated if behavior changed
- [ ] API docs updated if endpoints changed
- [ ] CHANGELOG entry added

### Deployment
- [ ] Database migrations included (if needed)
- [ ] Environment variables documented
- [ ] Breaking changes noted in description
"""
```

## Git Hooks via pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
```

```bash
pre-commit install     # install hooks
pre-commit run --all-files  # run manually
```

## Quick Reference

| Task | Tool | Notes |
|------|------|-------|
| Branch creation | `git checkout -b` | Always from fresh main |
| Conventional commits | Pattern: `type(scope): subject` | ≤50 char subject |
| PR checklist | Markdown template | Include in PR description |
| Pre-commit hooks | `pre-commit` | Run on every commit |
| Squash merge | `git merge --squash` | Clean history |
| Interactive rebase | `git rebase -i HEAD~N` | Clean up before PR |
