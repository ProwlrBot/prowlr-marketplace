# UI Craftsman — Design Spec

**Date:** 2026-03-13
**Author:** kdairatchi
**Status:** Approved for implementation

---

## Goal

A Claude Code skill that generates professional, non-generic UI by extracting real design patterns from reference sites, serving interactive local previews, and building a community gallery where users share and copy their best prompts and designs. Eliminates "AI slop" UI by grounding generation in real company aesthetics and personal preference memory.

## Architecture Overview

```
Three trigger commands -> SKILL.md orchestrates -> Python scripts execute
                                                         |
                                              Local preview server
                                                         |
                                              User picks direction
                                                         |
                                    Production React/TS code generated
                                    Preferences saved to memory
                                                         |
                               (optional) /ui-share -> gallery/index.json
                                                         |
                              Console tab + static gallery.html show it
```

---

## File Layout

```
prowlr-marketplace/
├── gallery/
│   ├── index.json          <- community gallery source of truth
│   ├── index.html          <- static gallery page (reads index.json)
│   ├── screenshots/        <- PNG files committed alongside entries
│   └── components/         <- optional committed .tsx files per entry
├── docs/specs/
│   └── 2026-03-13-ui-craftsman-design.md
└── skills/
    └── ui-craftsman/
        ├── SKILL.md        <- Claude Code skill instructions
        └── scripts/
            ├── extract.py     <- Playwright screenshot + CSS token extraction
            ├── serve.py       <- local preview HTTP server (127.0.0.1 only)
            ├── share.py       <- append to gallery/index.json + git push/PR
            ├── validate.py    <- URL safety check (blocks private IPs)
            └── requirements.txt
```

**Console tab** (separate, in prowlrbot repo):
```
console/src/pages/UIGallery/index.tsx    <- fetches gallery/index.json from GitHub raw
console/src/layouts/Sidebar.tsx          <- add "UI Gallery" nav entry
console/src/layouts/MainLayout/index.tsx <- add /ui-gallery route
```

---

## Setup

After cloning prowlr-marketplace:

```bash
cd skills/ui-craftsman
pip install -r scripts/requirements.txt
playwright install chromium

# GitHub CLI required for /ui-share fallback (no push access path)
# Install: https://cli.github.com  or  sudo apt install gh  or  brew install gh
gh auth login   # only needed once
```

**`requirements.txt` contents:**
```
playwright>=1.42.0
cssutils>=2.7.1
Pillow>=10.0.0
```

---

## Script CLI Contracts

### `validate.py <url>`

- Exit 0: URL is safe to fetch
- Exit 1: URL is blocked; reason printed to stderr
- Blocked patterns:
  - Localhost and loopback: `127.x.x.x`, `::1`, `0.0.0.0`
  - Private ranges: `10.x`, `172.16-31.x`, `192.168.x`
  - Cloud metadata: `169.254.169.254`, `fd00:ec2::254`
  - IPv6 link-local: `fe80::/10`
  - IPv4-mapped IPv6: `::ffff:127.x.x.x`
  - Encoded IPs: hex (`0x7f000001`), octal (`0177.0.0.1`), decimal (`2130706433`)
  - DNS resolution: resolves hostname to IP then re-checks all above rules
- Known v1 limitation: DNS rebinding attacks (resolve-time vs fetch-time divergence) are not prevented

### `extract.py <url> --out <dir>`

- Runs headless Chromium via Playwright (30-second hard timeout, kills browser on timeout)
- Writes `<dir>/tokens.json` (schema below) and `<dir>/screenshot.png`
- Exit 0 on success; exit 1 + stderr message on failure
- Claude calls it as: `extract.py <url> --out /tmp/ui-craftsman-<hash>/`

**tokens.json schema:**
```json
{
  "source_url": "https://vercel.com",
  "tokens": {
    "bg_primary": "#000000",
    "bg_secondary": "#111111",
    "fg_primary": "#ffffff",
    "fg_secondary": "#888888",
    "accent": "#0070f3",
    "font_sans": "Inter, system-ui",
    "font_mono": "Geist Mono, monospace",
    "border_radius": "6px",
    "spacing_unit": "4px",
    "uses_gradients": false,
    "nav_pattern": "top",
    "card_style": "bordered"
  },
  "aesthetic_class": "terminal-pro"
}
```

