---
doc:
  author: Wilbert Poeliejoe
  version: 0.6
  draft: true
  cover:
    title:
      - BI Applications migration to OCI
    subtitle:
      - to be added
  history:
    - version: "0.5"
      date: July 2022
      authors: Wilbert Poeliejoe
      comments: Inital Asset
    - version: "0.6"
      date: 20 February 2023
      authors: Wilbert Poeliejoe
      comments: Network Firewall content added    
  acronyms:
      ADW: Autonomous Data Warehouse
      CIDR: Classless Inter-Domain Routing
      DNS: Domain Name System
      DRG: Dynamic Routing Gateway
      ETL: Extract Transform Load
      IAM: Identity and Access Management
      IGW: Internet Gateway
      LFS: Liberty Financial Services
      NSG: Network Security Groups
      OAC: Oracle Analytics Cloud
      OCPU: Oracle Compute Unit
      OBIA: Oracle Business Intelligence Applications
      OBIEE: ORacle Business Intelligence Enterprise Edition
      ODI: Oracle Data Integrator
      OSN: Oracle Service Network
      PVO: Public View Object
      SGW: Service Gateway
      VCN: Virtual Cloud Network
      VNIC: Virtual Network Interface Card   
  customer:
       name: WAD Template
---

# Document Control

```{#history}
This is the document history
```

```{#acronyms}
common
```
\pagebreak

<!--
Begin Solution Definition
Start editing from here
-->

# Document Control
<!-- GUIDANCE -->
<!--
First Chapter of the document, describes meta data for the document. Such as versioning and team members.
 -->

## Team
<!-- GUIDANCE -->
<!--
A section describing the versions of this documents and it changes.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

<!-- EXAMPLE / TEMPLATE -->
Name           | eMail                     | Role                    | Company
:---           |:---                       |:---                     |:---
Wilbert Poeliejoe  | Wilbert.poeliejoe@oracle.com | Initial Author (to be removed for customer)| Oracle

## Document Purpose

<!-- GUIDANCE -->
<!--
Describe the purpose of this document and the Oracle specific terminology, specifically around 'Workload' and 'Lift'..

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

<!-- EXAMPLE / TEMPLATE -->
This document provides a high-level solution definition for the Oracle solution and aims at describing the current state, to-be state as well as a potential 'Oracle Lift' project scope and timeline. The Lift parts will be described as a physical implementable solution. The intended purpose is to provide all parties involved a clear and well-defined insight into the scope of work and intention of the project as it will be done as part of the Oracle Lift service.

