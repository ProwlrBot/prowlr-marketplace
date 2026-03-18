# Marketplace Web Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-file web frontend (`web/index.html`) for browsing the Prowlr Marketplace — grid view, detail view, filtering, search, light/dark theming, zero dependencies.

**Architecture:** Single HTML file with all CSS and JS inlined. Hash-based routing (`#/`, `#/listing/<id>`, `#/?q=...`). Fetches `../index.json` on load for grid, fetches individual `manifest.json` files on demand for detail views. Plain state object in memory, CSS custom properties for theming.

**Tech Stack:** Vanilla HTML/CSS/JS. No build tools, no frameworks, no external dependencies.

**Spec:** `docs/superpowers/specs/2026-03-17-web-frontend-design.md`

---

## File Structure

All work happens in a single file:

| File | Action | Responsibility |
|------|--------|---------------|
| `web/index.html` | Create | All HTML structure, CSS styles, and JS logic for the marketplace frontend |

The implementation is split into tasks by logical layer to keep each task focused and verifiable.

---

### Task 1: HTML Shell + CSS Foundation

**Files:**
- Create: `web/index.html`

Build the static HTML skeleton and complete CSS — theming, layout, cards, detail view, responsive breakpoints. No JS yet. This task produces a visually complete but non-functional page with hardcoded placeholder content.

- [ ] **Step 1: Create `web/` directory and `index.html` with HTML skeleton**

Write the complete HTML structure: doctype, head (meta, title, viewport), body with:
- Skip-to-content link (`<a href="#main" class="skip-link">Skip to content</a>`)
- `<header>` with wordmark, tagline, theme toggle button (aria-labeled), listing count span
- `<div id="filters">` with search input, category/pricing/difficulty/sort dropdowns
- `<main id="main">` with:
  - `<div id="spinner">` (loading state)
  - `<div id="error">` (error state with retry button, hidden)
  - `<div id="empty">` (empty filter state, hidden)
  - `<div id="grid">` (card container)
  - `<div id="detail">` (detail view, hidden)
- `<footer>` with links

The category dropdown options: All, Skills, Agents, Prompts, MCP Servers, Themes, Workflows, External.
The pricing dropdown: All, Free, Paid.
The difficulty dropdown: All, Beginner, Intermediate, Advanced.
The sort dropdown: Newest, A-Z, Category.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Prowlr Marketplace</title>
  <style>/* CSS goes here — see Step 2 */</style>
</head>
<body>
  <a href="#main" class="skip-link">Skip to content</a>
  <header>
    <div class="header-left">
      <h1 class="wordmark" tabindex="-1">Prowlr Marketplace</h1>
      <span class="tagline">The bazaar where agents shop</span>
    </div>
    <div class="header-right">
      <span id="listing-count"></span>
      <button id="theme-toggle" type="button" aria-label="Toggle dark mode">
        <span class="icon-sun">&#9728;</span>
        <span class="icon-moon">&#9790;</span>
      </button>
    </div>
  </header>

  <div id="filters">
    <input type="search" id="search" placeholder="Search listings..." aria-label="Search listings">
    <select id="filter-category" aria-label="Filter by category">
      <option value="">All categories</option>
      <option value="skills">Skills</option>
      <option value="agents">Agents</option>
      <option value="prompts">Prompts</option>
      <option value="mcp-servers">MCP Servers</option>
      <option value="themes">Themes</option>
      <option value="workflows">Workflows</option>
      <option value="external">External</option>
    </select>
    <select id="filter-pricing" aria-label="Filter by pricing">
      <option value="">All pricing</option>
      <option value="free">Free</option>
      <option value="paid">Paid</option>
    </select>
    <select id="filter-difficulty" aria-label="Filter by difficulty">
      <option value="">All levels</option>
      <option value="beginner">Beginner</option>
      <option value="intermediate">Intermediate</option>
      <option value="advanced">Advanced</option>
    </select>
    <select id="sort" aria-label="Sort order">
      <option value="newest">Newest</option>
      <option value="az">A-Z</option>
      <option value="category">Category</option>
    </select>
  </div>

  <main id="main">
    <div id="spinner"><div class="spin"></div></div>
    <div id="error" class="hidden">
      <span class="error-icon">!</span>
      <p>Could not load marketplace data. Check your connection and try again.</p>
      <button id="retry-btn" type="button">Retry</button>
    </div>
    <div id="empty" class="hidden">
      <p>No listings match your filters. Try broadening your search.</p>
    </div>
    <div id="grid" class="hidden"></div>
    <div id="detail" class="hidden"></div>
  </main>

  <footer>
    <span>ProwlrBot Marketplace</span>
    <nav>
      <a href="https://github.com/ProwlrBot/prowlr-marketplace">GitHub</a>
      <a href="https://github.com/ProwlrBot/prowlr-marketplace/blob/main/CONTRIBUTING.md">Contributing</a>
      <a href="https://github.com/ProwlrBot/prowlr-marketplace/blob/main/INSTALL.md">Install</a>
    </nav>
  </footer>

  <script>/* JS goes here — Task 3+ */</script>
