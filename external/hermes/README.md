# Hermes Agent — External Employee

Forked to `ProwlrBot/hermes-agent`. Upstream: `NousResearch/hermes-agent` — "the agent that grows with you."

## Why it's wired

The other employees are stateless transforms (Fabric runs a pattern, CBB writes a report, OpenFang sandboxes a command). Hermes is the only one that *learns across hunts*. Pair it with `prowlr-recall` and the bounty surface narrows over time — Hermes proposes new skills/prompts via the self-evolution loop (DSPy + GEPA), `prowlr-recall` provides the corpus.

## Use from agents

```yaml
employees: [hermes]
```

NEXUS delegates skill-discovery and prompt-optimization tasks:

```json
{"to": "hermes", "type": "delegate", "task": "evolve_skill", "skill": "subdomain-prioritization", "feedback": "<recall corpus>"}
```

## Companion repos (optional)

- `NousResearch/hermes-agent-self-evolution` — DSPy + GEPA optimizer
- `NousResearch/hermes-paperclip-adapter` — run Hermes as a managed Paperclip employee
