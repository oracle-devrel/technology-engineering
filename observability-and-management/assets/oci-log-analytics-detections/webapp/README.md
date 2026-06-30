# OCI Log Analytics Detections Webapp

`webapp/` contains the long-term Forge frontend for this repository. It is a Next.js App Router application that converts Sigma/YAML, Microsoft Sentinel KQL, Splunk SPL, Elastic/Lucene/KQL, and OCI Log Analytics QL passthrough examples into OCI Log Analytics QL by using this repo's generated artifacts and backend conversion script.

## Scope

- **Only exposed product surface:** `/forge`
- **API surface:** `/api/forge/session`, `/api/forge/convert`, and `/api/health`
- **Artifact source:** parent repository root by default, or `LOGAN_DETECTIONS_REPO` when explicitly set
- **Public repository link:** `https://github.com/adibirzu/oci-log-analytics-detections`
- **Production host targets:** `https://convert.octodemo.cloud` and `https://forge.octodemo.cloud`
- **Static host target:** GitHub Pages can serve a limited read-only build when `NEXT_PUBLIC_FORGE_STATIC_EXPORT=1`

The app does not duplicate query generation. It reads:

- `queries/logan_ql_reference_catalog.json`
- `queries/cross_ql_mapping_patterns.json`
- `queries/conversion_examples.json`
- `queries/ql_conversion_capability_matrix.json`
- `queries/catalog.json`
- `queries/dashboard_inventory.json`
- `test_data/manifest.json`
- `scripts/logan_workbench_convert.py`

## Local Development

```bash
cd webapp
pnpm install --frozen-lockfile
pnpm dev
```

The local app reads artifacts from `..` when `LOGAN_DETECTIONS_REPO` is unset. Set `LOGAN_DETECTIONS_REPO=/absolute/path/to/oci-log-analytics-detections` only when running from a different working directory.

Verification:

```bash
cd webapp
pnpm typecheck
pnpm lint
pnpm build
pnpm e2e
```

## GitHub Pages Static Build

GitHub Pages can host the Forge page only as a static/read-only build. Static mode does not include the Next.js API routes, CSRF session endpoint, Python converter, or backend deployment actions. It supports bundled example conversions and raw OCI Logan QL passthrough in the browser.

```bash
cd webapp
NEXT_PUBLIC_FORGE_BASE_PATH=/oci-log-analytics-detections pnpm build:pages
```

The static export is written to `webapp/out`. The `Forge GitHub Pages` workflow publishes that directory from GitHub Actions.

## Security Posture

- Middleware redirects HTML requests to `/forge` and returns `404` for non-allowed routes.
- The conversion API uses strict Zod request/response validation, CSRF tokens, origin checks, request size limits, rate limiting, and production-safe error messages.
- `FORGE_TRUSTED_INTERNAL_HOSTS` can list OKE service DNS names that are allowed as internal origins while still requiring a valid `X-Logan-Forge-CSRF` token.
- `FORGE_TRUSTED_PROXY_HOPS` makes `X-Forwarded-For` trust **opt-in**. It is the number of trusted reverse-proxy hops (e.g. OCI LB + ingress) that sit in front of the app and append to `X-Forwarded-For`; the rate limiter then keys on the entry that many positions from the **right** (the address your proxy inserted), so a client cannot bypass the limit by spoofing leftmost values. **When unset (or `0`) the app does NOT trust `X-Forwarded-For` at all and every request shares one rate-limit bucket (fail-closed).** Set it to the real proxy depth of the deployment — and ensure the app is only reachable through those proxies — to get per-client limiting.
- Production backend writes must go through `LOGAN_FORGE_BACKEND_URL`, intended to be an API Gateway endpoint protected by WAF. Without that secret, the app uses the bundled read-only converter script.
- No tenancy names, OCIDs, IP addresses, or secret values are rendered in the UI. Deployment scripts read environment variables and local OCI profiles at execution time only.

## Deployment

OKE deployment material lives in `deploy/oke/`. Build from `webapp/` after staging a minimal runtime artifact bundle:

```bash
cd webapp
./deploy/oke/stage-detections-runtime.sh
docker build -t "$FORGE_IMAGE" .
docker push "$FORGE_IMAGE"
envsubst < deploy/oke/forge-frontend.yaml | kubectl apply -f -
```

See `deploy/oke/README.md` for the existing Octo APM load-balancer and DNS wiring flow.