</body>
</html>
```

- [ ] **Step 2: Write complete CSS inside the `<style>` tag**

CSS custom properties for theming (light default, dark via `[data-theme="dark"]`). All colors from the spec's Visual Design section.

Key CSS sections:
1. **Reset & base** — box-sizing, margin reset, body font/colors using `var()`
2. **Skip link** — visually hidden, visible on focus
3. **Header** — flex row, wordmark styling, theme toggle (show sun in dark mode, moon in light)
4. **Filter bar** — flex wrap, sticky positioning, input/select styling for both themes
5. **Grid** — `display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px;`
6. **Cards** — white bg (light) / dark bg (dark), border, border-radius, shadow, hover lift, flex column layout
7. **Card internals** — category pill (color per category using data attributes), difficulty badge, verified checkmark, title, description (2-line clamp), tags row, security shield, metadata row, pricing badge, action buttons
8. **Detail view** — max-width 800px centered, section headers, install command box, config table, skill scan bars, color swatches, quote blocks
9. **Spinner** — centered rotating circle
10. **Error/empty states** — centered with muted text
11. **Footer** — minimal, flex, muted
12. **Responsive** — `@media (max-width: 768px)` stack filters vertically, single column grid
13. **Transitions** — card hover 0.15s, theme toggle 0.2s
14. **Utility** — `.hidden { display: none !important; }`

Category pill colors via `data-category` attribute:
```css
.pill[data-category="skills"] { background: var(--cat-skills); }
.pill[data-category="agents"] { background: var(--cat-agents); }
/* ... etc for all 7 categories */
```

Difficulty badge colors via `data-difficulty`:
```css
.badge-difficulty[data-difficulty="beginner"] { background: var(--diff-beginner); }
.badge-difficulty[data-difficulty="intermediate"] { background: var(--diff-intermediate); }
.badge-difficulty[data-difficulty="advanced"] { background: var(--diff-advanced); }
```

- [ ] **Step 3: Verify the static page renders correctly**

Open `web/index.html` in a browser. Verify:
- Header, filter bar, spinner, footer all visible
- Toggle `data-theme="dark"` on `<html>` via DevTools — colors change
- Resize browser — grid and filter bar respond at 768px breakpoint
- Skip link visible on Tab press
- All dropdowns render with correct options

- [ ] **Step 4: Commit**

```bash
git add web/index.html
git commit -m "feat(web): add HTML shell and CSS foundation for marketplace frontend"
```

---

### Task 2: Theme Toggle + State Initialization

**Files:**
- Modify: `web/index.html` (JS section)

Wire up the theme toggle and initialize the app state object. This task adds the first JS — theme detection, toggle, localStorage persistence.

- [ ] **Step 1: Add theme initialization JS**

Inside the `<script>` tag, add:

```js
(function () {
  'use strict';

  // --- State ---
  var state = {
    listings: [],
    filtered: [],
    filters: { category: '', search: '', pricing: '', difficulty: '' },
    sort: 'newest',
    view: 'grid',
    currentListing: null
  };

  // --- Theme ---
  function initTheme() {
    var saved = localStorage.getItem('prowlr-theme');
    if (saved) {
      document.documentElement.setAttribute('data-theme', saved);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  }

  function toggleTheme() {
    var current = document.documentElement.getAttribute('data-theme');
    var next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('prowlr-theme', next);
  }

  // --- Init ---
  initTheme();
  document.getElementById('theme-toggle').addEventListener('click', toggleTheme);

  // Rest of app code will be added in subsequent tasks...

})();
```

- [ ] **Step 2: Verify theme toggle works**

Open in browser:
- First visit respects system preference
- Click theme toggle — switches between light and dark
- Reload page — preference persists
- Sun icon visible in dark mode, moon in light mode

- [ ] **Step 3: Commit**

```bash
git add web/index.html
git commit -m "feat(web): add theme toggle with system preference detection and localStorage"
```

---

### Task 3: Data Loading + Path Normalization

**Files:**
- Modify: `web/index.html` (JS section)

Fetch `../index.json`, normalize paths, populate state, show/hide loading/error states.

- [ ] **Step 1: Add data loading functions**

Add after the theme code, inside the IIFE:

```js
  // --- Helpers ---
  function show(el) { el.classList.remove('hidden'); }
  function hide(el) { el.classList.add('hidden'); }
  function normalizePath(p) { return p ? p.replace(/\\/g, '/') : ''; }
  function getTitle(listing) { return listing.title || listing.name || '(untitled)'; }
  function esc(str) {
    if (str == null) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  // --- DOM refs (all defined here so every task can use them) ---
  var elSpinner = document.getElementById('spinner');
  var elError = document.getElementById('error');
  var elEmpty = document.getElementById('empty');
  var elGrid = document.getElementById('grid');
  var elDetail = document.getElementById('detail');
  var elCount = document.getElementById('listing-count');
  var elRetry = document.getElementById('retry-btn');
  var elSearch = document.getElementById('search');
  var elCat = document.getElementById('filter-category');
  var elPricing = document.getElementById('filter-pricing');
  var elDiff = document.getElementById('filter-difficulty');
  var elSort = document.getElementById('sort');

  // --- Data loading ---
  function loadIndex() {
    hide(elError);
    hide(elGrid);
    hide(elDetail);
    hide(elEmpty);
    show(elSpinner);

    fetch('../index.json')
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (data) {
        hide(elSpinner);
        state.listings = (data.listings || []).map(function (l) {
          l.path = normalizePath(l.path);
          l.manifest = normalizePath(l.manifest);
          return l;
        });
        totalListingCount = state.listings.length;
        elCount.textContent = totalListingCount + ' listing' + (totalListingCount !== 1 ? 's' : '');
        applyFiltersAndRender();
      })
      .catch(function () {
        hide(elSpinner);
        show(elError);
      });
  }

  elRetry.addEventListener('click', loadIndex);
  loadIndex();
```

- [ ] **Step 2: Verify data loads**

Open in browser, check DevTools Network tab:
- `../index.json` fetched successfully
- Spinner disappears after load
- Listing count shows "76 listings" (or current count)
- If you rename index.json temporarily, error state shows with retry button

- [ ] **Step 3: Commit**

```bash
git add web/index.html
git commit -m "feat(web): add index.json loading with path normalization and error handling"
```

---

### Task 4: Card Rendering + Grid View

**Files:**
- Modify: `web/index.html` (JS section)

Build the card rendering function and initial grid display. This is the core visual output.

- [ ] **Step 1: Add card builder and grid renderer**

```js
  // --- Card rendering ---
  function buildCard(listing) {
    var card = document.createElement('div');
    card.className = 'card';

    // Top row: category pill + difficulty + verified
    var topRow = document.createElement('div');
    topRow.className = 'card-top';

    var pill = document.createElement('span');
    pill.className = 'pill';
    pill.setAttribute('data-category', listing.category || '');
    pill.textContent = listing.category || 'unknown';
    topRow.appendChild(pill);

    if (listing.difficulty) {
      var diff = document.createElement('span');
      diff.className = 'badge-difficulty';
      diff.setAttribute('data-difficulty', listing.difficulty);
      diff.textContent = listing.difficulty;
      topRow.appendChild(diff);
    }

    if (listing.verified) {
      var verified = document.createElement('span');
      verified.className = 'badge-verified';
      verified.setAttribute('aria-label', 'Verified');
      verified.textContent = '\u2713';
      topRow.appendChild(verified);
    }

    card.appendChild(topRow);

    // Title
    var title = document.createElement('h3');
    title.className = 'card-title';
    title.textContent = getTitle(listing);
    card.appendChild(title);

    // Description
    var desc = document.createElement('p');
    desc.className = 'card-desc';
    desc.textContent = listing.description || '';
    card.appendChild(desc);

    // Tags (max 3)
    var tags = (listing.tags || []).slice(0, 3);
    if (tags.length > 0) {
      var tagsRow = document.createElement('div');
      tagsRow.className = 'card-tags';
      tags.forEach(function (t) {
        var tag = document.createElement('span');
        tag.className = 'tag';
        tag.textContent = t;
        tagsRow.appendChild(tag);
      });
      card.appendChild(tagsRow);
    }

    // Security shield
    var shield = document.createElement('div');
    shield.className = 'card-shield';
    var secStatus = listing.security_status || 'unscanned';
    shield.setAttribute('data-status', secStatus);
    var shieldIcon = document.createElement('span');
    shieldIcon.className = 'shield-icon';
    shieldIcon.textContent = '\u{1F6E1}';
    shield.appendChild(shieldIcon);
    var shieldText = document.createElement('span');
    shieldText.textContent = secStatus === 'passed' ? 'CI Passed' : secStatus === 'issues' ? 'Issues' : 'Unscanned';
    shield.appendChild(shieldText);
    card.appendChild(shield);

    // Metadata row: author, version, pricing
    var meta = document.createElement('div');
    meta.className = 'card-meta';
    var authorVer = document.createElement('span');
    authorVer.className = 'card-author';
    authorVer.textContent = (listing.author || 'unknown') + ' \u00B7 v' + (listing.version || '?');
    meta.appendChild(authorVer);
    var pricing = document.createElement('span');
    pricing.className = 'badge-pricing';
    pricing.textContent = listing.pricing_model === 'free' ? 'Free' : listing.pricing_model || 'Free';
    meta.appendChild(pricing);
    card.appendChild(meta);

    // Reserved slots (hidden)
    var featured = document.createElement('div');
    featured.className = 'card-featured hidden';
    card.appendChild(featured);
    var compat = document.createElement('div');
    compat.className = 'card-compat hidden';
    card.appendChild(compat);

    // Actions
    var actions = document.createElement('div');
    actions.className = 'card-actions';

    var viewBtn = document.createElement('button');
    viewBtn.className = 'btn btn-view';
    viewBtn.textContent = 'View';
    viewBtn.addEventListener('click', function () {
      window.location.hash = '#/listing/' + listing.id;
    });
    actions.appendChild(viewBtn);

    var copyBtn = document.createElement('button');
    copyBtn.className = 'btn btn-copy';
    copyBtn.textContent = 'Copy Install';
    copyBtn.setAttribute('aria-label', 'Copy install command for ' + getTitle(listing));
    copyBtn.addEventListener('click', function () {
      var cmd = 'prowlr marketplace install ' + listing.id;
      navigator.clipboard.writeText(cmd).then(function () {
        copyBtn.textContent = 'Copied!';
        setTimeout(function () { copyBtn.textContent = 'Copy Install'; }, 1800);
      }).catch(function () {
        copyBtn.textContent = 'Failed';
        setTimeout(function () { copyBtn.textContent = 'Copy Install'; }, 1800);
      });
    });
    actions.appendChild(copyBtn);

    card.appendChild(actions);
    return card;
  }

  // --- Grid rendering ---
  function renderGrid() {
    while (elGrid.firstChild) elGrid.removeChild(elGrid.firstChild);

    if (state.filtered.length === 0) {
      hide(elGrid);
      show(elEmpty);
      return;
    }

    hide(elEmpty);
    show(elGrid);
    state.filtered.forEach(function (listing) {
      elGrid.appendChild(buildCard(listing));
    });
  }

  // --- Stub: applyFiltersAndRender (full implementation in Task 5) ---
  function applyFiltersAndRender() {
    state.filtered = state.listings.slice(); // no filtering yet
    renderGrid();
  }
```

- [ ] **Step 2: Verify cards render**

Open in browser:
- All 76 listings display as cards in a responsive grid
- Each card shows: category pill (colored), difficulty badge, title, description (truncated), tags (max 3), security shield (gray "Unscanned"), author/version, pricing badge, View + Copy Install buttons
- Cards hover with lift effect
- "Copy Install" copies correct command to clipboard
- Resize to mobile — single column
- Verified badge shows only on listings that have `verified: true`

- [ ] **Step 3: Commit**

```bash
git add web/index.html
git commit -m "feat(web): add card rendering and grid view for all marketplace listings"
```

---

### Task 5: Filtering, Sorting, and Search

**Files:**
- Modify: `web/index.html` (JS section)

Replace the stub `applyFiltersAndRender` with full filtering/sorting logic. Wire up filter controls with debounced search.

- [ ] **Step 1: Implement filtering and sorting**

Replace the `applyFiltersAndRender` stub. Note: DOM refs (`elSearch`, `elCat`, `elPricing`, `elDiff`, `elSort`) were already defined in Task 3.

```js
  // --- Stub for hash sync (full implementation in Task 6) ---
  function syncFiltersToHash() { /* implemented in Task 6 */ }

  var searchTimeout = null;
  var totalListingCount = 0; // set in loadIndex, used for "N of M" display

  function applyFiltersAndRender() {
    var q = state.filters.search.toLowerCase();
    var cat = state.filters.category;
    var pricing = state.filters.pricing;
    var diff = state.filters.difficulty;

    state.filtered = state.listings.filter(function (l) {
      if (cat && l.category !== cat) return false;
      if (diff && l.difficulty !== diff) return false;
      if (pricing === 'free' && l.pricing_model !== 'free') return false;
      if (pricing === 'paid' && l.pricing_model === 'free') return false;
      if (q) {
        var haystack = (
          getTitle(l) + ' ' +
          (l.description || '') + ' ' +
          (l.tags || []).join(' ')
        ).toLowerCase();
        if (haystack.indexOf(q) === -1) return false;
      }
      return true;
    });

    // Sort
    var sortBy = state.sort;
    state.filtered.sort(function (a, b) {
      if (sortBy === 'az') {
        return getTitle(a).localeCompare(getTitle(b));
      }
      if (sortBy === 'category') {
        var c = (a.category || '').localeCompare(b.category || '');
        if (c !== 0) return c;
        return getTitle(a).localeCompare(getTitle(b));
      }
      // newest: preserve index.json order (no date/timestamp field in index data).
      // Index order is determined by build_index.py scan order, which is roughly
      // alphabetical by directory. When a date field is added, sort by it here.
      return 0;
    });

    if (state.filtered.length === totalListingCount) {
      elCount.textContent = totalListingCount + ' listing' + (totalListingCount !== 1 ? 's' : '');
    } else {
      elCount.textContent = state.filtered.length + ' of ' + totalListingCount + ' listings';
    }
    renderGrid();
  }

  function onFilterChange() {
    state.filters.category = elCat.value;
    state.filters.pricing = elPricing.value;
    state.filters.difficulty = elDiff.value;
    state.sort = elSort.value;
    syncFiltersToHash();
    applyFiltersAndRender();
  }

  function onSearchInput() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(function () {
      state.filters.search = elSearch.value;
      syncFiltersToHash();
      applyFiltersAndRender();
    }, 200);
  }

  elCat.addEventListener('change', onFilterChange);
  elPricing.addEventListener('change', onFilterChange);
  elDiff.addEventListener('change', onFilterChange);
  elSort.addEventListener('change', onFilterChange);
  elSearch.addEventListener('input', onSearchInput);

  // Restore sort preference
  var savedSort = localStorage.getItem('prowlr-sort');
  if (savedSort) {
    elSort.value = savedSort;
    state.sort = savedSort;
  }
  elSort.addEventListener('change', function () {
    localStorage.setItem('prowlr-sort', elSort.value);
  });