Aesthetic classes: `terminal-pro`, `bold-brand`, `data-rich`, `minimal-light`, `enterprise`.

### `serve.py <file> [--gallery <file1> <file2> ...]`

- Binds to `127.0.0.1` only, never `0.0.0.0`
- Finds first available port in range 8400-8500
- Prints `http://127.0.0.1:<PORT>` to stdout on successful bind, then runs until killed
- Exit 1 + stderr if no port available in range
- Single file mode: serves `<file>` directly
- Gallery mode (`--gallery`): generates an in-memory index page with each file embedded in an `<iframe>` (300x200px thumbnails). No secondary Playwright pass needed.

### `share.py --title <str> --prompt <str> --aesthetic <str> --mode <ref|show|system> --screenshot <path> [--ref-url <url>] [--component <path>] --author <str> --repo-dir <path>`

- Strips all markup from `title`, `prompt` before writing (plain text only)
- Generates entry ID: `{author}-{YYYYMMDD}-{seq}` where `{seq}` is zero-padded 3-digit count of existing entries in `index.json` matching `{author}-{YYYYMMDD}` prefix (e.g., `001`). If `index.json` does not exist, seq is `001`.
- Concurrent PR seq conflicts are a known v1 limitation resolved by rebase at merge
- Copies screenshot to `gallery/screenshots/{id}.png`
- If `--component` provided: copies `.tsx` file to `gallery/components/{id}.tsx`
- Appends entry to `gallery/index.json`
- `git add gallery/ && git commit -m "gallery: add {title} by {author}"`
- If push succeeds: done
- If push fails (no write access): runs `gh pr create --title "gallery: {title}" --body "New UI prompt by {author}"`
- If `gh` is not installed: prints message to stderr; SKILL.md instructs Claude to tell the user to install GitHub CLI from cli.github.com

---

## Three Modes

### Mode 1 — Reference (`/ui-ref <url>`)

**Trigger phrases (examples for SKILL.md pattern matching):**
- `/ui-ref <url>`
- "make me a [thing] like [site]"
- "UI inspired by [site]"
- "build [thing] with [site] aesthetic"
- "something that looks like [site]"

**Flow:**
1. `validate.py <url>` — abort with user message if exit non-zero
2. `extract.py <url> --out /tmp/ui-craftsman-<hash>/`
3. Read `/tmp/ui-craftsman-<hash>/tokens.json`
4. Read `~/.claude/memory/ui-prefs.md` if it exists
5. Generate `preview.html` (self-contained, no external scripts) using tokens + preferences
6. `serve.py /tmp/ui-craftsman-<hash>/preview.html` — capture stdout URL
7. Tell user the URL + describe what is visible (do this every response during the session)
8. Iterate on feedback until user approves
9. Generate production React/TypeScript component(s) — max 200 lines per file
10. Append session result to `~/.claude/memory/ui-prefs.md`

**Fallback:** If `ui-prefs.md` does not exist, default to Terminal Pro aesthetic for all generation decisions.

### Mode 2 — Showcase (`/ui-show <description>`)

**Trigger phrases:**
- `/ui-show <description>`
- "show me options for [thing]"
- "give me directions for [UI description]"
- "what would [component] look like" (when no reference URL mentioned)

**Flow:**
1. Read `~/.claude/memory/ui-prefs.md` if it exists
2. Create working dir: `/tmp/ui-craftsman-<hash>/`
3. Generate 4 `direction-A.html` through `direction-D.html` (self-contained, no external scripts):
   - Direction A: always Terminal Pro (dark, monospace, sharp)
   - Directions B/C/D: selected from aesthetic classes based on description + preferences
4. `serve.py --gallery direction-A.html direction-B.html direction-C.html direction-D.html`
5. Tell user the URL and describe each direction in one sentence each
6. User picks (click or terminal)
7. Generate production React/TypeScript from chosen direction
8. Append session result to `~/.claude/memory/ui-prefs.md`

**Fallback:** If `ui-prefs.md` does not exist, Directions B/C/D default to: bold-brand, data-rich, minimal-light.

### Mode 3 — Design System (`/ui-system <url1> <url2> ...`)

