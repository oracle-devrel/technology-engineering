---
doc:
    author: Manish Palaparthy, Grzegorz Reizer
    version: 1.1
    cover:
        title:
        - ${doc.customer.name}
        - Essbase
        subtitle:
        - Workload Architecture Document
        - Solution Definition and Design
    customer:
        name: A Company Making Everything
        alias: ACME
---

<!--
    Last Change: 30 June 2023
    Review Status: Live
    Based on WAD Template Version: 1.2
-->

# Document Control
<!-- GUIDANCE -->
<!--The first Chapter of the document, describes metadata for the document. Such as versioning and team members.
 -->


## Version Control
<!-- GUIDANCE -->
<!--
A section describing the versions of this document and it changes.

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

<!-- EXAMPLE / TEMPLATE -->
Version     | Author          | Date                    | Comment
:---        |:---             |:---                     |:---
1.0         | Name            | June 12th, 2023     | Initial version
2.0         | Name            | June 13th, 2023     | Draft for Review

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
Ada Lovelace   | ada.lovelace@acme.com     | Project Manager         | ACME
Mark Watson  | mark.watson@example.com     | Cloud Architect         | ACME

## Abbreviations and Acronyms
<!-- Guidance -->
<!--
Abbreviation: a shortened form of a word or phrase.
Acronyms: an abbreviation formed from the initial letters of other words and pronounced as a word (e.g. ASCII, NASA ).


Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

<!-- EXAMPLE / TEMPLATE -->
Term          | Meaning
:---          |:------
OCI           | Oracle Cloud Infrastructure
PROD          | Production
Dev           | Development
OEL           | Oracle Enterprise Linux

## Document Purpose
<!-- GUIDANCE -->
<!--
Describe the purpose of this document and the Oracle specific terminology, specifically around 'Workload' and 'Lift'.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

<!-- EXAMPLE / TEMPLATE -->
This document provides a high-level solution definition for the Oracle solution and aims at describing the current state, to-be state as well as a potential project scope and timeline. The intended purpose is to provide all parties involved a clear and well-defined insight into the scope of work and intention of the project.

