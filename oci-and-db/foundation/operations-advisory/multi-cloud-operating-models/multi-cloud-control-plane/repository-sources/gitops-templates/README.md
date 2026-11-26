# Approved GitOps catalog

Choose a template for your handed-off project repository. Each template shows the settings you can request.

| To request | Start with |
| --- | --- |
| An OCI, Azure or Google Cloud resource | [Resource catalog](resources-catalog/README.md) |
| An operation on an existing OCI resource | [Lifecycle operations catalog](operations-catalog/README.md) |

For a resource, replace the placeholders with approved inputs and add the entry to its regional manifest. Keep each Terraform root configuration in a single file. Use a dedicated secret reference for each database and approved public keys where required. Keep passwords, private keys and cloud credentials out of Git.

For an operation, put the selected template in `oci/{environment}/{region}/lifecycle_operations/` and use the exact target display name from Terraform state.

Follow the common process to review, merge and verify the request. [Project Team guide](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/usage/README.md)

## License

Copyright (c) 2026 Oracle and/or its affiliates. Licensed under the Universal Permissive License, Version 1.0. See [LICENSE](LICENSE).
