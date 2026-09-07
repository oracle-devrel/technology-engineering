# Security and GitHub controls

Project Teams submit reviewed Git changes but do not receive deployment
credentials. Cloud Operations manages repository controls, secrets, state, and
runner identities. A trusted runner accesses the cloud only after a human merges
an approved change.

## GitHub Free baseline

The supplied release uses one `repository-secrets` profile. GitHub Free private
repositories cannot access
[organization secrets or variables](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets#creating-secrets-for-an-organization),
so each environment uses one optional JSON repository secret:

| Environment | Secret bundle |
| --- | --- |
| `dev` | `GITOPS_SECRET_VALUES_DEV` |
| `test` | `GITOPS_SECRET_VALUES_TEST` |
| `uat` | `GITOPS_SECRET_VALUES_UAT` |
| `prod` | `GITOPS_SECRET_VALUES_PROD` |

A bundle is needed only when a manifest contains a matching placeholder. The
workflow passes only the selected environment bundle to Platform CI. It rejects
forks, workflow changes, invalid JSON, mixed environments or regions,
cross-environment placeholders, and any field a lifecycle operation does not
declare.

GitHub Free private repositories do not provide enforceable
[private branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
or deployment-environment approval. CODEOWNERS cannot enforce review without
branch protection. On this profile, approval is procedural: restrict direct
pushes and administrators, record independent review, verify the current plan
or check, and then merge. Do not describe this as GitHub-enforced approval.

## Required controls

- Keep shared and project repositories private.
- Restrict Platform CI writes to Cloud Operations and review every change to
  its `main` branch.
- Use the reviewed OCI, Azure, and Google Cloud orchestrator commits and
  reviewed GitHub Action release tags.
- Isolate state by organization, project, cloud, environment, and region.
- Give each runner only the cloud permissions and labels required for its scope.
- Keep non-production and production on separate runners.
- Keep Azure `ARM_*` values and Google credentials on the trusted runner, not in
  project manifests or secret bundles.
- Resolve passwords from the selected secret bundle; never commit them or add
  them to handoff or Codex configuration.
- Complete the [environment secret isolation test](verify-secret-isolation.md)
  before the first workload request.

## Additional controls for paid GitHub plans

These controls are not implemented by this release and require a separately
tested hardened profile. GitHub Pro and GitHub Team can use protected `main`
branches and environment secrets or variables in private repositories. They do
not provide required deployment reviewers for private repositories.

GitHub Enterprise Cloud can additionally use required deployment reviewers,
prevent self-review, and keep environment secrets behind an approval gate in
private repositories. It can support paired GitHub Environments such as `dev`
and `dev-apply` when that model has been qualified for the customer.

Availability depends on the GitHub plan and repository visibility. Verify the
current GitHub documentation for
[protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches),
[deployment environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments),
and [runner groups](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/manage-access)
before designing that profile. Do not add these controls as an untested switch
to the supplied GitHub Free workflow.
