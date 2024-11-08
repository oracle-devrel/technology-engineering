# Document Control
<!--
| Role  | RACI |
|:------|:-----|
| ACE   | R/A  |
| Impl. | None |
| PPM   | None |
-->

*Guide:*

*The first chapter of the document describes the metadata for the document. Such as versioning and team members.*

## Version Control
<!-- GUIDANCE -->
<!--
A section describing the versions of this document and its changes.
-->

| Version | Author       | Date                | Comment         |
|:--------|:-------------|:--------------------|:----------------|
| 1.0     | Name Surname | October 29th, 2024  | Initial version |
| 1.1     | Name Surname | Novermber 8th, 2024 | Updated         |

## Team
<!-- GUIDANCE -->
<!--
A section describing the versions of these documents and their changes.
-->

| Name         | E-Mail              | Role                   | Company |
|:-------------|:--------------------|:-----------------------|:--------|
| Name Surname | example@example.com | Accound Cloud Engineer | Oracle  |
| Name Surname | example@example.com | Lift Specialist        | Oracle  |

## Abbreviations and Acronyms
<!-- Guidance -->
<!--
Abbreviation: a shortened form of a word or phrase.
Acronyms: an abbreviation formed from the initial letters of other words and pronounced as a word (e.g. ASCII, NASA ).
Maintain a list of terms, if needed. Use this internal page to find and translate abbreviations and acronyms: https://apex.oraclecorp.com/pls/apex/f?p=15295:1:8900541624336:::::
-->


| Term | Meaning                                 |
|:-----|:----------------------------------------|
| OCM  | Oracle Cloud Migration Service          |
| OCI  | Oracle Cloud Infrastructure             |
| VCN  | Virtual Cloud Network                   |
| IAM  | Identity and Access Management          |
| VDDK | VMware Virtual Disk Development Kit   | |
| VDS  | VMware vSphere Distributed Switch       |
| ESXi | VMware vSphere Hypervisor (ESXi)        |
| VC   | VMware vCenter Server                   |
| OSS  | Object Storage Service                  |
| RMS  | Resource Manager Stack                  |

## Document Purpose

This document does provide the highlevel overview of the Oracle Cloud migration service known as OCM.

Oracle Cloud Migration Service is a suite of tools and services designed to facilitate the migration of workloads, applications, and data from on-premises environments to Oracle Cloud Infrastructure (OCI). Specifically, for moving on-premises vSphere virtual machines to OCI, Oracle provides tools and support to streamline the migration process.

Overall, Oracle Cloud Migration Service simplifies the process of migrating on-premises vSphere virtual machines to OCI, enabling customers to leverage the benefits of cloud infrastructure while minimizing downtime and risk.


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

A Company Making Everything is located in Frankfurt, Germany, and is the largest consumer electronics company. A Company Making Everything has 2500 employees at this location, generating millions of dollars in sales. There are subsidiaries under A Company Making Everything corporate family which contribute to overall sales for the parent organization.

A Company Making Everything is an existing Oracle Cloud customer and currently consuming various OCI services such as network, compute, storage, and databases in OCI Frankfurt Region. The current Production, Test, Dev & DMZ environments are hosted in an on-premises infrastructure with physical and VMware servers. The customer has a cloud and digital transformation strategy and would like to exit the data center by moving the on-premises workloads to the cloud.

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

A Company Making Everything is running a strategic program in FY24 called EXAMPLE. As part of their initiative, one pillar is dedicated to their IT cost saving. A Company is planning to reduce their IT estate spending by 15% in the current FY. Oracle can help them by reducing the VMware deployment complexity and operations while optimizing IT costs. A company's IT department wants to innovate other LoBs and enable quick-time-to-market for various applications and business needs. This allows ${doc.customer.name} to stay ahead in a competitive market.

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

**Thus, the objectives of this document are to:**

1.  Review together the existing on-premise architecture, map it to relevant Oracle OCI services, and propose a high-level tailored cloud architecture design.
2.  Define the Oracle Cloud Lift Services scope to help A Company Making Everything to physically migrate the agreed workload to the target cloud platform.