The document may refer to a 'Workload', which summarizes the full technical solution for a customer (You) during a single engagement. The Workload is described in chapter [Workload Requirements and Architecture](#workload-requirements-and-architecture). In some cases Oracle offers a free implementation service called 'Oracle Lift', which has its own dedicated scope and is typically a subset of the initial Workload. The Lift project, architecture and implementation details are documented in chapter [Oracle Lift Project and Architecture](#oracle-lift-project-and-architecture) and in chapter [Oracle Lift Implementation](#oracle-lift-implementation).

# Business Context
<!-- GUIDANCE -->
<!--
Describe the customers business and background. What is the context of the customers industry and LOB. What are the business needs and goals which this Workload is an enabler for? How does this technical solution impact and support the customers business goals? Does this solution support a specific customer strategy, or maybe certain customer values? How does this solution help our customers to either generate more revenue or save costs.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
ACE   | R
-->

Customer is using OBIA version 7.9.6.4 which is in sustaining support and modernisation of it is an important step to take. Customer is having Oracle eBS as source environment. 

Success criteria:

| Description                                                  | Success criteria                                             | Owner | Notes |
| ------------------------------------------------------------ | ------------------------------------------------------------ | ----- | ----- |
| Migration of Data Warehouse Database to Autonomous Data Warehouse Database | Successful migration of the database                         |       |       |
| Migration of OBIEE to OAC                                    | Successful migration of the OBIEE content to OAC, connected to ADW and analytics tested to be working |       |       |
| Migration of Informatica Powercenter to Informatica IDMC     | Successful migration of Powercenter content to IDMC and a execution of the data loads rseuling in data in the new ADW |       |       |
| New Solution for DAC                                         | A replacement solution for DAC will be able to run the Informatica mappings in the right sequence and load data in the Data warehouse tables and store the parameters required for the data load |       |       |

## Workload Business Value

<!-- GUIDANCE -->
<!--
A clear statement of specific business value as part of the full workload scope. Try to keep it SMART: Specific, Measurable, Assignable, Realistic, and Time-Related - Agree the SMART business value with the customer. Keep it business focused, and speak the language of the LOB which benefits from this Workload: "Increase Customer Retention by 3% in the next year" or "Grow Customer Base with Executive Decision-Making from our Sales and Support Data". Avoid technical success criteria such as "Migrate App X to Oracle Cloud" or "Provision 5 Compute Instances". Avoid Oracle success criteria and language "Get Workload Consuming on OCI".

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
ACE   | R
-->

(${doc.customer.name}) is running an outdated and unsupported installation of OBIA with support and security risks. Modernising this Data Warehouse and Analytics solution will help (${doc.customer.name}) to be ready for the future again. Migrating to OCI and using ADW, OAC and Informatica IDMC creates a cloud native solution and leverage existing OBIEE, Informatica and Database knowledge in a modern setting while preserving previously made investments in Data Warehouse, extractions and analytics. 

After the migration the OBIA installation will continue as a custom data warehouse and analytics solution based on the cloud native successors of the migrated stack.  

# Workload Requirements and Architecture

## Overview
<!-- GUIDANCE -->
<!--
Describe the Workload: What applications and environments are part of this Workload, what are their names? Lift will be scoped later and is typically a subset of the Workload. For example a Workload could exists of two applications, but Lift would only include one environment of one application. This Workload chapter is about the whole Workload and Lift will be described late in chapter [Scope](#scope).

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

Oracle Business Intelligence Applications version 7.9.6.4 with OBIEE + Database + Informatica Powercenter + DAC will be migrated to a new modern cloud based stack of OAC + ADW + Informatica IDMC + a solution for scheduling and parameter repository.

Main components will be migrated to OCI. The Source Database can stay in its current place and the Informatica control plane will be hosted by Informatica. 

## Non Functional Requirements

<!-- GUIDANCE -->
<!--
Describe the high-level technical requirements for the Workload. Consider all sub-chapters, but decide and choose which Non Functional Requirements are actually necessary for your engagement. You might not need to capture all requirements for all sub-chapters.

This chapter is for describing customer specific requirements (needs), not to explain Oracle solutions or capabilities.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->|

### Regulations and Compliances

<!-- GUIDANCE -->
<!--
This section captures and specific regulatory of compliance requirements for the Workload. These may limit the types of technologies that can be used and may drive some architectural decisions.

If there are none, then please state None.

Mandatory Chapter
-->

Run the OBIA installation in a supported stack of components

### Environments
<!-- GUIDANCE -->
<!--
A diagram or list detailing all the required environments (e.g. development, text, live, production etc).
- list each environment included in the scope
- map each environment to bronze/silver/gold MAA

Mandatory Chapter
-->

Name         | Size of Prod  | Location  | Scope
:---       |:---    |:---    |:---
Pilot | 100% | Xxxxxxxx |Yes

### Resilience and Recovery
<!-- GUIDANCE -->
<!--
This section captures the resilience and recovery requirements for the Workload. Note that these may be different from the current system.

The Recovery Point Objective (RPO) and Recovery Time Objective (RTO) requirement of each environment should be captured in the environments section above, and wherever possible, these should be mapped to the standard Bronze, Silver and Gold levels of Oracle's MAA.

- What are RTO and RPO requirements of the Application?
- What are SLA's of the application?
- What are the backup requirements

Note that if needed, this section may also include an overview of the proposed backup and disaster recovery proposed architectures.

This chapter is mandatory, while there could be no requirements on HA/DR, please mention that in a short single sentence.

Mandatory Chapter
-->

For the Pilot no additional measures are put in place for resilience and recovery.  For OAC the regular functionality of creating snapshots can be used to backup the RPD and Presentation Catalog. For ADW the automatic Backup mechanism is sufficient for the Pilot.

Once the Pilot is concluded and decision is taken to move ahead with this solution, Availability and and Distaster/Recovery architecture can be put in place depending on (${doc.customer.name})s requirements and needs 

### Security
<!-- GUIDANCE -->
<!--
Capture the non functional requirements for security related topics. Security is a mandatory subsection which is to be reviewed by the x-workload security team. The requirements can be separated into:
- Identity and Access Management
- Data Security

Other security topics, such as network security, application security or other can be added if needed.

Mandatory Chapter
-->

## Logical Future State Architecture
<!-- GUIDANCE -->
<!--
The Workload Future State Architecture can be described in various forms. In the easiest case we  just describe a Logical Architecture, possibly with a System Context Diagram.

Use [System Context Diagram](https://online.visual-paradigm.com/knowledge/system-context-diagram/what-is-system-context-diagram/) to show integration for the Workload solution.

Provide a high-level logical Oracle solution for the complete Workload. Indicate Oracle products as abstract groups, and not as a physical detailed instances. Create an architecture diagram following the latest notation and describe the solution.

Notation: https://apex.oraclecorp.com/pls/apex/patterns/r/patternlibrary/view-pattern?p118_id=567&session=17457054591654
Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

![Logical Architecture](images/Logical-Architecture.jpg)



The architecture focuses on the following logical divisions:

In general, the architecture includes the following logical  divisions. This reference architecture focuses on the data refinery and  data persistence architecture components:

- Data refinery

  Ingests and refines the data for use in each of the data layers in the  architecture. The shape is intended to illustrate the differences in  processing costs for storing and refining data at each level and for  moving data between them. The narrower the shape, the less refinery  effort; as the shape gets wider, the refinery effort also increases.

- Data persistence platform (curated information layer)

  Facilitates access and navigation of the data to show the current and historical  business view. It contains both raw data as well as granular and  aggregated curated data. For relational technologies, data may be  logical or physically structured in simple relational, longitudinal,  dimensional or OLAP forms. For non-relational data, this layer contains  one or more pools of data, either output from an analytical process or  data optimised for a specific analytical task.

  Oracle Autonomous Data Warehouse is a self-driving, self-securing, self-repairing database service that  is optimised for data warehousing workloads. You do not need to  configure or manage any hardware, or install any software. Oracle Cloud                                Infrastructure handles creating the database, as well as backing up, patching, upgrading, and tuning the database.                        

- Access and interpretation

  Abstracts the logical business view of the data for the consumers. This  abstraction facilitates agile approaches to development, migration to  the target architecture, and the provision of a single reporting layer  from multiple federated sources. The narrower the shape, the less access and interpretation effort; as the shape gets wider, the access and  interpretation effort also increases.

## Security

The proposed solution consists of OAC in OCI which is fully managed by Oracle. The authentication and authorisation of users is done by Oracle IAM Identity Domains. Protecting the communication between the on-premises and cloud services over the Internet is achieved by leveraging a VPN IP-Sec connection.

OAC and ADW instances are placed into private subnets which can't be accessed over the Internet. The users can access OAC via the corporate network, the VPN IP-Sec connection will be leveraged for that.

The OCI Bastion Service will allow temporary access by the development team during the project. Only during the implementation phase the OCI Bastion Service will be used by the Oracle Implementation team to access the ADW and OAC instances. The Bastion Service allows the implementation team to access ADW and OAC via the internet with an SSH tunnel.

Once the Implementation team has finished their work the Bastion Service can be deactivated or removed.

## Identity and Access Management

To facilitate the identity and access management the solution will make use of the standard Oracle OCI Identity and Access Management (IAM) with the IDCS Foundation integration. IDCS will be used to create the users and to configure access and roles for OAC. When going forward Identity and Access management can be setup to use an Active Directory or Identity Provider. 

OAC will require a separate Identity Domain

## Resilience & Recovery Requirements

  **ADW Backups**  By default the Automatic Backup feature for the Autonomous Data Warehouse is enabled. The service creates the following on an on-going basis: One weekly level 0 backup, generally created on a specified weekend day. A level 0 backup is the equivalent of a full backup. A daily level 1 backups, which are incremental backups created on each day for the six days following the level 0 backup day and an ongoing archived redo log backups (with a minimum frequency of every 60 minutes). The automatic backup process used to create level 0 and level 1 backups can run at any time within the daily backup window (between midnight and 6:00 AM). Automatic incremental backups (level 0 and level 1) are retained in Object Storage for 30 days by default. Level 0 and level 1 backups are stored in Object Storage and have an assigned OCID.

  **Autonomous Dataguard** In addition to the automatic backup and manual backups that can be created from the Autonomous Data Warehouse database it is possible to enable Autonomous Data Guard. When you enable Autonomous Data Guard the system creates a standby database that is continuously updated with the changes from the primary database. You can enable Autonomous Data Guard with a standby in the current region, a local standby, or with a standby in a different region, a cross-region standby. You can also enable Autonomous Data Guard with both a local standby and a cross-region standby.  

  **OAC Snapshots** will be used to perform full and partial backups of the OAC content. The data can be either restored on the same or a different OAC instance. OAC automatically takes a snapshot when changes are made to the data model. Those automatically created snapshots will be used by Oracle for recovery. It keeps up to 5 most recent snapshots taken in 1-hour intervals at most, if you need to revert to an earlier model version. Up to 40 snapshots can be stored. For manual recovery, manual snapshots have to be created.

  Please check this [link](https://docs.oracle.com/en/cloud/paas/analytics-cloud/acabi/snapshots.html#GUID-FAE709DE-3370-457C-9015-2E088ACA6181) for more details about OAC Snapshots.

## Deployment Architecture

![Deployment Architecture](images/Deployment-Architecture.jpg)The white subnets are in scope for this architecture

### Hub and Spoke

For this deployment architecture a Hub and Spoke topology is designed. A hub-and-spoke network, often called a star network, has a central component that's connected to multiple networks around it. 

The dynamic routing gateway (DRG) is a virtual router that provides a path for private network traffic between a virtual cloud networks (VCN) inside and outside the region, such as a VCN in another Oracle Cloud Infrastructure region, an on-premises network, or a network from another cloud provider.

The DRG connects to multiple VCNs, adding flexibility to how you design your cloud network.

The hub VCN has an internet gateway for network traffic to and from the public internet. It also has a dynamic routing gateway (DRG) to  enable private connectivity with your on-premises network, which you can implement by using Oracle Cloud Infrastructure FastConnect, or Site-to-Site VPN, or both.

You can use a OCI Bastion service to provide secure access to your resources. This architecture  uses Bastion Service.

### VCN and Subnets

For security reasons the the Data Warehouse and Analytics components are positioned in a separate VCN. Spoke VCNs are not accessible from the internet. All components are placed in private subnets. The subnets where OAC, ADW and the Linux developer instance are in can be configured to be accessible from customers network or accessed through the Bastion Service in the Hub VCN. VCN's require to have CIDR ranges that are not overlapping with other VCN's and are also not overlapping with IP ranges used in (${doc.customer.name}) network.

### Network Firewall

Optionally a managed Network Firewall can be leveraged to increase security posture of the workload.

OCI Network Firewall is a next-generation managed network firewall and intrusion detection and prevention service for VCNs, powered by Palo Alto Networks®. The Network Firewall service offers simple setup and deployment and gives visibility into traffic entering the cloud environment (North-south network traffic) as well traffic between subnets (East-west network traffic).

Use network firewall and its advanced features together with other Oracle Cloud Infrastructure security services to create a layered network security solution.

A network firewall is a highly available and scalable instance that you create in the subnet of your choice. The firewall applies business logic to traffic that is specified in an attached firewall policy. Routing in the VCN is used to direct network traffic to and from the firewall.

![Network Firewall deployment example](images/network-firewall-drg.png)

Above a simple example is presented where a Network Firewall is deployed in a DMZ subnet and for which all incoming traffic via the DRG as well as all the outgoing traffic from the private subnet is routed to the Network Firewall so that policies are enforced to secure traffic. 

#### Bill of materials

Environment | Description | Metric | Size | Monthly Cost | Annual Cost| Hours p/m
----------- | ----------- |----------- |----------- |----------- |----------- |-----------
Prod | Network Firewall (optional) | Instance per Hour | 1 |  |  | 744


| Part Number | Component                                                                                     | Unit of Measure  | Units    |
| :---------- | :-------------------------------------------------------------------------------------------- | :-------         | ----:    |
| B95403      | Oracle Cloud Infrastructure - Network Firewall Instance                                    | Instance per Hour              | 744    |

Further details can be found [here](https://docs.oracle.com/en-us/iaas/Content/network-firewall/overview.htm)

### Informatica Secure Agent

The Informatica Secure Agent requires a connection with the Informatica Control plane. This connection is established with a Network address translation (NAT) gateway. A NAT gateway enables private resources in a VCN to access hosts on the  internet, without exposing those resources to incoming internet  connections.

## OCI Cloud Landing Zone Architecture

<!-- GUIDANCE -->
<!--

Mandatory Chapter

| Role  | RACI |
| ----- | ---- |
| WLA   | R/A  |
| Impl. | None |
| PPM   | None |
| -->   |      |

The design considerations for an OCI Cloud Landing Zone have to do with OCI and industry architecture best practices, along with customer specific architecture requirements that reflect the Cloud Strategy (hybrid, multi-cloud, etc). An OCI Cloud Landing zone involves a variety of fundamental aspects that have a broad level of sophistication. A good summary of a Cloud Landing Zone has been published by [Cap Gemini](https://www.capgemini.com/2019/06/cloud-landing-zone-the-best-practices-for-every-cloud/).

High level Oracle OCI Landing zone architecture with some example content. Details specifically for this OAC and ADW workload is specified in other parts of this document.

![OCI CLoud Landing zone architecture](images/oci-cis-landingzone.jpg)

### Resource Naming Convention

<!-- GUIDANCE -->
<!--
If the customer provides a resource naming convention use it. They should have it already for their on-premises compute resources.
-->

Oracle recommends the following Resource Naming Convention:

- The name segments are separated by “-“
- Within a name segment avoid using <space> and “.”
- Where possible intuitive/standard abbreviations should be considered (e.g. “shared“ compared to "shared.cloud.team”)
- When referring to the compartment full path, use “:” as separator, e.g. cmp-shared:cmp-security

Some examples of naming are given below:

- cmp-shared
- cmp-\<workload>
- cmp-networking

The patterns used are these:

- \<resource-type>-\<environment>-\<location>-\<purpose>
- \<resource-type>-\<environment>-\<source-location>-\<destination-location>-\<purpose>
- \<resource-type>-\<entity/sub-entity>-\<environment>-\<function/department>-\<project>-\<custom>
- \<resource-type>-\<environment>-\<location>-\<purpose>

Abbreviation per resource type are listed below. This list may not be complete.

| Resource type                      | Abbreviation     | Example                                                  |
| ---------------------------------- | ---------------- | -------------------------------------------------------- |
| Bastion Service                    | bst              | bst-\<location>-\<network>                               |
| Block Volume                       | blk              | blk-\<location>-\<project>-\<purpose>                    |
| Compartment                        | cmp              | cmp-shared, cmp-shared-security                          |
| Customer Premise Equipment         | cpe              | cpe-\<location>-\<destination>                           |
| DNS Endpoint Forwarder             | dnsepf           | dnsepf-\<location>                                       |
| DNS Endpoint Listener              | dnsepl           | dnsepl-\<location>                                       |
| Dynamic Group                      | dgp              | dpg-security-functions                                   |
| Dynamic Routing Gateway            | drg              | drg-prod-\<location>                                     |
| Dynamic Routing Gateway Attachment | drgatt           | drgatt-prod-\<location>-\<source_vcn>-\<destination_vcn> |
| Fast Connect                       | fc# <# := 1...n> | fc0-\<location>-\<destination>                           |
| File Storage                       | fss              | fss-prod-\<location>-\<project>                          |
| Internet Gateway                   | igw              | igw-dev-\<location>-\<project>                           |
| Jump Server                        | js               | js-\<location>-xxxxx                                     |
| Load Balancer                      | lb               | lb-prod-\<location>-\<project>                           |
| Local Peering Gateway              | lpg              | lpg-prod-\<source_vcn>-\<destination_vcn>                |
| NAT Gateway                        | nat              | nat-prod-\<location>-\<project>                          |
| Network Security Group             | nsg              | nsg-prod-\<location>-waf                                 |
| Managed key                        | key              | key-prod-\<location>-\<project>-database01               |
| OCI Function Application           | fn               | fn-security-logs                                         |
| Object Storage Bucket              | bkt              | bkt-audit-logs                                           |
| Policy                             | pcy              | pcy-services, pcy-tc-security-administration             |
| Region Code, Location              | xxx              | fra, ams, zch # three letter region code                 |
| Routing Table                      | rt               | rt-prod-\<location>-network                              |
| Secret                             | sec              | sec-prod-wls-admin                                       |
| Security List                      | sl               | sl-\<location>                                           |
| Service Connector Hub              | sch              | sch-\<location>                                          |
| Service Gateway                    | sgw              | sgw-\<location>                                          |
| Subnet                             | sn               | sn-\<location>                                           |
| Tenancy                            | tc               | tc                                                       |
| Vault                              | vlt              | vlt-\<location>                                          |
| Virtual Cloud Network              | vcn              | vcn-\<location>                                          |
| Virtual Machine                    | vm               | vm-xxxx                                                  |
|                                    |                  |                                                          |

**Note:** Resource names are limited to 100 characters.

#### Group Names

OCI Group Names should follow the naming scheme of the Enterprise Identity Management system for Groups or Roles.

Examples for global groups are:

- \<prefix>-\<purpose>-admins
- \<prefix>-\<purpose>-users

For departmental groups:

- \<prefix>-\<compartment>-\<purpose>-admins
- \<prefix>-\<compartment>-\<purpose>-users

The value for \<prefix> or the full names **must be agreed** with customer.

### Security and Identity Management

This chapter covers the Security and Identity Management definitions and resources which will be implemented for customer.

#### Universal Security and Identity and Access Management Principles

- Groups will be configured at the tenancy level and access will be governed by policies configured in OCI.
- Any new project deployment in OCI will start with the creation of a new compartment. Compartments follow a hierarchy, and the compartment structure will be decided as per the application requirements.
- It is also proposed to keep any shared resources, such as Object Storage, Networks etc. in a shared services compartment. This will allow the various resources in different compartments to access and use the resources deployed in the shared services compartment and user access can be controlled by policies related to specific resource types and user roles.
- Policies will be configured in OCI to maintain the level of access / control that should exist between resources in different compartments. These will also control user access to the various resources deployed in the tenancy.
- The tenancy will include a pre-provisioned Identity Cloud Service (IDCS) instance (the primary IDCS instance) or, where applicable, the Default Identity Domain. Both provide access management across all Oracle cloud services for IaaS, PaaS and SaaS cloud offerings.
- The primary IDCS or the Default Identity Domain will be used as the access management system for all users administrating (OCI Administrators) the OCI tenant.

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

The policies and groups defined at the tenant level will provide access to administrators and authorized users, to manage or view resources across the entire tenancy. Tenant level authorization will be granted to tenant administrators only.

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

- OCI Audit log retention period set to 365 days. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.1](https://www.cisecurity.org/cis-benchmarks)
- At least one notification topic and subscription to receive monitoring alerts. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.3](https://www.cisecurity.org/cis-benchmarks)
- Notification for Identity Provider changes. [See CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.4](https://www.cisecurity.org/cis-benchmarks)
- Notification for IdP group mapping changes. [See CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.5](https://www.cisecurity.org/cis-benchmarks)
- Notification for IAM policy changes. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.6](https://www.cisecurity.org/cis-benchmarks)
- Notification for IAM group changes. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.7](https://www.cisecurity.org/cis-benchmarks)
- Notification for user changes. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.8](https://www.cisecurity.org/cis-benchmarks)
- Notification for VCN changes. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.9](https://www.cisecurity.org/cis-benchmarks)
- Notification for changes to route tables. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.10](https://www.cisecurity.org/cis-benchmarks)
- Notification for security list changes. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.11](https://www.cisecurity.org/cis-benchmarks)
- Notification for network security group changes. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.12](https://www.cisecurity.org/cis-benchmhas a staarks)
- Notification for changes to network gateways. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.13](https://www.cisecurity.org/cis-benchmarks)
- VCN flow logging for all subnets. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.14](https://www.cisecurity.org/cis-benchmarks)
- Write level logging for all Object Storage Buckets. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.17](https://www.cisecurity.org/cis-benchmarks)
- Notification for Cloud Guard detected problems.
- Notification for Cloud Guard remedied problems.

For IDCS or OCI Identity Domain Auditing events, the respective Auditing API can be used to retrieve all required information.

#### Data Encryption

All data will be encrypted at rest and in transit. Encryption keys can be managed by Oracle or the customer and will be implemented for identified resources.

##### Key Management

<!--
Make sure that the correct type of the vault is used:
shared - cheap to moderate pricing
private - expensive pricing
-->

All keys for **OCI Block Volume**, **OCI Container Engine for Kubernetes**, **OCI Database**, **OCI File Storage**, **OCI Object Storage**, and **OCI Streaming** are centrally managed in a shared or a private virtual vault will be implemented and placed in the compartment cmp-security.

**Object Storage Security**

For Object Storage security the following guidelines are considered.

- **Access to Buckets** -- Assign least privileged access for IAM users and groups to resource types in the object-family (Object Storage Buckets & Object)
- **Encryption at rest** -- All data in the Object Storage is encrypted at rest using AES-256 and is on by default. This cannot be turned off and objects are encrypted with a master encryption key.

**Data Residency**

It is expected that data will be held in the respective region and additional steps will be taken when exporting the data to other regions to comply with the applicable laws and regulations. This should be review for every project onboard into the tenancy.

#### Operational Security

**Security Zones**

Whenever possible OCI Security Zones will be used to implement a security compartment for Compute instances or Database resources. For more information on Security Zones refer to the in the *Oracle Cloud Infrastructure User Guide* chapter on [Security Zones](https://docs.oracle.com/en-us/iaas/security-zone/using/security-zones.htm).

**Remote Access to Compute Instances or Private Database Endpoints**

To allow remote access to Compute Instances or Private Database Endpoints, the OCI Bastion will be implemented for defined compartments.

To be able to use OCI services to for OS management, Vulnerability Scanning, Bastion Service, etc. it is highly recommended to implement the Oracle Cloud Agent as documented in the *Oracle Cloud Infrastructure User Guide* chapter [Managing Plugins with Oracle Cloud Agent](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/manage-plugins.htm).

#### Network Time Protocol Configuration for Compute Instance

Synchronized clocks are a necessity for securely operating environments. OCI provides a Network Time Protocol (NTP) server using the OCI global IP number 169.254.169.254. All compute instances should be configured to use this NTP service.

#### Regulations and Compliance

The customer is responsible for setting the access rules to services and environments that require stakeholders’ integration to the tenancy to comply with all applicable regulations. Oracle will support in accomplishing this task.



## Sizing and Bill of Materials

<!-- GUIDANCE -->
<!--
Estimate and size the physical needed resources of the Workload. The information can be collected and is based upon previously gathered capacities, business user numbers, integration points, or translated existing on-premises resources. The sizing is possibly done with or even without a Physical Architecture. It is ok to make assumptions and to clearly state them!

Clarify with sales your assumptions and your sizing. Get your sales to finalise the BoM with discounts or other sales calculations. Review the final BoM and ensure the sales is using the correct product SKU's / Part Number.

Even if the BoM and sizing was done with the help of Excel between the different teams, ensure that this chapter includes or links to the final BoM as well.

Price Lists and SKU's / Part Numbers: https://esource.oraclecorp.com/sites/eSource/ESRCHome

Describe the sizes of the complete workload solution and its components.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | C
PPM   | None
Sales | C
-->

<!-- Non Lift Workload End -->

Example for a small workload, but to be adjusted for (${doc.customer.name})s situation

| Environment | Component              | Quantity                | Metric    |
| ----------- | ---------------------- | ----------------------- | --------- |
| Pilot       | OAC Enterprise Edition | 2 | OCPU      |
| Pilot       | ADW-S                  | 2 | OCPU      |
| Pilot       | Object Storage         | 5 | Terrabyte |
| Pilot       | Compute Cloud - Oracle Free Linux Cloud Develop | 1 | OCPU |
| Pilot       | Compute Cloud for Informatica Secure Agent | 8 | OCPU |
| Pilot       | Exadata Storage        | 5 | Terrabyte |
| Pilot       | Block Volume           | 500 | Gb |

Next section is included in this document as an example covering the activities required for such migration and needs to be agreed with the migration partner (Lift, Oracle Consulting, 3rd party partner) to reflect the activities and effort required.

# Oracle Lift Project and Architecture

## Solution Scope

* OBIEE 11.1.1.9 will be migrated to OAC (in a private subnet). All data will be migrated, but testing will be done on a limited number of reports.
* Oracle Database will be migrated to ADW
* informatica Powercenter will be migrated to Informatica IDMC (IDMC)
* Solution for DAC to be defined and not in scope of this solution pack

### Disclaimer
<!-- GUIDANCE -->
<!--
A scope disclaimer should limit scope changes and create awareness that a change of scope needs to be agreed by both parties.
-->

<!-- EXAMPLE / TEMPLATE -->
As part of the Oracle Lift Project, any scope needs to be agreed upon by both the (${doc.customer.name}) and Oracle. A scope can change but must be confirmed again by both parties. Oracle can reject scope changes for any reason and may only design and implement a previously agreed scope. A change of scope can change any agreed times or deadlines and needs to be technically feasible.

All items not explicitly stated to be within the scope of the Lift project will be considered out of scope. Oracle recommends the use of professional services to implement extensions or customisations beyond the original scope, as well as to operate the solution, with an Oracle-certified partner.

### Overview
<!-- GUIDANCE -->
<!--
Describe the scope of Lift as a sub-set of the Workload scope. For example one environment from one application. Describe the sub-chapters

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | R
PPM   | C
-->
### Business Value

<!-- GUIDANCE -->
<!--
What's the value for the customer to do Lift? Why Lift? For example, speed of deployment and resulting impact on time to market, free service. Do not describe Oracle value or consumption.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | C
PPM   | C
-->

### Success Criteria
<!-- GUIDANCE -->
<!--
Technical success criteria for Lift. As always be S.M.A.R.T: Specific, Measurable, Achievable, Relevant, Time-bound. Example: 'Deployment of all OCI resources for the scoped environments in 3 month'.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | R
PPM   | C
-->

-

## Workplan

### Deliverables
<!-- GUIDANCE -->
<!--
Describe deliverables within the Lift scope. Including this documentation as Workload  Architecture Document - Solution Definition and the later following Workload Architecture Document - Solution Design. This should be a generic reusable text, provided by the implementers.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | A
Impl. | R
PPM   | None
-->

A Workload Architecture Document (WAD) which includes:

- Solution Definition

### Included Activities

<!-- GUIDANCE -->
<!--
Describe the implementation activities as part of the free Lift service. It does need to include a detailed list of cloud services or OCI capabilities, but rather includes activities such as 'Provisioning of Infrastructure Components'. This should be a generic reusable text, provided by the implementers.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | A
Impl. | R
PPM   | None
-->
#### Infrastructure and Landingzone

- OCI Infrastructure and landingzone setup
  - Compartments
  - VCN
  - Subnets
  - IAM, users, groups, identity domains, SL, RT, NSG
  - Connections with customer Network
    - VPN or Fastconnect IP Sec connection
    - Source system
  - Connection with Informatica control plane
- Provisioning of Services
  - ADW
  - Compute for IDMC agent migration tool
  - OAC +PAC
  - IAM and Users
  - Compute for Bastion
  - Compute for DB Migration (Developer cloud service)
  - Object Store bucket

#### Migration of On-premise DB to Oracle Autonomous Database

- Pre-migration tasks in source database:
   - Collect and analysis previous information related to the source database (Review space used by schemas, registry state, invalid objects, execution and analysis CPAT tool).
   - Support to export and copy Datapump files to OCI Object Storage which will be done by customer.

- Configure Working Migration Development (Developer cloud service, oracle client, OCI CLI, etc.)
- Database Migration using Oracle Datapump. Sample parameter might be used on certain tables if data volume is too big in size.
- Postmigration tasks:
   - Fix warning detected in the migration to ADW
   - Fix privileges not imported with Datapump
   - Support customer with validations after the database migration

#### OBIEE to Oracle Analytics Cloud

- Establishing the connectivity between ADW and OAC (Private Access Channel will be used)
- RPD is cleansed from Errors and Warnings during migration by customer with help from Oracle team
- Configuration of IAM Roles to Application Roles in OAC (limit to 5 users and 10 groups to Application Role mapping)
- Migration of the existing reports and dashboards
- Testing for a limited number of reports (up to 10 reports)

#### Informatica Powercenter to IDMC (Wilbert reached out to Infa Team)

- Deployment of IDMC agent on OCI (IDMC Market place)
- Export of Informatica Powercenter Repository (customer activity)
- Assessment step to check on possible issues to be covered
- Installation of IDMC + its new Repository
- Other preparation steps?????.........
- Use Migration tool from Informatica to migrate repository.
- Change or create connections to new ADW database
- Unit test for a limited number of mappings

#### DAC to ?????? (Manual Activity - solution definition still to be made and checked with Infa Team)

- Export of DAC repository content or access to running DAC environment at On-Premise
- Creation of new parameter storage solution
- Manually create schedule for migrated mappings

### Assumptions and exclusions

#### Infrastructure and Landingzone

- Predefined Reference Architecture can be used
- No implementation of AD and SSO integration
- VPN IP-Sec tunnel
- Creation of maximum 5 users and 5 groups
- creation of 2 identity domains

#### On premise DB to Oracle Autonomous Database

- Oracle Database
- Database minimum version of 10.2.0.5
- Size of DB maximum 2 TB
- CPAT tool outcome reveals no blocking errors
- One time migration of database content. Later adjustments and new data will not be taken in account.  

#### OBIEE to Oracle Analytics Cloud

- OBIEE is on minimum version 11.1.1.9
- RPD is in a consistent state
- Usage tracking will not be re-configured
- Customer will send us the RPD and the export of the migration tool from OBIEE
- Agents and schedulers will not be tested
- SMTP server will not be configured
- BI Publisher reports will not be tested
- No JS and/or CSS customisation of the reports
- No special characters (including spaces) are used in the names of the reports and entities in the catalog
- Unsupported functionality such as "Act As" is not used
- Reporting performance will remain as found (no performance improvement activities will be carried out)
- No setup/configuration of write-back functionality
- No security integration setup based on ICX-Session cookies. Data level security will not be tested and validated.

#### Informatica Powercenter to IDMC

-

#### DAC to ??????

-

#### Additional supporting documentation

The migration to OAC will be done using a JAR file as suggested in Oracle's official documentation (https://docs.oracle.com/en/cloud/paas/analytics-cloud/acmgb/migrate-oracle-bi-enterprise-edition.html#GUID-AB5F5552-82F0-4664-822B-F99F1EF7917E).
The customer will use the migration utility to export the content to a JAR file.

#### Security

For future reference related to data and object level security:

Configuration of groups and users will be done by following the documentation under (https://www.ateam-oracle.com/implementing-object-and-data-level-security-in-oracle-analytics-cloud-using-identity-cloud). To assign user responsibilities to OAC user sessions via initialisation blocks in **Oracle Analytics Client Tools** (https://www.oracle.com/middleware/technologies/oac-tools-downloads.html) is used. Session initialisation blocks will execute each time a user logs into OAC.

### Recommended Activities
<!-- GUIDANCE -->
<!--
Exclude all activities with the provided boilerplate text below. Agree on a few bullet points

Mandatory Chapter

Role  | RACI
------|-----
WLA   | A
Impl. | R
PPM   | None
-->
This Lift workload is designed to assist Customer to rapidly start utilizing Oracle Cloud Infrastructure and allow them to explore the benefits of the solution to them for further rollout. Once the Lift team finishes the work, the customer can leverage the knowledge acquired from this project to create additional environments themselves or with the help of Oracle Consulting and/or a partner.

### Timeline
<!-- GUIDANCE -->
<!--
Provide a very high-level Lift implementation plan. Use Phases to communicate an iterative implementation (called Delivery Geared Design)

Mandatory Chapter

Role  | RACI
------|-----
WLA   | A
Impl. | R
PPM   | C/I
-->
This high-level project timeline shows a representative timeline and is intended for planning purposes only.


| Step                                        | Description | Effort |
| ------------------------------------------- | ----------- | ------ |
| Initiation, INfrastructure and Connectivity |             | 6.5    |
| Migration of DB and OBIEE to ADW and OAC    |             | 25     |
| Migration of Powercenter to IDMC            |             | xx     |
| Documentation, Security, QA and handover    |             | 4      |
| TPM and PPM                                 |             | 7      |
| DAC replacement design                      |             | xx     |
| Total                                       |             | 42.5   |

Section To Be Added and updated

### Implementation RACI
<!-- GUIDANCE -->
<!--
Clarify implementation responsibilities between all parties, possibly including consulting partners. High- level view, without going into deployment or physical details.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | A
Impl. | R
PPM   | None
-->|
||

### Generic Assumptions
<!-- GUIDANCE -->
<!--
List any  assumptions, if any, which could impact the Lift solution architecture or the implementation.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | R
PPM   | None
-->

<!-- EXAMPLE / TEMPLATE -->
All work will be done remotely and within either local time or India standard time within normal office working hours.
The following assumptions have been made about the project, which will impact delivery:

- Disaster Recovery is not in scope
- Tenancy is provisioned as new with availability of Identity and Access Management Identity Domains
- Customer will have the export datapump prepared and he will copy datapump files to the Oracle Object Storage
- For the pilot customer accepts to pass warnings and errors when loading the data in the database.

### Out of scope

The following components and activities are out of scope:

- Provisioning and configuration of a second instance (only a NONPROD instance will be provisioned).
- Any third party or Customer on-premises integration.
- Third Party products, Backup tools, Firewall implementation, Security tools, monitoring tools implementation.
- Load Testing, Performance benchmarking testing, Functional/code change & tuning of any component in the solution.
- Any Vulnerability Assessment and Penetration Testing.
- Trainings on deployed products and cloud services.
- Any other activity not listed under “In Scope” section.
- Migration Apex workspaces in case of use.

### Obligations
<!-- GUIDANCE -->
<!--
List any obligations required by the customer to perform or have available, if any, which could impact the Lift solution architecture or the implementation. Please always include this chapter to capture the obligation that we have admin access to the customers tenancy.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | R
PPM   | None
-->

<!-- EXAMPLE / TEMPLATE -->
- You will have purchased the appropriate Universal Credits for the services required for the project.
- The Oracle Lift team will have admin access to the customers tenancy for implementation.
- You will ensure the appropriate product training has been obtained to maintain and support the implementation.
- Your business team will be available for the Testing phase, which will be completed within the agreed testing window.
- You will provide project management for the project and will manage any third party suppliers or vendors.
- Complete the OCI Site to Site VPN Request Form as supplied by the Oracle Workload Architect.
- Complete the OCI Fast Connect Request Form as supplied by the Oracle Workload Architect.
- Test cases to be defined and provided by the customer
- Customer to provide necessary encryption keys is required

<!-- End Solution Definition -->
<!-- Earliest Customer Lift Acceptance -->
<!-- Begin Solution Design -->

### Risks

- Solution for DAC

## Physical Future State Architecture

<!-- GUIDANCE -->
<!--
Create a detailed physical solution architecture for Lift. It will include physical attributes such as IP ranges or compute shaped. The architecture is ready for implementation.

Lists of physical details are available and to be provided to the implementation team in section 'Deployment Build'.

Notation: https://apex.oraclecorp.com/pls/apex/patterns/r/patternlibrary/view-pattern?p118_id=567&session=17457054591654

Mandatory Chapter (Can be logical/skipped for PaaS-only Projects)

Role  | RACI
------|-----
WLA   | R/A
Impl. | R
PPM   | None
-->

<!-- Latest Customer Lift Acceptance -->