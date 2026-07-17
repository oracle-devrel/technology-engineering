# Approved GitOps catalog

Use these JSON templates to prepare supported infrastructure and lifecycle
requests in a handed-off project repository.

- `resources-catalog/` contains Day 1 OCI, Azure, and Google templates.
- `operations-catalog/` contains available OCI Day 2 operations.

For a Day 1 request, choose the approved template, replace its
`__UPPER_SNAKE_CASE__` values, and merge the resulting entry into the project's
existing regional manifest. Do not create a second file with the same Terraform
root key: Terraform does not deep-merge variable files.

For secrets such as an OCI Autonomous Database admin password, keep a token such
as `__ADB_ADMIN_PASSWORD__` in Git and create a GitHub Actions secret with the
same name without underscores at the ends. The trusted workflow resolves it at
runtime.

For a Day 2 request, copy an available operation manifest into
`oci/{region}/lifecycle_operations/`. Use an exact resource display name from
Terraform state. OCI Autonomous Database start/stop and OCI Compute
`deploy-agent` are available; Azure and Google Day 2 are not.

Never copy landing-zone IAM, credential, or foundation configuration into a
project repository. Never commit passwords or cloud credentials.

See [resources-catalog](resources-catalog/README.md) and
[operations-catalog](operations-catalog/README.md) for the supported fields.

## License

Copyright (c) 2026 Oracle and/or its affiliates. Licensed under the Universal
Permissive License, Version 1.0. See [LICENSE](LICENSE).
