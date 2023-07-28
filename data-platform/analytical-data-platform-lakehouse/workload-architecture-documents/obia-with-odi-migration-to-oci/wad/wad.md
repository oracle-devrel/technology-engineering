# Document Control

| Version | Authors           | Date             | Comments                       |
|:--------|:------------------|:-----------------|:-------------------------------|
| 0.1     | Wilbert Poeliejoe | 25 January 2023  | Initial Draft                  |
| 0.2     | Wilbert Poeliejoe | 20 February 2023 | Network Firewall content added |

| Term  | Meaning                                         |
|:------|:------------------------------------------------|
| AD    | Availability Domain                             |
| ADW   | Autonomous Data Warehouse                       |
| CIDR  | Classless Inter-Domain Routing                  |
| DNS   | Domain Name System                              |
| DRG   | Dynamic Routing Gateway                         |
| ETL   | Extract Transform Load                          |
| IaaS  | Infrastructure as a Service                     |
| IAM   | Identity and Access Management                  |
| IGW   | Internet Gateway                                |
| LB    | Load Balancer                                   |
| LFS   | Liberty Financial Services                      |
| NSG   | Network Security Groups                         |
| OAC   | Oracle Analytics Cloud                          |
| OBIA  | Oracle Business Intelligence Applications       |
| OBIEE | ORacle Business Intelligence Enterprise Edition |
| OCI   | Oracle Cloud Infrastructure                     |
| OCPU  | Oracle Compute Unit                             |
| ODI   | Oracle Data Integrator                          |
| OSN   | Oracle Service Network                          |
| PVO   | Public View Object                              |
| SGW   | Service Gateway                                 |
| VCN   | Virtual Cloud Network                           |
| VNIC  | Virtual Network Interface Card                  |

```{=tex}
\pagebreak
```
# Document Control

## Team

| Name              | eMail                        | Role                                        | Company |
|:------------------|:-----------------------------|:--------------------------------------------|:--------|
| Wilbert Poeliejoe | Wilbert.poeliejoe@oracle.com | Initial Author (to be removed for customer) | Oracle  |

## Document Purpose

This document provides a high-level solution definition for the Oracle solution and aims at describing the current state, to-be state as well as a potential project scope and timeline. The parts will be described as a physical implementable solution.

--\>

# Business Context

(WAD Template) is using OBIA version 11g which they want to migrate to OCI and leverage where possible the advantages of a cloud native solution. It is important to know which version of OBIA (WAD Template) is using. The recommended version to deploy on OCI is OBIA 11.1.1.10.3 PS3. This version is certified with OAC and ADW. It is possible to use OBIA version 11.1.1.0.2 on OCI but only DBCS and OAC can be used as cloud products. Other components are on- premise applications. It would be best if the source application is running on OCI as well, but that is not a fixed requirement. It is important to check which version customer is using and what the latest certification matrix is and what current support guidelines are. Version 11.1.1.10.3 is still in support. An upgrade to the 11.1.1.10.3 version from 11.1.1.10.2 or earlier will be mainly a technology upgrade from 11g to 12c but due to the change of technology and the level of customisations in ODI this will require more or less effort.

Success criteria:

| Description                                                                | Success criteria                                                                                                               | Owner | Notes |
|----------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|-------|-------|
| Migration of Data Warehouse Database to Autonomous Data Warehouse Database | Successful migration of the database                                                                                           |       |       |
| Migration of OBIEE to OAC                                                  | Successful migration of the OBIEE content to OAC, connected to ADW and analytics tested to be working                          |       |       |
| Migration of ODI to ODI on OCI                                             | Successful migration of on premise ODI content to ODI on OCI and a execution of the data loads rseuling in data in the new ADW |       |       |

## Workload Business Value

(WAD Template) is running a recent installation of OBIA 11g. with support and security risks. Modernising this Data Warehouse and Analytics solution will help (WAD Template) to be ready for the future again. Migrating to OCI and using ADW, OAC and ODI creates an as much as possible cloud native solution and leverages the existing OBIEE, ODI and Database knowledge in a modern setting while preserving previously made investments in Data Warehouse, extractions and analytics.

After the migration the OBIA installation will continue as a custom data warehouse and analytics solution based on the cloud native successors of the migrated stack.

# Workload Requirements and Architecture

## Overview

Oracle Business Intelligence Applications version 11g with OBIEE + Database + ODI + OBIA Configuration manager will be migrated to a new modern cloud based stack of OAC + ADW + ODI Marketplace + OBIA Configuration manager and parameter repository.

Main components will be migrated to OCI. The Source Database can stay in its current place and and can be migrated to OCI over time, or replicated from on-premise to OCI.

## Current State

### Current State Architecture

The logical architecture of the current OBIA installation picture:

![Current State Architecture](images/current-state-logical-architecture.png)

