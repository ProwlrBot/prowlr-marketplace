# OpenFang — External Employee

Forked to `ProwlrBot/openfang` for pin control. Upstream: `RightNow-AI/openfang` — open-source agent operating system.

## Use from agents

```yaml
employees: [openfang]
```

Agents call via ROAR `delegate` to offload sandboxed execution:

```json
{"to": "openfang", "type": "delegate", "task": "run_in_sandbox", "input": "<command>"}
```

## Why

OpenFang gives us a process-isolated runtime for tool execution that doesn't trust the host shell. NEXUS routes intrusive-profile tasks through it so a bad payload can't escape the agent's own session.