**The goals of this document are to:**

Additionally, these are the high-level goals for this document:

1.  Provide the architecture guidelines as per A Company Making Everything needs for the target cloud OCI architecture.
2.  Fitting the solution into A Company Making Everything the OCI ecosystem.
3.  Address all OCI-related aspects at security, network, compute, storage, and other levels for implementing the target cloud architecture post migration using Oracle Cloud Migration.
4.  Analyze and capture the design decisions and migration requirements to migrate VMware VMs to OCI.
5.  Define the scope of the potential LIFT services migration of the A Company Making Everything workloads to Oracle Cloud.

## Non-Functional Requirements

### Regulations and Compliance

At the time of this document creation, no Regulatory and Compliance requirements have been specified.

### Environments

| Environment | Target Size of VMs | Location | Scope           |
|:------------|:-------------------|:---------|:----------------|
| ENV NAME    | 100%               | LOCATION | Workload - Lift |
| ENV NAME    | 80%                | LOCATION | Workload - Lift |

### High Availability and Disaster Recovery Requirements

At the time of this document creation, no high availability and disaster recovery requirements have been specified.

### Security Requirements

At the time of this document creation, no security requirements have been specified.

# Current State Architecture   

The current state architecture covers the current on-premises workloads.

## Current State VMware IT Architecture

Current environment is running in a data center (DC LOCATION) based on hardware (HARDWARE MODELS) infrastructure and VMware vSphere Hypervisor (ESXi).

__The Current VMware footprint consists of:__

-	VMware vSphere with 7.0 release
-	VMware vSAN Storage
- VMware NSX or NSX-T as a networking solution
-	Backup Solution

Below is the current high-level architecture of the customer's on-premises VMware environment.

![Current State Architecture](image/sample-currentstatearchitecture.jpg)

## Current VMware Inventory On-premises

The Virtual Machines identified for migration to OCI.

__VM resource allocations per location:__

| Location      | Type             | Total vCPU Cores | Total Memory (GB) | Used Storage (GB) | Total Storage (GB) |
|:--------------|:-----------------|:-----------------|:------------------|:------------------|:-|
| Location Name | Virtual Machines | 550              | 1800              | 23580             | 30000 |
| Location Name | Virtual Machines | 250              | 1000              | 12000             | 15000 |

__Operating Systems:__

The operating system supported by OCM service is mentioned in the OCM documentation supported guest operating system. Few of the examples are below. This is suggested to refer to the Oracle Cloud migration service official Documentation.

- Windows Server 2019
- Oracle Linux 8
- Red Hat Linux
- Windows Server 2012

# Future State Architecture

The future state architecture of the current on-premises VMware workloads will be based on the OCI native compute VMs, OCI networking and storage.


## Solution requirements with Oracle Cloud Migration

Below is the current high-level architecture of the customer's on-premises VMware environment and OCM in Oracle cloud Infrastructure.

![Future State Architecture](image/Futurestate-ocm-Architecture.jpg)


### Requirements for Setting up OCM Service.

- Tenancy Compartment Design
- Tenancy Users and Groups
- Secrets and Vaults
- Service Policies
- Buckets  
- vCenter Requirements
- Network Connectivity - We recommend to use high-spped low latency network connectivity.
- vSphere permissions
- VDDK & Change Block Tracking

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

#### Networking

The architecture has the following components:

-   **On-premises Network** - This network is the local network used by your organization. It is one of the spokes of the topology.

-   **Region** - An Oracle Cloud Infrastructure region is a localized geographic area that contains one or more data centers, called availability domains. Regions are independent of other regions, and vast distances can separate them (across countries or even continents).

-   **Virtual Cloud Network (VCN)** - A VCN is a customizable, private network that you set up in an Oracle Cloud Infrastructure region. Like traditional data center networks, VCNs give you complete control over your network environment. You can segment VCNs into subnets, which can be scoped to a region or an availability domain. Both regional subnets and availability domain-specific subnets can coexist in the same VCN. A subnet can be public or private.