```

- [ ] **Step 2: Verify filtering and sorting**

Open in browser:
- Type "api" in search — only listings with "api" in title/description/tags appear
- Select "Skills" category — only skills shown
- Select "Free" pricing — only free listings shown
- Select "Beginner" difficulty — only beginner listings shown
- Combine filters — AND logic works (e.g., skills + beginner = only beginner skills)
- Sort A-Z — alphabetical order
- Sort by Category — grouped by category, alphabetical within
- Listing count updates with each filter change
- Clear all filters — all listings return
- Search is debounced (type fast, only one re-render after 200ms pause)

- [ ] **Step 3: Commit**

```bash
git add web/index.html
git commit -m "feat(web): add filtering, sorting, and debounced search"
```

---

### Task 6: Hash Routing

**Files:**
- Modify: `web/index.html` (JS section)

Implement hash-based routing: encode filter state in URL, parse on load, handle `#/listing/<id>` and `#/category/<name>` routes. Back/forward navigation.

- [ ] **Step 1: Add hash sync and routing**

```js
  // --- Hash routing ---
  function syncFiltersToHash() {
    if (state.view === 'detail') return; // don't overwrite detail hash
    var params = [];
    if (state.filters.search) params.push('q=' + encodeURIComponent(state.filters.search));
    if (state.filters.category) params.push('category=' + encodeURIComponent(state.filters.category));
    if (state.filters.pricing) params.push('pricing=' + encodeURIComponent(state.filters.pricing));
    if (state.filters.difficulty) params.push('difficulty=' + encodeURIComponent(state.filters.difficulty));
    if (state.sort && state.sort !== 'newest') params.push('sort=' + encodeURIComponent(state.sort));
    var hash = params.length > 0 ? '#/?' + params.join('&') : '#/';
    if (window.location.hash !== hash) {
      history.replaceState(null, '', hash);
    }
  }

  function parseHash() {
    var hash = window.location.hash || '#/';

    // Detail view: #/listing/<id>
    var listingMatch = hash.match(/^#\/listing\/(.+)$/);
    if (listingMatch) {
      var id = decodeURIComponent(listingMatch[1]);
      showDetailView(id);
      return;
    }

    // Category shortcut: #/category/<name>
    var catMatch = hash.match(/^#\/category\/(.+)$/);
    if (catMatch) {
      state.filters.category = decodeURIComponent(catMatch[1]);
      elCat.value = state.filters.category;
    }

    // Filter params: #/?q=...&category=...
    var paramMatch = hash.match(/^#\/\?(.+)$/);
    if (paramMatch) {
      var pairs = paramMatch[1].split('&');
      pairs.forEach(function (pair) {
        var kv = pair.split('=');
        var key = decodeURIComponent(kv[0]);
        var val = decodeURIComponent(kv[1] || '');
        if (key === 'q') { state.filters.search = val; elSearch.value = val; }
        if (key === 'category') { state.filters.category = val; elCat.value = val; }
        if (key === 'pricing') { state.filters.pricing = val; elPricing.value = val; }
        if (key === 'difficulty') { state.filters.difficulty = val; elDiff.value = val; }
        if (key === 'sort') { state.sort = val; elSort.value = val; }
      });
    }

    // Show grid
    showGridView();
  }

  function showGridView() {
    state.view = 'grid';
    state.currentListing = null;
    hide(elDetail);
    show(elGrid);
    document.getElementById('filters').classList.remove('hidden');
    // Restore filter UI controls from state
    elSearch.value = state.filters.search || '';
    elCat.value = state.filters.category || '';
    elPricing.value = state.filters.pricing || '';
    elDiff.value = state.filters.difficulty || '';
    applyFiltersAndRender();
    // Focus management — wordmark has tabindex="-1" set in HTML
    document.querySelector('.wordmark').focus();
  }

  function showDetailView(id) {
    // Stub — full implementation in Task 7
    state.view = 'detail';
  }

  window.addEventListener('hashchange', parseHash);
```

