# Security

Project Teams submit requests through Git but do not receive deployment
credentials. Protected workflows use trusted runner identities to access cloud
services and Terraform state after approval.

## GitHub plan capability matrix

Select one security profile for the entire project repository. Private
repositories on a paid plan should use `github-environments`; private
repositories on GitHub Free must use the `repository-secrets` fallback.

| Capability | GitHub Free private repository | Pro/Team private repository | Enterprise private repository |
|---|---|---|---|
| Supported profile | `repository-secrets` | `github-environments` | `github-environments` |
| Workload-secret location | Environment-qualified repository bundles | GitHub Environment secrets | GitHub Environment secrets |
| Private-branch protection and enforced CODEOWNERS review | Not available | Available | Available |
| Required Environment reviewers and prevention of self-review | Not available | Not available for private repositories | Available |
| Apply/execute deployment history | Not created by this profile | Recorded by `<environment>-apply` | Recorded by `<environment>-apply` |
| Runner isolation | Repository-level runners and dedicated labels | Organization runner groups on GitHub Team | Organization or enterprise runner groups |
| Approval boundary | Procedural PR review | Enforced PR/CODEOWNERS review; Environment approval remains unavailable | Enforced PR/CODEOWNERS review plus apply/execute Environment approval |

GitHub Pro applies to user-owned private repositories; this asset targets a
GitHub organization, where GitHub Team is the corresponding paid
non-Enterprise plan. Environment secrets are available to private repositories
on paid plans, but required Environment reviewers for private repositories
require Enterprise. Organization runner groups require Team or Enterprise.
Verify these plan contracts against GitHub's current documentation for
[deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments),
[protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches),
and [runner groups](https://docs.github.com/en/actions/concepts/runners/runner-groups)
before each customer installation.

These plan differences affect GitHub governance only. Both profiles retain the
same protected-default-branch resolver, same-repository guard, manifest-only
validation, immutable component refs, environment-qualified placeholders,
state isolation, concurrency and cloud runner identity.

Before production rollout:

- Keep shared and project repositories private. Use the recommended
  `github-environments` profile on paid plans, protect `main`, require
  CODEOWNERS and successful checks, and configure Environment reviewers where
  the private-repository plan supports them. Use `repository-secrets` only as
  the GitHub Free fallback, with administration and direct pushes restricted
  by policy.
- Require a successful plan or check and human approval. GitHub Environment
  secrets and protected branches strengthen every paid tier and provide
  deployment history. Required Environment reviewers and prevention of
  self-review enforce an additional boundary on Enterprise private
  repositories; Free-profile approval remains procedural.
- Pin shared workflows, GitHub Actions, catalogs, and orchestrators to approved
  versions.
- Separate Terraform state by organization, project, cloud, environment, and
  region.
- Give each runner identity only the permissions required for its cloud and
  workload scope.
- For ExaCS out-of-place patching, use a separate runner dynamic group scoped
  to the project database compartment. `manage database-family` is required by
  the OCI Database API for the approved Database and Database Home move; never
  grant it tenancy-wide. The runtime additionally enforces the platform-owned
  ExaCS registry and exact VM-cluster/compartment checks.
- Resolve credentials and passwords at runtime; never store them in manifests,
  handoffs, the UI, or the Codex app.
- In `github-environments`, use a reviewer-free base Environment for plan/check
  and a reviewer-protected `<environment>-apply` Environment for apply/execute;
  keep identical `GITOPS_SECRET_VALUES` and `READINESS_MARKER` secrets in the
  pair. Same-named repository secrets containing only `{"INVALID":"true"}`
  and `false` are required fail-closed transport sentinels, not credential
  storage. In
  `repository-secrets`, keep one environment-qualified JSON repository secret
  and readiness variable per environment. The default-branch caller rejects
  forks, workflow changes, mixed tuples, and cross-environment placeholders in
  both profiles.
- Test failed plans, partial deployments, state recovery, runner isolation, SSH
  host verification, and audit evidence in non-production.

The optional UI and Codex app assistant can create Git changes only. They cannot
call cloud APIs, hold deployment credentials, merge their own pull requests, or
control deployment workflows.

Review these controls against your organization's security, compliance, data
residency, and change-management requirements before enabling production use.
