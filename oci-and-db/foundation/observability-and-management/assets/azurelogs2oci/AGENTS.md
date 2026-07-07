# Repository Guidelines

This guide orients new contributors to azurelogs2oci (Azure Event Hubs -> OCI Streaming). Keep changes small, validated, and production-minded.

## Project Structure & Module Organization
- function/EventHubsNamespaceToOCIStreaming/: Azure Function code (trigger binding in function.json, runtime config in host.json, docs in README.md/QUICKSTART.md, deps in requirements.txt).
- scripts/: Operational helpers for provisioning, draining, and credential checks (drain_eventhub_to_oci.sh, setup_eventhub_to_oci.sh, test_oci_simple.py).
- docs/: Event format notes and walkthrough content.
- deploy/: ARM template used by the portal deployment.
- Root: .env.example for local smoke tests; .env is git-ignored.

## Build, Test, and Development Commands
- Prepare dependencies for packaging: `python3 -m pip install -r function/EventHubsNamespaceToOCIStreaming/requirements.txt --target function/EventHubsNamespaceToOCIStreaming/.python_packages/lib/site-packages`.
- Local function run (requires local.settings.json in the function folder): `(cd function/EventHubsNamespaceToOCIStreaming && func start)`.
- Validate credentials and stream reachability without Azure Functions: `python ./scripts/test_oci_simple.py`.
- Smoke-test end to end using local .env: `./scripts/drain_eventhub_to_oci.sh --from-beginning` (reads Event Hubs and writes to OCI).
- Provision+deploy from scratch: `./scripts/provision_azure_to_oci.sh` (creates RG/storage/app, sets app settings, zips, and deploys).

## Coding Style & Naming Conventions
- Python 3.11, 4-space indent, type hints where practical; prefer logging over print, and add small helper functions instead of inline duplication.
- Use snake_case for Python identifiers, UPPER_SNAKE for environment variables/app settings, and keep module-level constants at the top of files.
- Shell scripts are bash with set -e; keep flags/envs upper-case and favor functions over long inline blocks.
- Keep log messages actionable (include endpoint/OCID masks, batch sizes, counts).

## Testing Guidelines
- There is no formal unit test suite; add targeted tests when adding non-trivial logic (pytest recommended under function/EventHubsNamespaceToOCIStreaming/tests if introduced).
- For every change touching OCI/Azure integration, run `python ./scripts/test_oci_simple.py` and/or `./scripts/drain_eventhub_to_oci.sh` to validate credentials and delivery.
- Capture log excerpts or script summaries in the PR to show processed/sent counts.

## Commit & Pull Request Guidelines
- Use short imperative commit subjects; include `Signed-off-by: Full Name <email>` (`git commit -s`) to satisfy the Oracle Contributor Agreement requirement.
- Branch names like `1234-fixes` or `feature/<topic>` help trace to issues; every PR should link to a GitHub issue.
- PR description must state the intent, config changes (if any), and validation steps/commands run; include screenshots or log snippets when helpful.
- Keep changes small and scoped; update related docs in README.md, QUICKSTART.md, or scripts when behavior changes.

## Security & Configuration Tips
- Never commit secrets; .env and local.settings.json stay local. Prefer Azure Key Vault references for production app settings.
- Use the OCI Stream OCID (not Stream Pool) and mask endpoints/OCIDs in logs.
- Ensure outbound access from the Function App to OCI; avoid widening firewall rules beyond the needed OCI Streaming endpoints.
