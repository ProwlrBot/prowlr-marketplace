# Prowlr Prism — LLM red team

Codename: **PRISM**. Your edge. Most bounty hunters can't test AI systems — you can.

## Coverage
- Prompt injection (direct + indirect via docs/repos/MCP tool results)
- System prompt extraction
- Data exfil via Files API, Markdown images, whitelisted domains
- MCP server exploitation (tool poisoning, SQL injection, path traversal — see Anthropic CVE catalog in vault)
- Multi-turn crescendo attacks (47% breach rate per OWASP LLM Top 10 2026)

## Tools
- `promptfoo` — quick OWASP scan
- `garak` — broad sweep
- `pyrit` — deep campaigns
- `deepteam` — compliance-mode

## Vault refs
- `06 - Knowledge Base/Anthropic/Anthropic Security Research.md`
- `08 - RedTeam/Red Team Playbook - Claude Ecosystem.md`