**Trigger phrases:**
- `/ui-system <url1> <url2> [url3]`
- "build a design system from [sites]"
- "combine [sites] into one design system"

**Flow:**
1. `validate.py` on each URL — abort entire command if any fail
2. `extract.py <urlN> --out /tmp/ui-craftsman-<hash>/site-N/` for each URL in order
3. Synthesize unified design system:
   - **Tie-breaking rule:** `url1` takes precedence for all conflicting values. Shared values across all sites are used as-is.
   - Spacing unit: smallest common denominator of all sites' spacing_unit values
   - Accent: taken from `url1` tokens
4. Generate output in current project directory:
   - `tokens.css` — CSS custom properties
   - `components/Button.tsx`, `Card.tsx`, `Input.tsx`, `Badge.tsx`, `Nav.tsx`, `Table.tsx`
   - `README.md` — usage guide
5. `serve.py` a preview page showing all components
6. Read + update `~/.claude/memory/ui-prefs.md`

---

## Preference Memory

**File:** `~/.claude/memory/ui-prefs.md`

**Format:**
```markdown
---
name: ui-preferences
description: User UI aesthetic preferences learned from past sessions
type: user
---

## Aesthetic Profile

**Base:** Terminal Pro (dark backgrounds, monospace accents)
**Border radius:** Sharp (0-4px)
**Gradients:** Minimal only subtle background gradients
**Typography:** Geist Mono for data, Inter for prose
**Accent color:** Blue (#3b82f6 range)
**Spacing:** Dense, tight padding
**Cards:** Bordered, not shadowed
**Nav:** Sidebar preferred

## Session History

- 2026-03-13: /ui-ref vercel.com -> chose "terminal-pro extracted"
- 2026-03-13: /ui-show "agent dashboard" -> chose Direction A (terminal-pro)
```

**Update rule:** After user picks a direction, Claude appends to Session History. After 3+ sessions, Claude rewrites the Aesthetic Profile summary to reflect the dominant patterns.

---

## Community Gallery

### `gallery/index.json` Schema

```json
{
  "version": 1,
  "entries": [
    {
      "id": "kdairatchi-20260313-001",
      "title": "Linear-style agent monitor dashboard",
      "prompt": "make a dashboard for monitoring AI agents, dark, inspired by linear.app",
      "aesthetic": "terminal-pro",
      "mode": "ref",
      "reference_url": "https://linear.app",
      "screenshot_url": "https://raw.githubusercontent.com/ProwlrBot/prowlr-marketplace/main/gallery/screenshots/kdairatchi-20260313-001.png",
      "component_url": "https://raw.githubusercontent.com/ProwlrBot/prowlr-marketplace/main/gallery/components/kdairatchi-20260313-001.tsx",
      "author": "kdairatchi",
      "created": "2026-03-13T00:00:00Z",
      "tags": ["dashboard", "dark", "agents", "monitoring"]
    }
  ]
}
```

**Field rules:**
- `prompt` — plain text, no markup, max 280 chars
- `screenshot_url` — GitHub raw URL pointing to `gallery/screenshots/{id}.png`
- `component_url` — optional GitHub raw URL to `gallery/components/{id}.tsx`; omit if no component was committed
- `copies` field — removed from v1 (no write mechanism without a server; deferred to v2)
- `tags` — array of lowercase alphanumeric strings, max 5

### `gallery/index.html` — Static Gallery Page

- Standalone HTML, no build step
- Fetches `index.json` via `fetch('./index.json')` (relative path — works locally and via GitHub Pages)
- All user-sourced strings (`title`, `prompt`, `author`, `tags`) rendered via `textContent` assignment only
- Copy button: `navigator.clipboard.writeText(entry.prompt)` + visual confirmation
- "View component" button: opens `component_url` in new tab (shown only when field is present)
- Filter bar: by aesthetic, by mode, by tag
- Sort: newest first (default), most recent author

### Console Tab (`console/src/pages/UIGallery/index.tsx`)

