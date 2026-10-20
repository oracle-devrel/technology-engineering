# Changelog

All notable changes to the OKE DevOps Starter are documented in this file.

This project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Configurable development, staging and production application environment names,
  plus independent nonproduction and production cluster target names. Generated
  pipelines, Helm values, labels, bootstrap stages and cluster-admin paths use
  the configured names while production approvals and image promotion remain
  tied to stable workflow roles. Defaults preserve existing naming conventions.
- Validation of unsafe names, duplicate targets, generated Helm release lengths
  and same-cluster namespace/release collisions, plus guidance for coordinated
  migration of existing installations.

## [1.2.0] - 2026-10-14

### Added

- Updated the portable `oke-devops-starter` skill with automatic-credential discovery and the separate execution/credential IAM boundaries.

- Structured Resource Manager inputs for applications/components and cluster-administration tools, with legacy JSON-string compatibility. Credential controls are grouped in the IAM section.

- Optional automatic credential creation in a selected identity domain: dedicated repository automation and read-only OCIR pull accounts, auth tokens, a regional Vault, AES key and token secrets. Repository seeding keeps the user-supplied auth token; generated pull credentials feed new application bootstrap defaults. IAM creation remains independently selectable.

### Security

- Automatic credentials always include their scoped Git/pull access policy in the DevOps project compartment, independently of pipeline IAM creation. Policy names include a stable random seven-character suffix.

- Restricted generated DevOps dynamic-group membership to stack-owned resource OCIDs and Vault reads to application bootstrap pipelines. Generated credentials are sensitive Terraform-state data and require controlled state access.

### Fixed

- Use auth-token-capable, non-console automation users and the selected Identity Domains token API. Wait for fresh Vault KMS endpoint DNS propagation before creating the credential key.
- Allow up to ten minutes for repository access authorization to propagate during initial seeding with the user-supplied token.
- Request Identity Domains group memberships and dynamic-group matching rules explicitly during refresh, and avoid drift on the write-only notification-suppression option.
- Treat blank optional Resource Manager attributes as omitted values, preserving namespace, chart-version and build-spec defaults.
- Aligned cluster operations runbooks and the seeded repository README with shared orchestrators, immutable target plans, and explicit decommissioning without a confirmation parameter.
- Restricted release packaging to an explicit file manifest, rejected missing or symlinked inputs, and generated a fresh SHA-256 checksum for each archive. Added packaging regression tests for local-file exclusions and release/development modes.

### Upgrade Notes

- Repository seeding always requires the current user's auth token, including automatic-credentials mode.
- Generated Vaults and secrets use the resolved DevOps project compartment. Deprecated credential-compartment overrides no longer change placement or secret-read policy scope.
- DevOps dynamic-group and automation-user identity domains have separate selectors. Legacy Terraform inputs retain the previous shared-domain fallback.
- Existing Resource Manager stacks must convert the saved cluster-administration object from `{ "tools": [...] }` (or legacy `noprod.tools`) to the tools list before opening the new Console form. Terraform still accepts legacy representations.
- Review the plan for credential policy name/location changes. Release-mode protections continue preserving customized DevOps starter resources.

### Verification

- Amsterdam functional testing covered automatic identities, bootstrap, two-component PR-to-production delivery, image digests, cluster tools, negative access checks and credential stability.
- Later form/policy refinements passed local validation, 74 regression tests and eight mocked plans. A child-domain comparison was blocked by domain-creation permissions; no hard domain-placement rule was added.

## [1.1.1] - 2026-09-18

### Fixed

- Added configurable IAM policy placement at a common ancestor (tenancy root by default) so grants work across sibling OKE and network compartments. Vault access remains in the secret compartment.
- Reject new and reused tenancy-root DevOps projects when application delivery or cluster administration needs Container Instance Shell stages. Pure build-only mode remains allowed.
- Set OCI's reserved `ENFORCE_HELM_DEPLOYMENT=true` parameter on generated application and component deployment pipelines so explicit reruns execute Helm even when inputs are unchanged.

### Upgrade Notes

- Review the Terraform plan for the IAM policy location change. The applying identity needs policy-management permissions in the selected ancestor compartment. Grant targets are unchanged.
- Existing customized deployment pipelines retain template ownership (`ignore_changes = all`). Add `ENFORCE_HELM_DEPLOYMENT` with default `true` manually to existing application baseline and component dev/release pipelines, or pass it on an individual deployment run.
- No live OCI functional test was performed for this patch; local regression and Terraform validation results are recorded in the release PR.

## [1.1.0] - 2026-09-07

### Delivery Ownership

