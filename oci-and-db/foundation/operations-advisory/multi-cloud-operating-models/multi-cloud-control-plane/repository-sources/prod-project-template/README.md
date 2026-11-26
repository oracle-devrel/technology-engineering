# Production project repository

Use this repository to request approved changes in `prod`. Use the separate `nonprod-<project>` repository for non-production.

1. For OCI and Google Cloud, use the approved foundation references in `environments/prod/environment_information.md`. For Azure, use the approved foundation inputs from the request or existing resource JSON. The handoff can include Azure notes, and the runner supplies Azure authentication.
2. Choose an item from the [organization's catalog](https://github.com/__CUSTOMER_ORG__/gitops-templates) and edit its manifest under `<cloud>/prod/<region>/`.
3. Open a pull request for review and follow the matching workflow. [Project Team guide](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/usage/README.md)

## Review ownership

The Project Team configures its reviewers through a reviewed change. When ready, rename `.github/CODEOWNERS.template` to `.github/CODEOWNERS` and replace `__PLATFORM_OWNERS__` and `__PROD_OWNERS__` with the approved GitHub teams. Keep the template in place until ownership is configured. On a GitHub Free private repository, record independent review through the team's approved process.

Cloud Operations owns the handoff, workflows, runner access and deployment credentials. Keep Terraform state and secret values in their approved stores.