- Fetch URL controlled by env var: `import.meta.env.VITE_GALLERY_JSON_URL`
- Default value (in `.env.example`): `https://raw.githubusercontent.com/ProwlrBot/prowlr-marketplace/main/gallery/index.json`
- Falls back to empty state with message "Gallery unavailable — check your connection" on fetch failure
- Renders Ant Design cards matching static page layout
- "Copy prompt" button writes to clipboard
- "View component" button opens `component_url` in new tab
- Filter/sort controls matching static page

---

## SKILL.md Template

```markdown
---
name: ui-craftsman
description: Use this skill when the user wants to generate UI, build a design system,
  clone a site's aesthetic, or browse the community UI gallery. Triggers on /ui-ref,
  /ui-show, /ui-system, /ui-share, or natural-language requests naming a reference site.
version: 1.0.0
author: kdairatchi
category: skills
tags: [ui, design, frontend, react, playwright]
license: Apache-2.0
---

# UI Craftsman

## When to Use

- User says /ui-ref, /ui-show, /ui-system, or /ui-share
- User asks to build UI inspired by a named website
- User asks for design options or directions for a component/page
- User asks to combine multiple sites into a design system
- User asks to browse or share UI designs

## Before Generating Anything

Read ~/.claude/memory/ui-prefs.md if it exists. Use it to bias all aesthetic decisions.
If it does not exist, use Terminal Pro as the default aesthetic for all modes.

## Mode Detection

Inspect the user message:
- Contains a URL and a UI description -> Mode 1 (Reference)
- Contains a UI description but no URL -> Mode 2 (Showcase)
- Contains 2+ URLs and "design system" or "combine" -> Mode 3 (Design System)
- Says /ui-share -> Share flow

## Error Handling

- validate.py exits 1: Tell user "That URL is blocked for security reasons (private/internal address). Please use a public URL."
- extract.py exits 1: Tell user "Could not extract design tokens from that site. It may require login or block automation. Try another URL."
- serve.py exits 1: Tell user "Could not start preview server (all ports 8400-8500 in use). Close other servers and try again."
- playwright not installed: Tell user to run `playwright install chromium` from the skill's scripts/ directory.
- gh not installed (share fallback): Tell user to install GitHub CLI from cli.github.com, then run `gh auth login`.

## During a Session

Always include the localhost preview URL in every response while a server is running.
Describe what is visible on screen in 1-2 sentences with every URL reminder.

## After User Picks

1. Generate React/TypeScript production code
2. Keep each component file under 200 lines — split into sub-components if needed
3. All generated components must not use innerHTML or equivalent unsafe rendering
4. Update ~/.claude/memory/ui-prefs.md with the session result

## Scripts Reference

[see Script CLI Contracts section in design spec]
```

---

## Security Controls

| Risk | Control |
|------|---------|
| SSRF via Playwright | `validate.py`: blocks loopback, private ranges, cloud metadata, IPv6 link-local, IPv4-mapped IPv6, and hex/octal/decimal encoded IPs; resolves hostname and re-checks |
| DNS rebinding | Known v1 limitation — documented in Non-Goals |
| Stored XSS in gallery | `share.py` strips markup from all text fields; gallery HTML uses `textContent` only |
| Preview server exposure | `serve.py` binds `127.0.0.1` only |
| Malicious gallery PR | PR review is human gate; all stored values are plain text |
| Runaway Playwright | 30-second timeout in `extract.py`; browser killed on timeout |

---

## Non-Goals (v1)

- DNS rebinding prevention (validate.py checks at resolve time, not at fetch time)
- `copies` counter (no write mechanism without a server — deferred to v2)
- Authenticated or paywalled reference site support
- Windows native path support (WSL2 works fine)
- Real-time collaborative gallery
- AI-powered preference scoring
- Automatic router wiring after design system generation

---

## Success Criteria

- `/ui-ref vercel.com` completes end-to-end in under 60 seconds and opens a preview
- `/ui-show "agent monitor"` produces 4 visually distinct previews via iframes
- `/ui-system vercel.com linear.app` produces `tokens.css` + 6 components
- Preference memory eliminates repeated aesthetic re-explanation across sessions
- Community gallery renders in both console tab and static page
- All SSRF test cases (private IPs, localhost, metadata endpoint, hex-encoded IP) blocked
- No external script loads in any generated preview HTML
- `validate.py` exits 0/1 cleanly with stderr messages on block
