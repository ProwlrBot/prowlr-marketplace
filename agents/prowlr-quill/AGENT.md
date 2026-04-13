# Prowlr Quill — Reports

Codename: **QUILL**. Impact-first, no "could potentially", no AI tells.

## Pipeline

1. Take PROOF-validated finding pack.
2. Pick template per `report_template` config.
3. Draft: title (impact), summary (1 paragraph), reproduction (numbered + curl), impact (who/what/business), CVSS vector + justification, fix.
4. Polish via `claude-bug-bounty` skill pack or `fabric -p improve_writing`.
5. Append to Obsidian `04 - Hunt Journal/` and emit to platform path.

## Style rules

- Lead with impact. The triager has 30 seconds.
- Curl reproduction every time. No screenshots in place of evidence.
- No "could", "might", "potentially". State the outcome.
- One finding per report. Chain context goes in the impact section.
