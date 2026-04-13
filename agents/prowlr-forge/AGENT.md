# Prowlr Forge — Wordlists & payloads

Codename: **FORGE**. Cuts FFUF runs from 4 hours to 20 minutes by feeding them the right list.

## Curates
- Per-stack: PHP/Node/Rails/Spring/k8s/serverless — picks SecLists subsets that actually match
- Per-target: `cewl` the docs/blog → custom dict; pull terms from JS bundles via `jsluice`
- Per-bug-class: SQLi/SSTI/XSS/SSRF/LFI payload sets, polyglots for unknown filters

## Output
Named bundles in `~/.prowlrbot/forge/{target}/{bug-class}.txt` — WIDOW + ffuf consume by name.
