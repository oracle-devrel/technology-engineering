# evaluate-pg-rpo.py

RPO Estimation for a FSDR Protection Group

Reviewed: 24.03.2026

# When to use this asset?

It can be used to roughly estimate the global RPO of a _FSDR Protection Group_ and as an example on how
use the Python SDK and OCI API to get the replication metrics of some services.

# How to use this asset?

This is a simple Python script that can be used just passing the FSDR Protection Group ID and having access to the
Primary and Secondary region.

# Disclaimer 

This is program is just meant as an example on how to collect replication information from the FSDR PG underlying services. The 
evaluate RPO is not to consider an indication on a _real RPO_ which depends on multiple factors and which should be always 
evaluated taking into account the workload characteristics and the application behavior.   

# Overview

FSDR is DR coordinator and orchestrator service and it doesn't influence its Protection Groups RPO in any way. 
The PG RPO depends only on the underline services and their replication methods. That said, this python script 
allows to evaluate the _maximum RPO_ of the group using the exposed replication metrics of its services.

# Prerequisites 

You'll need Python3 and the following packages:

- OCI module
- PyYAML module


For example, on Linux or MacOS, using a virtual environment configured with _pyenv_: 

```sh
pyenv shell 3.14.2 
pip install OCI
pip install PyYAML
```

# Currently Supported Services

Currently, the script supports the following resources in the protection group:

- Movable Virtual Machine
- Block Volume Group
- File System Service
- Object Storage Buckets
- Base DB System
- Autonomous Database
- OKE Cluster 

# Usage 

The script -h flag shows the usage options: 

```sh
./evaluate_pg_rpo.py -h
usage: evaluate_pg_rpo [-h] [-p PROTECTION_GROUP_ID] [-r REGION] [-t] [-c CONFIGURATION_FILE] [-d] [-v]

Evaluate the RPO of a FSDR Protection Group.

options:
  -h, --help            show this help message and exit
  -p, --protection_group_id PROTECTION_GROUP_ID
  -r, --region REGION
  -t, --tagging         Tagging flag, when enabled write the RPO in a free-form tag on the PG. Defaulting to no
                        tagging.
  -c, --configuration_file CONFIGURATION_FILE
                        OCI configuration file, defaulting to ~/.oci/config. If the string "none" is provided, instance principal
                        authentication is used.
  -d, --debug           Debug flag, defaulting to no debug
  -v, --version         Shows version.
  ```


# Output Example

```sh
 python3 ./evaluate-pg-rpo.py -p ocid1.drprotectiongroup.oc1.eu-milan-1.<hidden>

Components RPO:
-------- Type --------   -------- Name --------   --- RPO (sec) ---
OBJECT_STORAGE_BUCKET    mushop-media-cris           108
OBJECT_STORAGE_BUCKET    mushop-cris                 108
VOLUME_GROUP             mushop-vg                   173
AUTONOMOUS_DATABASE      MuShopDB-cris                60

Protection Group RPO:
Global RPO            :    173 sec
Component driving RPO : VOLUME_GROUP
```

# Useful Links

- [FSDR Documentation](https://docs.oracle.com/en-us/iaas/disaster-recovery/index.html)
- [OCI Python SDK](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/pythonsdk.htm)
- [pyenv util](https://github.com/pyenv/pyenv)
- [PyYAML Module](https://pypi.org/project/PyYAML/)


# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.