# Reference specifications

These JSON Schema documents describe the OCI, Azure, and Google Cloud resource
manifest shapes published by this catalog. They are documentation artifacts
only: no workflow, runtime validator, or Terraform execution reads them.

`oci/adb.schema.json`, `oci/compute.schema.json`, and `oci/nsg.schema.json`,
plus the Azure and Google Cloud ADB and Compute schemas, mirror the governed
project-manifest shapes accepted by the current control plane.

The schemas allow catalog placeholders in addition to rendered values so that
both the catalog template and a project manifest can be read against the same
reference. They do not replace the pinned upstream Orchestrator or Terraform
module contracts.