-   **Security List** - For each subnet, you can create security rules that specify the source, destination, and type of traffic that must be allowed in and out of the subnet.

-   **Network Security Group (NSG)** - NSGs act as virtual firewalls for your cloud resources. With the zero-trust security model of Oracle Cloud Infrastructure, all traffic is denied, and you can control the network traffic inside a VCN. An NSG consists of a set of ingress and egress security rules that apply to only a specified set of VNICs in a single VCN.

-   **Route Table** - Route tables contain rules to route traffic from subnets to destinations outside a VCN, typically through gateways.

-   **Dynamic Routing Gateway (DRG)** - The DRG is a virtual router that provides a path for private network traffic between a VCN and a network outside the region, such as a VCN in another Oracle Cloud Infrastructure region, an on-premises network, or a network in another cloud provider.

-   **Bastion Host** - The bastion host is a compute instance that serves as a secure, controlled entry point to the topology from outside the cloud. The bastion host is provisioned typically in a demilitarized zone (DMZ). It enables you to protect sensitive resources by placing them in private networks that can't be accessed directly from outside the cloud. The topology has a single, known entry point that you can monitor and audit regularly. So, you can avoid exposing the more sensitive components of the topology without compromising access to them.

-   **VPN Connect** - VPN Connect provides site-to-site IPSec VPN connectivity between your on-premises network and VCNs in Oracle Cloud Infrastructure. The IPSec protocol suite encrypts IP traffic before the packets are transferred from the source to the destination and decrypts the traffic when it arrives.

-   **FastConnect** - Oracle Cloud Infrastructure FastConnect provides an easy way to create a dedicated, private connection between your data center and Oracle Cloud Infrastructure. FastConnect provides higher-bandwidth options and a more reliable networking experience when compared with internet-based connections.

#### Network connectivity options (on-premises to OCI)

##### IPSec VPN

IPSec VPN architecture has the following components:

-   **VPN Connect** - Function that manages IPSec VPN connections to your tenancy.

-   **Customer-Premises Equipment (CPE)** - An object that represents the network asset that lives in the on-premises network and establishes the VPN connection. Most border firewalls act as the CPE, but a separate device (like an appliance or a server) can be a CPE.

-   **Internet Protocol Security (IPSec)** - A protocol suite that encrypts IP traffic before packets are transferred from the source to the destination.

-   **Tunnel** - Each connection between the CPE and Oracle Cloud Infrastructure.

-   **Border Gateway Protocol (BGP) routing** - Allows routes to be learned dynamically. The DRG dynamically learns the routes from your on-premises network. On the Oracle side, the DRG advertises the VCN's subnets.

-   **Static Routing** - When you create the VPN connection, you inform the existing networks on each side. Changes are not learned dynamically.

IPSec VPN will be used to provide for the connection between A Company Making Everything" data center and Oracle OCI Public cloud region for standard day-to-day operational purposes. Based on the current information IPSec connection is already established.

##### Fast Connect

To set up a FastConnect connection between your on-premises network and Virtual Cloud Network (VCN) has following key components:

-   **Border Gateway Protocol (BGP) routing** - Allows routes to be learned dynamically. The DRG dynamically learns the routes from your on-premises network. On the Oracle side, the DRG advertises the VCN's subnets.

-   **Private Peering** - Extends existing infrastructure by using private IP addresses.

-   **Public Peering** - Allows public Oracle Cloud Infrastructure services to be accessed using a private connection instead of the internet.

-   **Virtual Circuit** - The private path used to connect on-premises and Oracle Cloud Infrastructure. It can include multiple lines, physical or logical, depending on the requirements and capabilities of the line provider.

Fast Connect will be used to provide for the connection between A Company Making Everything" data center and Oracle OCI Frankfurt cloud region for the period migrations of VMs from on-premise to Oracle cloud. It is a requirement to use Fast Connect at least for the period of workload migration.

# Components Overview of Oracle Cloud Migration Service.

This section describes the OCM Components and various phases:

__Oracle Cloud Migration Service (OCM):__ The OCI native services such Like OCM is highly available since this is a SAAS offering.

__OCB Agent VM:__ The OCM service does provide the OCB agent pre-built virtual Machine OVA files to be deployed and configured in on-premises vSphere Environment. There will be three different plugins of this OCB agent.

__OCI Object Storage:__ The OCI Object Storage offers the highest level of data resiliency by the backend system at the availability domain. The OCI Oject storage stored the VMDK of the replicated assets to the Object storage bucket.

__Discovery:__ This plugin gather the information about the virtual machines data and represent the assets information in Inventory.

__Inventory:__ A service storing information about the assets (Virtual Machines) discovered. Once discovery process completes, the customer can browse discovered assets and start planning migration.

__Replication:__ This plugin replicate the data and copy and transfer the virtual machines data to the Object storage bucket.

__Migration project:__ A “root folder” to manage migrations, can contain one or multiple migration plans.

__Migration plan:__ A folder under a migration project, grouping the assets to be migrated together. Normally those assets would be managed together.

__Agent Health Monitoring:__ This Plugin does help in the monitoring of the process running on the remote agent applicance and keep connecting to the Oracle cloud infrasturcture enviornment created in the OCI tenancy.

# Oracle Cloud Migration Service Workflow

This section describes the high level migration workflow of the OCM service:

![Future State Architecture](image/On-Prem-OCM.jpg)

Once the OCM Environment is setup.The workflow is based on the following five modules that enable migration:

## Phase 1: Discovery
A virtual appliance is deployed in your on-premises environment.
The appliance launches two plugins - discovery and replication.
The discovery plugin searches for VMware virtual machines in the source environment using environment-specific connectors.
The replication plugin manages the replication of source assets snapshots from the source environment to OCI.

## Phase 2: Inventory

The inventory module retrieves metadata information that tracks the virtual machine's physical and runtime properties, such as operating system, hardware, and resource utilization. The module then stores them in the inventory service.

The inventory module is used to store information about virtual machines discovered in the on-premises environment that can be migrated. These machines are added to inventory by using API and importing the CSV file, or by running automated discovery in the external environment.

## Phase 3: Assessment and Planning
Oracle Cloud Migrations provides ongoing inventory analysis that contains statistics, summaries, and histograms about the virtual machines in your inventory.

A virtual machine contains metadata and metrics along with their history and how they are discovered or imported. Metadata history is tracked so that you can monitor a virtual machine's evolution over the course of their long-running migration. Hence, Oracle Cloud Migrations can highlight any changes that might require revisiting the migration plan.

Migration project A migration project is created that contains the migration plans for replicating the virtual machines.

Migration Plan A migration plan can group interrelated and dependent virtual machines that can be migrated together.

## Phase 4: Replication

VMware virtual machines reference a replication policy that describes how the machines are migrated into OCI.

Replication plugin manages the replication of external assets snapshots. Oracle Cloud Migrations determines and manages full-image or incremental virtual-machine snapshots. For information about replication, see Understanding VM Replication.

## Phase 5: RMS Stack

Once the replication is complete. RMS Stack will created under migration project and click to Generate RMS Stack. We need to deploy the RMS stack once it is created.

## Phase 6: Hydration agent

A hydration agent is a temporary compute instance that is launched in your tenancy during the migration. A hydration agent reads and writes replicated source data from object storage to target boot or block volumes.

## Phase 7: Execution

Within a project, you create migration plans. A migration plan is a mapping of VMware virtual machines to target resource types in OCI. A migration plan provides the context to launch virtual machines, including compartment, subnets, and launch dependencies.

The virtual machines are replicated on OCI instances.

You can mark the project as complete. After a project is marked complete, Oracle Cloud Migrations decouples the production environment from the migration workflow and archives migrated inventory.


Click Generate RMS Stack. We need to deploy the RMS stack once it wil completed.

## Oracle Cloud Migrations Terminologies

Review the following terms to understand the Oracle Cloud Migrations service.