Then modify `loadIndex` success handler to call `parseHash()` instead of `applyFiltersAndRender()`:

Replace `applyFiltersAndRender();` at end of loadIndex success with:
```js
        parseHash();
```

- [ ] **Step 2: Verify routing**

- Navigate to `web/index.html#/?q=api&category=skills` — search filled with "api", category set to "skills", grid filtered
- Change a filter — URL hash updates
- Navigate to `#/category/agents` — category filter set, grid shows agents
- Click browser back — previous filter state restored
- Copy a filter URL to new tab — same filter state loads

- [ ] **Step 3: Commit**

```bash
git add web/index.html
git commit -m "feat(web): add hash-based routing with filter state in URL"
```

---

### Task 7: Detail View

**Files:**
- Modify: `web/index.html` (JS section)

Implement the full detail view: fetch manifest, render all sections conditionally, back navigation, error/loading states.

- [ ] **Step 1: Implement showDetailView function**

Replace the stub `showDetailView`:

```js
  function showDetailView(id) {
    state.view = 'detail';

    // Find listing in cached data
    var listing = null;
    for (var i = 0; i < state.listings.length; i++) {
      if (state.listings[i].id === id) { listing = state.listings[i]; break; }
    }

    if (!listing) {
      elDetail.innerHTML = '<div class="detail-error"><p>Listing not found. <a href="#/">Back to listings</a></p></div>';
      hide(elGrid);
      hide(elSpinner);
      hide(elEmpty);
      document.getElementById('filters').classList.add('hidden');
      show(elDetail);
      return;
    }

    // Show loading
    hide(elGrid);
    hide(elEmpty);
    document.getElementById('filters').classList.add('hidden');
    elDetail.innerHTML = '<div id="detail-spinner"><div class="spin"></div></div>';
    show(elDetail);

    // Fetch full manifest
    var manifestPath = listing.manifest
      ? '../' + listing.manifest
      : '../' + listing.path + '/manifest.json';

    fetch(manifestPath)
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (manifest) {
        state.currentListing = manifest;
        renderDetailView(manifest, listing);
      })
      .catch(function () {
        // Show error notice + fallback render with index data
        renderDetailView(listing, listing, true);
      });
  }

  function renderDetailView(manifest, indexEntry, fetchFailed) {
    var html = '';

    // Back link
    html += '<a href="#/" class="detail-back">&larr; Back to listings</a>';

    // Error notice if manifest fetch failed
    if (fetchFailed) {
      html += '<div class="detail-error-notice">Could not load full listing details. Showing summary from index. <a href="#/">Back to listings</a></div>';
    }

    // Top badges
    html += '<div class="detail-badges">';
    html += '<span class="pill" data-category="' + esc(manifest.category || indexEntry.category || '') + '">' + esc(manifest.category || indexEntry.category || '') + '</span>';
    if (manifest.difficulty || indexEntry.difficulty) {
      html += '<span class="badge-difficulty" data-difficulty="' + esc(manifest.difficulty || indexEntry.difficulty) + '">' + esc(manifest.difficulty || indexEntry.difficulty) + '</span>';
    }
    if (manifest.verified || indexEntry.verified) {
      html += '<span class="badge-verified" aria-label="Verified">&#10003;</span>';
    }
    html += '</div>';

    // Title + pricing
    html += '<div class="detail-header">';
    html += '<h2 class="detail-title" tabindex="-1">' + esc(getTitle(manifest) || getTitle(indexEntry)) + '</h2>';
    html += '<span class="badge-pricing">' + esc(manifest.pricing_model === 'free' ? 'Free' : manifest.pricing_model || indexEntry.pricing_model || 'Free') + '</span>';
    html += '</div>';

    // Author, version, license
    html += '<p class="detail-meta">' + esc(manifest.author || indexEntry.author || '') + ' &middot; v' + esc(manifest.version || indexEntry.version || '?');
    if (manifest.license) html += ' &middot; ' + esc(manifest.license);
    html += '</p>';

    // Install command (copy button uses addEventListener, not inline onclick, to prevent XSS)
    var installId = manifest.id || indexEntry.id;
    html += '<div class="install-box">';
    html += '<code>prowlr marketplace install ' + esc(installId) + '</code>';
    html += '<button class="btn btn-copy detail-copy-btn" aria-label="Copy install command">Copy</button>';
    html += '</div>';

    // Description
    html += '<section class="detail-section"><h3>Description</h3>';
    html += '<p>' + esc(manifest.description || indexEntry.description || '') + '</p></section>';

    // Security & Capabilities
    var caps = manifest.capabilities || [];
    html += '<section class="detail-section"><h3>Security & Capabilities</h3>';
    var secStatus = manifest.security_status || indexEntry.security_status || 'unscanned';
    html += '<div class="card-shield" data-status="' + esc(secStatus) + '"><span class="shield-icon">&#128737;</span> ';
    html += secStatus === 'passed' ? 'CI Passed' : secStatus === 'issues' ? 'Issues Found' : 'Unscanned';
    html += '</div>';
    if (caps.length > 0) {
      html += '<div class="detail-caps">';
      caps.forEach(function (c) { html += '<span class="tag">' + esc(c) + '</span>'; });
      html += '</div>';
    }
    if (manifest.min_prowlrbot_version) {
      html += '<p class="detail-meta">Min ProwlrBot: v' + esc(manifest.min_prowlrbot_version) + '</p>';
    }
    html += '</section>';

    // Configuration (config_schema)
    if (manifest.config_schema && Object.keys(manifest.config_schema).length > 0) {
      html += '<section class="detail-section"><h3>Configuration</h3>';
      html += '<table class="config-table"><thead><tr><th>Field</th><th>Type</th><th>Default</th><th>Options</th></tr></thead><tbody>';
      Object.keys(manifest.config_schema).forEach(function (key) {
        var field = manifest.config_schema[key];
        html += '<tr>';
        html += '<td><code>' + esc(key) + '</code></td>';
        html += '<td>' + esc(field.type || '') + '</td>';
        html += '<td>' + esc(field.default != null ? String(field.default) : '') + '</td>';
        html += '<td>' + esc(field.enum ? field.enum.join(', ') : '') + '</td>';
        html += '</tr>';
      });
      html += '</tbody></table></section>';
    }

    // Tags (all)
    var allTags = manifest.tags || indexEntry.tags || [];
    if (allTags.length > 0) {
      html += '<section class="detail-section"><h3>Tags</h3><div class="card-tags">';
      allTags.forEach(function (t) { html += '<span class="tag">' + esc(t) + '</span>'; });
      html += '</div></section>';
    }

    // Links
    if (manifest.repository) {
      html += '<section class="detail-section"><h3>Links</h3>';
      html += '<p>Repository: <a href="' + esc(manifest.repository) + '" target="_blank" rel="noopener">' + esc(manifest.repository) + '</a></p>';
      if (manifest.license) html += '<p>License: ' + esc(manifest.license) + '</p>';
      html += '</section>';
    }

    // Persona tags (cross-category)
    var personas = manifest.persona_tags || indexEntry.persona_tags || [];
    if (personas.length > 0) {
      html += '<section class="detail-section"><h3>Personas</h3><div class="card-tags">';
      personas.forEach(function (p) { html += '<span class="tag">' + esc(p) + '</span>'; });
      html += '</div></section>';
    }

    // --- Consumer-specific fields (field-presence-based) ---

    // Before/After
    if (manifest.before_after) {
      html += '<section class="detail-section"><h3>Before &amp; After</h3>';
      html += '<div class="before-after">';
      html += '<div class="ba-before"><strong>Before:</strong> ' + esc(manifest.before_after.before || '') + '</div>';
      html += '<div class="ba-after"><strong>After:</strong> ' + esc(manifest.before_after.after || '') + '</div>';
      if (manifest.before_after.time_saved) {
        html += '<div class="ba-saved">Time saved: ' + esc(manifest.before_after.time_saved) + '</div>';
      }
      html += '</div></section>';
    }

    // Setup time
    if (manifest.setup_time_minutes) {
      html += '<p class="detail-meta">Setup time: ~' + esc(String(manifest.setup_time_minutes)) + ' min</p>';
    }

    // Works with
    if (manifest.works_with && manifest.works_with.length > 0) {
      html += '<section class="detail-section"><h3>Works With</h3><div class="card-tags">';
      manifest.works_with.forEach(function (w) { html += '<span class="tag">' + esc(w) + '</span>'; });
      html += '</div></section>';
    }

    // Setup steps
    if (manifest.setup_steps && manifest.setup_steps.length > 0) {
      html += '<section class="detail-section"><h3>Setup Steps</h3><ol class="setup-steps">';
      manifest.setup_steps.forEach(function (s) {
        html += '<li>' + esc(s.instruction || '') + '</li>';
      });
      html += '</ol></section>';
    }

    // User stories
    if (manifest.user_stories && manifest.user_stories.length > 0) {
      html += '<section class="detail-section"><h3>User Stories</h3>';
      manifest.user_stories.forEach(function (s) {
        html += '<blockquote class="user-story">';
        html += '<p>&ldquo;' + esc(s.quote || '') + '&rdquo;</p>';
        html += '<cite>&mdash; ' + esc(s.name || '') + ', ' + esc(s.role || '') + '</cite>';
        html += '</blockquote>';
      });
      html += '</section>';
    }

    // Skill scan
    if (manifest.skill_scan) {
      html += '<section class="detail-section"><h3>Skill Scan</h3><div class="skill-scan">';
      Object.keys(manifest.skill_scan).forEach(function (key) {
        var val = manifest.skill_scan[key];
        html += '<div class="scan-bar">';
        html += '<span class="scan-label">' + esc(key) + '</span>';
        var pct = Math.min(100, Math.max(0, val * 10));
        html += '<div class="scan-track"><div class="scan-fill" style="width:' + pct + '%"></div></div>';
        html += '<span class="scan-val">' + val + '/10</span>';
        html += '</div>';
      });
      html += '</div></section>';
    }

    // --- Category-specific fields ---

    // MCP: transport, tools
    if (manifest.transport) {
      html += '<section class="detail-section"><h3>Transport</h3><div class="card-tags">';
      (Array.isArray(manifest.transport) ? manifest.transport : [manifest.transport]).forEach(function (t) {
        html += '<span class="tag">' + esc(t) + '</span>';
      });
      html += '</div></section>';
    }
    if (manifest.tools && Array.isArray(manifest.tools)) {
      html += '<section class="detail-section"><h3>Tools</h3><div class="card-tags">';
      manifest.tools.forEach(function (t) { html += '<span class="tag">' + esc(t) + '</span>'; });
      html += '</div></section>';
    }

    // Workflows: steps, triggers
    if (manifest.steps && Array.isArray(manifest.steps)) {
      html += '<section class="detail-section"><h3>Workflow Steps</h3><ol>';
      manifest.steps.forEach(function (s) { html += '<li>' + esc(s) + '</li>'; });
      html += '</ol></section>';
    }
    if (manifest.triggers && Array.isArray(manifest.triggers)) {
      html += '<section class="detail-section"><h3>Triggers</h3><div class="card-tags">';
      manifest.triggers.forEach(function (t) { html += '<span class="tag">' + esc(t) + '</span>'; });
      html += '</div></section>';
    }

    // Prompts: prompts list
    if (manifest.prompts && Array.isArray(manifest.prompts)) {
      html += '<section class="detail-section"><h3>Prompts</h3><div class="card-tags">';
      manifest.prompts.forEach(function (p) { html += '<span class="tag">' + esc(p) + '</span>'; });
      html += '</div></section>';
    }

    // Themes: colors
    if (manifest.colors && typeof manifest.colors === 'object') {
      html += '<section class="detail-section"><h3>Color Palette</h3><div class="color-swatches">';
      Object.keys(manifest.colors).forEach(function (key) {
        html += '<div class="swatch"><div class="swatch-color" style="background:' + esc(manifest.colors[key]) + '"></div><span>' + esc(key) + '</span></div>';
      });
      html += '</div></section>';
    }

    // External: source, registry, risk_level
    if (manifest.source) {
      html += '<section class="detail-section"><h3>Source</h3>';
      html += '<p>Registry: ' + esc(manifest.registry || '') + '</p>';
      html += '<p>Source: <a href="' + esc(manifest.source) + '" target="_blank" rel="noopener">' + esc(manifest.source) + '</a></p>';
      if (manifest.risk_level) {
        html += '<p>Risk level: <span class="badge-risk" data-risk="' + esc(manifest.risk_level) + '">' + esc(manifest.risk_level) + '</span></p>';
      }
      html += '</section>';
    }

    // hero_animation, demo_url: ignored for v1
    // TODO: if demo_url is non-empty in future, render as "View Demo" link

    elDetail.innerHTML = html;
    show(elDetail);

    // Attach copy button event listener (avoids inline onclick XSS risk)
    var detailCopyBtn = elDetail.querySelector('.detail-copy-btn');
    if (detailCopyBtn) {
      var cmd = 'prowlr marketplace install ' + installId;
      detailCopyBtn.addEventListener('click', function () {
        navigator.clipboard.writeText(cmd).then(function () {
          detailCopyBtn.textContent = 'Copied!';
          setTimeout(function () { detailCopyBtn.textContent = 'Copy'; }, 1800);
        }).catch(function () {
          detailCopyBtn.textContent = 'Failed';
          setTimeout(function () { detailCopyBtn.textContent = 'Copy'; }, 1800);
        });
      });
    }

    // Focus management — move focus to title
    var titleEl = elDetail.querySelector('.detail-title');
    if (titleEl) titleEl.focus();
  }

  // Note: esc() is defined in Task 3 helpers section
```

