# Repository sources

Each directory is the source for one published repository. The Optional UI is
an optional runtime artifact staged by the MCCP installation process.

| Source | Published purpose |
| --- | --- |
| `platform-ci/` | Shared approved Terraform and Ansible execution workflows |
| `gitops-templates/` | Approved Day 1 resource and Day 2 operation catalog |
| `nonprod-project-template/` | Shared `dev`, `test`, and `uat` project repository template |
| `prod-project-template/` | Isolated production project repository template |
| `optional-ui/` | Optional web request interface |

Cloud Operations prepares these sources through the
[shared-repositories guide](../docs/installation/installation-runbook.md).
