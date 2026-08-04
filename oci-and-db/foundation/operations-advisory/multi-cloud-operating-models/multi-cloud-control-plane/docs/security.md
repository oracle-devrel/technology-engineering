# Security

Project teams submit reviewed Git changes but do not receive deployment
credentials. Trusted runner identities access cloud services and Terraform
state only after a human merges an approved change.

## MVP profile: GitHub Free repository secrets

The supplied MVP uses one fixed profile in every project repository, including
production: `repository-secrets`. Each logical environment has one
environment-qualified JSON repository secret and one readiness variable:

| Environment | Secret | Readiness variable |
| --- | --- | --- |
| `dev` | `GITOPS_SECRET_VALUES_DEV` | `CONTROL_PLANE_READY_DEV` |
| `test` | `GITOPS_SECRET_VALUES_TEST` | `CONTROL_PLANE_READY_TEST` |
| `uat` | `GITOPS_SECRET_VALUES_UAT` | `CONTROL_PLANE_READY_UAT` |
| `prod` | `GITOPS_SECRET_VALUES_PROD` | `CONTROL_PLANE_READY_PROD` |

The default-branch caller rejects forks, workflow changes, mixed tuples,
invalid JSON, and cross-environment placeholders. It passes exactly one named
secret bundle to the release-tag-pinned Platform CI reusable workflow. It
never inherits all secrets or serializes the repository secret collection.

GitHub Free private repositories do not provide the enforceable private branch
protection, CODEOWNERS review, or Environment approval controls needed for a
technical approval boundary. The operational control is therefore procedural:
restrict administrators and direct pushes, record independent human review,
verify the current-commit plan/check, then merge. Do not represent that as
enforced GitHub approval.

Before accepting a workload request:

- Keep shared and project repositories private. Pin internal MCCP release tags
  without moving them, use reviewed major release tags for official GitHub
  Actions, pin the OCI orchestrator to its reviewed commit SHA, and pin the
  Azure and Google adapters to reviewed immutable release tags.
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

The paid-plan model uses paired GitHub Environments,
protected branches, required reviews, and runner groups where the selected
GitHub plan supports them. Enable it only after testing the controls in the
customer organization. See
[final-environment-hardening.md](final-environment-hardening.md).
