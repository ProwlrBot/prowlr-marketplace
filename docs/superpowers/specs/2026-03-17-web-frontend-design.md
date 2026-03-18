# Prowlr Marketplace Web Frontend — Design Spec

**Date:** 2026-03-17
**Feature:** Feature 8 — Web Frontend for Marketplace Browsing (Phase 2)
**Approach:** Single HTML file with hash routing, zero dependencies

---

## Overview

A single `web/index.html` file that provides a browsable, searchable marketplace experience. Reads from `../index.json` for the grid view and fetches individual `manifest.json` files for detail views. Zero build tools, zero external dependencies, deployable via GitHub Pages.

### Important Implementation Notes

- **Path normalization:** index.json may contain backslash path separators (Windows-generated). The JS must normalize all paths to forward slashes before using them in `fetch()` calls. Without this, GitHub Pages deployment will break.
- **Field precedence:** Use `title` field for display. Fall back to `name` if `title` is absent. Never display both.
- **Listing count:** The index currently has 76 listings across 6 categories (skills, agents, prompts, mcp-servers, themes, workflows). External is included in the UI as a category filter but may not yet exist in the data. Always derive counts from actual data.
- **Accessibility:** Follow WCAG 2.1 AA. All icon-only buttons (theme toggle, copy) must have `aria-label`. Color-coded elements (difficulty, security shield) must also have text labels. Focus management on hash route transitions — move focus to the detail view heading or back to grid heading. Include a skip-to-content link.

## Architecture & Data Flow

### File Structure

```
web/
  index.html    — all HTML, CSS, JS inlined
```

### Data Flow

```
Page load → fetch("../index.json") → parse → render grid view
                                              ↓
User clicks "View" → hash changes to #/listing/<id>
                   → fetch("../<path>/manifest.json")
                   → render detail view with full manifest data

User clicks back / logo → hash changes to #/ → render grid view
```

### Routing

Hash-based routing, no page reloads:

| Route | View |
|-------|------|
| `#/` or empty | Grid/browse (default) |
| `#/listing/<id>` | Detail view |
| `#/category/<name>` | Grid filtered to category (bookmarkable) |
| `#/?q=api&pricing=free&difficulty=beginner` | Full filter state in URL |

Browser back/forward works naturally through hash change listener.

### State Management

Plain object in memory. No framework, no store.

```js
state = {
  listings: [],        // from index.json
  filters: { category, search, pricing, difficulty, tag },
  sort: "newest",
  view: "grid" | "detail",
  currentListing: null  // full manifest when in detail view
}
```

### Theming

CSS custom properties. Light by default, `[data-theme="dark"]` on `<html>` toggles dark mode.

- First visit: respects `prefers-color-scheme`
- User toggle: saved to `localStorage` as `prowlr-theme`

---

## Grid/Browse View

### Header

- "Prowlr Marketplace" wordmark (text only, no image)
- Tagline: "The bazaar where agents shop"
- Theme toggle (sun/moon icon, CSS-only)
- Listing count (e.g., "76 listings") — derived from loaded data

### Filter Bar (sticky on scroll)

- **Search input** — filters title + description + tags, case-insensitive substring, 200ms debounce
- **Category dropdown** — All / Skills / Agents / Prompts / MCP Servers / Themes / Workflows / External
- **Pricing filter** — All / Free / Paid
- **Difficulty filter** — All / Beginner / Intermediate / Advanced
- **Sort** — Newest / A-Z / Category

All filters are AND-combined. State encodes into hash for shareable URLs.

### Card Layout

```
┌──────────────────────────────────┐
│ [Category pill]  [Difficulty] [✓] │
│                                   │
│ Title                             │
│ Short description (2 lines)       │
│                                   │
│ [tag] [tag] [tag]                 │
│ [🛡 Unscanned]                    │
│                                   │
│ author · v1.0.0           [Free]  │
│───────────────────────────────────│
│  [View]           [Copy Install]  │
└──────────────────────────────────┘
```

**Card fields:**

| Field | Source | Notes |
|-------|--------|-------|
| Category pill | `category` | Color-coded per category |
| Difficulty badge | `difficulty` | Green/amber/red. Beginner/Intermediate/Advanced |
| Verified badge | `verified` | Small checkmark, only when true. Currently present on select skills listings. Render only when field exists and is `true`. |
| Title | `title` | Primary text |
| Description | `description` | 2-line truncated (CSS `-webkit-line-clamp`) |
| Tags | `tags` | First 3 only |
| Security shield | `security_status` | Green=passed, gray=unscanned, red=issues. Default: gray/unscanned for all listings until Feature 6 adds `security_status` field to index.json. Check for field presence; if absent, render gray shield with "Unscanned" text. |
| Capabilities | `capabilities` | **Detail view only.** Capabilities are not in index.json — they exist only in individual manifest.json files. Cards do NOT show capabilities. The detail view fetches the manifest and renders capabilities there. |
| Author + version | `author`, `version` | Muted metadata text |
| Pricing badge | `pricing_model` | "Free" or price tier |
| View button | — | Primary action, navigates to `#/listing/<id>` |
| Copy Install button | `id` | Copies `prowlr marketplace install <id>` to clipboard |

