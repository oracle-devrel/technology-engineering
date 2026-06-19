---
name: Bug report
about: Something didn't work as expected
title: "[bug] "
labels: bug
---

> ⚠️ **Redact before posting.** No OCIDs, IPs, tenancy namespaces, install keys,
> wallet passwords, or `input.rsp` contents. Replace real values with `<PLACEHOLDER>`.

## What happened

A clear description of the bug.

## Component

- [ ] `Install-OCI-Prometheus.ps1` (Windows proxy/target)
- [ ] `install-node-exporter.sh` / `install-gcp-exporter.sh` (Linux target)
- [ ] `install-otel-collector.sh` (Linux OTEL)
- [ ] `manage-oci-datasource.sh` (OCI data source)
- [ ] `discover-oci-instances.sh` (discovery)
- [ ] `otel-destination/` (test sink)
- [ ] docs

## Environment

- OS / version:
- PowerShell version (if Windows): `$PSVersionTable.PSVersion`
- OCI region (no OCIDs):
- Export path: OCI Monitoring / OTEL / both

## Steps to reproduce

1.
2.

## Expected vs actual

## Logs (redacted)

```
paste redacted output here
```

## Did you check the KB?

- [ ] I searched [`docs/KNOWLEDGE_BASE.md`](../../docs/KNOWLEDGE_BASE.md)
