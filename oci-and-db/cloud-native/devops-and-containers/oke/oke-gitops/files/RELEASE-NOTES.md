# OKE GitOps stack 2.2.0

This release adds automatic runtime credentials, simplifies Resource Manager
configuration, and improves Argo CD and Flux bootstrap workflows.

## Features and Fixes

- Optionally create an OCI Vault, encryption key, dedicated Git and OCIR reader
  accounts, auth tokens, credential secrets, and scoped runtime access policies.
  The Vault and policy follow the actual DevOps project compartment, including
  reused projects. Runtime policies are independent of execution-IAM creation.
- Automatically connect generated secret OCIDs to bootstrap and installation
  pipelines. The applying user's auth token remains repository-seeding-only;
  runtime accounts have separate read-only credentials.
- Separate build, bootstrap, and installer execution groups. Bound registry
  access by repository prefix, restrict Kubernetes access to the selected
  cluster, and use explicit secret allowlists for manually supplied credentials.
  Bootstrap and installer DevOps management remains compartment-scoped.
- Default new stacks to Argo CD and cluster-administration-only scope, with
  `company-name/org` as the OCIR repository prefix. Helm charts use its `/charts`
  subtree; container images use the base prefix.
- Simplify the Resource Manager form with concise descriptions, independent
  execution/automation identity-domain pickers, consecutive feature-dependent
  fields, optional policy names, and hidden maintenance inputs.
- Honor exact chart-version overrides without a LATEST lookup. Preserve resolved
  versions across managed-build steps and the automatic installer handoff.
- Keep transient credential files outside workspace snapshots, clear disabled
  optional repository sources, and allow newly created Vault endpoints to settle.
- Include `manage-oke-with-argocd.zip` and `manage-oke-with-flux.zip` alongside the
  Resource Manager stack. Shared release automation also includes
  `oke-devops-starter.zip` in future OCI DevOps Starter releases.

## Existing Installations

- Preserve explicitly selected agent/scope values when adopting the new defaults.
- Existing Git repositories remain customer-owned. Merge updated build specs
  before using the updated pipelines.
- Build pipelines still accept `chart_version`. Direct calls to the internal
  `install-gitops-agent` pipeline now use `resolved_chart_version` with an exact,
  already-mirrored chart version.
- Manual credentials with stack-managed execution IAM require an explicit
  `execution_secret_ids` allowlist. An empty list grants no Vault secret access.
- Generated auth tokens enter Terraform state; restrict access to that state.

The authoritative layout is [REPOSITORY-CONTRACT.md](REPOSITORY-CONTRACT.md).
