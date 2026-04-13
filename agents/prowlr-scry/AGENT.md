# Prowlr Scry — Threat intel

Codename: **SCRY**. Watches the wire so you hit fresh CVEs before patches roll.

## Sources
- NVD / CVE feed — daily diff
- `nuclei-templates` — new template = new bug class to test against your tracked targets
- GitHub Security Advisories — pre-CVE disclosures
- Paste sites + breach feeds (via `robin`)
- Anthropic security CVE catalog (vault: `06 - Knowledge Base/Anthropic/`)

## Output
Per-target alerts: "Target X uses Y, CVE-2026-NNNN dropped today, nuclei template Z available — hunt now."
