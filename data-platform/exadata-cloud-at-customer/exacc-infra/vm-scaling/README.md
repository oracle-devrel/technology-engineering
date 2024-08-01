# VM scaling

**To be able to achieve the best possible consumption results it is highly advisable to set up automated scaling for the VM clusters running on Exadata Cloud@Customer.**

# VM Cluster Scaling based on CPU load

Scaling the number of OCPUs allocated to a VM cluster based on CPU load is possible by using Dynamic Scaling. Dynamic Scaling is currently not part of the official cloud tooling, therefore it can not be configured from the OCI console.

**Installation Best Practices**

Please follow the installation instructions in the bellow linked MOS notes. The system running the Dynamic Scaling scripts has to have internet access to be able to connect to OCI. Oracle DynamicScaling can be executed as standalone executable or as daemon on VM cluster nodes. DynamicScaling is leveraging on oci-cli or restAPI to perform the scale operations hence you have same network requirements to access OSN (Oracle Service Network). You can find the link for oci-cli GitHub page below.

# Autonomous VM Cluster Scaling based on CPU load

Scaling the number of OCPUs/ECPUs allocated to an Autonomous VM cluster is possible by activating the Auto Scaling feature, which is part of the official cloud tooling and can be activated at the creation of an Autonomous environment or at any later point.

**Installation Best Practices**

With auto-scaling enabled, the database can use up to three times more CPU and IO resources than specified by the number of CPUs currently shown in the Scale Up/Down dialog. If auto-scaling is disabled while more CPU cores are in use than the database's currently assigned number of cores, then Autonomous Database scales the number of CPU cores in use down to the assigned number.

# Automation of resource stopping/starting

For environments, where 7/24 availability is not required it is highly advisable to implement automatic stopping the resources for out of hours, then automatically restarting those when necessary. This can be achieved by using the REST API. Please see an example written in python on the below GitHub link.

# Useful Links

- [(ODyS) Oracle Dynamic Scaling Suite Main Index Page (Doc ID 2774779.1)](https://support.oracle.com/epmos/faces/DocumentDisplay?_afrLoop=462034266570470&id=2774779.1&displayIndex=5&_afrWindowMode=0&_adf.ctrl-state=28hy4urnp_72)
- [(ODyS) Oracle Dynamic Scaling engine - Scale-up and Scale-down automation utility for OCI DB System (ExaCS/ExaC@C) (Doc ID 2719916.1](https://support.oracle.com/epmos/faces/DocumentDisplay?_afrLoop=462547894780385&parent=DOCUMENT&sourceId=2774779.1&id=2719916.1&_afrWindowMode=0&_adf.ctrl-state=28hy4urnp_121)
- [oci-cli on GitHub](https://github.com/oracle/oci-cli)
- [ExaCC VM cluster manipulation with python](https://github.com/oracle/oci-python-sdk/blob/master/examples/exacc_vmcluster_example.py)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
