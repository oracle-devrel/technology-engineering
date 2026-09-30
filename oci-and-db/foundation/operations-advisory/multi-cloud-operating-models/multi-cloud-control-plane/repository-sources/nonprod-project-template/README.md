# Non-production project repository

This handed-off MCCP repository is the Project Team workspace for approved `dev`, `test`, and `uat` resource requests. Production requests belong in the separate `prod-<project>` repository.

Project manifests use `<cloud>/<environment>/<region>/...`. The approved foundation references for each environment are recorded in `environments/<environment>/environment_information.md`.

Project Teams change only supported manifests through reviewed pull requests. The Project Team owns review ownership. When it is ready to configure it, copy `.github/CODEOWNERS.template` to `.github/CODEOWNERS` and replace `__PLATFORM_OWNERS__`, `__DEV_OWNERS__`, `__TEST_OWNERS__`, and `__UAT_OWNERS__` with GitHub teams. A template-only file is valid until then. On a GitHub Free private repository, CODEOWNERS records intended ownership but does not enforce review without branch protection. Cloud Operations owns the handoff, protected workflows, runner configuration, and deployment credentials. Terraform state and secret values never belong in this repository.

Use the organization's [approved catalog](https://github.com/__CUSTOMER_ORG__/gitops-templates) and follow the canonical [Project Team guide](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/usage/README.md).

## ExaCS Day-2 database requests

The reusable ExaCS Day-2 request templates are under
`templates/exacs-day2/`, outside `oci/`; they do not invoke a workflow until a
project team copies one into its lifecycle-operations directory. Copy exactly
one CRQ template to:

```text
oci/<environment>/<region>/lifecycle_operations/crq-<number>-<operation>.json
```

Replace the logical-name and secret placeholders, then commit the request once.
After the operation executes, never edit that CRQ file; create a new CRQ for a
new change. The workflow resolves resources by logical display name, performs
and verifies the operation, and only then creates or refreshes the OCI-observed
inventory at:

```text
inventory/oci/<environment>/<region>/exacs-databases.json
```

That inventory is a read-only observed record of DB Homes, CDBs, and PDBs. It
is not an input to Terraform or Ansible, and it must not be used to supply OCI
identifiers to either tool.
