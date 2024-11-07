---
doc:
  author: Name Surname                  #Mandatory
  version: 2.5                            #Mandatory
  cover:                                #Mandatory
    title:                              #Mandatory
      - ${doc.customer.name}            #Mandatory
      - \<Workload\> to OCI       #Mandatory
    subtitle:                           #Mandatory
      - Solution Definition             #Mandatory
  customer:                             #Mandatory
    name: \<Customer Name\>                           #Mandatory
    alias: \<Customer Alias\>                          #Mandatory
  config:
    impl:
      type: \<Service Provider\>            #Mandatory: Can be 'Oracle Lift', 'Oracle Fast Start', 'Partner' etc. Use with ${doc.config.impl.type}     
      handover: ${doc.customer.name}    #Mandatory: Please specify to whom to hand over the project after implementation. eg.: The Customer, a 3rd party implementation or operations partner, etc.           
  draft: false
  history:
    - version: 1.0
      date: 1st June 2023
      authors:
        - Base Template
      comments:
        - Created a new Solution Definition document. To be used for iterative review and improvement.
    - version: 1.1
      date: 1st July 2023
      authors: Base Template
      comments:
        - Update Template per feedback. Added security-templated texts and annex.
    - version: 1.2
      date: 1st August 2023
      authors: Base Template
      comments:
        - Update Template per feedback. As per Confluence.
    - version: 2
      date: 1st September 2023
      authors: Base Template
      comments:
        - Added Networking Annex
    - version: 2.1
      date: 1st September 2023
      authors: Base Template
      comments:
        - Updated LZ Snippet
        - Added 'Base Template' to version table instead of 'Name Surname'
    - version: 2.2
      date: 16th October 2023
      authors: Base Template
      comments:
        - Upgraded the Logical Architecture as mandatory. It is now included in the 'Mandatory' template.
    - version: 2.3
      date: 16th January 2024
      authors: Base Template
      comments:
        - Added comment for workload snippets
        - Updates Acronyms
    - version: 2.4
      date: 26th February 2024
      authors: Base Template
      comments:
        - Added the network firewall in the requirment, the solution considerations and in the Annex.
    - version: 2.5
      date: 25th March 2024
      authors: Base Template
      comments:
        - Added 'manageability' in the requirment, the solution considerations and in the Annex.
  team:
    - name: ${doc.author}
      email: example@example.com
      role: Tech Solution Specialist
      company: Oracle
    - name: Ada Lovelace
      email: example@example.com
      role: Account Cloud Engineer
      company: Oracle
  acronyms:
    Dev: Development
---

<!--
    Last Change: 18th May 2022
    Review Status: Development
    Review Notes: see https://confluence.oraclecorp.com/confluence/x/9Vyyvw
    How to use this template: https://confluence.oraclecorp.com/confluence/x/LBRBvg
-->

<!--
If you need to control the hyphenation of words. Use the example below and remove the comment. Example of the default hyphenation De-vOps or in-fras-truc-ture. You can change it by defining a new hyphenation as in the example below 'in-fra-struc-ture'. Or define words without any hyphenation, for example for names such as ArgoCD.
-->
<!--
\hyphenation{Dev-Ops ArgoCD in-fra-struc-ture re-li-a-bil-i-ty}
-->

*Guide:*

*Author Responsibility*

- *Chapter 1-3: Sales Consultant*
- *Chapter 4: Implementer*

# Document Control
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | None
PPM   | None
-->

*Guide:*

*The first chapter of the document describes the metadata for the document. Such as versioning and team members.*

## Version Control
<!-- GUIDANCE -->
<!--
A section describing the versions of this document and its changes.
-->

| Version | Author       | Date                 | Comment         |
|:--------|:-------------|:---------------------|:----------------|
| 1.0     | Ravindra Kumar | February 29th, 2024 | Initial version |
| 1.1     | Ravindra Kumar | February 29th, 2024 | Updated |

## Team
<!-- GUIDANCE -->
<!--
A section describing the versions of these documents and their changes.
-->

| Name         | E-Mail              | Role                              | Company |
|:-------------|:--------------------|:----------------------------------|:--------|
|  |  |  | = |
| |  | |   |

