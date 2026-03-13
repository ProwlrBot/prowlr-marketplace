#!/usr/bin/env python3
"""extract.py <url> --out <dir> — screenshot + CSS token extraction via Playwright."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_TOKENS: dict[str, Any] = {
    "bg_primary": "#000000",
    "bg_secondary": "#111111",
    "fg_primary": "#ffffff",
    "fg_secondary": "#888888",
    "accent": "#0070f3",
    "font_sans": "system-ui",
    "font_mono": "monospace",
    "border_radius": "4px",
    "spacing_unit": "4px",
    "uses_gradients": False,
    "nav_pattern": "top",
    "card_style": "bordered",
}

# JS evaluated inside the page to extract computed CSS values
_EXTRACT_JS = """
(() => {
    const root = document.documentElement;
    const body = document.body;
    const rootStyle = window.getComputedStyle(root);
    const bodyStyle = window.getComputedStyle(body);

    const firstColor = (...props) => {
        for (const p of props) {
            const v = rootStyle.getPropertyValue(p).trim() ||
                      bodyStyle.getPropertyValue(p).trim();
            if (v) return v;
        }
        return null;
    };

    const bgPrimary = bodyStyle.backgroundColor ||
        firstColor('--background', '--bg', '--color-bg', '--bg-primary') ||
        '#000000';
    const fgPrimary = bodyStyle.color ||
        firstColor('--foreground', '--fg', '--color-fg', '--fg-primary') ||
        '#ffffff';
    const accent = firstColor('--accent', '--primary', '--color-primary',
        '--brand', '--link-color') || '#0070f3';
    const fontSans = bodyStyle.fontFamily || 'system-ui';
    const fontMono = firstColor('--font-mono', '--font-code') || 'monospace';

    const card = document.querySelector(
        'article, [class*="card"], [class*="Card"], section > div'
    );
    const borderRadius = card ? window.getComputedStyle(card).borderRadius : '4px';

    const paddedEls = Array.from(document.querySelectorAll(
        'button, a, [class*="btn"], [class*="tag"], [class*="badge"]'
    )).slice(0, 10);
    const paddings = paddedEls.map(el => parseInt(window.getComputedStyle(el).paddingTop) || 0)
        .filter(v => v > 0).sort((a, b) => a - b);
    const spacingUnit = paddings.length ? paddings[0] + 'px' : '4px';

    const allBgs = Array.from(document.querySelectorAll('*'))
        .slice(0, 200)
        .map(el => window.getComputedStyle(el).backgroundImage);
    const usesGradients = allBgs.some(v => v && v.includes('gradient'));

    const navEl = document.querySelector('nav, [role="navigation"]');
    let navPattern = 'top';
    if (navEl) {
        const rect = navEl.getBoundingClientRect();
        if (rect.height > window.innerHeight * 0.5) navPattern = 'sidebar';
    }

    const firstCard = document.querySelector('[class*="card"], [class*="Card"]');
    let cardStyle = 'bordered';
    if (firstCard) {
        const shadow = window.getComputedStyle(firstCard).boxShadow;
        if (shadow && shadow !== 'none') cardStyle = 'shadowed';
    }

    return {
        bg_primary: bgPrimary,
        bg_secondary: bodyStyle.backgroundColor,
        fg_primary: fgPrimary,
        fg_secondary: '#888888',
        accent: accent,
        font_sans: fontSans,
        font_mono: fontMono,
        border_radius: borderRadius,
        spacing_unit: spacingUnit,
        uses_gradients: usesGradients,
        nav_pattern: navPattern,
        card_style: cardStyle,
    };
})()
"""

_AESTHETIC_RULES = [
    ("terminal-pro", lambda t: t.get("bg_primary", "").lower() in (
        "#000000", "#0a0a0a", "#0d0d0d", "#080808", "#111111",
        "rgb(0, 0, 0)", "rgb(10, 10, 10)", "rgb(13, 13, 13)",
    )),
    ("data-rich", lambda t: t.get("nav_pattern") == "sidebar"),
    ("bold-brand", lambda t: t.get("uses_gradients") is True),
    ("minimal-light", lambda t: t.get("bg_primary", "").lower() in (
        "#ffffff", "#fafafa", "#f9f9f9", "#f5f5f5",
        "rgb(255, 255, 255)", "rgb(250, 250, 250)",
    )),
]


def classify_aesthetic(tokens: dict[str, Any]) -> str:
    for name, pred in _AESTHETIC_RULES:
        if pred(tokens):
            return name
    return "enterprise"


def extract(url: str, out_dir: Path) -> None:
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        print("playwright not installed — run: pip install playwright && playwright install chromium",
              file=sys.stderr)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.set_default_timeout(30_000)
            try:
                page.goto(url, wait_until="networkidle", timeout=30_000)
            except PWTimeout:
                print(f"Timeout loading {url}", file=sys.stderr)
                sys.exit(1)

            page.screenshot(path=str(out_dir / "screenshot.png"), full_page=False)

            raw = page.evaluate(_EXTRACT_JS)
            tokens: dict[str, Any] = {**DEFAULT_TOKENS, **raw}
            tokens["uses_gradients"] = bool(tokens.get("uses_gradients"))
            aesthetic = classify_aesthetic(tokens)

            result = {
                "source_url": url,
                "tokens": tokens,
                "aesthetic_class": aesthetic,
            }
            (out_dir / "tokens.json").write_text(
                json.dumps(result, indent=2), encoding="utf-8"
            )
        finally:
            browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    extract(args.url, Path(args.out))
