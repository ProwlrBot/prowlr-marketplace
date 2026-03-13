---
name: web-scraper
description: Use this skill when you need to extract structured data from websites — handling dynamic JavaScript content, pagination, login flows, or when you want Claude to intelligently identify the data to extract.
source: https://github.com/block/goose/tree/main/docs/recipes
---

# Web Scraper

## Overview

Playwright-powered web scraper with Claude for intelligent data extraction. Handles JavaScript-heavy sites, pagination, and variable page structures. Respects robots.txt and rate limits.

## Setup

```bash
pip install playwright anthropic
playwright install chromium
```

## Basic Page Scraper

```python
import anthropic
import asyncio
from playwright.async_api import async_playwright

client = anthropic.Anthropic()

async def scrape_page(url: str, data_description: str) -> dict:
    """Scrape a page and use Claude to extract structured data."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Rate limit: be a good citizen
        await asyncio.sleep(1)

        await page.goto(url, wait_until="networkidle")
        html = await page.content()
        await browser.close()

    # Let Claude extract the structured data
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        system="Extract structured data from HTML. Return only the requested data as JSON.",
        messages=[{
            "role": "user",
            "content": f"""Extract: {data_description}

HTML (truncated to relevant sections):
{html[:8000]}

Return as JSON."""
        }],
    )

    import json
    try:
        return json.loads(response.content[0].text)
    except json.JSONDecodeError:
        return {"raw": response.content[0].text}
```

## Paginated Scraper

```python
async def scrape_all_pages(base_url: str, data_description: str,
                            max_pages: int = 10) -> list[dict]:
    all_results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        current_url = base_url
        pages_scraped = 0

        while current_url and pages_scraped < max_pages:
            await asyncio.sleep(1)  # respect rate limits
            await page.goto(current_url, wait_until="networkidle")
            html = await page.content()

            # Extract data from this page
            page_data = extract_from_html(html, data_description)
            all_results.extend(page_data if isinstance(page_data, list) else [page_data])

            # Find next page link
            next_link = await page.query_selector("a[rel='next'], .pagination .next, [aria-label='Next']")
            if next_link:
                current_url = await next_link.get_attribute("href")
                if current_url and not current_url.startswith("http"):
                    from urllib.parse import urljoin
                    current_url = urljoin(base_url, current_url)
            else:
                current_url = None

            pages_scraped += 1

        await browser.close()

    return all_results
```

## Screenshot-Based Extraction

```python
async def extract_from_screenshot(url: str, question: str) -> str:
    """Use Claude's vision to extract from a screenshot."""
    import base64

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        await page.goto(url)
        screenshot = await page.screenshot(full_page=False)
        await browser.close()

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": base64.b64encode(screenshot).decode()}},
                {"type": "text", "text": question}
            ]
        }],
    )
    return response.content[0].text
```

## Quick Reference

| Approach | Best for |
|----------|----------|
| HTML extraction | Text content, tables, links |
| Screenshot + vision | Visual layouts, charts, images |
| Paginated scraper | Multi-page catalogs, search results |
| Rate limit | 1 req/sec minimum — be polite |
