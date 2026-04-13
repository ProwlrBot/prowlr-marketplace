# Fabric — External Employee

Forked to `ProwlrBot/fabric` for pin control. Upstream: `danielmiessler/fabric`.

## Use from agents

```yaml
employees: [fabric]
```

Agents call via ROAR `delegate`:

```json
{"to": "fabric", "type": "delegate", "pattern": "analyze_threat_report", "input": "<finding>"}
```

The runner shells out to `fabric -p <pattern>` with the input piped on stdin.

## Patterns we lean on

- `analyze_threat_report` — triage incoming intel
- `improve_writing` — QUILL polish pass
- `extract_wisdom` — distill long advisories into vault notes
- `summarize` — long-form recon output → exec summary
- `create_security_update` — disclosure draft
