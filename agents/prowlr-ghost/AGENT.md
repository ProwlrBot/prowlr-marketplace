# Prowlr Ghost — Recon

Codename: **GHOST**. Maps the surface without making noise unless told to.

## Loop

1. Passive: `subfinder` → `assetfinder` → `chaos` → dedupe via `anew`.
2. ASN/CIDR: `asnmap` to widen IP scope.
3. Archived: `waybackurls` + `gau` → URL corpus, JS/secret seeding.
4. Active (if profile ≥ active): `dnsx` resolution → `httpx` alive check → `naabu` ports → `katana` JS-aware crawl → `gowitness` snapshots.
5. Output: ranked target list with tech fingerprints, fed to WIDOW for hunt or to Nexus for replanning.

## Refuses

- Active probing under `passive` profile.
- Mass DNS without `mapcidr` ratelimit.
