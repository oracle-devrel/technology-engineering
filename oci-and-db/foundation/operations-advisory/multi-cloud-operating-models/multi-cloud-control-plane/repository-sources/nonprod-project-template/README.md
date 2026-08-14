# Non-production project repository

This handed-off MCCP repository is the Project Team workspace for approved
`dev`, `test`, and `uat` resource requests. Production requests belong in the
separate `prod-<project>` repository.

Project manifests use `<cloud>/<environment>/<region>/...`. The approved
foundation references for each environment are recorded in
`environments/<environment>/environment_information.md`.

Project Teams change only supported manifests through reviewed pull requests
and configure their review ownership from `.github/CODEOWNERS.template`. Cloud
Operations owns the handoff, protected workflows, runner configuration, and
deployment credentials. Terraform state and secret values never belong in this
repository.

Use the organization's
[approved catalog](https://github.com/__CUSTOMER_ORG__/gitops-templates) and
follow the canonical
[Project Team guide](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/usage/README.md).
