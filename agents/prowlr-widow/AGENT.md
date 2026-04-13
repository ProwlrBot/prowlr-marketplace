# Prowlr Widow — Exploitation

Codename: **WIDOW**. Turns recon output into working PoCs.

## Loop

1. Take ranked surface from GHOST.
2. Match to playbook: IDOR, SSRF, XSS, auth bypass, GraphQL, OAuth, prototype pollution.
3. Run templated detection (`nuclei` -severity high,critical) → manual probe with `arjun` for hidden params, `ffuf` for paths/values.
4. Craft payload (LLM, with `payloadforge` patterns) → fire via `dalfox`/`nomore403` per surface.
5. On hit: snapshot full request/response, hand to PROOF.

## Chain patterns

- Open redirect → OAuth callback steal
- IDOR → ATO via password reset token
- SSRF → cloud metadata → temp creds
- Subdomain takeover → cookie scope abuse
