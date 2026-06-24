# Integrated Forge Webapp

Date: 2026-05-18

`webapp/` is the long-term Forge frontend for this repository. It replaced the old `LoganSecurityDashboardv0` sibling app as the maintained UI surface.

## Runtime Contract

- The app is a Next.js App Router project under `webapp/`.
- The only browser product surface is `/forge`; root HTML requests redirect there.
- Allowed API routes are `/api/forge/session`, `/api/forge/convert`, and `/api/health`.
- Local development reads artifacts from the repository root by default.
- Container deployments stage a minimal read-only artifact bundle with `webapp/deploy/oke/stage-detections-runtime.sh`.

## Artifacts Used by the UI

- `queries/logan_ql_reference_catalog.json`
- `queries/cross_ql_mapping_patterns.json`
- `queries/conversion_examples.json`
- `queries/catalog.json`
- `queries/dashboard_inventory.json`
- `test_data/manifest.json`
- `scripts/logan_workbench_convert.py`

The webapp must not hand-author query-generation logic. Arbitrary conversions go through `/api/forge/convert`, which either proxies to `LOGAN_FORGE_BACKEND_URL` or executes the bundled read-only converter script.

## Security Notes

- Public Repo links point to `https://github.com/adibirzu/oci-log-analytics-detections`.
- The UI must not render tenancy names, OCIDs, public IPs, OCI profile names, backend URLs, or tokens.
- Production write-capable conversion belongs behind API Gateway and WAF. The frontend defaults to read-only behavior when backend secrets are absent.
- The Kubernetes manifest disables service-account token mounting, runs as a non-root user, drops Linux capabilities, uses a read-only root filesystem, and keeps backend credentials in an optional secret.

## Verification

```bash
cd webapp
pnpm typecheck
pnpm lint
pnpm build
```

Producer-side artifact changes should still run the relevant Python checks from the repository root before deployment.

For OKE production rollout, use [OKE_OBSERVABILITY_RUNBOOK.md](OKE_OBSERVABILITY_RUNBOOK.md)
and [webapp/deploy/oke/README.md](../webapp/deploy/oke/README.md). The runbook
captures the platform checks from the latest Forge deployment: build for the
worker node architecture, roll out through the existing OCI Load Balancer,
verify `/forge` and `/api/health`, and confirm legacy/admin routes return
`404`.
