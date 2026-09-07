# Changelog

All notable changes to the OKE DevOps Starter are documented in this file.

This project follows [Semantic Versioning](https://semver.org/).

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
- Added release packaging exclusions for local state, credentials, development artifacts, maintainer agent context, and private stack update helpers.

### Documentation

- Added a customer quickstart and a Deploy to Oracle Cloud entry point.
- Added separate developer and cluster-operations guides, workflows, runbooks, architecture diagrams, naming conventions, chart lifecycle documentation, security guidance, troubleshooting, responsibilities, and template-upgrade guidance.

### Lifecycle Notes

- Generated OCI DevOps resources are starter templates, not a continuously enforced CI/CD policy.
- Removing an application, component, tool, or manifest from configuration does not automatically delete its Git content or live Kubernetes resources.
- Production can target the same physical OKE cluster as pre-production for evaluation, but separate clusters are recommended for production isolation.
