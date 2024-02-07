## Terraform - Provisioning Single host SDDC
Create by: richard.garsthagen@oracle.com
Date: February 2024

This is an example Terraform script to provision a single host SDDC.

The terraform creates:
- a VCN for deploying SDDC into
- Needed subnet for ESXi servers
- Needed VLANS for the VMware stack

The vSphere VLAN will be configured to allow egress traffic to internet via 
NAT Gateway. This is needed for provisioning to succeed. As internet access
is needed to license registration with VMware.

more info:
https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/ocvp_sddc

# License
Copyright (c) 2024 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.