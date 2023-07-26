# Document Control

## Version Control

| Version | Author | Date | Comment |
|---------|--------|------|---------|

## Team

| Name | e-mail | Role | Company |
|------|--------|------|---------|

## Document Purpose

This document provides a high-level solution definition for the Oracle solution and aims at describing the current state, to-be state as well as a potential 'Lift' project scope and timeline. The Lift parts will be described as a physical implementable solution. The intended purpose is to provide all parties involved with a clear and well-defined insight into the scope of work and intention of the project as it will be done as part of the Oracle Lift service.

The document may refer to a 'Workload', which summarizes the full technical solution for a customer (You) during a single engagement. The Workload is described in chapter [Workload Requirements and Architecture](#workload-requirements-and-architecture). In some cases Oracle offers an implementation service called 'Lift', which has its dedicated scope and is typically a subset of the initial Workload. The Lift project, architecture, and implementation details are documented in chapter Oracle Lift Project and Architecture and in chapter Oracle Lift Implementation.

This is a living document, additional sections will be added as the engagement progresses resulting in a final Workload Architecture Document to be handed over at the end of the engagement. Where Oracle Lift is involved, detailed design sections will be added after customer acceptance of the content of the Workload Architecture Document as it stands at the time acceptance is requested.

# Business Context

A Company Making Everything will be provided with a next-generation cloud analytics solution in the form of Oracle Analytics Cloud (OAC) that will replace the existing on-premises Oracle Business Intelligence Enterprise Edition (OBIEE) for the customer.

## Workload Business Value

The Oracle Analytics Cloud solution is a cloud-native service that provides the capabilities required to address the entire analytics process from data ingestion and modeling, through data preparation and enrichment, to visualization and collaboration without compromising security and governance. Embedded machine learning and natural language processing technologies help increase productivity and build an analytics-driven culture in organizations.

# Workload Requirements and Architecture

## Overview

The objective of this project is to successfully migrate on-premises OBIEE to OAC in Oracle Cloud Infrastructure. The Lift project will take care of the migration of only one (1) environment. For the rest of the environments, the customer can leverage the knowledge from Lift to create additional ones themselves or with the help of Oracle Consulting and/or a partner. There are a number of pre-requisites that need to be met in order for the implementation to be successful.

## Non Functional Requirements

## Current State Architecture

![Current State Architecture](images/Current_State_Architecture_v01.png)

-   **Data Sources** - represent the various data sources from which A Company Making Everything collects its data.

-   **ETL** - is the ETL tool used to extract the data from various sources, transform them and load them into Data Warehouse.

-   **Data Warehouse** - central location where all data is stored. This creates a single source of truth and allows for further manipulation of data.

-   **Oracle Business Intelligence Enterprise Edition (OBIEE)** - A Company Making Everything's central reporting platform. Used daily by A Company Making Everything to access various reports, dashboards and visualizations.

-   **Auth Provider** - the Authentication and Authorization provider deployed by A Company Making Everything

-   **OBIEE Users** - represents the end users of OBIEE.

## Future State Architecture

![Future State Architecture](images/Target_State_Architecture_v01.png)

In the target logical diagram, the following **new** components are represented:

-   **Private Access Channel** - enables OAC with public and private endpoints to access private data sources directly.

-   **Oracle Analytics Cloud (OAC)** - A Company Making Everything's target central reporting platform in the cloud. Will be used daily by A Company Making Everything to access various reports, dashboards and visualizations.

-   **IDCS** - IDCS provides the security and manages authentication and authorization for the end users.

### Data Access

A Company Making Everything's data will remain on-permises. To access this data securely, a PDAC (Private Data Access Channel) will be configured. This ensures a secure connection to A Company Making Everything's on-premises database in their private network. A detailed description of how a PDAC is setup can be found here (https://docs.oracle.com/en/cloud/paas/analytics-cloud/acoci/manage-service-access-and-security.html#GUID-19F1F4B0-3709-4243-BC00-0FD078F1E444). This scenario gives the on-premises network private access to Oracle Analytics Cloud, so that the on-premises hosts can use their private IP addresses and the traffic does not go over the public internet. Instead, the traffic travels over VPN, transits through a virtual cloud network (VCN), and then through a service gateway to the Oracle Analytics Cloud.

### Security

The solution will use Oracle Identity Cloud Service for authentication and authorization.

Up to five (6) users will be manually created in Oracle Identity Cloud Service (IDCS) for authentication and linked to OAC.

## OCI Cloud Landing Zone Architecture

The design considerations for an OCI Cloud Landing Zone have to do with OCI and industry architecture best practices, along with A Company Making Everything specific architecture requirements that reflect the Cloud Strategy (hybrid, multi-cloud, etc). An OCI Cloud Landing zone involves a variety of fundamental aspects that have a broad level of sophistication. A good summary of a Cloud Landing Zone has been published in the [OCI User Guide](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/landing-zone.htm).

### Naming Convention

A naming convention is an important part of any deployment to ensure consistency as well as security within your tenancy. Hence we jointly agree on a naming convention, matching Oracle's best practices and A Company Making Everything requirements.

Please find the agreed naming convention in the chapter [Resource Naming Convention](#resource-naming-convention).

### Security and Identity Management

This chapter covers the Security and Identity Management definitions and resources which will be implemented for A Company Making Everything.

#### Universal Security and Identity and Access Management Principles

-   Groups will be configured at the tenancy level and access will be governed by policies configured in OCI.
-   Any new project deployment in OCI will start with the creation of a new compartment. Compartments follow a hierarchy, and the compartment structure will be decided as per the application requirements.
-   It is also proposed to keep any shared resources, such as Object Storage, Networks etc. in a shared services compartment. This will allow the various resources in different compartments to access and use the resources deployed in the shared services compartment and user access can be controlled by policies related to specific resource types and user roles.
-   Policies will be configured in OCI to maintain the level of access / control that should exist between resources in different compartments. These will also control user access to the various resources deployed in the tenancy.
-   The tenancy will include a pre-provisioned Identity Cloud Service (IDCS) instance (the primary IDCS instance) or, where applicable, the Default Identity Domain. Both provide access management across all Oracle cloud services for IaaS, PaaS and SaaS cloud offerings.
-   The primary IDCS or the Default Identity Domain will be used as the access management system for all users administrating (OCI Administrators) the OCI tenant.

#### Authentication and Authorization for OCI

Provisioning of respective OCI administration users will be handled by A Company Making Everything.

##### User Management

Only OCI Administrators are granted access to the OCI Infrastructure. As a good practice, these users are managed within the pre-provisioned and pre-integrated Oracle Identity Cloud Service (primary IDCS) or, where applicable, the OCI Default Identity Domain, of OCI tenancy. These users are members of groups. IDCS Groups can be mapped to OCI groups while Identity Domains groups do not require any mapping. Each mapped group membership will be considered during login.

**Local Users**

The usage of OCI Local Users is not recommended for the majority of users and is restricted to a few users only. These users include the initial OCI Administrator created during the tenancy setup, and additional emergency administrators.

**Local Users are considered as Emergency Administrators and should not be used for daily administration activities!**

**No additional users are to be, nor should be, configured as local users.**

**A Company Making Everything is responsible to manage and maintain local users for emergency use cases.**

**Federated Users**

Unlike Local Users, Federated Users are managed in the Federated or Enterprise User Management system. In the OCI User list Federated Users may be distinguished by a prefix which consists of the name of the federated service in lower case, a '/' character followed by the user name of the federated user, for example:

`oracleidentityservicecloud/user@example.com`

In order to provide the same attributes (OCI API Keys, Auth Tokens, Customer Secret Keys, OAuth 2.0 Client Credentials, and SMTP Credentials) for Local and *Federated Users* federation with third-party Identity Providers should only be done in the pre-configured primary IDCS or the Default Identity Domain where applicable.

All users have the same OCI-specific attributes (OCI API Keys, Auth Tokens, Customer Secret Keys, OAuth 2.0 Client Credentials, and SMTP Credentials).

OCI Administration user should only be configured in the pre-configured primary IDCS or the Default Identity Domain where applicable.

**Note:** Any federated user can be a member of 100 groups only. The OCI Console limits the number of groups in a SAML assertion to 100 groups. User Management in the Enterprise Identity Management system will be handled by A Company Making Everything.

**Authorization**

In general, policies hold permissions granted to groups. Policy and Group naming follows the Resource Naming Conventions.

**Tenant Level Authorization**

The policies and groups defined at the tenant level will provide access to administrators and authorized users, to manage or view resources across the entire tenancy. Tenant level authorization will be granted to tenant administrators only.

These policies follow the recommendations of the [CIS Oracle Cloud Infrastructure Foundations Benchmark v1.2.0, recommendations 1.1, 1.2, 1.3](https://www.cisecurity.org/cis-benchmarks).

**Service Policy**

A Service Policy is used to enable services at the tenancy level. It is not assigned to any group.

**Shared Compartment Authorization**

Compartment level authorization for the cmp-shared compartment structure uses the following specific policies and groups.

Apart from tenant level authorization, authorization for the cmp-shared compartment provides specific policies and groups. In general, policies will be designed that lower-level compartments are not able to modify resources of higher-level compartments.

Policies for the cmp-shared compartment follow the recommendations of the [CIS Oracle Cloud Infrastructure Foundations Benchmark v1.2.0, recommendations 1.1, 1.2, 1.3](https://www.cisecurity.org/cis-benchmarks).

**Compartment Level Authorization**

Apart from tenant level authorization, compartment level authorization provides compartment structure specific policies and groups. In general, policies will be designed that lower-level compartments are not able to modify resources of higher-level compartments.

**Authentication and Authorization for Applications and Databases**

Application (including Compute Instances) and Database User management is completely separate of and done outside of the primary IDCS or Default Identity Domain. The management of these users is the sole responsibility of A Company Making Everything using the application, compute instance and database specific authorization.

#### Security Posture Management

**Oracle Cloud Guard**

Oracle Cloud Guard Service will be enabled using the pcy-service policy and with the following default configuration. Customization of the Detector and Responder Recipes will result in clones of the default (Oracle Managed) recipes.

Cloud Guard default configuration provides a number of good settings. It is expected that these settings may not match with A Company Making Everything's requirements.

**Targets**

In accordance with the [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.2.0, Chapter 3.15](https://www.cisecurity.org/cis-benchmarks), Cloud Guard will be enabled in the root compartment.

**Detectors**

The Oracle Default Configuration Detector Recipes and Oracle Default Activity Detector Recipes are implemented. To better meet the requirements, the default detectors must be cloned and configured by A Company Making Everything.

**Responder Rules**

The default Cloud Guard Responders will be implemented. To better meet the requirements, the default detectors must be cloned and configured by A Company Making Everything.

**Vulnerability Scanning Service**

In accordance with the [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.2.0, OCI Vulnerability Scanning](https://www.cisecurity.org/cis-benchmarks) will be enabled using the pcy-service policy.

Compute instances which should be scanned *must* implement the *Oracle Cloud Agent* and enable the *Vulnerability Scanning plugin*.

**OCI OS Management Service**

Required policy statements for OCI OS Management Service are included in the pcy-service policy.

By default, the *OS Management Service Agent plugin* of the *Oracle Cloud Agent* is enabled and running on current Oracle Linux 6, 7, 8 and 9 platform images.

#### Monitoring, Auditing and Logging

In accordance with the [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.2.0, Chapter 3 Logging and Monitoring](https://www.cisecurity.org/cis-benchmarks) the following configurations will be made:

-   OCI Audit log retention period set to 365 days.
-   At least one notification topic and subscription to receive monitoring alerts.
-   Notification for Identity Provider changes.
-   Notification for IdP group mapping changes.
-   Notification for IAM policy changes.
-   Notification for IAM group changes.
-   Notification for user changes.
-   Notification for VCN changes.
-   Notification for changes to route tables.
-   Notification for security list changes.
-   Notification for network security group changes.
-   Notification for changes to network gateways.
-   VCN flow logging for all subnets.
-   Write level logging for all Object Storage Buckets.
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

Synchronized clocks are a necessity for securely operating environments. OCI provides a Network Time Protocol (NTP) server using the OCI global IP number 169.254.169.254. All compute instances should be configured to use this NTP service.

#### Regulations and Compliance

A Company Making Everything is responsible for setting the access rules to services and environments that require stakeholders’ integration to the tenancy to comply with all applicable regulations. Oracle will support in accomplishing this task.

## Bill of Materials

| Environment | Description                               | Metric  | Size      | Monthly Cost | Annual Cost | Hours p/m |
|-------------|-------------------------------------------|---------|-----------|--------------|-------------|-----------|
| Pilot       | Oracle Analytics Cloud Service–Enterprise | OCPU/Hr | 2         |              |             | 744       |
|             |                                           |         | **TOTAL** | **XXX**      | **XXX**     |           |

## Prerequisites:

The following prerequisites need to be in place:

-   OBIEE is on version 12.2.1.4
-   RPD is in a consistent state
-   No object level security is used
-   No usage tracking is implemented
-   No JS and/or CSS customization of the reports
-   No special characters (including spaces) are used in the names of the reports and entities in the catalog
-   No OBIEE variables like :USER, :ROLE, :GROUP are used
-   Unsupported functionality such as "Act As" is not used.
-   Disaster Recovery is not in scope
-   VPN is already set up by A Company Making Everything

# Oracle Lift Project and Architecture

==**the Lift part below here is not yet confirmed nor validated by Lift team if achievable or realistic**==

## Solution Scope

### Disclaimer

As part of the Oracle Lift Project, any scope needs to be agreed upon by both the customer and Oracle. A scope can change but must be confirmed again by both parties. Oracle can reject scope changes for any reason and may only design and implement a previously agreed scope. A change of scope can change any agreed times or deadlines and needs to be technically feasible.

All items not explicitly stated to be within the scope of the Lift project will be considered out of scope. Oracle recommends the use of professional services to implement extensions or customizations beyond the original scope, as well as to operate the solution, with an Oracle-certified partner.

### Business Value

This Lift implementation of this project will give A Company Making Everything a kickstart into a new Analytics world, allowing them to increase their agility and to gain deeper insights to make data driven decision. The project will deliver a foundation based on best practices of OCI with a sound basis to extend and expand. By utilizing Lift, A Company Making Everything will have an extensible foundation for analytics.

### Success Criteria

A Company Making Everything will have a functional OAC environment with the existing reports build by them in OBIEE.

## Workplan

### Deliverables

-   A Workload Architecture Document (WAD) which includes:
    -   Solution Definition
    -   Solution Design
-   Handover Documentation

### Included Activities

The following components and activities are included in the project scope:

1.  Tenancy

    -   Provisioning and configuration of compartments, groups, policies and tags
    -   Provisioning and configuration of VCN, subnets, gateways, security lists, ingress/egress rules

2.  Identity and Authentication

    -   A maximum of 6 users and 3 groups will be created

3.  Oracle Analytics Cloud

    -   provisioning of the instances
    -   migration of the existing reports and dashboards
    -   testing for a limited number of reports (2)

4.  Documentation

### Migration approach

The migration to OAC will be done using a BAR file as suggested in Oracle's official documentation (https://docs.oracle.com/en/cloud/paas/analytics-cloud/acabi/migrate-content-oracle-bi-enterprise-edition-12c.html).

Most objects such as data models, dashboards, analyses, and application roles are migrated from Oracle BI Enterprise Edition 12c using a BAR file. A Company Making Everything will use WebLogic Scripting Tool (WLST) to export the content to a BAR file (that is, repository data, catalog content, and security policy).

### Security migration approach

Application roles are migrated using a BAR file while initialization blocks for authentication and authorization should be migrated manually. Configuration of groups and users will be done by following the documentation under (https://www.ateam-oracle.com/implementing-object-and-data-level-security-in-oracle-analytics-cloud-using-identity-cloud). To assign user responsibilities to OAC user sessions via initialization blocks an **Oracle Analytics Client Tools** (https://www.oracle.com/middleware/technologies/oac-tools-downloads.html) is used. Session initialization blocks will execute each time a user logs into OAC.

### Recommended Activities

This Lift workload is designed to assist A Company Making Everything to rapidly start utilising Oracle Cloud Infrastructure and allow them to explore the benefits of the solution to them for further rollout. Once the Lift team finishes the work, A Company Making Everything can leverage the knowledge acquired from this project to create additional environments themselves or with the help of Oracle Consulting and/or a partner.

### Timeline

This high-level project timeline shows a representative timeline and is intended for planning purposes only

TODOTODOTODO

### Implementation RACI

### Assumptions

The following assumptions have been made about the project, which will impact delivery:

-   OBIEE is on version 12.2.1.4
-   RPD is in a consistent state
-   No object level security is used
-   No usage tracking is implemented
-   No JS and/or CSS customization of the reports
-   No special characters (including spaces) are used in the names of the reports and entities in the catalog
-   No OBIEE variables like :USER, :ROLE, :GROUP are used
-   Unsupported functionality such as "Act As" is not used.
-   Disaster Recovery is not in scope
-   VPN is already set up by A Company Making Everything and the appropriate ports are opened in order to be access the on-prem data sources

### Out of scope

The following components and activities are out of scope:

-   Provisioning and configuration of a second instance
-   VPN setup, On Premise VPN Tunnel, Fast Connect, VPN Firewall Configuration.
-   Functional Testing of OAC reports.
-   Any third party or A Company Making Everything on-premise integration
-   Third Party products, Backup tools, Firewall implementation, Security tools, monitoring tools implementation.
-   Load Testing, Performance benchmarking testing, Functional/code change & tuning of any component in the solution.
-   Any Vulnerability Assessment and Penetration Testing.
-   Trainings on deployed products and cloud services.
-   Any other activity not listed under “In Scope” section.

### Obligations

The following obligations will be required to be met for the project:

-   A Company Making Everything will have purchased the appropriate Universal Credits for the services required for the project.
-   A Company Making Everything will provide Oracle with users with admin access to the A Company Making Everything tenancy.
-   A Company Making Everything will provide functional or business subject matter experts who understand the current environment and are able to answer functional and technical questions that might arise.
-   A Company Making Everything will ensure the appropriate product training has been obtained to maintain and support the implementation
-   A Company Making Everything's business team will be available for the Testing phase, which will be completed within the agreed testing window.
-   A Company Making Everything will provide project management for the project and will manage any third party suppliers or vendors.

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

The value for \<prefix\> or the full names **must be agreed** with A Company Making Everything.
