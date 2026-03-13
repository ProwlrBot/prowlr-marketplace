---
name: web-monitor
description: Use this skill when the user wants to watch a webpage for changes, monitor a URL, detect content updates, or get notified when a site changes.
---

# Web Monitor

## Overview

Monitors any URL for content changes and sends alerts via webhook, Discord, Telegram, or email. Uses content hashing for efficient change detection and CSS selectors to target specific page elements.

## Quick Start

```python
import requests, hashlib, json
from pathlib import Path

def check_url(url: str, state_file: str = "monitor_state.json") -> bool:
    """Returns True if content changed since last check."""
    state = json.loads(Path(state_file).read_text()) if Path(state_file).exists() else {}
    content = requests.get(url, timeout=10).text
    new_hash = hashlib.sha256(content.encode()).hexdigest()
    changed = state.get(url) != new_hash
    state[url] = new_hash
    Path(state_file).write_text(json.dumps(state))
    return changed
```

## Targeted Element Monitoring (CSS Selectors)

```python
from bs4 import BeautifulSoup
import requests, hashlib

def monitor_element(url: str, selector: str, state: dict) -> tuple[bool, str]:
    """Watch a specific element on a page."""
    soup = BeautifulSoup(requests.get(url, timeout=10).text, "html.parser")
    el = soup.select_one(selector)
    text = el.get_text(strip=True) if el else ""
    h = hashlib.sha256(text.encode()).hexdigest()
    changed = state.get(f"{url}#{selector}") != h
    state[f"{url}#{selector}"] = h
    return changed, text
```

## Content Diffing

```python
import difflib

def compute_diff(old: str, new: str) -> str:
    """Return a unified diff string between old and new content."""
    return "\n".join(difflib.unified_diff(
        old.splitlines(), new.splitlines(),
        fromfile="previous", tofile="current", lineterm=""
    ))
```

## Notifications

### Discord Webhook
```python
import requests

def notify_discord(webhook_url: str, url: str, diff: str) -> None:
    content = f"**Change detected on:** {url}\n```diff\n{diff[:1800]}\n```"
    requests.post(webhook_url, json={"content": content}, timeout=5)
```

### Telegram
```python
def notify_telegram(bot_token: str, chat_id: str, url: str, diff: str) -> None:
    msg = f"Change on {url}:\n{diff[:3000]}"
    requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={"chat_id": chat_id, "text": msg},
        timeout=5,
    )
```

### Generic Webhook
```python
def notify_webhook(endpoint: str, payload: dict) -> None:
    requests.post(endpoint, json=payload, timeout=5)
```

## Full Monitor Loop

```python
import time

def run_monitor(urls: list[str], interval_seconds: int = 300,
                discord_webhook: str | None = None) -> None:
    state = {}
    while True:
        for url in urls:
            try:
                changed, text = monitor_element(url, "body", state)
                if changed:
                    print(f"[CHANGED] {url}")
                    if discord_webhook:
                        notify_discord(discord_webhook, url, text[:500])
            except Exception as e:
                print(f"[ERROR] {url}: {e}")
        time.sleep(interval_seconds)
```

## JavaScript-Rendered Pages (Playwright)

```python
from playwright.sync_api import sync_playwright

def get_rendered_content(url: str, selector: str = "body") -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        text = page.locator(selector).inner_text()
        browser.close()
    return text
```

## Quick Reference

| Task | Tool | Notes |
|------|------|-------|
| Hash whole page | `hashlib.sha256` | Fast, no parsing |
| Watch one element | `beautifulsoup4` + CSS selector | Precise targeting |
| JS-rendered pages | `playwright` | Slower, handles SPAs |
| Diff output | `difflib.unified_diff` | Human-readable changes |
| Discord alert | `requests.post(webhook)` | Free, instant |
| Rate limiting | `time.sleep(interval)` | Respect robots.txt |