* Agent dependency: Third-party libraries that are required for migration tasks. To comply with licensing terms, you must obtain these libraries separately and make them available to the remote agent appliance.

* Assets: The Oracle Cloud Migrations service works with multiple types of assets including virtual machines and their associated data disks. Assets are categorized depending on the stage of the migration workflow. Refer to the following asset types:

* External asset: The external assets are hosted in an external environment outside Oracle Cloud Infrastructure (OCI). For example, a VMware vSphere environment that is located on-premises.

* Inventory asset:  A representation of a resource that exists outside of OCI. These resources contain metadata, metrics, history, and how the physical or virtual entities are discovered and imported. Assets can be added to inventory by running discovery in the source environment, CSV import, or using the API.

* Migration asset: A migration asset is defined by an inventory asset and an associated replication location for a migration project. It can only belong to a single migration project. Migration assets can be replicated manually or scheduled as part of a migration project.

* Target asset: An asset in a migration plan that represents the deployment configuration, which launches an OCI native resource, and with that completing the migration of an external asset.

* Asset source: The asset source represents the connectivity information for a source environment that you define. An asset source can be an on-premises environment or another cloud environment, which is the source of the assets to be migrated to OCI.

* Discovery schedule: Defines the frequency at which a work request is created to refresh an asset source against a source environment. The work request adds new inventory assets and refreshes the metadata for existing inventory assets.

* External asset discovery: A process to ingest and store collected external asset metadata to inventory.

* External environment: An on-premises or cloud environment from which external assets are migrated to OCI.

## Summary Of Target Architecture Sizing

- OCM will provide recommendations on sizing of the OCI compute VM and the shape.
- The recommendations can be ignored and you can use any OCPU, Memory and Storage configuration for the migrated VM.

**BoQ Notes:**

1.  Bring Your Own License (BYOL) of Microsoft Windows should be validated with Microsfoft.

| Part \# | Product Name                       | Metric                                  | Quantity |
|:--------|:-----------------------------------|:----------------------------------------|:-|
| BXXXXX  | OCI Compute Flex Shape             | OCPU per Hour                           | 208 |
| XXXXXX  |                                    | OCPU Per Hour                           | 1 |
| B91628  | OCI Object Storage                 | Gb per month                            | 52000 |
| B91627  | OCI Object Storage Requests        | 10K requests per month (first 50k free) | 1 |
| B91961  | OCI Block Volume Storage           | Gb per month                            | 20000 |
| B91962  | OCI Block Volume Performance Units | Gb per month                            | 200000 |
| XXXXX   | OCI FastConnect 1 x 10 Gbps        | Port per hour                           | 1 |

# Project Implementation (Only for Oracle Implementations!)

## Solution Scope

### Disclaimer

As part of the Oracle Lift Project, any scope needs to be agreed upon by both the customer and Oracle. A scope can change but must be confirmed again by both parties. Oracle can reject scope changes for any reason and may only design and implement a previously agreed scope. A change of scope can change any previously agreed milestone and needs to be technically feasible.

All items not explicitly stated to be within the scope of the Lift project will be considered out of scope. Oracle recommends the use of professional services to implement extensions or customizations beyond the original scope, as well as to operate the solution, with an Oracle-certified partner.

### Overview

Below is a suggested outline for the Workload Architecture and Oracle Cloud Lift engagement in the context of A Company Making Everything VMs migration to OCI.

-   **Workload Architecture**

This team is involved in the production of specific implementation deliverables, as well as with the respective tasks for information gathering, document production, review, etc. The deliverables of this team are used as input for the implementation tasks, architecture governance, and any respective business case evaluation.

-   **Cloud Lift Services**

This team is responsible for setting up a target OCM environment and the technical work performed during the migration that in case of A Company Making Everything will consist of the deployment of the agreed scope of the target workload. These services will be delivered by a combination of on-shore and off-shore Oracle resources.

### Business Value

