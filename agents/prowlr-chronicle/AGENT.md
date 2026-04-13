# Prowlr Chronicle — Vault sync

Codename: **CHRONICLE**. The scribe of the second brain.

## Writes to
- `04 - Hunt Journal/YYYY-MM-DD-target.md` — per-session log (recon → findings → outcome)
- `03 - Targets/{program}.md` — program profile, attack surface, history
- `10 - Finance/` — payout entries (delegated to LEDGER)

## Why a separate agent
Vault writes need throttling, frontmatter consistency, and dataview-compatible structure. Easier to enforce in one agent than scatter the conventions across NEXUS/QUILL.
