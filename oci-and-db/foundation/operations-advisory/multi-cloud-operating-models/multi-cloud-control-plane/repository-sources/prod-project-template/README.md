# Production project repository

This handed-off MCCP repository is the Project Team workspace for approved
`prod` resource requests. Non-production requests belong in the separate
`nonprod-<project>` repository.

Project manifests use `<cloud>/prod/<region>/...`. The approved production
foundation references are recorded in
`environments/prod/environment_information.md`.

Project Teams change only supported manifests through reviewed pull requests.
The Project Team owns review ownership. When it is ready to configure it, copy
`.github/CODEOWNERS.template` to `.github/CODEOWNERS` and replace
`__PLATFORM_OWNERS__` and `__PROD_OWNERS__` with GitHub teams. A template-only
file is valid until then. On a GitHub Free private repository, CODEOWNERS
records intended ownership but does not enforce review without branch
protection. Cloud Operations owns the handoff, protected workflows, runner
configuration, and deployment credentials. Terraform state and secret values
never belong in this repository.

Use the organization's
[approved catalog](https://github.com/__CUSTOMER_ORG__/gitops-templates) and
follow the canonical
[Project Team guide](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/usage/README.md).