The Oracle Lift service brings several benefits to this project. All the activities mentioned within the scope will ensure the deployment of workload as per Oracle's best practices. As a tried and tested methodology by many customers, Oracle Lift brings the speed of deployment resulting in successful projects without any setbacks. Oracle Lift services will bring value to the overall project provisioning OCI environments for the application workload.

Oracle Cloud Lift services provide guidance from cloud engineers and project managers on planning, project management, architecting, deploying, and managing cloud migrations.

### Success Criteria

The project success criteria are based on the configuration of the Oracle Cloud Migration Service in the Customer's Oracle Cloud Infrastructure tenancy and successful migration of the VMs from on-premises VMware to OCI native VMs. A Company Making Everything applications and database servers will be migrated to Oracle Cloud Infrastructure within the agreed scope and migration window and prepared to execute in this new technical environment. A Company Making Everything will be provided with the knowledge needed to be able to independently operate the environment.

## Workplan

### Deliverables

The following are the project deliverables:

-   Workload architecture document.
-   Knowledge sharing session.

### Included Activities

Following high-level scope lift scope:

-   Deploy and configure OCB agents.
-   Assist in setting up Fast Connect connection.
-   Agreed scope of workload migration.

The following high-level Activities will be carried out by Lift:

-   OCI Landing Zone design
-   One Fast Connect setup between on-premises and OCI before migration
-   OCB agent deployment and configuration
-   Migrate VMs using OCM
-   Post migration validation.
-   Any additional tooling to support overall migration as agreed in the design.



### Project Timeline

Insert project plan here

# RACI Matrix

The following RACI matrix is applicable for the OCM migration projects:

R- Responsible, I- Informed, A- Accountable, C- Consulted

| Task                                            | Responsible (R)        | Accountable (A)        | Consulted (C) | Informed (I) |
|:------------------------------------------------|:-----------------------|:-----------------------|:--------------|:-|
| Define project scope and objectives             | Consultant             | Account Cloud Engineer | Team Members  | Stakeholders |
| Identify migration requirements                 | Consultant             | Account Cloud Engineer | Team Members  | Stakeholders |
| Analyze current infrastructure and applications | Consultant             | Account Cloud Engineer | Team Members  | Stakeholders |
| Select appropriate Oracle cloud services        | Consultant             | Account Cloud Engineer | Team Members  | Stakeholders |
| Develop migration plan and timeline             | Consultant             | Account Cloud Engineer | Team Members  | Stakeholders |
| Allocate resources for migration                | Account Cloud Engineer | Account Cloud Engineer | Consultant    | Stakeholders |
| Execute migration plan                          | Team Members           | Account Cloud Engineer | Consultant    | Stakeholders |
| Monitor migration progress                      | Account Cloud Engineer | Account Cloud Engineer | Consultant    | Stakeholders |
| Resolve migration issues and escalations        | Team Members           | Account Cloud Engineer | Consultant    | Stakeholders |
| Validate successful migration                   | Team Members           | Account Cloud Engineer | Consultant    | Stakeholders |
| Document migration process and outcomes         | Team Members           | Account Cloud Engineer | Consultant    | Stakeholders |
| Conduct post-migration review                   | Consultant             | Account Cloud Engineer | Team Members  | Stakeholders |




- Responsible (R): Individuals or roles responsible for completing the task.
- Accountable (A): Individuals ultimately answerable for the task's completion or outcome.
- Consulted (C): Individuals or roles to be consulted for their input or expertise.
- Informed (I):
Individuals or roles to be kept informed about the task's progress or outcome.



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

### Transition Plan

#### Introduction

Following the deployment of the solution to Oracle Cloud Infrastructure by the Lift team, it is important to ensure a smooth handover to a technical team, or a partner. Lift values the continuation of the cloud journey and we focus our efforts to ensure you start with the best possible foundation, to set you up for success in OCI.