-   **Data Sources** consist of the Oracle eBS (Other source systems like JD Edwards, Siebel, Peoplesoft or Fusion Apps maybe in place).
-   **Oracle BI Applications** (OBIA) is a prebuilt BI solution with pre defined connector for eBS. OBIA provides prebuilt content for ODI, OBIEE and Database schema making use of the technology components in the architecture
-   **Oracle Data Integrator (ODI)** extracts information from the source databases and loads the data into the Data Warehouse model in Oracle Database. ODI's current version is 11g.
-   **Data Warehouse** is Oracle Database with data model optimised for analytical purposes. It contains the prebuilt OBIA data model.
-   **Oracle Business Intelligence Enterprise Edition (OBIEE)** is the reporting and analytical tool. It contains both the prebuilt OBIA semantic model and presentation catalog complemented with custom content. OBIEE's current version is 11g or 12c.

### OBIA Modules

The following OBIA modules are installed and used:

-   Oracle Financial Analytics
-   Oracle Procurement and Spend Analytics
-   Oracle SCM Analytics
-   Oracle Project Analytics
-   Oracle HR Analytics

### Current Sizing

|     |     |     |     |
|-----|-----|-----|-----|
|     |     |     |     |
|     |     |     |     |
|     |     |     |     |
|     |     |     |     |
|     |     |     |     |

## Non Functional Requirements

| 

### Regulations and Compliances

Run the OBIA installation in a supported stack of components

### Resilience and Recovery

-   Databases must be periodically backed up.
-   OAC models, reports, and dashboards must be periodically backed up.

### Security

OBIA Application roles and other security embedded in OBIEE must be available in OAC.

## Logical Future State Architecture

![Logical Architecture](images/target-state-logical-architecture.png)

The architecture focuses on the following logical divisions:

In general, the architecture includes the following logical divisions. This reference architecture focuses on the data refinery and data persistence architecture components:

-   Data refinery

    Ingests and refines the data for use in each of the data layers in the architecture. The shape is intended to illustrate the differences in processing costs for storing and refining data at each level and for moving data between them. The narrower the shape, the less refinery effort; as the shape gets wider, the refinery effort also increases.

-   Data persistence platform (curated information layer)

    Facilitates access and navigation of the data to show the current and historical business view. It contains both raw data as well as granular and aggregated curated data. For relational technologies, data may be logical or physically structured in simple relational, longitudinal, dimensional or OLAP forms. For non-relational data, this layer contains one or more pools of data, either output from an analytical process or data optimised for a specific analytical task.

    Oracle Autonomous Data Warehouse is a self-driving, self-securing, self-repairing database service that is optimised for data warehousing workloads. You do not need to configure or manage any hardware, or install any software. Oracle Cloud Infrastructure handles creating the database, as well as backing up, patching, upgrading, and tuning the database.

-   Access and interpretation

    Abstracts the logical business view of the data for the consumers. This abstraction facilitates agile approaches to development, migration to the target architecture, and the provision of a single reporting layer from multiple federated sources. The narrower the shape, the less access and interpretation effort; as the shape gets wider, the access and interpretation effort also increases.

## Security

The proposed solution consists of OAC in OCI which is fully managed by Oracle. The authentication and authorisation of users is done by Oracle IAM Identity Domains. Protecting the communication between the on-premises and cloud services over the Internet is achieved by leveraging a VPN IP-Sec or through a dedicated Fastconnect connection.

OAC and ADW instances are placed into private subnets which can't be accessed over the Internet. The users can access OAC via the corporate network, the defined connection will be leveraged for that.

## Identity and Access Management

To facilitate the identity and access management the solution will make use of the standard Oracle OCI Identity and Access Management (IAM) with the IDCS Foundation integration. IDCS will be used to create the users and to configure access and roles for OAC. When going forward Identity and Access management can be setup to use an Active Directory or Identity Provider.

OAC will require a separate Identity Domain.

Special attention will be needed if eBS is used as source environment and security integration making use of ICX Session Cookies is in use in OBIEE. In that case the architecture may have to be changed or during the migration some areas in OAC have to be altered like Init-Blocks, Data Security settings..

## Resilience & Recovery Requirements

**ADW Backups** By default the Automatic Backup feature for the Autonomous Data Warehouse is enabled. The service creates the following on an on-going basis: One weekly level 0 backup, generally created on a specified weekend day. A level 0 backup is the equivalent of a full backup. A daily level 1 backups, which are incremental backups created on each day for the six days following the level 0 backup day and an ongoing archived redo log backups (with a minimum frequency of every 60 minutes). The automatic backup process used to create level 0 and level 1 backups can run at any time within the daily backup window (between midnight and 6:00 AM). Automatic incremental backups (level 0 and level 1) are retained in Object Storage for 30 days by default. Level 0 and level 1 backups are stored in Object Storage and have an assigned OCID.