## Abbreviations and Acronyms
<!-- Guidance -->
<!--
Abbreviation: a shortened form of a word or phrase.
Acronyms: an abbreviation formed from the initial letters of other words and pronounced as a word (e.g. ASCII, NASA ).
Maintain a list of terms, if needed. Use this internal page to find and translate abbreviations and acronyms: https://apex.oraclecorp.com/pls/apex/f?p=15295:1:8900541624336:::::
-->


| Term  | Meaning                               |
|:------|:--------------------------------------|
| OCM   | Oracle Cloud Migration Service        |
| OCI   | Oracle Cloud Infrastructure           |
| VCN   | Virtual Cloud Network                 |
| IAM   | Identity and Access Management        |
| VDDK  | VMware Virtual Disk Development Kit   |       |
| VDS   | VMware vSphere Distributed Switch     |
| ESXi  | VMware vSphere Hypervisor (ESXi)      |
| VC    | VMware vCenter Server                 |
| OSS   | Object Storage Service                |
| NSX-T | VMware Network Virtualization (NSX-T) |
| HCX   | VMware Hybrid Cloud Extension (HCX)   |
| RMS   | Resource Manager Stack

## Document Purpose

This document does provide the highlevel overview of the Oracle Cloud migration service known as OCM.

Oracle Cloud Migration Service is a suite of tools and services designed to facilitate the migration of workloads, applications, and data from on-premises environments to Oracle Cloud Infrastructure (OCI). Specifically, for moving on-premises vSphere virtual machines to OCI, Oracle provides tools and support to streamline the migration process.

Overall, Oracle Cloud Migration Service simplifies the process of migrating on-premises vSphere virtual machines to OCI, enabling customers to leverage the benefits of cloud infrastructure while minimizing downtime and risk.



## Document Purpose

```{.snippet}
uc-document-purpose
```

# Business Context
<!-- GUIDANCE -->
<!--
Describe the customer's business and background. What is the context of the customer's industry and Line of Business (LOB)? What are the business needs and goals which this Workload is an enabler for? How does this technical solution impact and support the customer's business goals? Does this solution support a specific customer strategy, or maybe certain customer values? How does this solution help our customers to either generate more revenue or save costs?

Mandatory Chapter

| Role  | RACI |
|:------|:-----|
| ACE   | R/A  |
| Impl. | None |
| PPM   | None |
-->

*Example:*

${doc.customer.name} is located in Frankfurt, Germany, and is the largest consumer electronics company. ${doc.customer.name} has 2500 employees at this location, generating
millions of dollars in sales. There are subsidiaries under ${doc.customer.name} corporate family which contribute to overall sales for the parent organization.

${doc.customer.name} is an existing Oracle Cloud customer and currently consuming various OCI services such as network, compute, storage, and databases in OCI Frankfurt Region. The current Production, Test, Dev & DMZ environments are hosted in an on-premises infrastructure with physical servers. The customer has a cloud and digital transformation strategy and would like to exit the data center by moving the on-premises workloads to the cloud.

The mission-critical application workloads are hosted primarily in VMware.  The customer is looking for quick and seamless migration to the cloud with minimal interruption to the services. They have decided to use the Oracle Cloud Infrastructure using the Oracle cloud Migration for quick migration of the VMware workloads before their current data center contract expires. The Oracle Cloud Infrastructure offers flexible, highly scalable, and cost-effective solutions to host critical workloads without disrupting their core business.

## Executive Summary

## Workload Business Value

<!-- GUIDANCE -->
<!--
A clear statement of specific business value as part of the full workload scope. Try to keep it SMART: Specific, Measurable, Assignable, Realistic, and Time-Related - Agree on the SMART business value with the customer. Keep it business focused, and speak the language of the LOB which benefits from this Workload: "Increase Customer Retention by 3% in the next year" or "Grow Customer Base with Executive Decision-Making from our Sales and Support Data". Avoid technical success criteria such as "Migrate App X to Oracle Cloud" or "Provision 5 Compute Instances". Avoid Oracle success criteria and language "Get Workload Consuming on OCI".

Mandatory Chapter

| Role  | RACI |
|:------|:-----|
| ACE   | R/A  |
| Impl. | None |
| PPM   | None |
-->