When Lift completes the deliverables as described in the [Workplan](#workplan) section of this document, Lift will hand over the controls of the new OCI environment.

A Company Making Everything, or a partner of your choice, will assume the ownership of the OCI tenancy and responsibility for further development of the OCI environment. From that moment forward, having completed the [Solution Scope](#solution-scope), Lift will disengage. For post-implementation support, Oracle provides you with three distinct resources:

1.  Oracle Account Cloud Engineer (ACE) – This is your first point of contact and will provide technical leadership and support for Oracle cloud technologies and your cloud transformation.
2.  Cloud Adoption Manager (CAM) - Introduces and plans operation monitoring and optimization advisory activities, and continues working with you on the next milestones. Please contact your ACE for further information.
3.  [My Oracle Support](https://support.oracle.com/portal/)

#### Transition Acceptance

When Lift completes the deliverables as specified in the [Workplan](#workplan) section of this document, a closure session will be scheduled within 1-2 weeks to recap the project and to hand it over to the accepting party. In the case of this project, the accepting party is A Company Making Everything. A Company Making Everything is now responsible for the OCI tenancy.

From this moment forward, the Oracle Lift team will fully remove their access from your OCI tenancy and provide the access credentials to the accepting party. This marks the completion of the Lift project. There is no sign-off signature required.

# Annex

## Oracle Security, Identity, and Compliance

Oracle Cloud Infrastructure (OCI) is designed to protect customer workloads with a security-first approach across compute, network, and storage – down to the hardware. It’s complemented by essential security services to provide the required levels of security for your most business-critical workloads.

-   [Security Strategy](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/security-strategy.htm) – To create a successful security strategy and architecture for your deployments on OCI, it's helpful to understand Oracle's security principles and the OCI security services landscape.
-   The [security pillar capabilities](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/security.htm#capabilities) reflect fundamental security principles for architecture, deployment, and maintenance. The best practices in the security pillar, help your organization to define a secure cloud architecture, identify and implement the right security controls, and monitor and prevent issues such as configuration drift.

## References

-   The Best Practices Framework for OCI provides architectural guidance about how to build OCI services in a secure fashion, based on recommendations in the [Best practices framework for Oracle Cloud Infrastructure](https://docs.oracle.com/en/solutions/oci-best-practices).
-   Learn more about [Oracle Cloud Security Practices](https://www.oracle.com/corporate/security-practices/cloud/).
-   For detailed information about security responsibilities in Oracle Cloud Infrastructure, see the [Oracle Cloud Infrastructure Security Guide](https://docs.oracle.com/iaas/Content/Security/Concepts/security_guide.htm).

## Compliance and Regulations

Cloud computing is fundamentally different from traditional on-premises computing. In the traditional model, organizations are typically in full control of their technology infrastructure located on-premises (e.g., physical control of the hardware, and full control over the technology stack in production). In the cloud, organizations leverage resources and practices that are under the control of the cloud service provider, while still retaining some control and responsibility over other components of their IT solution. As a result, managing security and privacy in the cloud is often a shared responsibility between the cloud customer and the cloud service provider. The distribution of responsibilities between the cloud service provider and the customer also varies based on the nature of the cloud service (IaaS, PaaS, SaaS).

## Additional Resources

-   [Oracle Cloud Compliance](https://www.oracle.com/corporate/cloud-compliance/) – Oracle is committed to helping customers operate globally in a fast-changing business environment and address the challenges of an evermore complex regulatory environment. This site is a primary reference for customers on the Shared Management Model with Attestations and Advisories.
-   [Oracle Security Practices](https://www.oracle.com/corporate/security-practices/) – Oracle’s security practices are multidimensional, encompassing how the company develops and manages enterprise systems, and cloud and on-premises products and services.
-   [Oracle Cloud Security Practices](https://www.oracle.com/corporate/security-practices/cloud/) documents.
-   [Contract Documents](https://www.oracle.com/contracts/cloud-services/#online) for Oracle Cloud Services.
-   [OCI Shared Security Model](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/security.htm#shared-security-model)
-   [OCI Cloud Adoption Framework Security Strategy](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/security-strategy.htm)
-   [OCI Security Guide](https://docs.oracle.com/en-us/iaas/Content/Security/Concepts/security_guide.htm)
-   [OCI Cloud Adoption Framework Security chapter](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/security.htm)