**Reserved slots (hidden until data supports them):**
- `<div class="card-featured">` — for future "Featured" badge
- `<div class="card-compat">` — for runtime/compatibility hints (Python, Node, Docker, ROAR-compatible)

### Grid Responsive Behavior

CSS Grid with `auto-fill, minmax(300px, 1fr)`:
- `>1200px`: 3-4 columns
- `768-1200px`: 2-3 columns
- `<768px`: single column, filter bar stacks vertically

### Empty State

Friendly message when filters match nothing: "No listings match your filters. Try broadening your search."

### Footer

Minimal — "ProwlrBot Marketplace" + links to GitHub repo, CONTRIBUTING.md, INSTALL.md.

---

## Detail View

Triggered by `#/listing/<id>`. The router looks up the listing by `id` in the cached listings array from index.json, then uses the listing's `path` field (normalized to forward slashes) to construct the fetch URL: `fetch("../" + listing.path + "/manifest.json")`. If the listing has a `manifest` field, use that directly instead.

**Loading state:** Show a centered spinner while fetching the manifest (same style as initial page load).

**Error state:** If the manifest fetch fails (404 or network error), show: "Could not load listing details. [Back to listings]" with a link back to grid. Display whatever data is available from the index.json entry as a fallback.

### Layout

```
┌──────────────────────────────────────────────────┐
│ ← Back to listings                               │
│                                                   │
│ [Category pill] [Difficulty] [Verified ✓]         │
│ Title                                    [Free]   │
│ author · v1.0.0 · Apache-2.0                     │
│                                                   │
│ ┌──────────────────────────────────────────────┐ │
│ │ prowlr marketplace install <id>       [Copy] │ │
│ └──────────────────────────────────────────────┘ │
│                                                   │
│ ── Description ──────────────────────────────────│
│ Full description text, no truncation              │
│                                                   │
│ ── Security & Capabilities ──────────────────────│
│ [🛡 CI Passed]                                    │
│ Capabilities: [filesystem] [network] [shell] ...  │
│ Min ProwlrBot: v0.1.0                            │
│                                                   │
│ ── Configuration ────────────────────────────────│
│ config_schema as readable table:                  │
│   Field          Type      Default                │
│   output_format  string    "markdown"             │
│   timeout        integer   30                     │
│                                                   │
│ ── Tags ─────────────────────────────────────────│
│ All tags shown                                    │
│                                                   │
│ ── Links ────────────────────────────────────────│
│ Repository: github.com/...                        │
│ License: Apache-2.0                               │
│                                                   │
│ ── Consumer Details (conditional) ───────────────│
│ Persona: [parent] [freelancer]                    │
│ Setup time: ~8 min                                │
│ Works with: Gmail, Outlook, Slack                 │
│ Before → After story                              │
│ Setup steps (numbered list)                       │
│ Skill scan bar chart (automation: 9/10, etc.)     │
│                                                   │
│ ── Category-Specific (conditional) ──────────────│
│ MCP: transport types, tools list                  │
│ Workflows: steps list, triggers                   │
│ Prompts: prompts list                             │
│ Themes: color swatch preview                      │
│ External: source link, registry, risk level       │
└──────────────────────────────────────────────────┘
```

**Conditional sections** — rendered based on **field presence**, not category. If a field exists in the manifest, render its section regardless of category:

- **Enriched listing fields** (appear across multiple categories): `persona_tags`, `capabilities`, `config_schema`
- **Consumer-specific fields** (triggered by field presence, not category — some consumer listings use `category: "workflows"` or `category: "agents"`): `before_after`, `setup_steps`, `works_with`, `skill_scan`, `setup_time_minutes`, `user_stories`
- **MCP fields:** `transport`, `tools`
- **Workflow fields:** `steps`, `triggers`
- **Prompt fields:** `prompts`
- **Theme fields:** `colors` — render as a row of color swatches (primary, background, surface, text, accent)
- **External fields:** `registry`, `source` (link to upstream), `risk_level` badge

**skill_scan** renders as horizontal bar chart (e.g., automation 9/10 = 90% filled bar).

