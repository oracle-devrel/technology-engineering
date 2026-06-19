## Summary

What does this PR change and why?

## Type

- [ ] feat
- [ ] fix
- [ ] docs
- [ ] refactor / chore / ci

## How tested

- OS / shell:
- OCI region/profile (redacted):
- Export path exercised: OCI Monitoring / OTEL / both / N/A

## Checklist

- [ ] No secrets, OCIDs, IPs, or tenancy namespaces in the diff (`<PLACEHOLDER>` used in examples)
- [ ] `shellcheck *.sh otel-destination/*.sh` passes
- [ ] `Invoke-ScriptAnalyzer` passes (no Errors) for PowerShell changes
- [ ] `docker compose -f otel-destination/docker-compose.yml config` valid (if touched)
- [ ] Backward compatible with Windows PowerShell 5.1 / older Windows (for installer changes)
- [ ] KB updated in `docs/KNOWLEDGE_BASE.md` (if a bug was fixed)
- [ ] CHANGELOG.md updated
