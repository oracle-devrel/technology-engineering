# Exadata Cloud@Customer VM Serial Console Access

Announcing the General Availability (GA) of VM Serial Console Access for Exadata Cloud@Customer. With this new feature, customers can:

- Enable a serial console connection to each individual VM
- Access the virtual serial console via SSH (via proxy and hypervisor)
- Terminate the serial console connection when the required actions have been completed

Reviewed: 24.06.2024

# Key Benefit

This new feature allows customers to access the serial console of their Virtual Machines in case a need arises for emergency debugging. Use cases include accessing GRUB to fix boot issues or accessing the VM when SSH access is unavailable. Typical reasons for this access include accidentally changing or deleting keys, killing or a processes is in a tucked state, and having firewall issues on the VM, among many others.

# Additional Links:

- [What's New announcement in product documentation](https://docs.oracle.com/en/engineered-systems/exadata-cloud-at-customer/ecccm/ecc-whats-new-in-exadata-cloud-at-customer-gen2.html#GUID-303FAF7D-A607-4D3F-95BB-25A477E3F09A)

- Proper OCI user permissions are required to create a serial console connection - see [product documentation](https://docs.oracle.com/en/engineered-systems/exadata-cloud-at-customer/ecccm/ecc-policy-details.html#GUID-CBEEA1B3-8CFC-4E9C-ACA8-6675F4582920) for details


# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