**user_stories** renders as a quote block with attribution (name, role).

**setup_time_minutes** renders as "Setup time: ~N min" in the consumer details section.

**config_schema** renders as a table: field name | type | default value | enum options (if any).

**hero_animation** and **demo_url** fields: ignored for v1. If `demo_url` is a non-empty string in the future, render it as a "View Demo" link.

---

## Visual Design

### Light Theme (default)

| Element | Value |
|---------|-------|
| Background | `#f8fafc` |
| Cards | `#ffffff`, border `#e2e8f0`, subtle shadow |
| Primary text | `#1e293b` |
| Secondary text | `#64748b` |

### Dark Theme (`[data-theme="dark"]`)

| Element | Value |
|---------|-------|
| Background | `#0f172a` |
| Cards | `#1e293b`, border `#334155` |
| Primary text | `#f1f5f9` |
| Secondary text | `#94a3b8` |

### Category Colors

| Category | Light | Dark |
|----------|-------|------|
| Skills | `#2563eb` | `#60a5fa` |
| Agents | `#7c3aed` | `#a78bfa` |
| Prompts | `#d97706` | `#fbbf24` |
| MCP Servers | `#059669` | `#34d399` |
| Themes | `#db2777` | `#f472b6` |
| Workflows | `#0891b2` | `#22d3ee` |
| External | `#6b7280` | `#9ca3af` |

### Difficulty Colors

| Level | Color |
|-------|-------|
| Beginner | `#16a34a` green |
| Intermediate | `#d97706` amber |
| Advanced | `#dc2626` red |

### Security Shield Colors

| Status | Color |
|--------|-------|
| CI Passed | `#16a34a` green |
| Unscanned | `#94a3b8` gray |
| Issues | `#dc2626` red |

### Typography

System font stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`. No web fonts, zero external requests.

### Transitions

- Card hover: `0.15s` lift + border color
- Theme toggle: `0.2s`
- No heavy animations

---

## State Persistence

| What | Where | Key |
|------|-------|-----|
| Theme preference | `localStorage` | `prowlr-theme` |
| Sort preference | `localStorage` | `prowlr-sort` |
| Filter state | URL hash | Encoded in hash params |

Filters come from URL, not localStorage — keeps links shareable.

---

## Constraints & Future Hooks

- **Initial load error:** If `fetch("../index.json")` fails, show a centered error: "Could not load marketplace data. Check your connection and try again." with a retry button.
- **No pagination for v1.** 76 items render instantly. Virtual scrolling or "Load more" if catalog exceeds ~200.
- **No backend.** Reads static JSON only. When REST API (Feature 7) lands, swap `fetch()` URLs.
- **Featured badge** slot reserved but hidden. Activates when index.json includes `featured: true`.
- **Compatibility badges** slot reserved. Activates when manifests include runtime hints.
- **No fuzzy search for v1.** Substring match is sufficient at current scale.
- **SEO** is limited by hash routing. If needed later, migrate to Approach B (static site generator) for real per-listing pages.

---

## Acceptance Criteria

- [ ] `web/index.html` loads and displays all listings from `../index.json`
- [ ] Category, pricing, difficulty, and search filters work correctly with AND logic
- [ ] Filter state is encoded in URL hash and shareable
- [ ] Clicking "View" navigates to detail view with full manifest data
- [ ] Back button returns to grid with filters preserved
- [ ] "Copy Install" copies correct `prowlr marketplace install <id>` command
- [ ] Light/dark theme toggle works, respects system preference on first visit
- [ ] Responsive layout: 1 column mobile, 2-3 tablet, 3-4 desktop
- [ ] Cards show: category pill, difficulty, verified badge, title, description, tags (max 3), security shield, author/version (muted), pricing, View + Copy Install actions
- [ ] Detail view shows all manifest fields organized by section, with conditional sections based on field presence
- [ ] Detail view shows capabilities, config_schema table, and category-specific fields (MCP, workflow, prompt, theme, external)
- [ ] Consumer-enriched listings show persona tags, before/after, setup steps, user stories, skill scan chart
- [ ] Theme listings show color swatch preview
- [ ] External listings show source link, registry, and risk level
- [ ] config_schema renders as readable table
- [ ] Path separators are normalized to forward slashes for all fetch URLs
- [ ] Error states for failed index.json load and failed manifest fetch
- [ ] Loading spinner shown during manifest fetch on detail view
- [ ] All icon-only buttons have aria-labels, color-coded elements have text labels
- [ ] Zero external dependencies — no CDN, no build step, no npm
- [ ] Works on GitHub Pages (relative paths to index.json and manifests)