*Example:*

${doc.customer.name} is running a strategic program in FY23 called EXAMPLE. As part of their initiative, one pillar is dedicated to their IT cost saving. ${doc.customer.name} is planning to reduce their IT estate spending by 15% in the current FY. Oracle can help ${doc.customer.name} by reducing the VMware deployment complexity and operations while optimizing IT costs. ${doc.customer.name} IT department wants to innovate other LoBs and enable quick-time-to-market for various applications and business needs. This allows ${doc.customer.name} to stay ahead in a competitive market.

The Oracle Cloud migration service is a customer-managed SAAS (Software as a service) solution. It does provide the flexibility to the customers to move their on-premises virtual machines to Oracle cloud infrasturcture. Overall, Oracle Cloud Migration Service simplifies the process of migrating on-premises vSphere virtual machines to OCI, enabling customers to leverage the benefits of cloud infrastructure while minimizing downtime and risk.


# Overview

The Oracle Cloud Migrations service provides an end-to-end comprehensive self-service experience for migrating existing VMware virtual machine-based workloads from on-premises to Oracle Cloud Infrastructure (OCI).
Oracle Cloud Migrations allows you to identify virtual-machine workloads hosted in an environment external to OCI, plan migrations, and automate migration workflows.

The Oracle Cloud Migrations service enables you to perform the following tasks:

* Automatically discover virtual machines external to Oracle Cloud Infrastructure.
* Organize virtual machines for migration.
* Project cost of the migration running on OCI, using customer’s rate card
* Replicate the virtual machine data to OCI.
* Plan the redeployment of virtual machines.
* Reconfigure virtual machines to launch successfully as OCI compute instances automatically.
* Launch virtual machines as OCI compute instances using replicated data.


Oracle guides in planning, architecting, prototyping, and managing cloud migrations. Customers can move critical workloads in weeks, or even days, instead of months by leveraging OCM Oracle Cloud Migration Services. OCM service is free of the cost for the Oracle cloud Infrastructure services customers.

# Current On-premises vSphere environment components.   


The current state architecture covers the current on-premises workloads.

### Current State IT Architecture (VMware)

Current environment is running in a data center (DC LOCATION) based on hardware (HARDWARE MODELS) infrastructure and VMware vSphere Hypervisor (ESXi).

__The Current VMware footprint consists of:__

-	VMware vSphere with 7.0 release
-	VMware vSAN Storage
- VMware NSX or NSX-T as a networking solution
-	Backup Solution

Below is the current high-level architecture of the customer's on-premises VMware environment.

![Current State Architecture](image/sample-currentstatearchitecture.jpg)

### Current VMware Inventory On-premises

__VM resource allocations per location:__

| Location      | Type             | Total vCPU Cores | Total Memory (GB) | Used Storage (GB) | Total Storage (GB) |
|:--------------|:-----------------|:-----------------|:------------------|:------------------|:-|
| Location Name | Virtual Machines | 550              | 1800              | 23580             | 30000 |
| Location Name | Virtual Machines | 550              | 1800              | 23580             | 30000 |



# Requirements for Setting up OCM Service.


- Tenancy Compartment Design
- Tenancy Users and Groups
- Secrets and Vaults
- Service Policies
- Buckets  
- vCenter Requirements
- Network Connectivity
- vSphere permissions
- VDDK & Change Block Tracking
- Customer documentation
- See Migrating VMware VMs to OCI Compute

#### OCM Pre-requisites

* Access to an active OCI tenancy, which will be the target environment.

* A Compartment in the tenancy. This can be a new or existing compartment.

* Appropriate policy and permissions in place to manage Oracle Cloud Migrations and required components in the selected compartment.

* Please find details about required IAM Polices at: IAM and Oracle Cloud Migrations Policies. and On-prem vCenter roles and permissions.

* Supported vSphere environment (6.5 and Above). Supported vSphere versions & Operating systems. Supported vSphere versions and Operating systems.

* Provide agent dependency, which is a 3rd party package required by remote agent appliance for it’s function. Oracle Cloud Migrations replication function running on the remote agent appliance depends on the appropriate VMware Virtual Disk Development Kit (VDDK) agent to perform the snapshot operations on the VMware VM disk. This can be downloaded from theVMware portal.
For more information and download links for vSphere VDDK, see vSphere VDDK.