- [ ] **Step 2: Verify detail view**

Test with multiple listing types:
- Click "View" on a skill (e.g., api-tester) — shows description, capabilities, config table, tags, repository link
- Click "View" on an agent — shows similar fields
- Navigate to `#/listing/meal-planner` — shows consumer fields: before/after, setup steps, user stories, skill scan bars, works with, setup time
- Click "Back to listings" — returns to grid with filters preserved
- Browser back button works
- Copy install command works in detail view
- If you temporarily break a manifest path — fallback renders with index data + error message

- [ ] **Step 3: Commit**

```bash
git add web/index.html
git commit -m "feat(web): add detail view with conditional sections for all listing types"
```

---

### Task 8: Polish and Final Verification

**Files:**
- Modify: `web/index.html`

Final CSS polish, edge case fixes, and comprehensive verification pass.

- [ ] **Step 1: CSS polish pass**

Review and fix:
- Card spacing consistency (padding, margins, gap)
- Detail view section spacing
- Skill scan bar styling (track height, fill color, rounded corners)
- Color swatch sizing (40x40px square with label below)
- Before/after styling (subtle background differentiation)
- User story blockquote styling (left border accent, italic quote)
- Config table styling (alternating row backgrounds, monospace code font for field names)
- Install command box styling (dark background, monospace, copy button aligned right)
- Filter bar mobile stacking (vertical layout below 768px)
- Footer alignment and spacing

