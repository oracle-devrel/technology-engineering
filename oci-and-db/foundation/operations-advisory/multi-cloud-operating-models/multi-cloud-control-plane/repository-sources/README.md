# Repository sources

Each directory contains a repository or runtime artifact prepared during MCCP
installation. General installation, usage, architecture, support, and security
guidance stays in the [MCCP documentation](../README.md); source READMEs
describe only the local technical contract that remains useful after
publication.

| Source | Purpose |
| --- | --- |
| `platform-ci/` | Shared approved Terraform and Ansible execution workflows |
| `gitops-templates/` | Approved resource and lifecycle operation catalog |
| `nonprod-project-template/` | Shared `dev`, `test`, and `uat` project repository template |
| `prod-project-template/` | Isolated production project repository template |
| `optional-ui/` | Optional UI runtime artifact; not one of the four shared repositories |

Cloud Operations prepares these sources through the
[shared-repositories guide](../docs/installation/installation-runbook.md).
