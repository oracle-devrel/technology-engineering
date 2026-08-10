# Security

Project teams submit reviewed Git changes but do not receive deployment
credentials. Trusted runner identities access cloud services and Terraform
state only after a human merges an approved change.

## MVP profile: GitHub Free repository secrets

The supplied MVP uses one fixed profile in every project repository, including
production: `repository-secrets`. GitHub Free private repositories cannot
access organization secrets or variables, so a workload that contains secret
placeholders uses one environment-qualified JSON repository secret. A project
with no secret placeholders requires no repository secret:

| Environment | Conditional secret |
| --- | --- |
| `dev` | `GITOPS_SECRET_VALUES_DEV` |
| `test` | `GITOPS_SECRET_VALUES_TEST` |
| `uat` | `GITOPS_SECRET_VALUES_UAT` |
| `prod` | `GITOPS_SECRET_VALUES_PROD` |

The default-branch caller rejects forks, workflow changes, mixed tuples,
invalid JSON, and cross-environment placeholders. It passes exactly one named
secret bundle to the Platform CI `main` reusable workflow when one is needed.
It never inherits all secrets or serializes the repository secret collection.
Platform CI stays private and is shared with organization workflows through
GitHub Actions access settings. The reusable workflow downloads its directly
referenced composite action on `main` with GitHub's scoped token; no deploy
key or personal access token is used.

GitHub Free private repositories do not provide the enforceable private branch
protection, CODEOWNERS review, or Environment approval controls needed for a
technical approval boundary. The operational control is therefore procedural:
restrict administrators and direct pushes, record independent human review,
verify the current-commit plan/check, then merge. Do not represent that as
enforced GitHub approval.

Before accepting a workload request:

- Keep shared and project repositories private. Use the protected Platform CI
  `main` branch, reviewed major release tags for official GitHub Actions, the
  OCI orchestrator's reviewed commit SHA, and reviewed release tags for the
  Azure and Google adapters.
- Keep state isolated by organization, project, cloud, environment, and
  region.
- Give each runner only the cloud permissions and routing labels needed for
  its assigned scope.
- Resolve passwords at runtime from the one selected secret bundle; never put
  them in manifests, handoffs, or Codex configuration.
- Validate a successful plan/check and the repository-secret acceptance test
  in non-production before a real change.

The initial OCI-hosted runner can carry OCI, Azure, and Google routing labels.
Keep Azure service-principal `ARM_*` values and the Google ADC file on that
runner; neither belongs in a workload secret bundle. The target separation
model uses one native runner boundary per cloud, with the same manifests and
pull-request gate.

## Paid-plan enforcement model

The paid-plan profile keeps the same native private Actions access and
repository-and-environment scoped workload secret bundles. It adds paired
GitHub Environments, protected branches, required reviews, and runner groups
where the selected GitHub plan supports them. Enable it only after testing the
controls in the customer organization. See
[final-environment-hardening.md](final-environment-hardening.md).