- [ ] **Step 2: Accessibility pass**

Verify:
- Tab through entire page — logical focus order
- Theme toggle has `aria-label` that updates ("Switch to dark mode" / "Switch to light mode")
- Copy buttons have `aria-label` with listing name
- Color-coded elements (difficulty, security, category pills) all have text content (not color-only)
- Skip link works (Tab → Enter → focus jumps to main)
- Detail view title gets focus on navigation
- All images (none currently) would have alt text

- [ ] **Step 3: Cross-browser spot check**

Open in:
- Chrome: full functionality
- Firefox: verify CSS grid, custom properties, clipboard API
- Edge: basic rendering check
- Mobile viewport (Chrome DevTools device toolbar): responsive layout

- [ ] **Step 4: Commit**

```bash
git add web/index.html
git commit -m "feat(web): polish CSS, accessibility, and cross-browser compatibility"
```

---

### Task 9: Final Commit and Verification

**Files:**
- No new files

Run through all acceptance criteria from the spec.

- [ ] **Step 1: Acceptance criteria checklist**

Verify each item:
1. `web/index.html` loads and displays all listings from `../index.json` — YES/NO
2. Category, pricing, difficulty, and search filters work with AND logic — YES/NO
3. Filter state is encoded in URL hash and shareable — YES/NO
4. Clicking "View" navigates to detail view with full manifest data — YES/NO
5. Back button returns to grid with filters preserved — YES/NO
6. "Copy Install" copies correct command — YES/NO
7. Light/dark theme toggle works, respects system preference — YES/NO
8. Responsive layout: 1 col mobile, 2-3 tablet, 3-4 desktop — YES/NO
9. Cards show all specified fields — YES/NO
10. Detail view shows conditional sections based on field presence — YES/NO
11. Consumer listings show persona tags, before/after, setup steps, user stories, skill scan — YES/NO
12. Theme listings show color swatches — YES/NO
13. External listings show source, registry, risk level — YES/NO
14. config_schema renders as table — YES/NO
15. Path separators normalized — YES/NO
16. Error states for failed loads — YES/NO
17. Loading spinner during manifest fetch — YES/NO
18. All icon-only buttons have aria-labels — YES/NO
19. Zero external dependencies — YES/NO
20. Works on GitHub Pages paths — YES/NO

- [ ] **Step 2: Final commit if any fixes were needed**

```bash
git add web/index.html
git commit -m "fix(web): address acceptance criteria issues found during verification"
```

Only commit if changes were made. If all criteria pass, skip this step.
