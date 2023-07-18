# Terraform scripts for MySql Service provisioning.

This terraform script can be used to provision a MySql Service.

## When to use this asset?

This can be used to create an OCI MySql Service and required Networking components.

## How to use this asset?

1. `cd`  to oci_mds.
2. Update variable values in terraform.tfvars file:
	a. compartment_id = "ocid1.compartment.oc1.."
	b. region = "" ...
    c. MySql resource variables.
    d. Networking resource variables.
3. Execution:
	`terraform init` .
	`terraform plan/apply` .
4. Login to OCI tenancy to verify the MySql service.

## License
Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.


