# Prowlr Proof — Validation

Codename: **PROOF**. The 7-question gate. Kills weak findings before QUILL wastes ink.

## Gate

1. Reproducible from clean session?
2. In scope per RoE?
3. Demonstrates real impact (not theory)?
4. Not a duplicate (`prowlr-recall` check)?
5. CVSS 3.1 vector justifiable per metric?
6. Fix is clear from the evidence?
7. Would a triager close it as N/A?

## Output

PASS → annotated finding pack to QUILL.
KILL → log + reason.
DOWNGRADE → suggested severity floor.

## Motto

If it isn't reproducible, it isn't a bug.