The document may refer to a 'Workload', which summarizes the full technical solution for a customer (You) during a single engagement. The Workload is described in chapter [Workload Requirements and Architecture](#workload-requirements-and-architecture). 

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

## Executive Summary
<!-- GUIDANCE -->
<!--
A section describing the Oracle differentiator and key values of the solution of our solution for the customer, allowing the customer to make decisions quickly.


Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
ACE   | R
-->
The scope of this project is to deliver a working **Test environment including one deployment of Essbase 21c marketplace** in OCI.

Customer's on-premises Essbase deployments can be migrated to run on Oracle Cloud Infrastructure without requiring significant configuration, integration, or process changes. The resulting implementation will be more flexible and more reliable than on-premises or other cloud deployments. Oracle has a validated solution to accomplish these goals, quickly and reliably. This solution includes procedures, supporting Oracle Cloud Infrastructure platform services, and reference architectures. These consider real production needs, like security, network configuration, disaster recovery (DR), identity integration, and cost management.

By moving Essbase systems to Oracle Cloud Infrastructure the following benefits could be realized:

1. Lower total cost of ownership (TCO) than on-premises deployments
2. Managing and reducing CAPEX, and ensuring that the data centers you maintain are efficient, while eliminating server hardware, and taking advantage of cloud flexibility where possible
3. Rapid in-place technology refresh
4. Proactive monitoring of usage and costs
5. Scaling up or down to handle business growth or workload bursts

## Workload Business Value
<!-- GUIDANCE -->
<!--
A clear statement of specific business value as part of the full workload scope. Try to keep it SMART: Specific, Measurable, Assignable, Realistic, and Time-Related - Agree the SMART business value with the customer. Keep it business focused, and speak the language of the LOB which benefits from this Workload: "Increase Customer Retention by 3% in the next year" or "Grow Customer Base with Executive Decision-Making from our Sales and Support Data". Avoid technical success criteria such as "Migrate App X to Oracle Cloud" or "Provision 5 Compute Instances". Avoid Oracle success criteria and language "Get Workload Consuming on OCI".


Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
ACE   | R
-->
Customer has been using Essbase for more than X years and is one of the key strategic applications that is used to analyze data and support enterprise-wide planning, budgeting, and forecasting. Customer intends to improve the overall performance and availability of the Essbase applications to enable faster modeling and decision making. With Oracle Cloud Infrastructure, customer benefits by eliminating hardware management and flexible scaling options for increased usage during consolidation processes.

# Workload Requirements and Architecture

## Overview
<!-- GUIDANCE -->
<!--
Describe the Workload: What applications and environments are part of this Workload, what are their names? Lift will be scoped later and is typically a subset of the Workload. For example a Workload could exists of two applications, but Lift would only include one environment of one application. This Workload chapter is about the whole Workload and Lift will be described late in chapter [Scope](#scope).



Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->
The current project includes provisioning of the Oracle Cloud Infrastructure infrastructure and deploying Essbase 21c via MarketPlace.
This project also involves the migration of two Essbase applications from version 11.1.2.4 currently hosted on-premises and used by the customer.

The customer has 2 Essbase environments currently:

| Environment     | Description |
| -------- | ---------------- |
| PROD   | 1 single server deployed on Windows 2012 R2 STD with MS SQL Server  |
| DEV    | 1 single server deployed on Windows 2012 R2 STD with MS SQL Server   |


## Functional Requirements
<!-- GUIDANCE -->
<!--
Provide a brief overview of the functional requirements, the functional area they belong to, the impacted business processes, etc.

Provide a formal description of the requirements as 1. a set of Use Cases or 2. a description of Functional Capabilities or 3. a Requirement Matrix. The three descriptions are not mutually exclusive.

Some Workload team, especially the Analytics and Merging Tech teams, will create new application based on functional requirements, some Workload team will not touch the functional requirements at all and just change the platform under an application. But it is important to understand who is using the system and for what reason.

Recommended Chapter (Mandatory for Analytics and Emerging Tech)

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->
Oracle Essbase is a business analytics solution that uses a proven, flexible, best-in-class architecture for analysis, reporting, and collaboration. Oracle Essbase delivers instant value and greater productivity for your business users, analysts, modelers, and decision-makers, across all lines of business within your organization.

Oracle Essbase provides a complete set of tools and features for deriving and sharing data insights.
Oracle Essbase on Oracle Cloud Infrastructure (OCI) via Marketplace is a powerful analytic platform with robust new features added since Release 11g.

However, as part of the workload migration project, no functional changes are implemented to the Essbase applications. Please refer to official documentation for differences between Essbase 11g and Essbase 21c [here] (https://docs.oracle.com/en/database/other-databases/essbase/21/essoa/differences-essbase-11g-and-essbase-21c.html)


### Functional Capabilities
<!-- GUIDANCE -->
<!--
In specific cases, a set of Functional Capabilities can be represented in a Functional Decomposition Diagram. This is typical of Functional Analysis in System Engineering domain. For more information on Functional Analysis see, e.g. https://spacese.spacegrant.org/functional-analysis/.



Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

Oracle Essbase stands for Extended Spread Sheet Database. Essbase is an OLAP (On-line Analytic Processing) business analysis server technology that provides an environment for rapidly developing custom analytic applications, uses complex queries to analyze aggregated historical data from OLTP systems. Multidimensional analysis uses a database that is structured on business concepts and that is designed around business needs.

In addition, Essbase is built on middle tier application server (Weblogic) and DB tier.
Further information can be found [here](https://docs.oracle.com/en/database/other-databases/essbase/21/essst/what-is-oracle-essbase.html)


### Requirement Matrix
<!-- GUIDANCE -->
<!--
A Requirement Matrix can be used when the solution will be based on software capabilities already available in existing components (either custom or vendor provided). The Requirements Matrix is a matrix that is used to capture client requirements for software selection and to evaluate the initial functional “fit” of a vendor’s software solution to the business needs
of the client.

For example, rows can list required functional capabilities and columns can list available software components. Cells can contain a simple Y/N or provide more detail. The Requirements Matrix also is used to identify initial functional gaps or special software enhancements needed to enable each vendor’s software to fulfill the client’s desired system capabilities.



Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

|:-------------------------------------------------------------------------------------|:------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| :----------------------                                                              | :---------------------------------------------------- | :--------------------------------------------------                                                                                                                    |
| Essbase Server / Essbase Provider Services Web / Essbase Administration Services Web | Essbase (EPM) 11.1.2.4                    | Essbase 21c (21.X). EAS console functionalities have been replaced by Web based UI + Cube Designer                                                                     |
| Authentication                                                                       | EPM Shared Services security 11.1.2.4     | Identity Cloud Service (IDCS) proposed for the workload                                                                                                                |
| Database                                                                             |Oracle Database 19c                 | Oracle Autonomous Database (ATP) 19c proposed for the workload                                                                                                         |
| Operating System                                                                     | Microsoft Windows 2012 R2 Standard 64-bit | Oracle Linux 7.9 64-bit                                                                                                                                                |
| Browser                                                                              | **TBC BY THE CUSTOMER**                   | Firefox (79.0 64bit) or Chrome (Version 88.0.4324.150) or Edge Driver Version 88.0.705.63 (Official build) (64-bit) or Mac Safari Version 14.0 (15610.1.28.1.9, 15610) |
| Oracle Smart View                                                                    | **TBC BY THE CUSTOMER**                   | Latest Essbase 21c (21.3) is certified with **Oracle Smart View 21.1.0.0.0**                                                                                           |

## Non Functional Requirements
<!-- GUIDANCE -->
<!--
Describe the high-level technical requirements for the Workload. Consider all sub-chapters, but decide and choose which Non Functional Requirements are actually necessary for your engagement. You might not need to capture all requirements for all sub-chapters.

This chapter is for describing customer specific requirements (needs), not to explain Oracle solutions or capabilities.



Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

This section captures all the non-functional requirements of the workload migration project.

### Integration and Interfaces
<!-- GUIDANCE -->
<!--
A list of all the interfaces into and out of the defined Workload. The list should detail the type of integration, the type connectivity required (e.g. VPN, VPC etc) the volumes and the frequency
- list of integrations
- list of user interfaces


-->

This table lists the existing integrations/Interfaces with current Essbase On-Premises deployment.

**TBC BY THE CUSTOMER**


**The integrations/Interfaces are out of scope of the workload. No connectivity will be implemented with OnPremises Enterprise Applications for the Test environment for integration.**

### Regulations and Compliances
<!-- GUIDANCE -->
<!--
This section captures and specific regulatory of compliance requirements for the Workload. These may limit the types of technologies that can be used and may drive some architectural decisions.

If there are none, then please state None.


-->

At the time of this document creation, no Regulatory and Compliance requirements have been specified.

For documentation purpose, the list of frameworks for which an Oracle line of business has achieved a third-party attestation or certification for one or more of its services is public available on [Oracle Cloud Compliance](https://www.oracle.com/ae/corporate/cloud-compliance/) .

### Environments
<!-- GUIDANCE -->
<!--
A diagram or list detailing all the required environments (e.g. development, text, live, production etc).
- list each environment included in the scope
- map each environment to bronze/silver/gold MAA


-->

The following table lists all the environments (current + required) as part of the workload project. The scope column mentions whether the environment is included in the workload migration project scope or not, and also identifies if it is included within the Lift services scope or not.

| Name       | Size of Prod | Customer DC/ OCI Region | MAA | Scope        |
|------------|--------------|-------------------------|-----|--------------|
| Production | 100%         | Customer DC             | NA  | Not in Scope |
| DEV        | 25%          | Customer DC             | NA  | Not in Scope |
| Test       | **50%**      | Amsterdam               | NA  | Workload     |

### System Configuration Control Lifecycle
<!-- GUIDANCE -->
<!--
This section should detail the requirements for the development and deployment lifecycle across the Workload. This details how code will be deployed and how consistency across the environments will be maintained over future software deployment. This may include a need for CI/CD.
- will a CI/CD tool need access to deploy to the target environment
- does the customer require software to be delivered to a repository
- how will configuration and software be promoted through the environments



Oracle recommends the below approach to automate continuous delivery onto servers running on OCI for customer’s application:

- Git version management
- Automating deployment
- Automate LCM export

More details on automating the Infrastructure deployments on OCI for Hyperion reference architecture can be found [here](https://github.com/oracle-quickstart/oci-essbase).

More information on automating the Essbase installation can be found [here](https://docs.oracle.com/en/database/other-databases/essbase/21/essst/how-do-i-get-started.html).
-->

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


-->

The following table captures the RPO and RTO requirements of each of the environments for the workload.

Environment  |RPO   |RTO
--|---|--
TEST  | 24 Hours  |  4 Hours

**Backup requirements:**

Current Backup Schedule:

Currently, Essbase is backed up with some backup scripts once every day. Incremental backups once every day and log backups once every hour.

OCI Backup Requirements:

Essbase backup and restore planning is required at both the application and instance level to have full flexibility to manage the life cycle of the Essbase instances, and also to provide disaster recovery.

Backups of individual applications protect you from application failures or application artifact corruption, and can easily be migrated between servers. When you restore a single application, there is no disruption to user activity with other applications in your instance. Essbase application backups are taken using LCM export and import commands.

Use Essbase instance backups to restore all applications on your instance to a common point in time. Instance backups are primarily for disaster recovery, but are also appropriate when you want to migrate or restore all applications at once. Backups of Essbase on OCI depend on some details of the Essbase stack. A complete backup must protect all information that makes your Essbase deployment unique. Items you may be instructed to back up include:

* Relational database schemas which store some application, user and configuration information.
* Essbase application and database information stored on a block volume mounted as /u01/data.
* WebLogic domain and configuration information stored** on a block volume mounted as /u01/confg.


#### High Availability
<!-- GUIDANCE -->
<!--
A subsubsection, if cleaner separation of Resilience and Recovery into HA, DR, and Backup & Restore is needed.


-->

<!-- EXAMPLE / TEMPLATE -->
| Service Name        | KPI              | Unit    | Value |
|---------------------|------------------|---------|-------|
| Oracle DB           | Uptime           | percent | 99.98 |
| Essbase Application | Max Interruption | minutes | 20    |

#### Disaster Recovery
<!-- GUIDANCE -->
<!--
A subsubsection, if cleaner separation of Resilience and Recovery into HA, DR, and Backup & Restore is needed.


-->

<!-- EXAMPLE / TEMPLATE -->
| Service Name        | KPI | Unit  | Value |
|:--------------------|:----|:------|:------|
| Essbase Application | RTO | Hours | 24    |
| Essbase Application | RPO | Hours | 4     |

#### Backup and Restore
<!-- GUIDANCE -->
<!--
A subsubsection, if cleaner separation of Resilience and Recovery into HA, DR, and Backup & Restore is needed.


-->

<!-- EXAMPLE / TEMPLATE -->

When a single Essbase instance is deployed to an Autonomous Transaction Processing database, you can use scripts provided by Oracle to back up the entire database and the Essbase block volumes.

### Operating Model
<!-- GUIDANCE -->
<!--
This section captures requirements on how the system will be managed after implementation and migration. In the vast majority of cases, the solution will be handed back to the customer (or the customer's SI/partner), but in some cases, Oracle may also take on some sustaining responsibilities through ACS or OC

Also capture requirements for tools to monitor and manage the solution.


-->

The workload migration will be implemented by Customer/Partner/Oracle Consulting or a combination of these. Post implementation, the Hyperion environments in scope of the project will be handed over to the customer/partner/Oracle ACS team as agreed with the customer. Customer/Partner/Oracle ACS team will be responsible for managing and maintaining the Hyperion workload and OCI post implementation.

### Management and Monitoring
<!-- GUIDANCE -->
<!--
This subsection captures any requirements for integrations into the customer's existing management and monitoring systems - e.g. system monitoring, systems management etc. Also, if the customer requires new management or monitor capabilities, these should also be recorded.


-->

OCI can provide metrics automatically for many of the native resources. There is no need to install an agent on a block storage volume or VCN, as these resources will emit predefined metrics on their own.

The following table lists all the different kinds of metrics and logs that can be collected and used in monitoring the proposed solution:

| **Components**     | **Logs/Metrics** | **Agent Based** | **Types of data**                                                                                  |
| ------------------ | ---------------- | --------------- | -------------------------------------------------------------------------------------------------- |
| Audit              | Log              | No              | OCI Audit Log                                                                                      |
| VCN                | Metrics          | No              | VNIC traffic (packets), Security List statistics                                                   |
| VCN                | Logs             | No              | Flow logs                                                                                          |
| Compute            | Metrics          | Yes             | CPU, Disk, Memory, Network usage                                                                   |
| Block Storage      | Metrics          | No              | IOPS and throughput                                                                                |
| LBR                | Metrics          | No              | Typical performance metrics                                                                        |
| OS                 | Metrics          | Yes             | Process information                                                                                |
| OS                 | Logs             | Yes             | Syslogs and other defined logs, ex: ssh acces logs                                                 |
| Database           | Metrics          | Yes             | CPU, Memory, Disk usage, SQL performance, etc                                                      |
| Database           | Logs             | Yes             | DB, listener and audit logs                                                                        |
| Application server | Metrics          | Yes             | WLS and OHS specific metrics: response times, memory usage, etc. For ATP/ADW no agent is required. |
| Application server | Logs             | Yes             | WLS and OHS specific logs                                                                          |
| Browser            | Metrics          | No              | Response time and transaction correlation                                                          |

Oracle recommends leveraging Oracle Management Cloud which provides integrated monitoring across hybrid and multi-cloud environments. It performs monitoring through use of agents across various tiers from infrastructure to application performance, security, and even end-user activity. It also integrates with Oracle Enterprise Manager for Oracle Database performance and capacity analytics.

### Performance
<!-- GUIDANCE -->
<!--
The performance requirements cover all aspects related to the time required to perform a given operation. They can be measured in different ways, for example: (1) AvrgTime: average response time that can be accepted for a given online or real interactions (data retrieve, data insert, etc.) (2) MaxTime: maximum response time for the same operations defined for AvrgRtime The operations can be online (user interactions), offline (batch execution) or (near)realtime (messaging).


-->

<!-- EXAMPLE / TEMPLATE

_The table below lists indicative performance metrics that can be used to validate the performance of Hyperion application between source and target (OCI)._

<!-- EXAMPLE / TEMPLATE
Type		  | Operation				       | KPI		  | Unit	| Value	| Notes
---			  |---					           |---		    |---		|---	  |---
Online		| Data Load (FDMEE) | MaxTime	| sec		| TBD	  | Compare selected data load times between the source and target environments
Online		| Consolidation Time (HFM) | MaxTime	| sec		| TBD	  | Compare selected consolidation times between the source and target environments
Online    |	Run calculation in a webform (Planning)	 | MaxTime	| sec	| TBD	  | Compare calculation time for selected webforms between the source and target environments
Online    | Run selected calculations in Essbase application (Essbase)  | MaxTime  | sec  | TBD  |  Compare selected calculation time in Essbase applications between the source and target environments
-->

### Capacity
<!-- GUIDANCE -->
<!--
Capacity is a measure of the total workload the system can bear without affecting performance. There are many KPIs to measure capacity, depending on the system functionalities. Some of the most relevant KPIs are:
(1) MaxVol: maximum volume of data that can be stored in the system (can be different for different types of data, e.g. relational and file): **800-900GB** current database size (probably with significant waste of space)
(2) MaxFlow: maximum data flow (input/output) that can be managed by the system (can be two different numbers for each major system interface and/or operation): the current value has not been measured but is expected to be **at most a few GB.**
(3) MaxUser: maximum number of concurrent users (can be differentiated by user profile): up to **10 (number of registered users)**.

Recommended Chapter
-->

<!-- EXAMPLE / TEMPLATE -->
The following table indicates the current sizing available onpremises and also outlines any additional capacity requested by the customer or required for the workload migration to OCI. Incase of 1:1 sizing and no performance issues/growth considerations, the current capacity will be matched on OCI.

| System         | Capacity           | KPI                    | Unit | Value   | Notes                                                                                                                                 |
|:---------------|:-------------------|:-----------------------|:-----|:--------|:--------------------------------------------------------------------------------------------------------------------------------------|
| DB server      | DB size            | MaxVol                 | GB   | 11GB    | Metadata sizing stored on existing Production environment                                                                             |
| Essbase Server | Simultaneous users | Concurrent / Max Users | Nb   | 150/700 |                                                                                                                                       |
| Essbase Server | CPU                | usage                  | %    | 30      | Feedback from customer: cpu peak at 30% for evaluated period with Intel Xeon CPU E7-8870 v4@2.10GHz (2 processors - 40 virtual cores) |
| Essbase Server | Memory             | usage                  | %    | 24      | Feedback from customer for evaluated period for a total of 128GB RAM                                                                  |

### Security
<!-- GUIDANCE -->
<!--
Capture the non functional requirements for security related topics. Security is a mandatory subsection which is to be reviewed by the x-workload security team. The requirements can be separated into:
- Identity and Access Management
- Data Security

Other security topics, such as network security, application security or other can be added if needed.

Mandatory Chapter
-->

This section captures the security requirements from the customers for this workload:

* No Corporate Directory integration for Essbase on OCI
* SSL Offloading required for HTTPS access for end-users


#### Identity and Access Management
<!-- GUIDANCE -->
<!--
The requirements for identity and access control. This section describes any requirements for
authentication, identity management, single-sign-on and necessary integrations to retained customer systems
(e.g. corporate directories)
- Is there any Single Sign On or Active Directory Integration Requirement?
- Is the OS hardened if so please share the hardening guide line?


-->

OCI Identity and Access Management (IAM) is the access control plane for OCI and Oracle Cloud Applications. It’s the OCI-native authentication service and policy engine for OCI services that has been used to manage access to OCI resources such as networking, compute, storage, and analytics.
OCI IAM uses identity domains to provide identity and access management features such as authentication, single sign-on (SSO), and identity lifecycle management for Oracle Cloud as well as for Oracle and non-Oracle applications, whether SaaS, cloud hosted, or on premises.

Currently there isn't a requirement to federate users for this workload.

Temporary access to customer’s OCI tenancy will be available to the implementation team for their scope detailed later in this document. OCI implementation will adopt the tenet of no access by default and least privilege for any access configured.

#### Data Security
<!-- GUIDANCE -->
<!--
Capture any specific or special requirements for data security. This section should also describe any additional constraints such as a requirement for data to be held in a specific locations or for data export restrictions

Recommended Chapter
-->

## Constraints and Risks
<!-- GUIDANCE -->
<!--
Constraints are limitations which will impact the resulting project or Solution Architecture. It is a technology- or project-related condition or event that prevents the project from fully delivering the ideal solution to customers and end-users. Constraints can be identified on our customer, partner or even Oracle's side.

A project risk is an uncertain event that may or may not occur during a project.

Describe constraints and risks affecting the Workload and possible Logical Solution Architecture. These can be of technical nature, but might also be non-technical. Consider: budgets, timing, preferred technologies, skills in the customer organization, location, etc.

Recommended Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->
Name                | Description                                    | Type           | Impact                         | Mitigation Approach
:---                |:---                                            |:---            |:---                              |:---
OCI skills          | Limited OCI skills in customers organization   | Risk     | No Operating Model                | Involve Ops partner, for example Oracle ACS
Team Availability  | A certain person is only available on Friday CET time zone  | Constraint  | | Arrange meetings to fit that persons availability
Access Restriction  | We are not allowed to access a certain tenancy without customer presence  | Constraint   | | Invite customer key person to implementation sessions

## Current State Architecture
<!-- GUIDANCE -->
<!--
Provide a high-level logical description of the Workload current state. Stay in the Workload scope, show potential integrations, but do not try to create a full customer landscape. Use architecture diagrams to visualize the current state. I recommend not putting lists of technical resources or dependencies here. Refer to attachments instead.

Recommended Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

This section describes the current state architecture and environments.

| Environment | Description                                                  |
|:------------|:-------------------------------------------------------------|
| PROD        | Microsoft SQL Server 2012, single application node EPM 11.1.2.4 on Windows 2012 R2 Standard Edition 64-Bit  |
| DEV         | Microsoft SQL Server 2012, single application node EPM 11.1.2.4 on Windows 2012 R2 Standard Edition 64-Bit  |


The current Essbase deployment is depicted below.

![Current Functional state Architecture](images/Current-Functional-Diagram-Onprem.png)

## Future State Architecture
<!-- GUIDANCE -->
<!--
The Workload Future State Architecture can be described in various forms. In the easiest case we  just describe a Logical Architecture, possibly with a System Context Diagram.

Additional architectures, in the subsections, can be used to describe needs for specific workloads or for non Lift engagements.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

This section describes the future state logical and physical deployment architecture of the Essbase application on Oracle Cloud Infrastructure and also lists the environments.

| Environment | Description                                                                                                 |
|:------------|:------------------------------------------------------------------------------------------------------------|
| TEST        | Public Load Balancer, Oracle ATP, single instance Essbase 21c MarketPlace (OEL) |

### Logical Architecture
<!-- GUIDANCE -->
<!--
Use [System Context Diagram](https://online.visual-paradigm.com/knowledge/system-context-diagram/what-is-system-context-diagram/) to show integration for the Workload solution.

Provide a high-level logical Oracle solution for the complete Workload. Indicate Oracle products as abstract groups, and not as a physical detailed instances. Create an architecture diagram following the latest notation and describe the solution.


Mandatory Chapter
-->

Based on the customer requirements, the future state logical architecture of Essbase on OCI is depicted below.

![Future Logical Architecture](images/Future-Functional-Diagram-OCI.png)

The main building blocks that compose this cloud architecture:

* __Essbase 21c__: The targeted version of Essbase on OCI will be Essbase 21C (21.3). Essbase 21c will be deployed via Oracle Cloud Infrastructure Marketplace.

* Database for Essbase metadata: Autonomous Database using the __Autonomous Transaction Processing workload__ (ATP). ATP is proposed to evaluate exclusive functionalities for federated partitions. ATP is a managed database integrated with Object Storage and optimized for analytical queries. Federated partitions enable to integrate Essbase cubes with Autonomous Data Warehouse, to combine Essbase's analytical power with the benefits of Autonomous Database.

### Physical Architecture
<!-- GUIDANCE -->
<!--

The Workload Architecture is typically not described in a physical form. If we deliver a Lift project, the scoped Lift Project in chapter 4 includes the physical architecture.

Nevertheless, an architect might want to describe the full physical Workload here, if this is a non-Lift project or if 3rd party implementation partner implement the non Lift environments.

Recommended Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

Essbase sizing on OCI for **Test environment** (current Workload) is reflected in the below table "Sizing Inputs" for the Test environment.

| Description                                                     | Value                                                                      |
|-----------------------------------------------------------------|----------------------------------------------------------------------------|
| Number of Expected Concurrent Users                             | 10 peak                                                                     |
| Bastion?                                                        | **Bastion Host on Windows proposed for orchestration/integration testing** |
| Number of Planned Essbase Databases                             | 2 monthly reporting apps                                                   |
| Avg Size of Planned Essbase Database (in GB)                    | 15GB                                                                       |
| Number of Essbase Database Planned to be Loaded from Flat Files | **TBC**                                                                    |
| Number of Planned Monthly Database Backups (ATP/DBCS)           | **TBC** N/A (Test environment)                                             |
| Additional Planned Custom Object Storage (in GB)                | **TBC** N/A (Test environment)                                             |
| Number of Planned Monthly Essbase Backups                       | **TBC** N/A (Test environment)                                             |
| % Planned Usage of Block Data Volume                            | **TBC** N/A (Test environment)                                             |
| # of Planned Essbase Instances                                  | **TBC**  1                                                                 |
| Share ATP/DBCS for Essbase Instance Repository?                 | **TBC**  No                                                                |
| Include a Load Balancer?                                        | Yes                                                                        |
| Load Balancer Shape                                             | Flexible Shape                                                             |
| Key Management System                                           | **TBC**  No (Test environment)                                             |


The diagram below depicts Physical architecture.

![Future State Physical Architecture](images/Future-Technical-Diagram-OCI.png)

* **One instance of __Essbase 21c__** will be provisioned in a private subnet in a dedicated compartment.
* **One instance of Autonomous Database ATP** will be provisioned with a private endpoint in a dedicated compartment.
* The other OCI services are already ready to use when the tenancy was created: Oracle Cloud Infrastructure Object Storage, Oracle Cloud Infrastructure Logging, Oracle Cloud Infrastructure Monitoring, Oracle Identity Cloud Service and Identity and Access Management.

<!--### Data Architecture
<!-- GUIDANCE -->
<!--
Show how data is acquired, transported, store, queried, and secured as in scope of this Workload. This could include Data Ecosystem Reference Architectures, Master Data Management models or any other data centric model.



Optional Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

<!--### Functional Architecture
<!-- GUIDANCE -->
<!--
Provide a brief description of the functional architecture, split into two main areas: application capabilities and data.

Optional Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

### Architecture Decisions
<!-- GUIDANCE -->
<!--
List the architecture decisions for the previous future state architecture(s). The decisions can be based upon the previously defined requirements or can be based on common architecture best practices or architecture design patterns.

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

#### Requirements Evaluation
<!-- GUIDANCE -->
<!--
List architecture decisions and how they impact previous functional, non-function, or other requirement. Do a realist evaluation and also highlight lowlights where an architecture decision might not fully comply to a previous requirement. Discuss with your customer and get feedback from your colleagues if some requirements are not fully satisfied.

Recommended Chapter
-->

| Architecture Decision | Description |
|:---------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| AD1: Deployment to tenancy | The essbase resources will be deployed in the existing tenancy |          |
| AD2: Database Edition and Version   | The Oracle ATP Database version 19c on OCI has been selected as the database for Essbase’s metadata repository. ATP may be used as staging area for Data before the data moves to Essbase cubes. ATP is proposed to evaluate exclusive functionalities for federated partitions with Essbase on OCI.                                                                                |          |
| AD3: Access through public Internet | The services and functionality of Essbase will only be accessed from the Internet over http(s). **Customer to share the HTTPS certificates** needed to be imported in the Load Balancer. The access may be available only to a set of white listed IPs provided by the customer |          |


#### Architecture Best Practices
<!-- GUIDANCE -->
<!--
Refer or cite architecture best practices or design patterns. Explain how they are reflected in your architecture and how they improve the solution.

Recommended Chapter
-->

| Architecture Best Practice | Description                                                                                                                                                                                                   | Status        |
|:---------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------|
| Compartment structure      | It is recommended to have separate compartments for similar group of OCI resources. For example: Network compartment, Security compartment   | Project scope        |
| Fast Connect               | It is recommended to have fastconnect connectivity from the customer data center to OCI for Production environment. This eliminates internet exposure and essentially extends your data center directly into Oracle Cloud Infrastructure | Future Scope |

## OCI Cloud Landing Zone Architecture
<!-- GUIDANCE -->
<!--

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

The design considerations for an OCI Cloud Landing Zone have to do with OCI and industry architecture best practices, along with customer specific architecture requirements that reflect the Cloud Strategy (hybrid, multi-cloud, etc). An OCI Cloud Landing zone involves a variety of fundamental aspects that have a broad level of sophistication. A good summary of a Cloud Landing Zone has been published by [link](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/technology-implementation.htm).

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

| Resource type | Abbreviation | Example |
|---|---|---|
| Bastion Service | bst | bst-\<location>-\<network> |
| Block Volume | blk | blk-\<location>-\<project>-\<purpose>
| Compartment | cmp | cmp-shared, cmp-shared-security |
| Customer Premise Equipment | cpe | cpe-\<location>-\<destination> |
| DNS Endpoint Forwarder | dnsepf | dnsepf-\<location> |
| DNS Endpoint Listener | dnsepl | dnsepl-\<location> |
| Dynamic Group | dgp | dpg-security-functions |
| Dynamic Routing Gateway | drg | drg-prod-\<location>
| Dynamic Routing Gateway Attachment | drgatt | drgatt-prod-\<location>-\<source_vcn>-\<destination_vcn> |
| Fast Connect | fc# <# := 1...n> | fc0-\<location>-\<destination> |
| File Storage | fss | fss-prod-\<location>-\<project> |
| Internet Gateway | igw | igw-dev-\<location>-\<project> |
| Jump Server | js | js-\<location>-xxxxx |
| Load Balancer | lb | lb-prod-\<location>-\<project> |
| Local Peering Gateway | lpg | lpg-prod-\<source_vcn>-\<destination_vcn> |
| NAT Gateway | nat | nat-prod-\<location>-\<project> |
| Network Security Group | nsg | nsg-prod-\<location>-waf |
| Managed key | key | key-prod-\<location>-\<project>-database01 |
| OCI Function Application | fn | fn-security-logs |
| Object Storage Bucket | bkt | bkt-audit-logs |
| Policy | pcy | pcy-services, pcy-tc-security-administration |
| Region Code, Location | xxx | fra, ams, zch # three letter region code |
| Routing Table | rt | rt-prod-\<location>-network |
| Secret | sec | sec-prod-wls-admin |
| Security List | sl | sl-\<location> |
| Service Connector Hub | sch | sch-\<location> |
| Service Gateway | sgw | sgw-\<location> |
| Subnet | sn | sn-\<location> |
| Tenancy | tc | tc |
| Vault | vlt | vlt-\<location> |
| Virtual Cloud Network | vcn | vcn-\<location> |
| Virtual Machine | vm | vm-xxxx |
| | | |

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

Oracle Cloud Guard Service will be enabled using the pcy-service policy and with the following default configuration. Customization of the Detector and Responder Recipes will result in clones of the default (Oracle Managed) recipes.

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
- Notification for network security group changes. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.12](https://www.cisecurity.org/cis-benchmarks)
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

## Operations
<!-- GUIDANCE -->
<!--
In this chapter we provide a high-level introduction to various operations related topics around OCI. We do not design, plan or execute any detailed operations for our customers. We can provide some best practices and workload specific recommendations.

The below example text represents the first asset from this catalogue PCO#01. Please consider including other assets as well. You can find MD text snippets within each asset.

Recommended Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

This chapter provides an introduction and collection of useful resources, to relevant topics to operate the solution on Oracle Infrastructure Cloud.

Cloud Operations Topic                       | Short Summary      | References
:---                                         |:------             |:---
Cloud Shared Responsibility Model            | The shared responsibility model conveys how a cloud service provider is responsible for managing the security of the public cloud while the subscriber of the service is responsible for securing what is in the cloud.	                |  [Shared Services Link](https://www.oracle.com/a/ocom/docs/cloud/oracle-ctr-2020-shared-responsibility.pdf)
Oracle Support Portal	                       | Search Oracle knowledge base and engage communities to learn about products, services, and to find help resolving issues.	   |  [Oracle Support Link](https://support.oracle.com/portal/)
Support Management API	                     | Use the Support Management API to manage support requests	  |  [API Documentation Link](https://docs.oracle.com/en-us/iaas/api/#/en/incidentmanagement/20181231/) and [Other OCI Support Link](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/contactingsupport.htm)
OCI Status	                                 | Use this link to check the global status of all OCI Cloud Services in all Regions and Availability Domains.	  |  [OCI Status Link](https://ocistatus.oraclecloud.com/)
Oracle Incident Response	                   | Reflecting the recommended practices in prevalent security standards issued by the International Organization for Standardization (ISO), the United States National Institute of Standards and Technology (NIST), and other industry sources, Oracle has implemented a wide variety of preventive, detective, and corrective security controls with the objective of protecting information assets.	  |  [Oracle Incident Response Link](https://ocistatus.oraclecloud.com/)
Oracle Cloud Hosting and Delivery Policies   | Describe the Oracle Cloud hosting and delivery policies in terms of security, continuity, SLAs, change management, support, and termination.	  |  [Oracle Cloud Hosting and Delivery Policies](https://www.oracle.com/us/corporate/contracts/ocloud-hosting-delivery-policies-3089853.pdf)
OCI SLAs                                     | Mission-critical workloads require consistent performance, and the ability to manage, monitor, and modify resources running in the cloud at any time. Only Oracle offers end-to-end SLAs covering performance, availability, manageability of services. This document applies to Oracle PaaS and IaaS Public Cloud Services purchased, and supplements the Oracle Cloud Hosting and Delivery Policies | [OCI SLA's](https://www.oracle.com/cloud/sla/) and [PDF Link](https://www.oracle.com/assets/paas-iaas-pub-cld-srvs-pillar-4021422.pdf)

## Roadmap
<!-- GUIDANCE -->
<!--
Explain a high-level roadmap for this Workload. Include a few easy high-level steps to success (See Business Context). Include Lift services (if possible) as a first fast step. Add other implementation partners and their work as part of your roadmap as well. Does not include details about the Lift scope or any timeline. This is not about product roadmaps.

Recommended Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

Customer should regularly patch and upgrade to the new releases of essbase to avail new functionalities.
Please refer to this [link](https://docs.oracle.com/en/database/other-databases/essbase/21/essad/patch-and-roll-back-version-19.3.0.3.4-and-later.html) for details.

## Sizing and Bill of Materials
<!-- GUIDANCE -->
<!--
Estimate and size the physical needed resources of the Workload. The information can be collected and is based upon previously gathered capacities, business user numbers, integration points, or translated existing on-premises resources. The sizing is possibly done with or even without a Physical Architecture. It is ok to make assumptions and to clearly state them!

Clarify with sales your assumptions and your sizing. Get your sales to finalize the BoM with discounts or other sales calculations. Review the final BoM and ensure the sales is using the correct product SKU's / Part Number.

Even if the BoM and sizing was done with the help of Excel between the different teams, ensure that this chapter includes or links to the final BoM as well.

-->

### Sizing
<!-- GUIDANCE -->
<!--
Describe the sizes of the complete workload solution and its components.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | C
PPM   | None
Sales | C
-->

Test environment on OCI will be deployed in one Availability Domain (AD1) and will include the following components:

* Web Tier:
  * 1 Public Load balancer. No OCI Web Application Firewall protection considered at this stage.

* Application/DB Tier deployed in private tier
  * 1 Essbase 21c instance deployed in Fault Domain FD1: the proposed Essbase Instance is a **VMStandard 2.8 with 8 OCPU** to evaluate the performance on OCI against the current environment. Customer may decrease or increase OCPU based on performance testing and needs.
  * 1 ATP deployed with a 1OCPU shape.

* **TBC** 1 Windows bastion host


 _**A newer shape is recommended for Essbase Instance: VM.Standard.E4.Flex may be used instead. Please refer to documentation[here](https://docs.oracle.com/en-us/iaas/Content/Compute/References/computeshapes.htm)**_

### Bill of Material
<!-- GUIDANCE -->
<!--
A full Bill of Material can be described in addition.

Optional Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
Sales | R
-->

<!-- Latest Customer Lift Acceptance -->

# Implementation

## Approach
<!-- GUIDANCE -->
<!--

Mandatory Chapter

Role  | RACI
------|-----
WLA   | A
Impl. | R
PPM   | None
-->

- Market place Essbase stack deployment in OCI.
- Essbase applications migration using standalone LCM tool.

## Project Prerequisites

<!-- GUIDANCE -->
<!--
The purpose of this section is to document all the technical items that we expect the customer to under take, for example:

- ingress/egress between on-prem & OCI so the customer firewall can be configured
- VPN/FastConnect config
- any specific commands for data export.

Optional Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

<!-- EXAMPLE / TEMPLATE -->

### Customer / OCI Network

#### Ingress/Egress

| Item | From CIDR      | From Port | To CIDR         | To Port | Description           |
|:----:|:---------------|:----------|:----------------|:--------|:----------------------|
| 1    | xxx.xxx.x.x/24 | TCP-22    | xx.xx.x.x/24     | TCP-22  | SSH to Bastion Subnet |
| 2    | xx.x.x.x/32   | TCP-25    | xxx.xxx.x.xx/32 | TCP-25  | SMTP Out              |
| 3    | xxx.xxx.x.x/24 | TCP-443   | xx.x.x.x/24     | TCP-443 | HTTPS                 |


#### IPSEC/VPN

Details of the customer's IPSEC/VPN On-Premise to OCI network connection are detailed in the document "xxx"

#### FastConnect

Details of the customer's FastConnect On-Premise to OCI network connection are detailed in the document "xxx.xlsx"

## Design
<!-- GUIDNCE -->
<!--

Recommended Chapter

Role  | RACI
------|-----
WLA   | A
Impl. | R
PPM   | None
-->

### Design Principles
<!-- GUIDANCE -->
<!--

Recommended Chapter

Role  | RACI
------|-----
WLA   | A
Impl. | R
PPM   | None
-->

### Specification
<!-- GUIDANCE -->
<!--

Recommended Chapter

Role  | RACI
------|-----
WLA   | A
Impl. | R
PPM   | None
-->

<!-- EXAMPLE / TEMPLATE -->

### Mockups
<!-- GUIDANCE -->
<!--

Recommended Chapter

Role  | RACI
------|-----
WLA   | A
Impl. | R
PPM   | None
-->

## Project Plan
<!-- GUIDANCE -->
<!--
The final 'alive' project plan which gets maintained throughout the complete implementation. Do not replicate a project plan in this document, it is a separate document which is only mentioned here. Link to a shared repository, such as customer Confluence Spaces, OraSites or possible slack channels. Alternatively a Project Plans and updates can be shared via emails.

Include Customer Responsibilities from previous chapter.

Recommended Chapter

Role  | RACI
------|-----
WLA   | I/A
Impl. | C
PPM   | R

-->

<!-- EXAMPLE / TEMPLATE -->
The implementation project plan can be found in our shared project repository [here]

<!-- EXAMPLE / TEMPLATE -->
Project plans are communicated bi-weekly to the following recipients via email:

- hello.world@acme.com
- will.smith@acme.com

## RAID Analysis
<!-- GUIDANCE -->
<!--
This chapter presents the standard Risk/Assumptions/Issues/Dependencies analysis for the implementation project. It may partially overlap with the previous parts of the Implementation chapter, so some rework may be required to align them without overlap or repetitions. Since RAID is a standard, simple PM technique, there is a lot of documentation online. Two good starting points for the reader are [here](https://www.projectsmart.co.uk/raid-log.php) and [here](https://www.groupmap.com/map-templates/raid-analysis/).

As attachment.

Recommended Chapter

Role  | RACI
------|-----
WLA   | I/A
Impl. | C
PPM   | R
-->

<!-- Rotate PDF pages, to give tables more space. Please put in comments here and also after the Deployment Build to remove -->
\newpage
\blandscape

## Deployment Build
<!-- GUIDANCE -->
<!--
The Deployment Build is a list of all OCI resources needed for the Lift implementation. It serves two purposes: as a customers documentation; and as a Lift implementer handover. The checklist below defines mandatory requirements as per project scope for the Lift implementation. This table replaces the CD3 file for the architecture team.

Agile Approach: The architect creates and fills in the first version of this table. We work together with our customers to get and confirm the detailed data. Afterwards, the architect and the implementer are working together to iteratively fill these tables. In the meantime some development might already been done by the implementers.

RACI: The architect is Accountable and Responsible for this section. The implementer will actively Consult to provide missing data.

Automatic Parsing: This section is going to be automatically parsed by the implementers. As architects, please try to avoid changing the sub-section names or table structures and attributes. Change only with a strong need, and let me (Alexander Hodicke) know if you need a change here. In addition, please put a comment around each table as seen in the example below - Do not delete them.

For all sub-chapters:

Mandatory Chapter (Partly Optional: If part of your solution / Some subchapters might be mutual exclusive.)

Role  | RACI
------|-----
WLA   | R/A
Impl. | C
PPM   | None
-->

Deployment is based on official documentation, that can be found [here] (https://docs.oracle.com/en/database/other-databases/essbase/21/essad/set-oracle-essbase.html)

<!--### Phase 1: <name>
<!-- Guidance -->
<!--
Please group the Deployment Build into phases depending on the size of the engagement. Each chapter of the Deployment Build belongs to a phase and represents an iterative implementation. First we implement phase 1 and we need to collect data here for that phase. Rearrange the chapters to fit to the right phases. An implementation could have as many phases as needed, and if it has just one, do not group it into just a single phase.

-->

#### Compartments
<!-- GUIDANCE -->
<!--
All the fields are mandatory except Tags.
Parent Compartment:- Leave it empty or mention 'root' to create under root compartment, mention compartment in compartment1:compartment2 order if not below root compartment.
Region:- Home Region of Tenancy.
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
| Name | Parent Compartment | Description | Tags |
| ------- | ------ | --------------- | ----- |
| cmp-essb |  (root) | Compartment to host all resources required to run Essbase | |
| cmp-essb-network | cmp-essb | Compartment to group network resources specific to Essbase (VCNs, subnets, security groups/lists, gateways,Bastion, Load Balancer) | |
| cmp-essb-security | cmp-essb | OCI security elements: notifications, topics, key management, logs | |
| cmp-essb-test | cmp-essb | Compartment to host all resources required to run Essbase (object, block and file storage, compute, database) | |
<!--END-->

#### Policies
<!-- GUIDANCE -->
<!--
All the fields are mandatory except Tags.
Statements:- Policy to create.
Region: Home region of Tenancy
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
|  Name                 |  Statements |  Region   |  Compartment          |  Description                                           |
| ------------------ | ---------------------------------------- | --------------- | --------------- | ------------------------------------------------------ |
| EssbaseIAMPolicy      | Allow group EssbaseIAMAdminsGrp to manage policies in tenancy  | Amsterdam |  gaetancourtel (root) | Allow users to manage policies                         |
| EssbaseNetworkPolicy  |  Allow group EssbaseNetworkAdminsGrp to manage all-resources in compartment cmp-essb-network  | Amsterdam | cmp-essb-network      |  Manage all resources in cmp-essb-network compartment  |
| EssbaseSecurityPolicy |  Allow group EssbaseSecurityAdminsGrp to manage all-resources in compartment cmp-essb-security   | Amsterdam | cmp-essb-security     |  Manage all resources in cmp-essb-security compartment |
| EssbaseAppPolicy      |  Allow group EssbaseAppAdminsGrp to manage orm-stacks in compartment cmp-essb, Allow group EssbaseAppAdminsGrp to manage orm-jobs in compartment cmp-essb, Allow group EssbaseAppAdminsGrp to manage virtual-network-family in compartment cmp-essb, Allow group EssbaseAppAdminsGrp to manage instances in compartment cmp-essb, Allow group EssbaseAppAdminsGrp to manage volume-family in compartment cmp-essb, Allow group EssbaseAppAdminsGrp to manage load-balancers in compartment cmp-essb, Allow group EssbaseAppAdminsGrp to manage buckets in compartment cmp-essb, Allow group EssbaseAppAdminsGrp to manage objects in compartment cmp-essb, Allow group EssbaseAppAdminsGrp to manage autonomous-database-family in compartment cmp-essb, Allow group EssbaseAppAdminsGrp to use instance-family in compartment cmp-essb, Allow group EssbaseAppAdminsGrp to manage autonomous-backups in compartment cmp-essb, Allow group EssbaseAppAdminsGrp to manage buckets in compartment cmp-essb, Allow group EssbaseAppAdminsGrp to manage vaults in compartment cmp-essb, Allow group EssbaseAppAdminsGrp to manage secret-family in compartment cmp-essb, Allow group EssbaseAppAdminsGrp to manage app-catalog-listing in compartment cmp-essb, Allow dynamic-group essb-dynamic-group to use autonomous-database in compartment cmp-essb, Allow dynamic-group essb-dynamic-group to use secret-family in compartment cmp-essb, Allow dynamic-group essb-dynamic-group to read buckets in compartment cmp-essb, Allow dynamic-group essb-dynamic-group to manage objects in compartment cmp-essb, Allow dynamic-group essb-dynamic-group to inspect volume-groups in compartment cmp-essb, Allow dynamic-group essb-dynamic-group to manage volumes in compartment cmp-essb, Allow dynamic-group essb-dynamic-group to manage volume-group-backups in compartment cmp-essb, Allow dynamic-group essb-dynamic-group to manage volume-backups in compartment cmp-essb, Allow dynamic-group essb-dynamic-group to manage autonomous-backups in compartment cmp-essb, Allow dynamic-group essb-dynamic-group to manage database-family in compartment cmp-essb | Amsterdam | cmp-essb  |  Essbase Stack Deployment requirements   |
<!--END-->

#### Groups
<!-- GUIDANCE -->
<!--
Optional Chapter
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
|  Name                    |  Matching Rule        |  Region     |  Authentication  |  Description                                          |  Tags  |
| ------------------------ | --------------------- | ----------- | ---------------- | ----------------------------------------------------- | ------ |
| EssbaseIAMAdminsGrp      | EssbaseIAMPolicy      |  Amsterdam  | IAM              |  Users that have admin access to policies in tenancy  |        |
| EssbaseNetworkAdminsGrp  | EssbaseNetworkPolicy  | Amsterdam   |  IAM             |  Users managing cmp-essb-network                      |
| EssbaseSecurityAdminsGrp | EssbaseSecurityPolicy | Amsterdam   |  IAM             |  Users managing cmp-essb-security                     |
| EssbaseAppAdminsGrp      | EssbaseAppPolicy      | Amsterdam   |  IAM             |  Users managing cmp-essb-test                         |
<!--END-->

#### Dynamic Group Policies
<!-- GUIDANCE -->
<!--
Optional Chapter
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
| Dynamic Group Name | Description                        | Matching Rule                                                     |
| ------------------ | ---------------------------------- | ----------------------------------------------------------------- |
| essb-dynamic-group | Requirement for essbase deployment | Any {instance.compartment.id = '<TBC ocid compartment>ocid.....'} |

> __Note__: When defining the dynamic group in the tenancy you must substitute with the real ocid assigned to the compartment cmp-essb.

<!--END-->

#### Tags
<!-- GUIDANCE -->
<!--
<!--
All the fields are mandatory.
Tag Namespace: Specify the Tag Namespace.
Namespace Description: Description of Tags Namespace.
Cost Tracking: Specify "Yes" if tag is cost tracking tag else "No".
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Tag Namespace | Namespace Description | Tag Keys | Tag Description | Cost Tracking | Tag Values | Region
:---          |:---                   |:---      |:---             |:---           |:---        |:---
Application | Inventory | Environment | Environments Identification | Yes | Production Development Test | Region
<!--END-->

#### Users
<!-- EXAMPLE / TEMPLATE -->

| Name              | Email                       | Group                                                                                       | Description      |
| ----------------- | --------------------------- | ------------------------------------------------------------------------------------------- | ---------------- |


#### Virtual Cloud Networks
<!-- GUIDANCE -->
<!--
All the fields are mandatory except Tags and DNS Label. If DNS Label is left empty, DNS Label will be created with VCN Name.
IGW:- Internet Gateway, mention the name of internet gateway, enter None if not needed, if left empty it will treated as None.
SGW:- Service Gateway, mention the name of Service gateway, enter None if not needed, if left empty it will treated as None.
NGW:- NAT Gateway, mention the name of NAT gateway, enter None if not needed, if left empty it will treated as None.
DRG:- Dynamic Routing Gateway, enter the name of Dynamic Routing gateway, mention None if not needed, if left empty it will treated as None. DRG should be unique in the region. If same DRG to be attached to multiple VCN please mention same in respective VCN's.
Region:- Region under which VCN's to be created
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->

| Compartment | VCN Name | CIDR Block | DNS Label | IGW | DRG | NGW | SGW | Region | Tags |
|:------|:------|:------|:------|:------|:------|:------|:------|:------|:------|
| cmp-essb-network | vcn-essb |  xx.x.x.x/24 |  vcnessb | igw-essb |drg-essb | ngw-essb | sgw-essb | Amsterdam | |

<!--END-->

#### Virtual Cloud Network Information
<!-- GUIDANCE -->
<!--
None of the fields are mandatory.
onprem_destinations: Enter on-premise CIDR, separated by comma.
ngw_destination: Enter NAT Gatewat CIDR.
igw_destination: Enter Internet Gatewat CIDR.
subnet_name_attach_cidr: Mention y if you want to attachd AD and CIDR to object's display name; defaults to n.
-->
<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Property | Value
:---     |:---
onprem_destinations | xx.x.x.x/16
ngw_destination | 0.0.0.0/0
igw_destination | 0.0.0.0/0
subnet_name_attach_cidr | n

<!--END-->

#### Subnets
<!-- GUIDANCE -->
<!--
All the fields are mandatory except Security List Name, Route Table Name and Tags.
Subnet Span:- Valid Values are AD1/AD2/AD3/Regional.
Type:- Valid Values are Private/Public
Security List Name:- Specify Security list to be attached to subnet, if left blank security list with name as that of subnet will attached,
specify None if not to attach any custom security list.
Route Table Name:- Specify Route Table Name to be attached to subnet, if left blank route Table with name as that of subnet will attached,
specify None if not to attach any custom route table.
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
| Compartment | VCN Name | Subnet Name | CIDR Block | Subnet Span | Type | Security List Name | Route Table Name | Region | Tags |
|:------|:------|:------|:------|:------|:------|:------|:------|:------|:------|
| cmp-essb-network | vcn-essb |  sn-essb-lb | 10.0.0.32/28 | Regional  | Public | | | Amsterdam |  |
| cmp-essb-network | vcn-essb  | sn-essb-bastion  | 10.0.0.16/28  | Regional  | Public  | | rt-essb-bastion| Amsterdam |  |
| cmp-essb-network | vcn-essb  | sn-essb-app  | 10.0.0.0/28  | Regional  | Private  |   |   | Amsterdam  |   |
| cmp-essb-network | vcn-essb  | sn-essb-db  | 10.0.0.48/28  | Regional  | Private  |   |   | Amsterdam  |   |
<!--END-->

<!--### Phase 2: <name>
<!-- Guidance -->
<!--
Please group the Deployment Build into phases depending on the size of the engagement. Each chapter of the deployment Build belongs to a phase and represents an iterative implementation. Secondly we implement phase 2 and we need to collect data here for that phase. Rearrange the chapters to fit to the right phases. An implementation could have as many Phases as needed, and if it has just one, do not group it into just a single Phases.
-->

#### DNS Zones
<!-- EXAMPLE / TEMPLATE -->
<!--START
Zone Name | Compartment | Region | Zone Type | Domain | TTL | IP Address | View Name | Tags
:---      |:---         |:---    |:---       |:---    |:--- |:---        |:---       |:---
PrivateZone | anand.as.singh | zurich | private/public | example.com | 300 | 10.0.0.0/32 | privateview |
<!--END-->

#### DNS Endpoint
<!-- EXAMPLE / TEMPLATE -->
<!--START
Name | Subnet | Endpoint Type | NSG | IPAddress (Listner/Forwarder)
:--- |:---    |:---           |:--- |:---
privateforwarder | subnetname | Listening/Fowarding | nsg | ipaddress
<!--END-->

#### Dynamic Routing Gateways Attachment
<!-- GUIDANCE -->
<!--
All the fields are mandatory except Tags.
IPSEC/Virtual Circuit: Ipsec VPN or FastConnect Virtual Circuit Name, Leave empty if not needed.
-->
<!-- WIP: Split IPSEC and Virtual Circuit into two coloumns (By JC, to be reviewed by Impl) -->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Name | VCN | Compartment | IPSEC/ Virtual Circuit | Region | Tags
:--- |:--- |:---         |:---                    |:---    |:---
drg-essb | vcn-essb | cmp-essb-network | examplevpn | Amsterdam |
<!--END-->

#### Route Tables
<!-- GUIDANCE -->
<!--
All the fields are mandatory except Tags.
Table Compartment: Specify Compartment in which route table is to be created.
Destination CIDR: Specify the destination CIDR.
Target Type: Valid options are CIDR_BLOCK/Service
Target Compartment: Specify the Compartment in which Target Exist.
Target: Valid Targets are Name of the DRG/IGW/SGW/LPG/Private IP/NGW
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Name | Table Compartment | Destination CIDR | Target Type | Target Compartment | Target | Region | Description | Tags | VCN Name
:--- |:---               |:---              |:---         |:---                |:---    |:---    |:---           |:---  |:---
rt-essb-bastion | cmp-essb-network  |  0.0.0.0/0 | Internet Gateway | cmp-essb-network  |  igw-essb | Amsterdam  | Incoming Traffic for Windows Bastion host  |  | vcn-essb
rt-essb-sce | cmp-essb-network  |  All AMS Services In Oracle Services Network | Service Gateway |  cmp-essb-network |  sgw-essb | Amsterdam  |   |  | vcn-essb
rt-essb-sce | cmp-essb-network | 0.0.0.0/0 | NAT | cmp-essb-network | ngw-essb | Amsterdam | All communications through Service Gateways | | vcn-essb |
<!--END-->

#### Network Security Groups
<!-- GUIDANCE -->
<!--
All the fields are mandatory.
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
This following NSG will be created

* for ATP databases
* for accessing Windows Bastion host. **For security reasons, customer should provide IP adresses to restrict access to Windows Bastion host**

Name | VCN | Compartment | Region | Description | Tags
:--- |:--- |:---         |:---    |:---         |:---
nsg-essb-bastion | vcn-essb | cmp-essb-network | Amsterdam | NSG to access Bastion host |
nsg-essb-atp | vcn-essb | cmp-essb-network | Amsterdam | NSG to access ATP Database |
<!--END-->

#### NSG Rules (Egress)
<!-- GUIDANCE -->
<!--
All the fields are mandatory.
Egress Type: Valid options are CIDR_BLOCK/NETWORK_SECURITY_GROUP/SERVICE_CIDR_BLOCK.
protocol: Valid options are TCP/UDP/HTTP.
Destination: Specify the Destination CIDR.
Destination Port: Specify the Destination Port.
Attached Components: Leave it empty as of now
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
This following NSG will be created.

| NSG Name | Attached Components | Egress Type | Destination | Protocol | Source Port | Destination Port | Region | Description | Tags |
|:------|:------|:------|:------|:------|:------|:------|:------|:------|:------|
| nsg-essb-bastion | essb-bastion | CIDR | 0.0.0.0/0 | TCP | ALL | ALL | Amsterdam | egress rule for Bastion host |   |
| nsg-essb-atp |  atpdb-essbase-test | CIDR | 10.0.0.0/24 | TCP | ALL | ALL | Amsterdam | egress rule for ATP Database |   |

<!--END-->

#### NSG Rules (Ingress)
<!-- GUIDANCE -->
<!--
All the fields are mandatory.
Ingress Type: Valid options are CIDR_BLOCK/NETWORK_SECURITY_GROUP/SERVICE_CIDR_BLOCK.
protocol: Valid options are TCP/UDP/HTTP.
Source: Specify the Source CIDR.
Source Port: Specify the Source Port.
Attached Components: Leave it empty as of now
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
This following NSG will be created

**For security reasons, customer should provide IP adresses to restrict access to Windows Bastion host**


| NSG Name | Attached Components | Ingress Type | Source | Protocol | Source Port | Destination Port | Region | Description | Tags |
|:------|:------|:------|:------|:------|:------|:------|:------|:------|:------|
| nsg-essb-bastion | essb-bastion | CIDR | <TBC CUSTOMER IP@> | TCP | ALL | 3389 | Amsterdam | Remote access from customer network to Bastion host |   |
| nsg-essb-atp |  atpdb-essbase-test | CIDR | xx.x.x.x/28 | TCP | ALL | 1522 | Amsterdam | ingress rule for Database host DB port from Essbase Instance  |   |
| nsg-essb-atp |  atpdb-essbase-test | CIDR | xx.x.x.x/28 | ICMP | ALL | ALL | Amsterdam | ingress rule for ICMP to Database host |   |
| nsg-essb-atp |  atpdb-essbase-test | CIDR | xx.x.x.xx/28 | TCP | ALL | 1522 | Amsterdam | ingress rule for Database host DB port from Bastion host |   |
<!--END-->

#### Security Lists (Egress)
<!-- GUIDANCE -->
<!--
All the fields are mandatory except Tags.
Destination: Specify Destination CIDR.
Protocol: Specify the protocol For Example: TCP/HTTP/ICMP
Destination Port: Specify egress port to allow.
Egress Type: Valid option is CIDR
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Name | Compartment | Egress Type | Destination | Protocol | Source Port | Dest. Port | VCN Name | Region | Description | Tags
:--- |:---         |:---         |:---         |:---      |:---         |:---        |:---      |:---    |:---          |:---
examplelist | compartment | Stateful/ CIDR | 0.0.0.0/0 | TCP | all | all | | Region | | |
<!--END-->

#### Security Lists (Ingress)
<!-- GUIDANCE -->
<!--
All the fields are mandatory except Tags.
Destination: Specify Destination CIDR.
Protocol: Specify the protocol For Example: TCP/HTTP/ICMP
Destination Port: Specify ingress port to allow.
Ingress Type: Valid option is CIDR
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Name | Compartment | Ingress Type | Source | Protocol | Source Port | Dest. Port | VCN Name | Region | Description | Tags
:--- |:---         |:---          |:---    |:---      |:---         |:---        |:---      |:---    |:---           |:---
examplelist | compartment | Stateful/ CIDR | 0.0.0.0/0 | TCP | all | all | | Region | |
<!--END-->

#### Local Peering Gateways
<!-- GUIDANCE -->
<!--
Optional chapter
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Name | LPG Compartment | Source VCN | Target VCN | Region | Description | Tags
:--- |:---             |:---        |:---        |:---    |:---         |:---
examplelpg | Networks | examplevcn | examplevcn2 | Region | |
examplelpg2 | Networks | examplevcn2 | examplevcn | Region | |
<!--END-->

#### Compute Instances
<!-- GUIDANCE -->
<!--
All the fields are mandatory except NSG and Tags.
Availability Domain:- Valid values are AD1/AD2/AD3 which also depend upon Region.
Fault Domain:- Valid values are FD1/FD2/FD3 or FD-1/FD-2/FD-3, if left blank OCI will take it default.
OS Image:- Valid Values are image name with version without period(.) For Example: OracleLinux79 or Windows2012,
to create instance from boot volume bootvolume OCID.
Shape: Valid Values are compute shapes, for Flex shapes specify Flexshape::NoCPU For Example: VM.Standard.E3.Flex::2.
Backup Policy: Valid Values are Gold/Silver/Bronze
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
The display name for this workload will be **essbtest**.

**essbtest is used as Stack Display Name to prefix the names of the resources.**

**The Timezone for Essbase instance will be set to Europe/Paris.**

**08/04/2022: Proposed shape VM.Standard.E4.Flex::8 OCPU(128 G RAM) is instead of VM.Standard.2.8**

The required entries will be created by the marketplace stack for Essbase instance as mentioned below:

| Compartment   | Availability Domain | Name             | Fault Domain | Subnet      | OS Image         | Shape           | Backup Policy | Region    | NSG | Tags |
| ------------- | ------------------- | ---------------- | ------------ | ----------- | ---------------- | --------------- | ------------- | --------- | --- | ---- |
| cmp-essb-test | AD1                 |  essbtest-node-1 |  N/A         | sn-essb-app | Oracle Linux 7.9 | VM.Standard.E4.Flex::8(128) | N/A           | Amsterdam | N/A |      |



An additional Bastion host on Windows will be created.

| Compartment | Availability Domain | Name         | Fault Domain | Subnet          | OS Image     | Shape                      | Backup Policy | Region    | NSG              | Tags |
| ----------- | ------------------- | ------------ | ------------ | --------------- | ------------ | -------------------------- | ------------- | --------- | ---------------- | ---- |
| cmp-essb    | AD1                 | essb-bastion | FD1          | sn-essb-bastion | Windows 2019 | VM.Standard.E3.Flex::1(16) | N/A           | Amsterdam | nsg-essb-bastion |      |


<!--END-->

#### Block Volumes
<!-- GUIDANCE -->
<!--
All the fields are mandatory except tags.
Size (in GB):- Specify Block Volume size in GB's.
Availability Domain:- Valid values are AD1/AD2/AD3, make sure to specify same AD in which instance is provisioned.
Attached to Instance:- Instance to which Block Volume to be attached.
Backup Policy:- Valid values are Gold/Silver/bronze
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
The required entries will be created by the marketplace stack as mentioned in the table below.

| Compartment | Name | Size (in GB) | Availability Domain | Attached to Instance | Backup Policy | Region | Tags |
|:------|:------|:------|:------|:------|:------|:------|:------|
| cmp-essb | essbtest-data-volume |  1024 |  AD1 | essbtest-node-1  | N/A | Amsterdam | |
| cmp-essb | essbtest-config-volume-1 |  64 |  AD1 | essbtest-node-1  | N/A | Amsterdam | |
| cmp-essb | essbtest-temp-volume-1 |  64 |  AD1 | essbtest-node-1  |  N/A | Amsterdam | |
<!--END-->

#### Object Storage Buckets
<!-- GUIDANCE -->
<!--
Optional Chapter
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
The following bucket will be created.

| Compartment | Bucket | Storage Tier | Region | Description | Tags |
| ------- | ------ | ------ | ------ | --------------- | ----- |
| cmp-essb | bkt-essb | Standard | Amsterdam | Object Storage bucket for custom customer usage | |
<!--END-->

<!--#### File Storage
<!-- GUIDANCE -->
<!--
Optional Chapter
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-
| Compartment | Availability Domain | Mount Target Name | Mount Target Subnet | FSS Name | Path | IP Whitelist | Region | NSG | Tags |
|:------|:------|:------|:------|:------|:------|:------|:------|:------|:------|
| Production | AD1 |  prdhypmt |  appsubnet | prodhypfss  | /prodhypfss | 10.0.1.0/25 | Region | | |
| Non-Production   | AD2  | nprodhypmt  | appsubnet  | nprodhypfss  | /nprodhypfss  | 10.0.2.0/25  | Region  |   |   |
<!--END-->

#### Load Balancers
<!-- GUIDANCE -->
<!--
All the fields are mandatory except tags
LB Name:- Specify LB Name
Shape:- Specify LB Shapes in 10Mbps/100Mbps/400Mbps/8000Mbps
Visibility:- Valid values are Private/Public
LBR Hostname: Valid values are Name:Hostname
-->

The required entries will be created by the marketplace stack: load Balancer with public Visibility with following information.

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
| Compartment | LB Name | Shape | Subnet | Visibility | Hostnames | NSG | Region | Tags |
|:------|:------|:------|:------|:------|:------|:------|:------|:------|
|  cmp-essb-network | essbtest-loadbalancer |  100Mbps |  sn-essb-lb | Public  |  |  | Amsterdam | |
<!--END-->

##### Backend Sets
<!-- GUIDANCE -->
<!--
All the fields are Mandatory.
LB Name:- Load Balancer Name should exist in Load Balancer Chapter.
Backend Set Name: Specify Backend Set Name.
Backend Server:Port: Specify Backend Server name:Port.Backend server should exist in tenancy.
Backend Policy:- Valid options for backend policy is LEAST_CONNECTIONS/IP_HASH/ROUND_ROBIN.
SSL: Valid option to use SSL is 'yes'/'no'.
HC Protocol: Health Check Protocol valid options are HTTP/TCP.
HC Port: Health Check Port Specify Health Check Port.
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->

The required entries will be created by the marketplace stack.

<!--END-->

##### Listeners
<!-- GUIDANCE -->
<!--
All the fields are mandatory.
LB Name: Specify Load Balancer Name should exist in Load Balancer Chapter.
Backend Set Name: Specify Backend Set Name should exist in Backend Sets Chapter.
Hostname: Spcify name ( name:hostnames ) hostname fields from Load Balancer Chapter.
SSL: Specify 'yes' if SSL Listener 'no' if non SSL Listener.
Protocol: Valid options are HTTP/TCP.
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
The required entries will be created by the marketplace stack.
<!--END-->

#### Databases

<!-- ##### DBSystem Info
<!-- GUIDANCE -->
<!--
All the Fields are Mandatory Except Tags.
Shape: Specify VM.Standard for VM DBCS BM.DenseIO2 for Bare Metal DBCS and Exadata for Exadata DBCS System.
DB Software Edition: Valid Options are ENTERPRISE_EDITION_EXTREME_PERFORMANCE, STANDARD_EDITION, ENTERPRISE_EDITION, ENTERPROSE_EDITION_HIGH_PERFORMANCE.
DB Size: Specify DB Size in GB's.
DB Disk Redundancy: Valid options are High/Low.
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-
| Region | Compartment  | Display Name | Shape | Total Node count | DB Software Edition | DB Size | DB Disk Redundancy | Region | Tags |
|:-------|:------------|:------------|:--------------------|:-------------|:------|:-----------------|:--------------|:------|:------|
| amsterdam | network|devdb | VMStandard/BMStandard/Exa | 1 | ENTERPRISE_EDITION | 256 | Normal/High | Region | |
<!--END

**DB Size:** Virtual machine DB systems use Oracle Cloud Infrastructure block storage. More details on available storage options for the VM DB System can be found in the documentation [here](https://docs.oracle.com/en-us/iaas/Content/Database/Concepts/overview.htm)
<!--END-->

<!-- ##### DBSystem Network
<!-- GUIDANCE -->
<!--
All the Fields are mandatory
Display Name: Specify the display name should exist in DBSystem Info Chapter.
Availability Domain: Valid Options are AD1/AD2/AD3, AD varies Region to Region.
License Type: Valid options are LICENSE_INCLUDED/BRING_YOUR_OWN_LICENSE, please specify one of them.
Time Zone: Specify the appropriate time zone.
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-
| Display Name | Hostname Prefix | Subnet Name | Availability Domain | License Type | Time Zone |
|:-----------|:----------------|:------------|:--------------------|:-------------|:---------|
| devdb | dbhost | db-sl | AD1 | LICENSE_INCLUDED/BRING_YOUR_OWN_LICENSE | UTC |
<!--END-->

<!-- ##### Database
<!-- GUIDANCE -->
<!--
All the Fields are mandatory
Display Name: Specify the display name should exist in DBSystem Info Chapter.
Workload Type: Valid Options are OLTP/DSS.
Database Version: Valid options are given below. Please specify one from the below.
11.2.0.4 or 11.2.0.4.201020 or 11.2.0.4.210119 or 11.2.0.4.210420 or 12.1.0.2 or 12.1.0.2.201020 or 12.1.0.2.210119 or 12.1.0.2.210420
or 12.2.0.1 or 12.2.0.1.201020 or 12.2.0.1.210119 or 12.2.0.1.210420 or 18.0.0.0 or 18.12.0.0 or 18.13.0.0 or 18.14.0.0 or 19.0.0.0 or 19.10.0.0 or 19.11.0.0
or 19.9.0.0 or 21.0.0.0 or 21.1.0.0
nCharacter Set: Valid Options are AL16UTF16/UTF8.
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START
| Display Name | PDB Name | Workload Type | Database Name | Database Version | Character Set | ncharacter Set |
|:------------|:---------|:--------------|:--------------|:----------------|:--------------|:-------------|
| devdb | | OLTP/DSS | Testdb | 19c | | |
<!--END-->

#### Autonomous Databases

##### Autonomous Database Information
<!-- GUIDANCE -->
<!--
All the fields are mandatory except Tags.
Workload Type: Valid options are ADW/ATP.
Infrastructure Type: Valid Options are Shared/Dedicated.
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
The following ATP database will be created.

| Compartment | Display Name | DB Name | Workload Type | Infra.Type | DB Version | OCPU Count | Storage(TB) | Region | Tags |
| --------------- | ------------ | ------- | ------------- | ---------- | ---------- | ---------- | ----------- | --------- | ----- |
| cmp-essb-test | atpdb-essbase-test | atpdbessbtest | ATP | Shared | 19c | 1 | 1 | Amsterdam | |
<!--END-->

##### Automation Database Network
<!-- GUIDANCE -->
<!--
All the Fields are mandatory
Display Name: Specify the display name should exist in Autonomous Database Information Chapter.
Auto Scaling: Valid Options are Yes/No.
Network Access: Valid options are Shared/Private.
Access Control Rules: Leave it Blank as of now.
License Type: Valid Options BYOL/LICENSE_INCLUDED
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
| Display Name | Auto Scaling | Network Access | Access Control Rules | License Type | NSG |
| -------- | -------- | --------------- | ----------- | -------- | ----- |
| atpdb-essbase-test | Yes | Private | Disabled | LICENSE_INCLUDED | sn-essb-db |
<!--END-->

#### Key Management System Vaults
<!-- GUIDANCE -->
<!--
Optional Chapter
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Oracle Cloud Infrastructure [Key Management (KMS)] enables you to manage sensitive information when creating a stack. You are required to use KMS to encrypt credentials during provisioning by creating a key. Passwords chosen for Essbase administrator and Database must meet their respective password requirements.

| Compartment  | Name | Type | Description |  Region | Tags |
| -------- | -------- | --------------- | ----------- | -------- | ----- |
| cmp-essb-security | vlt-essbase | Virtual private | Amsterdam |
<!--END-->

#### Key Management System Keys
<!-- GUIDANCE -->
<!--
Optional Chapter
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
| Compartment  | Protection Mode | Name | Key Algorithm | Key Length |
|:--|:---|:---|:---|:--|
| cmp-essb-security  | Software  | key-essbasetest  | AES  | 128 bits |
<!--END-->

<!-- Rotate PDF pages, to give tables more space. Please put in comments here and also before the Deployment Build to remove -->
\elandscape
\newpage

# Glossary
<!-- GUIDANCE -->
<!--
A chapter for Product, Technology or Concept descriptions

Please avoid describing products, and link to product documentation at the first occurrence of a product.

Optional Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | C
PPM   | None
-->

You can learn about Oracle Cloud Infrastructure terms and concepts in this [glossary](https://docs.oracle.com/en-us/iaas/Content/libraries/glossary/glossary-intro.htm). Further terms, product names or concepts are described below in each subsection.

## 2-Factor Authentication

A second verification factor is required each time that a user signs in. Users can't sign in using just their user name and password.

For more information please visit our documentation for [Administering Oracle identity Cloud](https://docs.oracle.com/en/cloud/paas/identity-cloud/uaids/enable-multi-factor-authentication-security-oracle-cloud.html).

## Other

<!-- End of Solution Design -->

<!--
          ^^                   @@@@@@@@@
     ^^       ^^            @@@@@@@@@@@@@@@
                           @@@@@@@@@@@@@@@@@@              ^^
                          @@@@@@@@@@@@@@@@@@@@
~~~~ ~~ ~~~~~ ~~~~~~~~ ~~ &&&&&&&&&&&&&&&&&&&& ~~~~~~~ ~~~~~~~~~~~ ~~~
~         ~~   ~  ~       ~~~~~~~~~~~~~~~~~~~~ ~       ~~     ~~ ~
  ~      ~~      ~~ ~~ ~~  ~~~~~~~~~~~~~ ~~~~  ~     ~~~    ~ ~~~  ~ ~~
  ~  ~~     ~         ~      ~~~~~~  ~~ ~~~       ~~ ~ ~~  ~~ ~
~  ~       ~ ~      ~           ~~ ~~~~~~  ~      ~~  ~             ~~
      ~             ~        ~      ~      ~~   ~             ~
-->
