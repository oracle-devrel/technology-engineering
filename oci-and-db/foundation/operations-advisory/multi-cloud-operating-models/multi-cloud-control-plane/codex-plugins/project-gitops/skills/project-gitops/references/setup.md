# Setup

1. Resolve the project repository as `multicloud-control-plane/<repository>`. Its `origin` must match the expected handed-off private `nonprod-<project>` or `prod-<project>` repository with default branch `main`. Read `environments/<environment>/environment_information.md` for approved OCI foundation references. Google requests still require their reviewed foundation references there. For Azure, use the request inputs below; its Markdown section is optional context.
2. Use `multicloud-control-plane/gitops-templates` at `main`: `resources-catalog` for infrastructure or `operations-catalog` for OCI lifecycle work. The selected catalog and its README own field shapes, destination paths and capacity profiles. Platform CI and the selected orchestrator own runtime validation; do not recreate their checks locally.
3. A template-only `.github/CODEOWNERS.template` is valid; Project Team owns its active CODEOWNERS configuration.

## Azure request inputs

Use explicit request values or the relevant existing resource JSON at `main` for the region, resource group and other catalog inputs. Ask only for missing or conflicting values. A new ADB needs its own secret OCID; never reuse another database's secret. Private profiles also need existing approved network references. Public mTLS profiles need no VNet or subnet. Keep the chosen profile's literal settings.

Azure uses an existing foundation and the trusted runner's `ARM_*` configuration for subscription and authentication. Never request or read those credentials or add them to a manifest. The optional Azure Markdown section can suggest values, but its absence or incompleteness does not block an Azure request or require a separate handoff PR. Explicit request values take precedence over suggestions and existing JSON; show any requested change in the preview. Human review checks the intended destination and the runner's effective IAM controls access. This skill does not create Azure foundations or configure runners.

## Native secret prerequisites

For OCI and Azure ADB, render `__ADB_ADMIN_PASSWORD_SECRET_OCID__` into `admin_password_secret_id` with one distinct OCI Vault secret OCID per database in the approved project/environment. Keep a supplied OCID. When it is missing in Codex, offer [Project Team secret preparation](secret-preparation.md), then insert the resulting OCID before the GitHub proposal. In the web UI, or when the user chooses manual preparation, ask for the missing OCID. Never ask for passwords. Do not use logical dependency keys, password tokens, binding names or extra secret-region fields.

OCI requires the deployment region. Its native module reads `CURRENT` with Instance Principal. The published password policy is 12 to 30 characters, uppercase, lowercase and digit, no double quote and no `admin` substring in any casing. State this prerequisite without checking the value.

For Azure, Platform CI validates every secret against the trusted handoff and uses its OCI region before reading `CURRENT` using the runner's existing Instance Principal and IAM permissions. It passes the password privately to the Azure adapter. No additional project mapping, scope file or per-secret binding is registered. Google ADB keeps its provider-native `properties.secret_id` reference.

Project Team manages values and current versions; Cloud Operations prepares scoped runner access. List the selected references and their project/environment prerequisites in the preview. For supplied OCIDs, state prerequisites without claiming cloud checks. During Codex preparation, report only the secret metadata actually observed; never claim to have checked contents, current versions or runner IAM. A new current version is consumed by the next reviewed plan/apply; rotation alone does not deploy a password change. Diagnose deployment failures from workflow evidence only; preparation failures follow [secret recovery](secret-preparation.md#continue-or-recover). There is no GitHub Secrets fallback.

Azure and Google VM requests render their approved SSH public keys directly into manifests. Public keys need no Vault registration; private keys remain protected outside Git. Render every catalog placeholder before publishing.

The shared workload Vault belongs to environment security. Each project owns its AES-256 HSM key and secrets in Database; the key OCID is a reference and key material remains in HSM. Project Team prepares each database's independent secret using the handoff references, either through the confirmed Codex preparation or its approved manual process. The manifest keeps the same `admin_password_secret_id` field. Cloud Operations supplies the Vault, key, compartments and access; it does not prepare ADB requests for Project Team.

Platform CI checks all ADB secret metadata before reading any value, initializing Terraform or accessing its backend. The authorization handoff is `environments/<environment>/environment_information.md` from the immutable PR base for plan and merged commit for apply. The request branch cannot replace that authorization. Compartment, Vault, key, OCI region and ACTIVE state must all match; query failures stop the run. OCI retains the native secret OCID; Azure resolves `CURRENT` into private temporary variables only after all references pass. Azure location does not select the OCI Vault region. There are no additional project scope files or bindings.

These checks protect the governed workflow. They do not create IAM isolation between executions using the shared runner identity. Keep secret values, raw Terraform diagnostics and private temporary variables out of Git and PR comments. CloudOps retains the Vault during project retirement and manually completes project-secret and key removal first.
