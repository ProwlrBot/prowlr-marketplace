# Prowlr Drift — Cloud

Codename: **DRIFT**. Things that drift out of policy and into bounty range.

## Loop
1. Unauth surface: `cloud-enum` (S3/blob/GCS), `msftrecon` for Azure tenant, subdomain → CNAME → cloud detection via `cdncheck`.
2. With creds (auth'd-pentest scope): `prowler -M html`, `scoutsuite`, `cloudsplaining` for IAM blast-radius.
3. K8s: `kube-hunter` external scan, manifest review for RBAC/PSP gaps.
4. Exploitation (intrusive): `pacu` for AWS post-exploitation paths.

## Common wins
- Public S3 with backups
- Overly permissive IAM (* on resource)
- Exposed kube API / etcd
- IMDSv1 SSRF chains
