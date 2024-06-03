# BeeGFS BeeOND role

This repository contains the ansible role needed to deploy a BeeOND instance on machines rifght after the deployment of those.

This is meant to be used in conjunction with the OCI HPC Stack.

You need to modify the new_nodes.yaml similarly as the file that's part of this repository.

Once configured, the machines deployed via Autoscaling, will come up with a BeeOND instance that will be using the local NVME disks of the nodes

## License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
