# Claude Bug Bounty — External Employee

Skill pack for Claude Code that ships our four heavy-hitters: `report-writer`, `chain-builder`, `validator`, `recon-ranker`.

## Wiring

Hunter / QUILL declare:

```yaml
employees: [claude-bug-bounty]
```

Loader confirms `claude` on PATH and `~/.claude/skills/{report-writer,chain-builder,validator,recon-ranker}/` exist. Missing skills surface install instructions instead of failing silently.

## Why a skill pack, not a model

These agents need long-context Claude reasoning, not the bounty-gemma4 fine-tune. They run on Anthropic API; everything else stays local.