- Added `application_delivery_mode` with `oci_devops` and `build_only` options.
- Added build-only CI that preserves component repositories, pull-request validation, protected main branches, and immutable SHA7 image builds while omitting application charts and OCI DevOps deployment resources.
- Made the shared build-assets repository configurable, with `devops-pipelines` as its default name.
- Made OKE environments, application deployment artifacts, chart repositories, release pipelines, and related IAM permissions conditional on enabled capabilities.
- Documented three independent OCI DevOps and GitOps ownership models, including object-level ownership for resources that share an application namespace.

### AI-Assisted Operations

- Added the directly downloadable `oke-devops-starter` skill and made it prominent in the main README.
- Made the skill portable for any AI agent that supports the Agent Skills `SKILL.md` convention.
- Added guided workflows for component PRs and releases, application bootstrap and baselines, cluster-tool administration, deployment verification, rollback, and troubleshooting.
- Kept the skill source and internal agent context outside the Resource Manager deployment archive.

## [1.0.0] - 2026-07-10

Initial public release of the OCI Resource Manager stack.

### Application Delivery

- Added support for multiple applications with multiple globally unique components from a concise JSON configuration.
- Added generated OCI Code repositories, protected main branches, pull-request validation pipelines, build pipelines, deployment pipelines, artifacts, triggers, and OCIR paths for every configured application and component.
- Added component-owned pull-request build specifications so teams can implement language-specific unit, integration, security, and quality checks.
- Added parameterless main builds that produce multi-architecture images tagged with the immutable 7-character Git commit SHA.
- Added automatic development deployment after a successful component build.
- Added release-candidate promotion with `skopeo`, staging deployment, production approval, final image promotion, production deployment, Helm status reporting, and final Git tagging.
- Separated application baseline charts from independently versioned and deployed component charts.
- Added per-application bootstrap pipelines that initialize application namespaces and OCIR pull secrets on pre-production and production clusters.
- Added cluster-specific application baseline values and environment-specific component values for development, staging, and production.

### Cluster Administration

- Added optional cluster administration behind the `enable_cluster_admin` feature flag.
- Added a dedicated `cluster-admin` repository for cluster tool configuration, values, supplemental namespaced resources, and cluster-wide baseline manifests.
- Added support for mirroring pinned public HTTP(S) and OCI Helm charts into OCIR.
- Added dependency-aware tool deployment using a configurable DAG, with independent tools deployed in parallel and dependent tools deployed in topological waves.
- Added immutable cluster values artifacts versioned by the full configuration commit SHA.
- Added selective deployments so a merged configuration change invokes only affected cluster and tool stages.
- Added matching pre-production and production orchestration, with approval required before production mutation.
- Added explicit tool decommission pipelines without automatic pruning of unrelated Kubernetes resources.

### Resource Manager Experience

- Added a guided Resource Manager form for OCI DevOps, applications, independent pre-production and production OKE targets, IAM, logging, notifications, and optional cluster administration.
- Added multiline, human-readable JSON defaults and validation for application/component and cluster-tool configuration.
- Added configurable DevOps project, logging, notification topic, Generic Artifact repository, IAM resource names, and component build-spec paths.
- Added structured application information outputs covering repositories, pipelines, environments, artifacts, OCIR paths, and suggested next actions.
- Added support for using one OKE cluster as both pre-production and production for evaluation environments.

### Template Ownership And Safety

- Added release-mode lifecycle protection so teams can customize generated OCI DevOps starter resources without later Resource Manager applies overwriting those changes.
- Added add-only Git repository seeding that preserves existing developer and administrator content.
- Added a separate hidden development packaging mode for stack maintainers to refresh template-managed resources during functional testing.
- Added Vault-backed OCIR pull credentials, private OKE endpoint access from configured worker subnets, optional NSGs, and scoped IAM policies.
- Added Vault secret-read access as a dedicated IAM policy in the configured Vault compartment.
- Added release packaging exclusions for local state, credentials, development artifacts, maintainer agent context, and private stack update helpers.

### Documentation

- Added a customer quickstart and a Deploy to Oracle Cloud entry point.
- Added separate developer and cluster-operations guides, workflows, runbooks, architecture diagrams, naming conventions, chart lifecycle documentation, security guidance, troubleshooting, responsibilities, and template-upgrade guidance.

### Lifecycle Notes

- Generated OCI DevOps resources are starter templates, not a continuously enforced CI/CD policy.
- Removing an application, component, tool, or manifest from configuration does not automatically delete its Git content or live Kubernetes resources.
- Production can target the same physical OKE cluster as pre-production for evaluation, but separate clusters are recommended for production isolation.
