# Exadata Cloud@Customer Single Node VM Cluster

With this enhancement, you can deploy and run multiple single-instance databases in a single-node cluster without RAC licenses being required.

Please note. This functionality should only be used in non-production environments where the customer does not have RAC licenses.

The lack of RAC licenses means that the customer is unable to easily instantiate the DB instance on another DB Server in the ExaDB infrastructure. This means that during maintenance, there will ALWAYS be an outage of the DB service unless the customer moves the service to the DR environment. 

Single Node VM Cluster provides ZERO capability for local failover for either planned or unplanned outages.

For customers who do have a RAC license, but want to run Single Node instances, the preferred mechanism is to use clusters, as outlined in the following deck: SIDB on ExaDB

The Single Node VM Cluster implementation is rolled out only to the MTY region. It will be rolled out to other regions in a phased manner

Reviewed: 24.06.2024

# Useful Links

- [About Single-Node VM Cluster](https://docs.oracle.com/en-us/iaas/exadata/doc/ecc-manage-vm-clusters.html#GUID-F528AA9C-2130-4E15-B8DE-DF65FD580789)

- [Using the Console to Create a Single-Node VM Cluster](https://docs.oracle.com/en-us/iaas/exadata/doc/ecc-manage-vm-clusters.html#GUID-6F475E61-176B-481D-92B9-5FD93326C7AA)

- [Using the Console to View Single-Node VM Cluster Details](https://docs.oracle.com/en-us/iaas/exadata/doc/ecc-manage-vm-clusters.html#GUID-CEDD32D1-3309-4ED3-BB28-335348CDE790)


# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
