---
name: oke-devops-starter
description: Operate application delivery and OKE cluster-administration workflows created by the OKE DevOps Starter. Use for pull-request validation, component builds and releases, application bootstrap and baseline delivery, cluster-tool changes, deployment verification, rollback, and troubleshooting in the generated OCI DevOps project and repositories.
---

# OKE DevOps Starter Skill

Use this skill to operate a deployed OKE DevOps Starter solution. It follows the
portable Agent Skills `SKILL.md` format and does not depend on one AI product.
If an agent cannot discover skills automatically, provide this directory or
`SKILL.md` as task context.

## Establish Context

Before acting, identify:

1. The OCI DevOps project and region.
2. The application and component, or the target cluster and tool.
3. Whether application delivery uses `oci_devops` or `build_only`.
4. Whether cluster administration is enabled.
5. The requested terminal condition, such as a successful PR build, dev
   deployment, production release, or healthy cluster tool.

Use Resource Manager outputs and the generated repository READMEs to resolve
names and OCIDs. Do not guess a target when several applications, components,
clusters, pipelines, or releases exist.

## Route The Task

- Read [references/solution-map.md](references/solution-map.md) to understand
  generated resources, ownership modes, and naming.
- Read [references/application-delivery.md](references/application-delivery.md)
  for component PRs, SHA builds, dev delivery, RC promotion, staging, approval,
  production, application bootstrap, and baseline charts.
- Read
  [references/cluster-administration.md](references/cluster-administration.md)
  for cluster-tool catalog changes, dependency ordering, configuration
  validation, deployment, and decommissioning.
- Read [references/safety.md](references/safety.md) before mutations, production
  approval, rollback, cleanup, or troubleshooting.

For hybrid OCI DevOps and GitOps installations, first establish which system
owns each Kubernetes object. Sharing a namespace or OCI DevOps project does not
transfer ownership and must not result in two systems reconciling the same
object identity.

## Operating Rules

- Inspect current OCI DevOps, Git, OCIR, Helm, and Kubernetes state before
  changing it.
- Treat generated repositories and pipeline internals as customer-owned after
  initial seeding.
- Keep secrets in OCI Vault. Never print, commit, or place secret values in
  pipeline parameters that are persisted or exposed.
- Use pull requests for repository changes and preserve protected `main`
  branches.
- Use immutable SHA7 image tags for builds and semantic release-candidate tags
  for promotion.
- Do not bypass staging, required approvals, final image promotion, or release
  commit tagging.
- Do not approve, release, decommission, clean up, or mutate production without
  explicit user authorization.
- Use OCI DevOps execution as the proof of pipeline behavior. Direct
  `kubectl`, Helm, Git, OCI CLI, or registry inspection may verify outcomes,
  but must not substitute for a requested pipeline test.

## Report Results

State the project, application/component or cluster/tool, repositories and
pipelines involved, immutable versions and commits, observed deployment state,
validation evidence, external actions performed, and any cleanup or approval
still required. Report partial outcomes separately when a final informational
stage fails after the deployment itself has succeeded.
