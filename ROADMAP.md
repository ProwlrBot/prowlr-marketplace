# ProwlrBot Marketplace — Roadmap

## v0.1 — Shipped (PR #1)

**Agency (10 agents):**
- `prowlr-hunter` — standalone all-in-one
- `prowlr-nexus` — orchestrator (delegates to GHOST/WIDOW/PROOF/QUILL via ROAR)
- `prowlr-ghost` — recon
- `prowlr-widow` — exploitation
- `prowlr-proof` — validation (7-question gate)
- `prowlr-quill` — reports
- `prowlr-triage` — pre-hunt scope/dedup gate
- `prowlr-ledger` — earnings + ROI tracker
- `prowlr-chronicle` — Obsidian vault sync writer
- `prowlr-prism` — LLM red-team specialist

**External employees (11):**
| id | upstream | role |
|---|---|---|
| fabric | danielmiessler/fabric | AI pattern pipelines |
| claude-bug-bounty | shuvonsec/claude-bug-bounty | Claude skill pack |
| openfang | RightNow-AI/openfang | sandbox runtime |
| hermes | NousResearch/hermes-agent | self-evolving agent |
| clawteam | HKUDS/ClawTeam | swarm orchestrator (alt) |
| openharness | HKUDS/OpenHarness | agent harness (alt) |
| cai | aliasrobotics/cai | offensive AI framework |
| agenticseek | Fosowl/agenticSeek | local browser agent |
| conquer | 1hehaq/conquer | subdomain takeover |
| robin | apurvsinghgautam/robin | dark-web OSINT |
| dark-web-osint-tools | apurvsinghgautam/dark-web-osint-tools | dark-web toolkit |
| wshobson-agents | wshobson/agents | Claude Code subagent pack |

**Tool registry:** `tools.yaml` — 70+ tools, profile-gated.

---

## v0.2 — Loader + ROAR (next PR)

- [ ] Patch `prowlrbot` core to honor `preferred_model` from manifest (bounty-gemma4 → Ollama)
- [ ] Validate `tools_required` against `$PATH` at agent boot; surface install hints
- [ ] Implement ROAR `delegate` message routing for `delegates` and `employees`
- [ ] Add `--profile {passive|active|intrusive}` global flag
- [ ] Schema: extend `manifest.schema.json` with `preferred_provider`, `preferred_model`, `fallback_models`, `tools_required`, `employees`, `delegates`, `kind`

---

## v0.3 — Specialist Agents (gap fill)

Big bounty surfaces not yet covered:

- [ ] **CIPHER** — Web3/smart contract auditor (Slither, Mythril, Echidna). High-payout space.
- [ ] **MIRROR** — Mobile app testing (frida, objection, MobSF, apkleaks). APK/IPA decompile + dynamic analysis.
- [ ] **PRYER** — GraphQL/API deep dive (graphw00f, gqlspection, postman flow). Already partially in WIDOW.
- [ ] **DRIFT** — Cloud misconfig (cloud-enum, prowler, scoutsuite, kube-hunter). 
- [ ] **BROKER** — Bounty-platform comms (HackerOne API, Bugcrowd API, Intigriti API). Auto-reply triager nudges, status sync.
- [ ] **SCRY** — Threat intel watcher (newly-disclosed CVEs, breach feeds, security advisories). Feeds into TRIAGE.
- [ ] **FORGE** — Wordlist/payload generator (curated SecLists subsets, custom dict generation per target stack).

---

## v0.4 — Knowledge / RAG

- [ ] Wire `prowlr-recall` (Obsidian RAG) as actual MCP server, not just `bin: prowlr`
- [ ] Sync vault → embeddings → searchable across agents
- [ ] Programs DB integration (`bounty-targets-data` repo)
- [ ] Per-program memory namespace (don't cross-contaminate findings)

---

## v0.5 — Browser + Proxy integration

- [ ] **CAIDO** plugin: ProwlrBot pane that fires WIDOW probes from selected request
- [ ] Playwright MCP wrapper for headless IDOR/auth testing (already in your tooling)
- [ ] HAR import → katana corpus

---

## v1.0 — Hardening

- [ ] Per-agent telemetry (token spend, tool runtime, success rate)
- [ ] Cost gate: refuse `claude-opus` calls if hourly budget exceeded
- [ ] Sandbox-by-default for intrusive profile (route through OpenFang/csbx)
- [ ] Audit log: every outbound request signed + appended to immutable log

---

## Brainstorm — what we're still missing

**Capabilities:**
- Web3 (high $$$, untouched)
- Mobile (medium $$$, untouched)
- Reverse engineering helper (Ghidra/IDA wrap)
- Binary fuzzing (AFL++, libfuzzer)
- Hardware/IoT (firmware extraction, JTAG) — probably out of scope
- Source code review at scale (semgrep + flaw + AI explainer)

**Workflow:**
- Auto-PoC video recording (asciinema for terminal, playwright trace for browser)
- Markdown → platform format converters (H1 markdown is *not* GFM)
- Bounty calculator (CVSS → expected payout per program)
- Re-test scheduler (after triager fixes, verify the patch)

**Brand / monetization:**
- Public bounty disclosure feed (your finds → blog → followers → leads)
- Methodology export: turn agent runs into shareable playbooks
- Marketplace of *playbooks*, not just agents (per CLAUDE.md monetization angle)
