#!/usr/bin/env python3
"""share.py — append a UI entry to gallery/index.json, commit, push or PR."""
from __future__ import annotations

import argparse
import datetime
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


def strip_markup(text: str) -> str:
    """Remove all HTML/XML tags and truncate to 280 chars."""
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"&[a-z]+;", " ", clean)
    return clean[:280]


def get_next_seq(entries: list, author: str, date_str: str) -> str:
    prefix = f"{author}-{date_str}-"
    count = sum(1 for e in entries if e.get("id", "").startswith(prefix))
    return str(count + 1).zfill(3)


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)


def _write_entry(
    repo_dir: Path,
    entry_id: str,
    title: str,
    prompt: str,
    aesthetic: str,
    mode: str,
    author: str,
    ref_url: str | None,
    screenshot_src: Path,
    component_src: Path | None,
) -> None:
    gallery = repo_dir / "gallery"
    screenshots_dir = gallery / "screenshots"
    components_dir = gallery / "components"
    index_path = gallery / "index.json"

    screenshots_dir.mkdir(parents=True, exist_ok=True)
    dest_screenshot = screenshots_dir / f"{entry_id}.png"
    shutil.copy2(screenshot_src, dest_screenshot)

    component_url = None
    if component_src and component_src.exists():
        components_dir.mkdir(parents=True, exist_ok=True)
        dest_component = components_dir / f"{entry_id}.tsx"
        shutil.copy2(component_src, dest_component)
        component_url = (
            f"https://raw.githubusercontent.com/ProwlrBot/prowlr-marketplace"
            f"/main/gallery/components/{entry_id}.tsx"
        )

    if index_path.exists():
        data = json.loads(index_path.read_text(encoding="utf-8"))
    else:
        data = {"version": 1, "entries": []}

    entry: dict = {
        "id": entry_id,
        "title": strip_markup(title),
        "prompt": strip_markup(prompt),
        "aesthetic": aesthetic,
        "mode": mode,
        "screenshot_url": (
            f"https://raw.githubusercontent.com/ProwlrBot/prowlr-marketplace"
            f"/main/gallery/screenshots/{entry_id}.png"
        ),
        "author": author,
        "created": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tags": [],
    }
    if ref_url:
        entry["reference_url"] = ref_url
    if component_url:
        entry["component_url"] = component_url

    data["entries"].append(entry)
    index_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def share(
    title: str,
    prompt: str,
    aesthetic: str,
    mode: str,
    screenshot: Path,
    author: str,
    repo_dir: Path,
    ref_url: str | None = None,
    component: Path | None = None,
) -> None:
    if not re.fullmatch(r"[a-zA-Z0-9_\-]{1,64}", author):
        print("author must be 1-64 alphanumeric/underscore/hyphen characters", file=sys.stderr)
        sys.exit(1)

    index_path = repo_dir / "gallery" / "index.json"
    existing: list = []
    if index_path.exists():
        existing = json.loads(index_path.read_text(encoding="utf-8")).get("entries", [])

    date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    seq = get_next_seq(existing, author, date_str)
    entry_id = f"{author}-{date_str}-{seq}"

    _write_entry(repo_dir, entry_id, title, prompt, aesthetic, mode,
                 author, ref_url, screenshot, component)

    add_result = _git(["add", "gallery/"], cwd=repo_dir)
    if add_result.returncode != 0:
        print(f"git add failed: {add_result.stderr}", file=sys.stderr)
        sys.exit(1)

    commit_msg = f"gallery: add {strip_markup(title)} by {author}"
    commit_result = _git(["commit", "-m", commit_msg], cwd=repo_dir)
    if commit_result.returncode != 0:
        print(f"git commit failed: {commit_result.stderr}", file=sys.stderr)
        sys.exit(1)

    push = _git(["push"], cwd=repo_dir)
    if push.returncode != 0:
        gh = shutil.which("gh")
        if gh is None:
            print(
                "Push failed and gh CLI is not installed.\n"
                "Install from https://cli.github.com then run: gh auth login",
                file=sys.stderr,
            )
            sys.exit(1)
        pr = subprocess.run(
            [
                gh, "pr", "create",
                "--title", f"gallery: {strip_markup(title)}",
                "--body", f"New UI prompt by {author}",
            ],
            cwd=repo_dir,
            capture_output=True,
            text=True,
        )
        if pr.returncode != 0:
            print(f"gh pr create failed: {pr.stderr}", file=sys.stderr)
            sys.exit(1)
        print(pr.stdout)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--aesthetic", required=True)
    parser.add_argument("--mode", required=True, choices=["ref", "show", "system"])
    parser.add_argument("--screenshot", required=True, type=Path)
    parser.add_argument("--author", required=True)
    parser.add_argument("--repo-dir", required=True, type=Path)
    parser.add_argument("--ref-url", default=None)
    parser.add_argument("--component", default=None, type=Path)
    args = parser.parse_args()
    share(
        title=args.title,
        prompt=args.prompt,
        aesthetic=args.aesthetic,
        mode=args.mode,
        screenshot=args.screenshot,
        author=args.author,
        repo_dir=args.repo_dir,
        ref_url=args.ref_url,
        component=args.component,
    )
