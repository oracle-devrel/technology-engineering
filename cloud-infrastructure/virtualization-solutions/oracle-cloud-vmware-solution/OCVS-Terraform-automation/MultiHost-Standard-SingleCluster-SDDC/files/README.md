## Terraform - Provisioning Multi host SDDC with single cluster

Create by: Richard Garsthagen

Date: February 2024

This is an example Terraform script to provision a hulti host SDDC environment with a single cluster based on a Standard shape (Block volumes based).

The terraform creates:
- a VCN for deploying SDDC into
- Needed subnet for ESXi servers
- Needed VLANS for the VMware stack

The vSphere VLAN will be configured to allow egress traffic to the internet via NAT Gateway. This is needed for provisioning to succeed. Internet access is needed to license registration with VMware.

[More Info](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/ocvp_sddc)

# License
Copyright (c) 2024 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.