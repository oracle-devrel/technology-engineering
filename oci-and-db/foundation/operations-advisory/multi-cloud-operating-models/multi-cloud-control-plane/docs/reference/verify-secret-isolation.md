# Verify first-project delivery

Cloud Operations and the Project Team use the first intended request to verify the handed-off project before deployment. Use only an enabled cloud, environment and region. Do not create an extra database, secret or cloud scope just for this check.

## Acceptance

1. Prepare the selected catalog request with approved foundation inputs: OCI/Google handoff references, or Azure request/JSON values and its configured runner. Azure Markdown is optional. For a request that uses a secret, prepare its native reference and the runner's required read access. Follow the [resource catalog](../../repository-sources/gitops-templates/resources-catalog/README.md) for the selected cloud. A request without secrets needs no secret-delivery setup.
2. Open its focused pull request. Verify that the expected runner and state scope are selected, and that the matching current-head plan or lifecycle check succeeds.
3. Review the safe resource-action report or validated operation targets. Confirm that the report matches the intended request and that the manifest and public evidence contain no passwords or private keys. Safe Terraform reports withhold all values; use the manifest diff for declared settings.
4. Confirm private variable files are removed after the job. Treat Terraform plans and state as sensitive. When this request first introduces a native secret reference, verify its delivery here; do not infer it from an earlier request without secrets.

A plan-only acceptance does not authorize deployment. Continue through independent human review and merge only when the actual workload change is approved. Close a disposable validation PR without merging it.

## Platform regression qualification

When changing Platform CI's secret handling, run its resolver and workflow regressions. Cover malformed secret OCIDs, denied reads, unavailable current versions, removed password fields, unresolved placeholders and cleanup after failure. These are platform qualification cases, not a manual series of negative pull requests required for every project installation.

## What this proves

The check verifies request routing and the delivery path exercised by that request. It does not prove per-project IAM isolation when projects share one runner identity. SQL connections and wallet tests are separate from this delivery check.

The shared workload Vault belongs to environment security. Each project owns its AES-256 HSM key and secrets in Database; the key OCID is a reference and key material remains in HSM. Project Team prepares each database's independent secret using the handoff references, through separately confirmed Codex preparation or its approved manual process. The manifest keeps the same `admin_password_secret_id` field. The optional UI requires an existing secret OCID.

Platform CI checks all ADB secret metadata before reading any value, initializing Terraform or accessing its backend. The authorization handoff is `environments/<environment>/environment_information.md` from the immutable PR base for plan and merged commit for apply. The request branch cannot replace that authorization. Compartment, Vault, key, OCI region and ACTIVE state must all match; query failures stop the run. OCI retains the native secret OCID; Azure resolves `CURRENT` into private temporary variables only after all references pass. Azure location does not select the OCI Vault region. There are no additional project scope files or bindings.

These checks protect the governed workflow. They do not create IAM isolation between executions using the shared runner identity. Keep secret values, raw Terraform diagnostics and private temporary variables out of Git and PR comments. CloudOps retains the Vault during project retirement and manually completes project-secret and key removal first.
