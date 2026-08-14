# Approved GitOps catalog

Use these JSON templates to prepare supported infrastructure and lifecycle
requests in a handed-off project repository. The catalog is versioned with the
templates and describes their local fields; the canonical
[Project Team guide](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/usage/README.md)
defines the request lifecycle.

- `resources-catalog/` contains Day 1 OCI, Azure, and Google templates.
- `operations-catalog/` contains available OCI Day 2 operations.

For a Day 1 request, choose the approved template, replace its non-secret
`__UPPER_SNAKE_CASE__` values, and merge the resulting entry into the project's
existing regional manifest. Do not create a second file with the same
Terraform root key: Terraform does not deep-merge variable files.

For secrets, commit only an environment-qualified runtime token such as
`__DEV_ADB_ADMIN_PASSWORD__`. The trusted workflow resolves its value from the
matching environment secret bundle at runtime.

For a Day 2 request, copy an available operation manifest into
`oci/{environment}/{region}/lifecycle_operations/`. Use an exact resource
display name from Terraform state. The operations catalog lists the available
operations and fields.

Never commit passwords or cloud credentials.

See [resources-catalog](resources-catalog/README.md) and
[operations-catalog](operations-catalog/README.md) for the supported fields.

## License

Copyright (c) 2026 Oracle and/or its affiliates. Licensed under the Universal
Permissive License, Version 1.0. See [LICENSE](LICENSE).
