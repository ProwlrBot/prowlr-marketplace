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
- Contains a URL and a UI description: Mode 1 (Reference)
- Contains a UI description but no URL: Mode 2 (Showcase)
- Contains 2+ URLs and "design system" or "combine": Mode 3 (Design System)
- Says /ui-share: Share flow

## Mode 1 - Reference (/ui-ref <url>)

1. Run: python skills/ui-craftsman/scripts/validate.py <url>
   - Exit non-zero: tell user URL is blocked (private/internal address)
2. Run: python skills/ui-craftsman/scripts/extract.py <url> --out /tmp/ui-craftsman-<hash>/
   - Exit non-zero: tell user extraction failed
3. Read /tmp/ui-craftsman-<hash>/tokens.json
4. Read ~/.claude/memory/ui-prefs.md if exists
5. Generate preview.html — self-contained, no external scripts
6. Run: python skills/ui-craftsman/scripts/serve.py /tmp/ui-craftsman-<hash>/preview.html
7. Tell user the URL and describe what is visible (repeat every response)
8. Iterate on feedback until user approves
9. Generate production React/TypeScript component(s) — max 200 lines per file, split into sub-components if needed
10. Update ~/.claude/memory/ui-prefs.md

## Mode 2 - Showcase (/ui-show <description>)

1. Read ~/.claude/memory/ui-prefs.md if exists
2. Create /tmp/ui-craftsman-<hash>/
3. Generate 4 HTML files:
   - direction-A.html: Terminal Pro (dark, monospace, sharp) — always
   - direction-B/C/D.html: from aesthetic classes based on description + preferences
   - Fallback when no prefs: Bold Brand, Data Rich, Minimal Light
4. Run: python skills/ui-craftsman/scripts/serve.py --gallery direction-A.html direction-B.html direction-C.html direction-D.html
5. Tell user URL and describe each direction in one sentence
6. User picks direction: generate React/TypeScript
7. Update ~/.claude/memory/ui-prefs.md

## Mode 3 - Design System (/ui-system <url1> <url2> ...)

1. validate.py on each URL — abort if any fail
2. extract.py for each URL in order
3. Synthesize tokens: url1 takes precedence for all conflicts
4. Write to current project directory:
   - tokens.css, components/Button.tsx, Card.tsx, Input.tsx, Badge.tsx, Nav.tsx, Table.tsx, README.md
5. serve.py a preview page showing all components
6. Update ~/.claude/memory/ui-prefs.md

## Share Flow (/ui-share)

Run share.py with: --title, --prompt, --aesthetic, --mode, --screenshot, --author, --repo-dir
See scripts/share.py --help for full argument list.

## Error Handling

- validate.py exits 1: "That URL is blocked for security reasons. Please use a public URL."
- extract.py exits 1: "Could not extract design tokens. The site may require login or block automation."
- serve.py exits 1: "Could not start preview server (all ports 8400-8500 in use). Close other servers and try again."
- playwright not installed: "Run: playwright install chromium from skills/ui-craftsman/scripts/ (after pip install -r requirements.txt)"
- gh not installed (share fallback): "Install GitHub CLI from https://cli.github.com then run: gh auth login"

## During a Session

Always include the localhost preview URL in every response while a server is running.
Describe what is visible on screen in 1-2 sentences with every URL reminder.

## After User Picks

1. Generate React/TypeScript production code
2. Keep each component file under 200 lines — split into sub-components if needed
3. Use safe rendering patterns only (textContent, JSX, no raw markup injection)
4. Update ~/.claude/memory/ui-prefs.md

## Preference Memory Format

File: ~/.claude/memory/ui-prefs.md

Frontmatter: name: ui-preferences, type: user

Sections:
- Aesthetic Profile: base style, border radius, gradients, typography, accent, spacing, cards, nav
- Session History: one line per session: date, command, chosen direction

Update rule: append to Session History after each pick. After 3+ sessions, rewrite Aesthetic Profile.

## Setup (first time)

  cd skills/ui-craftsman
  pip install -r scripts/requirements.txt
  playwright install chromium
  gh auth login   # only for /ui-share PR fallback