**Autonomous Dataguard** In addition to the automatic backup and manual backups that can be created from the Autonomous Data Warehouse database it is possible to enable Autonomous Data Guard. When you enable Autonomous Data Guard the system creates a standby database that is continuously updated with the changes from the primary database. You can enable Autonomous Data Guard with a standby in the current region, a local standby, or with a standby in a different region, a cross-region standby. You can also enable Autonomous Data Guard with both a local standby and a cross-region standby.

**OAC Snapshots** will be used to perform full and partial backups of the OAC content. The data can be either restored on the same or a different OAC instance. OAC automatically takes a snapshot when changes are made to the data model. Those automatically created snapshots will be used by Oracle for recovery. It keeps up to 5 most recent snapshots taken in 1-hour intervals at most, if you need to revert to an earlier model version. Up to 40 snapshots can be stored. For manual recovery, manual snapshots have to be created.

Please check this [link](https://docs.oracle.com/en/cloud/paas/analytics-cloud/acabi/snapshots.html#GUID-FAE709DE-3370-457C-9015-2E088ACA6181) for more details about OAC Snapshots.

## Deployment Architecture

![Deployment Architecture](images/deployment-architecture.png)

## Compartment Structure

![Compartment structure](images/compartments-uat-dev.png)

### Hub and Spoke

For this deployment architecture a Hub and Spoke topology is designed. A hub-and-spoke network, often called a star network, has a central component that's connected to multiple networks around it.

The dynamic routing gateway (DRG) is a virtual router that provides a path for private network traffic between a virtual cloud networks (VCN) inside and outside the region, such as a VCN in another Oracle Cloud Infrastructure region, an on-premises network, or a network from another cloud provider.

The DRG connects to multiple VCNs, adding flexibility to how you design your cloud network.

The hub VCN has an internet gateway for network traffic to and from the public internet. It also has a dynamic routing gateway (DRG) to enable private connectivity with your on-premises network, which you can implement by using Oracle Cloud Infrastructure FastConnect, or Site-to-Site VPN, or both.

You can use a OCI Bastion service to provide secure access to your resources. This architecture uses Bastion Service.

### VCN and Subnets

For security reasons the the Data Warehouse and Analytics components are positioned in a separate VCN. Spoke VCNs are not accessible from the internet. All components are placed in private subnets. The subnets where OAC, ADW and the Linux developer instance are in can be configured to be accessible from customers network or accessed through the Bastion Service in the Hub VCN. VCN's require to have CIDR ranges that are not overlapping with other VCN's and are also not overlapping with IP ranges used in (WAD Template) network.

### Network Firewall

Optionally a managed Network Firewall can be leveraged to increase security posture of the workload.

OCI Network Firewall is a next-generation managed network firewall and intrusion detection and prevention service for VCNs, powered by Palo Alto Networks®. The Network Firewall service offers simple setup and deployment and gives visibility into traffic entering the cloud environment (North-south network traffic) as well traffic between subnets (East-west network traffic).

Use network firewall and its advanced features together with other Oracle Cloud Infrastructure security services to create a layered network security solution.

A network firewall is a highly available and scalable instance that you create in the subnet of your choice. The firewall applies business logic to traffic that is specified in an attached firewall policy. Routing in the VCN is used to direct network traffic to and from the firewall.

![Network Firewall deployment example](images/network-firewall-drg.png)

Above a simple example is presented where a Network Firewall is deployed in a DMZ subnet and for which all incoming traffic via the DRG as well as all the outgoing traffic from the private subnet is routed to the Network Firewall so that policies are enforced to secure traffic.

#### Bill of materials

| Environment | Description                 | Metric            | Size | Monthly Cost | Annual Cost | Hours p/m |
|-------------|-----------------------------|-------------------|------|--------------|-------------|-----------|
| Prod        | Network Firewall (optional) | Instance per Hour | 1    |              |             | 744       |

| Part Number | Component                                               | Unit of Measure   | Units |
|:------------|:--------------------------------------------------------|:------------------|------:|
| B95403      | Oracle Cloud Infrastructure - Network Firewall Instance | Instance per Hour |   744 |

Further details can be found [here](https://docs.oracle.com/en-us/iaas/Content/network-firewall/overview.htm)

## OCI Cloud Landing Zone Architecture

|      \|

The design considerations for an OCI Cloud Landing Zone have to do with OCI and industry architecture best practices, along with customer specific architecture requirements that reflect the Cloud Strategy (hybrid, multi-cloud, etc). An OCI Cloud Landing zone involves a variety of fundamental aspects that have a broad level of sophistication. A good summary of a Cloud Landing Zone has been published by [Cap Gemini](https://www.capgemini.com/2019/06/cloud-landing-zone-the-best-practices-for-every-cloud/).

High level Oracle OCI Landing zone architecture with some example content. Details specifically for this OAC and ADW workload is specified in other parts of this document.

![OCI CLoud Landing zone architecture](images/oci-cis-landingzone.jpg)

### Resource Naming Convention

Oracle recommends the following Resource Naming Convention:

-   The name segments are separated by “-“
-   Within a name segment avoid using `<space>`{=html} and “.”
-   Where possible intuitive/standard abbreviations should be considered (e.g. “shared“ compared to "shared.cloud.team”)
-   When referring to the compartment full path, use “:” as separator, e.g. cmp-shared:cmp-security

Some examples of naming are given below:

-   cmp-shared
-   cmp-\<workload\>
-   cmp-networking

The patterns used are these:

-   \<resource-type\>-\<environment\>-\<location\>-\<purpose\>
-   \<resource-type\>-\<environment\>-\<source-location\>-\<destination-location\>-\<purpose\>
-   \<resource-type\>-\<entity/sub-entity\>-\<environment\>-\<function/department\>-\<project\>-\<custom\>
-   \<resource-type\>-\<environment\>-\<location\>-\<purpose\>

Abbreviation per resource type are listed below. This list may not be complete.

| Resource type                      | Abbreviation       | Example                                                     |
|------------------------------------|--------------------|-------------------------------------------------------------|
| Bastion Service                    | bst                | bst-\<location\>-\<network\>                                |
| Block Volume                       | blk                | blk-\<location\>-\<project\>-\<purpose\>                    |
| Compartment                        | cmp                | cmp-shared, cmp-shared-security                             |
| Customer Premise Equipment         | cpe                | cpe-\<location\>-\<destination\>                            |
| DNS Endpoint Forwarder             | dnsepf             | dnsepf-\<location\>                                         |
| DNS Endpoint Listener              | dnsepl             | dnsepl-\<location\>                                         |
| Dynamic Group                      | dgp                | dpg-security-functions                                      |
| Dynamic Routing Gateway            | drg                | drg-prod-\<location\>                                       |
| Dynamic Routing Gateway Attachment | drgatt             | drgatt-prod-\<location\>-\<source_vcn\>-\<destination_vcn\> |
| Fast Connect                       | fc# \<# := 1...n\> | fc0-\<location\>-\<destination\>                            |
| File Storage                       | fss                | fss-prod-\<location\>-\<project\>                           |
| Internet Gateway                   | igw                | igw-dev-\<location\>-\<project\>                            |
| Jump Server                        | js                 | js-\<location\>-xxxxx                                       |
| Load Balancer                      | lb                 | lb-prod-\<location\>-\<project\>                            |
| Local Peering Gateway              | lpg                | lpg-prod-\<source_vcn\>-\<destination_vcn\>                 |
| NAT Gateway                        | nat                | nat-prod-\<location\>-\<project\>                           |
| Network Security Group             | nsg                | nsg-prod-\<location\>-waf                                   |
| Managed key                        | key                | key-prod-\<location\>-\<project\>-database01                |
| OCI Function Application           | fn                 | fn-security-logs                                            |
| Object Storage Bucket              | bkt                | bkt-audit-logs                                              |
| Policy                             | pcy                | pcy-services, pcy-tc-security-administration                |
| Region Code, Location              | xxx                | fra, ams, zch \# three letter region code                   |
| Routing Table                      | rt                 | rt-prod-\<location\>-network                                |
| Secret                             | sec                | sec-prod-wls-admin                                          |
| Security List                      | sl                 | sl-\<location\>                                             |
| Service Connector Hub              | sch                | sch-\<location\>                                            |
| Service Gateway                    | sgw                | sgw-\<location\>                                            |
| Subnet                             | sn                 | sn-\<location\>                                             |
| Tenancy                            | tc                 | tc                                                          |
| Vault                              | vlt                | vlt-\<location\>                                            |
| Virtual Cloud Network              | vcn                | vcn-\<location\>                                            |
| Virtual Machine                    | vm                 | vm-xxxx                                                     |
|                                    |                    |                                                             |

**Note:** Resource names are limited to 100 characters.

#### Group Names

OCI Group Names should follow the naming scheme of the Enterprise Identity Management system for Groups or Roles.

Examples for global groups are:

-   \<prefix\>-\<purpose\>-admins
-   \<prefix\>-\<purpose\>-users

For departmental groups:

-   \<prefix\>-\<compartment\>-\<purpose\>-admins
-   \<prefix\>-\<compartment\>-\<purpose\>-users

The value for \<prefix\> or the full names **must be agreed** with (WAD Template).

### Security and Identity Management

This chapter covers the Security and Identity Management definitions and resources which will be implemented for (WAD Template).

#### Universal Security and Identity and Access Management Principles

-   Groups will be configured at the tenancy level and access will be governed by policies configured in OCI.
-   Any new project deployment in OCI will start with the creation of a new compartment. Compartments follow a hierarchy, and the compartment structure will be decided as per the application requirements.
-   It is also proposed to keep any shared resources, such as Object Storage, Networks etc. in a shared services compartment. This will allow the various resources in different compartments to access and use the resources deployed in the shared services compartment and user access can be controlled by policies related to specific resource types and user roles.
-   Policies will be configured in OCI to maintain the level of access / control that should exist between resources in different compartments. These will also control user access to the various resources deployed in the tenancy.
-   The tenancy will include a pre-provisioned Identity Cloud Service (IDCS) instance (the primary IDCS instance) or, where applicable, the Default Identity Domain. Both provide access management across all Oracle cloud services for IaaS, PaaS and SaaS cloud offerings.
-   The primary IDCS or the Default Identity Domain will be used as the access management system for all users administrating (OCI Administrators) the OCI tenant.

#### Authentication and Authorization for OCI

Provisioning of respective OCI administration users will be handled by the customer.

##### User Management

Only OCI Administrators are granted access to the OCI Infrastructure. As a good practice, these users are managed within the pre-provisioned and pre-integrated Oracle Identity Cloud Service (primary IDCS) or, where applicable, the OCI Default Identity Domain, of OCI tenancy. These users are members of groups. IDCS Groups can be mapped to OCI groups while Identity Domains groups do not require any mapping. Each mapped group membership will be considered during login.

**Local Users**

The usage of OCI Local Users is not recommended for the majority of users and is restricted to a few users only. These users include the initial OCI Administrator created during the tenancy setup, and additional emergency administrators.

**Local Users are considered as Emergency Administrators and should not be used for daily administration activities!**

**No additional users are to be, nor should be, configured as local users.**

**The customer is responsible to manage and maintain local users for emergency use cases.**

**Federated Users**

Unlike Local Users, Federated Users are managed in the Federated or Enterprise User Management system. In the OCI User list Federated Users may be distinguished by a prefix which consists of the name of the federated service in lower case, a '/' character followed by the user name of the federated user, for example:

`oracleidentityservicecloud/user@example.com`

In order to provide the same attributes (OCI API Keys, Auth Tokens, Customer Secret Keys, OAuth 2.0 Client Credentials, and SMTP Credentials) for Local and *Federated Users* federation with third-party Identity Providers should only be done in the pre-configured primary IDCS or the Default Identity Domain where applicable.

All users have the same OCI-specific attributes (OCI API Keys, Auth Tokens, Customer Secret Keys, OAuth 2.0 Client Credentials, and SMTP Credentials).

OCI Administration user should only be configured in the pre-configured primary IDCS or the Default Identity Domain where applicable.

**Note:** Any federated user can be a member of 100 groups only. The OCI Console limits the number of groups in a SAML assertion to 100 groups. User Management in the Enterprise Identity Management system will be handled by the customer.

**Authorization**

In general, policies hold permissions granted to groups. Policy and Group naming follows the Resource Naming Conventions.

**Tenant Level Authorization**

The policies and groups defined at the tenant level will provide access to administrators and authorised users, to manage or view resources across the entire tenancy. Tenant level authorization will be granted to tenant administrators only.

These policies follow the recommendations of the [CIS Oracle Cloud Infrastructure Foundations Benchmark v1.1.0, recommendations 1.1, 1.2, 1.3](https://www.cisecurity.org/cis-benchmarks).

**Service Policy**

A Service Policy is used to enable services at the tenancy level. It is not assigned to any group.

**Shared Compartment Authorization**

Compartment level authorization for the cmp-shared compartment structure uses the following specific policies and groups.

Apart from tenant level authorization, authorization for the cmp-shared compartment provides specific policies and groups. In general, policies will be designed that lower-level compartments are not able to modify resources of higher-level compartments.

Policies for the cmp-shared compartment follow the recommendations of the [CIS Oracle Cloud Infrastructure Foundations Benchmark v1.1.0, recommendations 1.1, 1.2, 1.3](https://www.cisecurity.org/cis-benchmarks).

**Compartment Level Authorization**

Apart from tenant level authorization, compartment level authorization provides compartment structure specific policies and groups. In general, policies will be designed that lower-level compartments are not able to modify resources of higher-level compartments.

**Authentication and Authorization for Applications and Databases**

Application (including Compute Instances) and Database User management is completely separate of and done outside of the primary IDCS or Default Identity Domain. The management of these users is the sole responsibility of the customer using the application, compute instance and database specific authorization.

#### Security Posture Management

**Oracle Cloud Guard**

Oracle Cloud Guard Service will be enabled using the pcy-service policy and with the following default configuration. Customisation of the Detector and Responder Recipes will result in clones of the default (Oracle Managed) recipes.

Cloud Guard default configuration provides a number of good settings. It is expected that these settings may not match with the customer's requirements.

**Targets**

In accordance with the [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.15](https://www.cisecurity.org/cis-benchmarks), Cloud Guard will be enabled in the root compartment.

**Detectors**

The Oracle Default Configuration Detector Recipes and Oracle Default Activity Detector Recipes are implemented. To better meet the requirements, the default detectors must be cloned and configured by the customer.

**Responder Rules**

The default Cloud Guard Responders will be implemented. To better meet the requirements, the default detectors must be cloned and configured by the customer.

**Vulnerability Scanning Service**

In accordance with the [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, OCI Vulnerability Scanning](https://www.cisecurity.org/cis-benchmarks) will be enabled using the pcy-service policy.

Compute instances which should be scanned *must* implement the *Oracle Cloud Agent* and enable the *Vulnerability Scanning plugin*.

**OCI OS Management Service**

Required policy statements for OCI OS Management Service are included in the pcy-service policy.

By default, the *OS Management Service Agent plugin* of the *Oracle Cloud Agent* is enabled and running on current Oracle Linux 6 and Oracle Linux 7 platform images.

#### Monitoring, Auditing and Logging

In accordance with the [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3 Logging and Monitoring](https://www.cisecurity.org/cis-benchmarks) the following configurations will be made:

-   OCI Audit log retention period set to 365 days. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.1](https://www.cisecurity.org/cis-benchmarks)
-   At least one notification topic and subscription to receive monitoring alerts. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.3](https://www.cisecurity.org/cis-benchmarks)
-   Notification for Identity Provider changes. [See CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.4](https://www.cisecurity.org/cis-benchmarks)
-   Notification for IdP group mapping changes. [See CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.5](https://www.cisecurity.org/cis-benchmarks)
-   Notification for IAM policy changes. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.6](https://www.cisecurity.org/cis-benchmarks)
-   Notification for IAM group changes. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.7](https://www.cisecurity.org/cis-benchmarks)
-   Notification for user changes. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.8](https://www.cisecurity.org/cis-benchmarks)
-   Notification for VCN changes. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.9](https://www.cisecurity.org/cis-benchmarks)
-   Notification for changes to route tables. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.10](https://www.cisecurity.org/cis-benchmarks)
-   Notification for security list changes. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.11](https://www.cisecurity.org/cis-benchmarks)
-   Notification for network security group changes. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.12](https://www.cisecurity.org/cis-benchmhas%20a%20staarks)
-   Notification for changes to network gateways. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.13](https://www.cisecurity.org/cis-benchmarks)
-   VCN flow logging for all subnets. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.14](https://www.cisecurity.org/cis-benchmarks)
-   Write level logging for all Object Storage Buckets. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.17](https://www.cisecurity.org/cis-benchmarks)
-   Notification for Cloud Guard detected problems.
-   Notification for Cloud Guard remedied problems.

For IDCS or OCI Identity Domain Auditing events, the respective Auditing API can be used to retrieve all required information.

#### Data Encryption

All data will be encrypted at rest and in transit. Encryption keys can be managed by Oracle or the customer and will be implemented for identified resources.

##### Key Management

All keys for **OCI Block Volume**, **OCI Container Engine for Kubernetes**, **OCI Database**, **OCI File Storage**, **OCI Object Storage**, and **OCI Streaming** are centrally managed in a shared or a private virtual vault will be implemented and placed in the compartment cmp-security.

**Object Storage Security**

For Object Storage security the following guidelines are considered.

-   **Access to Buckets** -- Assign least privileged access for IAM users and groups to resource types in the object-family (Object Storage Buckets & Object)
-   **Encryption at rest** -- All data in the Object Storage is encrypted at rest using AES-256 and is on by default. This cannot be turned off and objects are encrypted with a master encryption key.

**Data Residency**

It is expected that data will be held in the respective region and additional steps will be taken when exporting the data to other regions to comply with the applicable laws and regulations. This should be review for every project onboard into the tenancy.

#### Operational Security

**Security Zones**

Whenever possible OCI Security Zones will be used to implement a security compartment for Compute instances or Database resources. For more information on Security Zones refer to the in the *Oracle Cloud Infrastructure User Guide* chapter on [Security Zones](https://docs.oracle.com/en-us/iaas/security-zone/using/security-zones.htm).

**Remote Access to Compute Instances or Private Database Endpoints**

To allow remote access to Compute Instances or Private Database Endpoints, the OCI Bastion will be implemented for defined compartments.

To be able to use OCI services to for OS management, Vulnerability Scanning, Bastion Service, etc. it is highly recommended to implement the Oracle Cloud Agent as documented in the *Oracle Cloud Infrastructure User Guide* chapter [Managing Plugins with Oracle Cloud Agent](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/manage-plugins.htm).

#### Network Time Protocol Configuration for Compute Instance

Synchronised clocks are a necessity for securely operating environments. OCI provides a Network Time Protocol (NTP) server using the OCI global IP number 169.254.169.254. All compute instances should be configured to use this NTP service.

#### Regulations and Compliance

The customer is responsible for setting the access rules to services and environments that require stakeholders’ integration to the tenancy to comply with all applicable regulations. Oracle will support in accomplishing this task.

## Sizing and Bill of Materials

Example for a small workload, but to be adjusted for customers situation

| Environment | Component                                             | Quantity | Metric    |
|-------------|-------------------------------------------------------|----------|-----------|
| Dev         | OAC Enterprise Edition                                | 2        | OCPU      |
| Dev         | ADW-S                                                 | 2        | OCPU      |
| Dev         | Oracle Database - ODI repository and RCU installation | 1        | OCPU      |
| Dev         | Object Storage                                        | 2        | Terrabyte |
| Dev         | Compute Cloud - Oracle Free Linux Cloud Develop       | 1        | OCPU      |
| Dev         | Compute Cloud for OBIA and ODI                        | 2        | OCPU      |
| Dev         | Exadata Storage                                       | 5        | Terrabyte |
| Dev         | Block Volume                                          | 500      | Gb        |

Next section is included in this document as an example covering the activities required for such migration and needs to be agreed with the migration partner (Lift, Oracle Consulting, 3rd party partner) to reflect the activities and effort required.

# Migration Project and Architecture

## Solution Scope

-   OBIEE 11.1.1.9 will be migrated to OAC (in a private subnet). All data will be migrated, but testing will be done on a limited number of reports.
-   Oracle Database will be migrated to ADW
-   ODI will be migrated to ODI on Compute
-   The BIA administration Console will be installed on Compute Cloud

### Disclaimer

As part of the migration project, any scope needs to be agreed upon by both the customer and Oracle. A scope can change but must be confirmed again by both parties. Oracle can reject scope changes for any reason and may only design and implement a previously agreed scope. A change of scope can change any agreed times or deadlines and needs to be technically feasible.

All items not explicitly stated to be within the scope of the Lift project will be considered out of scope. Oracle recommends the use of professional services to implement extensions or customisations beyond the original scope, as well as to operate the solution, with an Oracle-certified partner.

### Overview

Various approaches can be taken to migrate an OBIA instance from on-premise to OCI. It also depends on the version that currently is being used and if an upgrade still needs to happen.

The approaches can vary from replicating exactly is it is in on-premise with similar tools/versions and patch levels and from there create a plan to upgrade to the latest versions if needed and migrate from on-premise tools to cloud native tools like OAC and ADW. To an approach of installing the latest version with cloud native components on OCI and migrate/upgrade when moving from on-premise to OCI at once.

Migrating to OCI by moving VM's from on-premise to OCI is not supported by Oracle Support. A fresh installation must be done and artefacts of OBIEE, ODI, OBIA etc can be migrated.

### Success Criteria

-   

## Workplan

### Deliverables

A Workload Architecture Document (WAD) which includes:

-   Solution Definition

### Included Activities

#### Infrastructure and Landingzone

-   OCI Infrastructure and landingzone setup
    -   Compartments
    -   VCN
    -   Subnets
    -   IAM, users, groups, identity domains, SL, RT, NSG
    -   Connections with customer Network
        -   VPN or Fastconnect IP Sec connection
        -   Source system
    -   Connection with Informatica control plane
-   Provisioning of Services
    -   ADW
    -   Compute for OBIA and ODI installation
    -   OAC +PAC
    -   IAM and Users
    -   DBaas for OBIA RCU and ODI repository
    -   Compute for DB Migration (Developer cloud service)
    -   Object Store bucket

#### Migration of On-premise DB to Oracle Autonomous Database

-   Pre-migration tasks in source database:
    -   Collect and analysis previous information related to the source database (Review space used by schemas, registry state, invalid objects, execution and analysis CPAT tool).
    -   Support to export and copy Datapump files to OCI Object Storage which will be done by customer.
-   Configure Working Migration Development (Developer cloud service, oracle client, OCI CLI, etc.)
-   Database Migration using Oracle Datapump. Sample parameter might be used on certain tables if data volume is too big in size.
-   Postmigration tasks:
    -   Fix warning detected in the migration to ADW
    -   Fix privileges not imported with Datapump
    -   Support customer with validations after the database migration

#### OBIEE to Oracle Analytics Cloud

-   Establishing the connectivity between ADW and OAC (Private Access Channel will be used)
-   RPD is cleansed from Errors and Warnings during migration by customer with help from Oracle team
-   Configuration of IAM Roles to Application Roles in OAC (limit to 5 users and 10 groups to Application Role mapping)
-   Migration of the existing reports and dashboards
-   Testing for a limited number of reports (up to 10 reports)

#### ODI on-premise to ODI on OCI

-   Smart export of ODI Repository (customer activity)
-   Smart import of ODI Repository
-   Change or create connections to new source and target DB's
-   Unit test for a limited number of mappings

#### OBIA Configuration manager

-   Export Configuration manager from on-premise environment
-   Import Configuration manager into environment in OCI

### Assumptions and exclusions

#### Infrastructure and Landingzone

-   Predefined Reference Architecture can be used
-   No implementation of AD and SSO integration
-   VPN IP-Sec tunnel
-   Creation of maximum 5 users and 5 groups
-   creation of 2 identity domains

#### On premise DB to Oracle Autonomous Database

-   Oracle Database
-   Database minimum version of 10.2.0.5
-   Size of DB maximum 2 TB
-   CPAT tool outcome reveals no blocking errors
-   One time migration of database content. Later adjustments and new data will not be taken in account.

#### OBIEE to Oracle Analytics Cloud

-   OBIEE is on minimum version 11.1.1.9
-   RPD is in a consistent state
-   Usage tracking will not be re-configured
-   Customer will send us the RPD and the export of the migration tool from OBIEE
-   Agents and schedulers will not be tested
-   SMTP server will not be configured
-   BI Publisher reports will not be tested
-   No JS and/or CSS customisation of the reports
-   No special characters (including spaces) are used in the names of the reports and entities in the catalog
-   Unsupported functionality such as "Act As" is not used
-   Reporting performance will remain as found (no performance improvement activities will be carried out)
-   No setup/configuration of write-back functionality
-   No security integration setup based on ICX-Session cookies. Data level security will not be tested and validated.

#### Additional supporting documentation

The migration to OAC will be done using a JAR file as suggested in Oracle's official documentation (https://docs.oracle.com/en/cloud/paas/analytics-cloud/acmgb/migrate-oracle-bi-enterprise-edition.html#GUID-AB5F5552-82F0-4664-822B-F99F1EF7917E). The customer will use the migration utility to export the content to a JAR file.

#### Security

For future reference related to data and object level security:

Configuration of groups and users will be done by following the documentation under (https://www.ateam-oracle.com/implementing-object-and-data-level-security-in-oracle-analytics-cloud-using-identity-cloud). To assign user responsibilities to OAC user sessions via initialisation blocks in **Oracle Analytics Client Tools** (https://www.oracle.com/middleware/technologies/oac-tools-downloads.html) is used. Session initialisation blocks will execute each time a user logs into OAC.

### Recommended Activities

This Lift workload is designed to assist Customer to rapidly start utilizing Oracle Cloud Infrastructure and allow them to explore the benefits of the solution to them for further rollout. Once the Lift team finishes the work, the customer can leverage the knowledge acquired from this project to create additional environments themselves or with the help of Oracle Consulting and/or a partner.

### Timeline

This high-level project timeline shows a representative timeline and is intended for planning purposes only.

| Step                                        | Description | Effort |
|---------------------------------------------|-------------|--------|
| Initiation, INfrastructure and Connectivity |             | 6.5    |
| Migration of DB and OBIEE to ADW and OAC    |             | 25     |
| Migration of Powercenter to IDMC            |             | xx     |
| Documentation, Security, QA and handover    |             | 4      |
| TPM and PPM                                 |             | 7      |
| DAC replacement design                      |             | xx     |
| Total                                       |             | 42.5   |

Section To Be Added and updated

### Implementation RACI

| 

\|\|

### Generic Assumptions

All work will be done remotely and within either local time or India standard time within normal office working hours. The following assumptions have been made about the project, which will impact delivery:

-   Disaster Recovery is not in scope
-   Tenancy is provisioned as new with availability of Identity and Access Management Identity Domains
-   Customer will have the export datapump prepared and he will copy datapump files to the Oracle Object Storage
-   For the pilot customer accepts to pass warnings and errors when loading the data in the database.

### Out of scope

The following components and activities are out of scope:

-   Provisioning and configuration of a second instance (only a NONPROD instance will be provisioned).
-   Any third party or Customer on-premises integration.
-   Third Party products, Backup tools, Firewall implementation, Security tools, monitoring tools implementation.
-   Load Testing, Performance benchmarking testing, Functional/code change & tuning of any component in the solution.
-   Any Vulnerability Assessment and Penetration Testing.
-   Trainings on deployed products and cloud services.
-   Any other activity not listed under “In Scope” section.
-   Migration Apex workspaces in case of use.

### Obligations

-   You will have purchased the appropriate Universal Credits for the services required for the project.
-   The Project team will have admin access to the customers tenancy for implementation.
-   You will ensure the appropriate product training has been obtained to maintain and support the implementation.
-   Your business team will be available for the Testing phase, which will be completed within the agreed testing window.
-   You will provide project management for the project and will manage any third party suppliers or vendors.
-   Complete the OCI Site to Site VPN Request Form as supplied by the Oracle Workload Architect.
-   Complete the OCI Fast Connect Request Form as supplied by the Oracle Workload Architect.
-   Test cases to be defined and provided by the customer
-   Customer to provide necessary encryption keys is required

### Risks

-   Solution for DAC

## Physical Future State Architecture
