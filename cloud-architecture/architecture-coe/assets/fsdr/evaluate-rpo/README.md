# RPO Evaluation for a FSDR Protection Group

## Overview

FSDR is DR coordinator and orchestrator service and it doesn't influence its Protection Groups RPO in any way. 
The PG RPO depends only on the underline services and their replication methods. That said, this python script 
allows to evaluate the _maximum RPO_ of the group using the exposed replication metrics of its services.

## Prerequisites 

You'll need Pyhon3 and the following packages:

- OCI module
- PyYAML module


For example, on Linux, using a virtual environemnt configured with _pyenv_: 

```sh
pyenv shell 3.14.2 
pip install OCI
pip install PyYAML
```


## Usage 

The script -h flag presents the usage options: 

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
## Supported Services

The script supports the following resources in the protection group:

- Movable Virtual Machine
- Block Volume Group
- File System Service
- Object Storage Buckets
- Base DB System
- Autonomous Database
- OKE Cluster 


## Disclaimer 

This is program is just meant as an example on how to collect replication information from the FSDR PG underline services. The 
evaluate RPO is not to consider an indication on a _real RPO_ which dependes on multiple factors and which should be always 
evaluated taking into account the workload caracteristics and the application behaviour.   
