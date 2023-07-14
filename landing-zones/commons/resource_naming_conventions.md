# RESOURCE NAMING CONVENTIONS

&nbsp; 

## 1. Introduction

A resource naming convention helps to identify resources, their type, and location by the name, quickly. If you don't have any naming convention in place, we recommend the following Resource Naming Convention:

- Segments of the name are separated by "-".
- Within a name segment avoid using &lt;space&gt; and ".".
- Where possible intuitive/standard abbreviations should be considered (e.g., use "shared" instead of "shared.cloud.team").
- When referring to the compartment fully qualified compartment path, use ":" as a separator, e.g. cmp-shared:cmp-security

Examples of names are:
- cmp-shared
- cmp-&lt;workload&gt;
- cmp-networking

The patterns used for the names are:
- &lt;resource-type&gt;-&lt;environment&gt;-&lt;location&gt;-&lt;purpose&gt;
  &lt;resource-type&gt;-&lt;environment&gt;-&lt;source-location&gt;-&lt;destination-location&gt;-&lt;purpose&gt;
- &lt;resource-type&gt;-&lt;entity/sub-entity&gt;-&lt;environment&gt;-&lt;function/department&gt;-&lt;project&gt;-&lt;custom&gt;

&nbsp; 

## 2. List of Resource Types


| RESOURCE TYPE  |  ABREVIATION | 
|---|---|
| Agent | agt | 
| Alarm | al |
| API Gateway |apigw |
| Autonomous Container Database (Dedicated) | adbc 
| Autonomous Database (Transaction Processing) | atp 
| Autonomous Data Warehouse | adw 
| Autonomous Exadata Infrastructure | aei 
| Autonomous JSON Database | ajd 
| Autonomous Database with APEX | apx 
| Bastion Service | bst |
| Bucket | bkt |
| Block Volume | blk |
| Cloud Guard Recipe (cloned) | cg-act, cg-cfg|
| Cloud Guard Responder (cloned) | cg-rsp |
| Cloud Guard Target | cg-tgt |
| Compartment | cmp |
| Container Repository | cir |
| Customer Premise Equipment | cpe |
| Database on VM | db |
| Database Backup | dbb |
| Database Backup Destination | dbbd |
| Database Connection | dbc |
| Database Home | dbh |
| Database Key Store | dks |
| Database Node | dbn |
| Database Pluggable Database | pdb |
| Database Server | dbs |
| Database Software Image | dbi |
| Database System | dbsys |
| DNS Endpoint Forwarder | dnsepf |
| DNS Endpoint Listener | dnsepl |
| Dynamic Group | dgp |
| Dynamic Routing Gateway | drg |
| Dynamic Routing Gateway Attachment | drgatt |
| Event Rule | rul |
| ExaCS Infrastructure | ecsi |
| ExaCS VMCluster Cloud | ecsvmc |
| Exadata Cloud@Customer Infrastructure | ecci |
| Exadata Cloud@Customer VMCluster | eccvmcls |
| Exadata Cloud@Customer Operator Control | eccop |
| Exadata Cloud@Customer Operator Control Assignment | eccopasgn |
| Exadata Cloud@Customer Operator Control Access Request | eccopreq |
| External Database | edb |
| External Container Database | edbc |
| External Pluggable Container Database | epdb |
| External Non-Container Database | edbn |
| External Database Connector | edbc |
| Fast Connect | fc# &lt;# := 1...n&gt; |
| File Storage | fss |
| Function | fun |
| Group | grp |
| Internet Gateway | igw |
| Load Balancer | lb |
| Location (Three-letter region code)| ams, fra, etc. |
| Log | log |
| Log Groups | lgrp |
| NAT Gateway | nat |
| Network Security Group | nsg |
| Notification Topic | nott |
| Managed key | key |
| OCI Function Application | fn |
| Object Storage Bucket | bkt |
| Policy | pcy |
| Routing Table | rt |
| Secret | sec |
| Security List | sl |
| Security Zone Recipe | sz-rcp |
| Security Zone Target | sz-tgt |
| Service Gateway | sgw |
| Service Connector Hub | sch |
| Stream | str |
| Subnet | sub |
| Tenancy | tcy |
| Vault | vlt |
| Virtual Cloud Network | vcn |
| Virtual Machine | vm |
| Vulnerability Scanning Recipe - Container | vss-recc |
| Vulnerability Scanning Recipe - Host | vss-rech |
| Vulnerability Scanning Target | vss-tgt |


&nbsp; 


# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-ngineering/blob/folder-structure/LICENSE) for more details.