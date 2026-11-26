# Repository sources

Cloud Operations uses these sources to set up MCCP. The [installation runbook](../docs/installation/installation-runbook.md) explains how to prepare and publish them.

| Source | Purpose |
| --- | --- |
| [Platform CI](platform-ci/README.md) | Shared workflows to check and execute reviewed requests |
| [GitOps catalog](gitops-templates/README.md) | Approved resource and operation templates |
| [Non-production project template](nonprod-project-template/README.md) | Starting point for `dev`, `test` and `uat` |
| [Production project template](prod-project-template/README.md) | Starting point for a separate `prod` repository |
| [Optional UI](optional-ui/README.md) | Optional service for preparing requests |

Each shared repository has its own technical reference. For the common operating model, see [How the Control Plane works](../docs/reference/architecture.md).
