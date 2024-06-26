# Exadata Cloud@Customer Single Node VM Cluster

With this enhancement, you can deploy and run multiple single-instance databases in a single-node cluster without RAC licenses being required.

Please note. This functionality should only be used on non-production environments, where under BYOL licensing, RAC licenses are not available.

The lack of RAC licenses means that it is impossible to easily instantiate the DB instance on another DB Server in the Exadata Cloud@Customer infrastructure. This means that during maintenance, there will ALWAYS be an outage of the DB service unless there is possibility to switch the service to a DR environment. 

Single Node VM Cluster provides ZERO capability for local failover for either planned or unplanned outages.

If the RAC license is available, but for some reason running Single Node instances is preferred, the suggested way is to use one of the bellow options:

Run each single instance database as a singleton workload or PDB in a shared RAC CDB (the preferred way)
Run each single instance database as a singleton workload or PDB in a dedicated CDB
Run each single instance database as a two–node cluster, but shut down unnecessary instances

# Useful Links

- [About Single-Node VM Cluster](https://docs.oracle.com/en-us/iaas/exadata/doc/ecc-manage-vm-clusters.html#GUID-F528AA9C-2130-4E15-B8DE-DF65FD580789)

- [Using the Console to Create a Single-Node VM Cluster](https://docs.oracle.com/en-us/iaas/exadata/doc/ecc-manage-vm-clusters.html#GUID-6F475E61-176B-481D-92B9-5FD93326C7AA)

- [Using the Console to View Single-Node VM Cluster Details](https://docs.oracle.com/en-us/iaas/exadata/doc/ecc-manage-vm-clusters.html#GUID-CEDD32D1-3309-4ED3-BB28-335348CDE790)


# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