* Create a Private Object Storage bucket in the OCI tenancy, to store the source asset snapshots.

* Create a vault to store the credentials used by the Oracle Cloud Migrations Service.

* Object Storage Configuration: OCI Object Storage will be used to store the replicated VM data by Oracle Cloud Migrations service from on-premises environment.

Oracle Cloud migration service Being a SAAS offering is deployed at tenancy level within the OCI region.  

The details of the Oracle Cloud Infrastructure SLAs are found in the link below.
[OCI Service SLA](https://www.oracle.com/ae/cloud/sla/).


# Workload Architecture of On-prem and OCM Environement.

Below is the current high-level architecture of the customer's on-premises VMware environment and OCM in Oracle cloud Infrastructure.

![Future State Architecture](image/Futurestate-ocm-Architecture.jpg)

### Current VMware Inventory On-premises

========================================================================= Ravindra

__VM resource allocations per location:__

| Location      | Type             | Total vCPU Cores | Total Memory (GB) | Used Storage (GB) | Total Storage (GB) |
|:--------------|:-----------------|:-----------------|:------------------|:------------------|:-|
| Location Name | Virtual Machines | XXX              | XXX              | XXX              |XXX |
| Location Name | Virtual Machines | XXX              | XXX             | XXX              |XXX |

__Operating Systems:__

The operating system supported by OCM service is mentioned in the OCM documentation supported guest operating system. Few of the examples are below. This is suggested to refer to the Oracle Cloud migration service official Documentation.

- Windows Server 2019
- Oracle Linux 8
- Red Hat Linux
- Windows Server 2012






# Overview of the components of the  Oracle Cloud Migration (OCM) Service.

This section describes the OCM Components.

__Oracle cloud migration service (OCM):__ The OCI native services such Like OCM is highly available since this is a SAAS offering.

__OCB Agent VM:__ The OCM service does provide the OCB agent pre-built virtual Machine OVA files to be deployed and configured in on-premises vSphere Environment. There will be three different plugins of this OCB agent.

#### Discovery

This plugin gather the information about the virtual machines data and represent the assets information in Inventory.

### Inventory:

A service storing information about the assets (Virtual Machines) discovered. Once discovery process completes, the customer can browse discovered assets and start planning migration.

#### Replication

This plugin replicate the data and copy and transfer the virtual machines data to the Object storage bucket.

### Migration project:

a “root folder” to manage migrations, can contain one or multiple migration plans.

### Migration plan:

A folder under a migration project, grouping the assets to be migrated together. Normally those assets would be managed together.

#### Agent Health Monitoring

This Plugin does help in the monitoring of the process running on the remote agent applicance and keep connecting to the Oracle cloud infrasturcture enviornment created in the OCI tenancy.



__OCI Object Storage:__ The OCI Object Storage offers the highest level of data resiliency by the backend system at the availability domain. The OCI Oject storage stored the VMDK of the replicated assets to the Object storage bucket.

# Work flow of OCM Service

High Level steps:

![Future State Architecture](image/On-Prem-OCM.jpg)

1. Once the OCM Environment is setup.The workflow is based on the following five modules that enable migration:

### Discovery
A virtual appliance is deployed in your on-premises environment.
The appliance launches two plugins - discovery and replication.
The discovery plugin searches for VMware virtual machines in the source environment using environment-specific connectors.
The replication plugin manages the replication of source assets snapshots from the source environment to OCI.

### Inventory

The inventory module retrieves metadata information that tracks the virtual machine's physical and runtime properties, such as operating system, hardware, and resource utilization. The module then stores them in the inventory service.

The inventory module is used to store information about virtual machines discovered in the on-premises environment that can be migrated. These machines are added to inventory by using API and importing the CSV file, or by running automated discovery in the external environment.

### Assessment and Planning
Oracle Cloud Migrations provides ongoing inventory analysis that contains statistics, summaries, and histograms about the virtual machines in your inventory.

A virtual machine contains metadata and metrics along with their history and how they are discovered or imported. Metadata history is tracked so that you can monitor a virtual machine's evolution over the course of their long-running migration. Hence, Oracle Cloud Migrations can highlight any changes that might require revisiting the migration plan.

Migration project A migration project is created that contains the migration plans for replicating the virtual machines.

Migration Plan A migration plan can group interrelated and dependent virtual machines that can be migrated together.

### Replication

VMware virtual machines reference a replication policy that describes how the machines are migrated into OCI.

Replication plugin manages the replication of external assets snapshots. Oracle Cloud Migrations determines and manages full-image or incremental virtual-machine snapshots. For information about replication, see Understanding VM Replication.

### RMS Stack

* Once the replication is complete. RMS Stack will created under migration project and click to Generate RMS Stack. We need to deploy the RMS stack once it is created.

### Hydration agent

A hydration agent is a temporary compute instance that is launched in your tenancy during the migration. A hydration agent reads and writes replicated source data from object storage to target boot or block volumes.

### Execution
Within a project, you create migration plans. A migration plan is a mapping of VMware virtual machines to target resource types in OCI. A migration plan provides the context to launch virtual machines, including compartment, subnets, and launch dependencies.

The virtual machines are replicated on OCI instances.

You can mark the project as complete. After a project is marked complete, Oracle Cloud Migrations decouples the production environment from the migration workflow and archives migrated inventory.


* Click Generate RMS Stack. We need to deploy the RMS stack once it wil completed.

## Oracle Cloud Migrations Terminologies

Review the following terms to understand the Oracle Cloud Migrations service.

* Agent dependency

Third-party libraries that are required for migration tasks. To comply with licensing terms, you must obtain these libraries separately and make them available to the remote agent appliance.

* Assets

The Oracle Cloud Migrations service works with multiple types of assets including virtual machines and their associated data disks. Assets are categorized depending on the stage of the migration workflow. Refer to the following asset types:

* External asset:

The external assets are hosted in an external environment outside Oracle Cloud Infrastructure (OCI). For example, a VMware vSphere environment that is located on-premises.

* Inventory asset:  

A representation of a resource that exists outside of OCI. These resources contain metadata, metrics, history, and how the physical or virtual entities are discovered and imported. Assets can be added to inventory by running discovery in the source environment, CSV import, or using the API.

* Migration asset:

A migration asset is defined by an inventory asset and an associated replication location for a migration project. It can only belong to a single migration project. Migration assets can be replicated manually or scheduled as part of a migration project.

* Target asset:

An asset in a migration plan that represents the deployment configuration, which launches an OCI native resource, and with that completing the migration of an external asset.

* Asset source

The asset source represents the connectivity information for a source environment that you define. An asset source can be an on-premises environment or another cloud environment, which is the source of the assets to be migrated to OCI.

* Discovery schedule

Defines the frequency at which a work request is created to refresh an asset source against a source environment. The work request adds new inventory assets and refreshes the metadata for existing inventory assets.

* External asset discovery
A process to ingest and store collected external asset metadata to inventory.

* External environment
An on-premises or cloud environment from which external assets are migrated to OCI.




R- Responsible, I- Informed, A- Accountable, C- Consulted

| Task                                           | Responsible (R) | Accountable (A) | Consulted (C) | Informed (I) |
|------------------------------------------------|------------------|------------------|----------------|---------------|
| Define project scope and objectives            | Consultant       | Account Cloud Engineer  | Team Members   | Stakeholders |
| Identify migration requirements                | Consultant       | Account Cloud Engineer  | Team Members   | Stakeholders |
| Analyze current infrastructure and applications| Consultant       | Account Cloud Engineer  | Team Members   | Stakeholders |
| Select appropriate Oracle cloud services       | Consultant       | Account Cloud Engineer  | Team Members   | Stakeholders |
| Develop migration plan and timeline            | Consultant       | Account Cloud Engineer  | Team Members   | Stakeholders |
| Allocate resources for migration               | Account Cloud Engineer | Account Cloud Engineer | Consultant     | Stakeholders |
| Execute migration plan                         | Team Members     | Account Cloud Engineer | Consultant     | Stakeholders |
| Monitor migration progress                     | Account Cloud Engineer | Account Cloud Engineer | Consultant     | Stakeholders |
| Resolve migration issues and escalations       | Team Members     | Account Cloud Engineer | Consultant     | Stakeholders |
| Validate successful migration                  | Team Members     | Account Cloud Engineer | Consultant     | Stakeholders |
| Document migration process and outcomes       | Team Members     | Account Cloud Engineer | Consultant     | Stakeholders |
| Conduct post-migration review                  | Consultant       | Account Cloud Engineer | Team Members   | Stakeholders |




Responsible (R): Individuals or roles responsible for completing the task.
Accountable (A): Individuals ultimately answerable for the task's completion or outcome.
Consulted (C): Individuals or roles to be consulted for their input or expertise.
Informed (I): Individuals or roles to be kept informed about the task's progress or outcome.



The participation of the following Customer stakeholders is required for the Service to be performed:

* Enterprise Architect
* Infrastructure Architect
* Backup/Recovery team leads
* VMware operations team leads
* Network Operations team leads

### Assumptions

* OCI Admin Access is provided to access the tenancy.
* The Fast Connect link with a minimum of 1 Gbps bandwidth is available beforehand for implementation to connect to Customer locations. OCI Fast Connect will be set up during the migration to handle the size of the workload to be migrated.
* Connection bandwidth available for data transfer during the migration will be available and will not depend (be limited) on a specific time window.
* Provided Lift effort is based on migration execution over Fast Connect link of min 1 Gbps.
* Post migration, Customer branches will connect to the environment using IPSec VPN.
* The CIDR which will be used for OCVS provisioning does not overlap with current on-premises network ranges and it is assumed that there is no requirement to extend networks between on-premises & cloud environments.
* There will be no dependency of the Lift migration project on a larger project context, i.e. timing and/or other project context.
* OCM will be deployed in the same tenancy in a OCI Region.
* Source Application/Database Source VMs are non-clustered.
* Inter-dependency of Application/database to be shared.
* Any downtime window required during migration and cut-over phases will be arranged by the Customer.
* There are no licensing constraints from Microsoft or any other software vendors. for example, Microsoft SQL Enterprise host-based unlimited license.
* The supplied sizing details of the cores are vCPUs and not actual physical cores.
* Customer will take care of the integration work required for different services post migrations of VMware workloads.
* Customer will have the necessary Oracle Support (MoS) contract for all the products that may/will be used during this project.
* Customer will be managing any other 3rd party vendors or suppliers.
* Customer will have adequate licenses for all the products that may/will be used during this project.
* Sequence of VM migration to be shared for each phase and agreed upon before delivery phase to accomplish delivery Schedule.
* It is assumed that all work will be done remotely and within either central European time or Indian standard time normal office working hours.
* Any problems, issues, errors, and anomalies to be addressed through MOS SRs & will continue to be owned by the Customer.
* Details and Naming convention will be provided for OCI resources.
* Any additional effort outside of the scope of this proposal will be managed by change control and mutually agreed upon by both Oracle and Customer.

## Windows Licensing

Oracle Cloud Migration Service (OCM) supports Bring Your Own License (BYOL) for Windows virtual machines, it's likely that the support may vary depending on the specific version of Windows being migrated and the licensing agreements in place.

For certain versions of Windows, customers may be able to migrate to dedicated virtual machine hosts on Oracle Cloud Infrastructure (OCI) to enable BYOL. Dedicated VM hosts provide physical servers dedicated to a single customer's use, offering enhanced control and security.

Customers should review their licensing agreements and consult with Oracle support or their Oracle account representative to determine the specific options available for migrating Windows virtual machines to OCI with BYOL. Additionally, they should ensure compliance with licensing requirements to avoid any potential issues.


&nbsp;

**Note:**

For more information regarding the OCM Service, please refer to [OCM Documentation.](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-overview.htm)

&nbsp;

How to setup the OCM [Step by Step Guide to Setup the OCM](https://docs.oracle.com/en/learn/ocm-migrate-on-prem-vm/index.html#migrate-vms-from-an-on-premises-vmware-environment-to-oracle-cloud-compute-vms-using-oracle-cloud-migrations-service)




 &nbsp;
 &nbsp;

# Conclusion

&nbsp;



&nbsp;

Acknowledgments
•	Author - Ravindra Kumar (Cloud VMware Solutions Specialist)
