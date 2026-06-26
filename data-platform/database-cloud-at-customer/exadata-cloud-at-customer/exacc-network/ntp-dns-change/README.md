# ExaDB-C@C Change NTP/DNS on ExaDB-C@C configuration

## Changing the NTP/DNS configuration on the CPS network

To change the NTP/DNS on the Control Plane Server (CPS) network, the customer must open an SR and cloudOps can make the changes.

## Changing the NTP/DNS configuration for a VM cluster

The only supported way to do so is to recreate the VM cluster : 

1. Terminate the Databases in the VM Cluster - destroys the database
2. Terminate the VM Cluster - destroys the VM Cluster
3. This leaves the VM Cluster Network editable
4. Edit VM Cluster Network as desired
5. Create VM Cluster using above VM Cluster Network
6. Create DB Home
7. Provision Databases or Restore from backups

# Useful Links

- [Documentation - Manage VM Cluster Networks](https://docs.oracle.com/en/engineered-systems/exadata-cloud-at-customer/ecccm/ecc-manage-vm-cluster-network.html#GUID-0BC2881E-8B56-4432-B24A-959A090800D8)

Reviewed: 06/23/26

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
