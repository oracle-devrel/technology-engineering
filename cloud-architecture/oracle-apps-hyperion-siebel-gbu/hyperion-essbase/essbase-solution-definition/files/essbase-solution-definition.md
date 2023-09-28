<!---   
      Replace ${doc.customer.name} in the document. Please specify to whom to hand over the project after implementation. eg.: The Customer, a 3rd party implementation or operations partner, etc.           
--->

*Guide:*

*Author Responsibility*

- *Chapter 1-3: Sales Consultant*

# Document Control

*Guide:*

*The first chapter of the document describes the metadata for the document. Such as versioning and team members.*

## Version Control

*Guide:*

*A section describing the versions of this document and its changes.*

*Example:*

Version     | Author          | Date                    | Comment
:---        |:---             |:---                     |:---
0.1         | Name            | June 12th, 2023     | Updates to network design
1.0         | Name            | June 13th, 2023     | Updates to HA design

## Team

*Guide:*

*A section describing the Oracle team.*

*Example:*

This is the team that is delivering the WAD.

Name           | eMail                     | Role                    | Company
:---           |:---                       |:---                     |:---
Name   | email@example.com     | Project Manager         | Oracle
Name  | email@example.com     | Cloud Architect         | Oracle

## Abbreviations and Acronyms (Optional)

*Guide:*

*If needed, maintain a list of:*
- *Abbreviation: a shortened form of a word or phrase.*
- *Acronyms: an abbreviation formed from the initial letters of other words and pronounced as a word (e.g. ASCII, NASA ).*

*Example:*

Acronyms:    
AD: Availability Domain  
DRG: Dynamic Routing Gateway  
OCI: Oracle Cloud Infrastructure   
IaaS: Infrastructure as a Service    
LB: Load Balancer    
NSG: Network Security Group   
VCN: Virtual Cloud Network

## Document Purpose

*Guide:*

*Describe the purpose of this document and the Oracle-specific terminology, specifically around 'Workload'.*

*Example:*

This document provides a high-level solution definition for the Oracle solution and aims at describing the current state, and to-be state as well as a potential project scope and timeline. The intended purpose is to provide all parties involved with a clear and well-defined insight into the scope of work and intention of the project.

The document may refer to a 'Workload', which summarizes the full technical solution for a customer (You) during a single engagement. The Workload is described in the chapter Workload Requirements and Architecture.

<!--                            -->
<!-- End of 1) Document Control -->
<!--                            -->

# Business Context

*Guide:*

*Describe the customer's business and background. What is the context of the customer's industry and line of business? What are the business needs and goals which this Workload is an enabler for? How does this technical solution impact and support the customer's business goals? Does this solution support a specific customer strategy, or maybe certain customer values? How does this solution help our customers to either generate more revenue or save costs?*

## Executive Summary

*Guide:*

*A section describing the Oracle differentiator and key values of the solution for the customer, allowing the customer to make decisions quickly.*

Example:

The scope of this project is to deliver a working **Test environment including one deployment of Essbase 21c marketplace** in OCI.

Customer's on-premises Essbase deployments can be migrated to run on Oracle Cloud Infrastructure without requiring significant configuration, integration, or process changes. The resulting implementation will be more flexible and more reliable than on-premises or other cloud deployments. Oracle has a validated solution to accomplish these goals, quickly and reliably. This solution includes procedures, supporting Oracle Cloud Infrastructure platform services, and reference architectures. These consider real production needs, like security, network configuration, disaster recovery (DR), identity integration, and cost management.

By moving Essbase systems to Oracle Cloud Infrastructure the following benefits could be realized:

1. The lower total cost of ownership (TCO) than on-premises deployments
2. Managing and reducing CAPEX, and ensuring that the data centers you maintain are efficient while eliminating server hardware, and taking advantage of cloud flexibility where possible
3. Rapid in-place technology refresh
4. Proactive monitoring of usage and costs
5. Scaling up or down to handle business growth or workload bursts

## Workload Business Value

*Guide:*

*A clear statement of specific business value as part of the full workload scope. Try to keep it SMART: Specific, Measurable, Assignable, Realistic, and Time-Related - Agree on the business value with the customer. Keep it business-focused, and speak the language of the LoB which benefits from this Workload: "Increase Customer Retention by 3% in the next year" or "Grow Customer Base with Executive Decision-Making from our Sales and Support Data". Avoid technical success criteria such as "Migrate App X to Oracle Cloud" or "Provision 5 Compute Instances".*

Example:

The customer has been using Essbase for more than X years and is one of the key strategic applications that is used to analyze data and support enterprise-wide planning, budgeting, and forecasting. The customer intends to improve the overall performance and availability of the Essbase applications to enable faster modelling and decision-making. With Oracle Cloud Infrastructure, customer benefits by eliminating hardware management and flexible scaling options for increased usage during consolidation processes.

<!--                            -->
<!-- End of 2) Business Context -->
<!--                            -->

# Workload Requirements and Architecture

## Overview

*Guide:*

*Describe the Workload: What applications and environments are part of this Workload migration or new implementation project, and what are their names? The implementation will be scoped later and can be a subset of the Solution Definition and proposed overall solution. For example, a Workload could exist of two applications, but the implementer would only include one environment of one application. The workload chapter is about the whole Workload and the implementation scope will be described late in the chapter Solution Scope.*

Example:

The current project includes provisioning of the Oracle Cloud Infrastructure infrastructure and deploying Essbase 21c via Marketplace.
This project also involves the migration of two Essbase applications from version 11.1.2.4 currently hosted on-premises and used by the customer.

The customer has 2 Essbase environments currently:

| Environment     | Description |
| -------- | ---------------- |
| PROD   | 1 single server deployed on Windows 2012 R2 STD with MS SQL Server  |
| DEV    | 1 single server deployed on Windows 2012 R2 STD with MS SQL Server   |

## Functional Requirements (Optional)

*Guide:*

*Provide a brief overview of the functional requirements, the functional area they belong to, the impacted business processes, etc.*

*Provide a formal description of the requirements as 1. a set of Use Cases or 2. a description of Functional Capabilities or 3. a Requirement Matrix. The three descriptions are not mutually exclusive.*

Example:

Oracle Essbase is a business analytics solution that uses a proven, flexible, best-in-class architecture for analysis, reporting, and collaboration. Oracle Essbase delivers instant value and greater productivity for your business users, analysts, modellers, and decision-makers, across all lines of business within your organization.

Oracle Essbase provides a complete set of tools and features for deriving and sharing data insights.
Oracle Essbase on Oracle Cloud Infrastructure (OCI) via Marketplace is a powerful analytic platform with robust new features added since Release 11g.

However, as part of the workload migration project, no functional changes are implemented to the Essbase applications. Please refer to the official documentation for differences between Essbase 11g and Essbase 21c [here] (https://docs.oracle.com/en/database/other-databases/essbase/21/essoa/differences-essbase-11g-and-essbase-21c.html)


### Use Cases (Optional)

*Guide:*

*A Use Case (UC) can be represented in a table as the following one. See https://www.visual-paradigm.com/guide/use-case/what-is-use-case-specification/ for a quick introduction to the concept of UC. See https://www.usability.gov/how-to-and-tools/methods/use-cases.html for more examples and detailed instructions.*

*Example:*

Element                         | Description
:---                            |:---
Use Case 1                      | Housekeeper does laundry
Stakeholder                     | Owner
Actor                           | Housekeeper
Use Case Overview               | It is Wednesday and there is laundry in the laundry room. The housekeeper sorts it, then proceeds to launder each load. The housekeeper folds the dry laundry as he/she removes it from the dryer. The housekeeper irons those items that need ironing.
Precondition 1                  | It is Wednesday
Precondition 2                  | There is laundry in the laundry room.
Trigger                         | Dirty laundry is transported to the laundry room on Wednesday.
Basic Flow                      | On Wednesdays, the housekeeper reports to the laundry room. The housekeeper sorts the laundry that is there. Then he/she washes each load. The housekeeper dries each load. He/She folds the items that need folding. He/She irons and hangs the wrinkled items.  The housekeeper throws away any laundry item that is irrevocably shrunken, soiled, or scorched.
Alternative Flow 1              | If he/she notices that something is wrinkled, he/she irons it and then hangs it on a hanger.
Alternative Flow 2              | If he/she notices that something is still dirty, he/she rewashes it.
Alternative Flow 3              | If he/she notices that something shrank, he/she throws it out.

### Functional Capabilities (Optional)

*Guide:*

*In specific cases, a set of Functional Capabilities can be represented in a functional decomposition diagram. This is typical of functional analysis in the System Engineering domain. For more information on Functional Analysis see, e.g. https://spacese.spacegrant.org/functional-analysis/.*

Oracle Essbase stands for Extended Spread Sheet Database. Essbase is an OLAP (Online Analytic Processing) business analysis server technology that provides an environment for rapidly developing custom analytic applications and uses complex queries to analyze aggregated historical data from OLTP systems. The multidimensional analysis uses a database that is structured on business concepts and that is designed around business needs.

In addition, Essbase is built on the middle-tier application server (Weblogic) and DB tier.
Further information can be found [here](https://docs.oracle.com/en/database/other-databases/essbase/21/essst/what-is-oracle-essbase.html)

### Requirement Matrix (Optional)

*Guide:*

*A Requirement Matrix can be used when the solution will be based on software capabilities already available in existing components (either custom or vendor provided). The Requirements Matrix is a matrix that is used to capture client requirements for software selection and to evaluate the initial functional “fit” of a vendor’s software solution to the business needs
of the client.*

*Example:*

|Requirement / Component|Currently Used|On OCI|
| :----------------------                                                              | :---------------------------------------------------- | :--------------------------------------------------                                                                                                                    |
| Essbase Server / Essbase Provider Services Web / Essbase Administration Services Web | Essbase (EPM) 11.1.2.4                    | Essbase 21c (21.X). EAS console functionalities have been replaced by Web based UI + Cube Designer                                                                     |
| Authentication                                                                       | EPM Shared Services security 11.1.2.4     | Identity Cloud Service (IDCS) proposed for the workload                                                                                                                |
| Database                                                                             |Oracle Database 19c                 | Oracle Autonomous Database (ATP) 19c proposed for the workload                                                                                                         |
| Operating System                                                                     | Microsoft Windows 2012 R2 Standard 64-bit | Oracle Linux 7.9 64-bit                                                                                                                                                |

## Non-Functional Requirements

*Guide:*

*Describe the high-level technical requirements for the Workload. Consider all sub-chapters, but decide and choose which Non-Functional Requirements are necessary for your engagement. You might not need to capture all requirements for all sub-chapters.*

*This chapter is for describing customer-specific requirements (needs), not to explain Oracle solutions or capabilities.*

### Regulations and Compliances Requirements

*Guide:*

*This section captures specific regulatory or compliance requirements for the Workload. These may limit the types of technologies that can be used and may drive some architectural decisions.*

*The Oracle Cloud Infrastructure Compliance Documents service lets you view and download compliance documents:
https://docs.oracle.com/en-us/iaas/Content/ComplianceDocuments/Concepts/compliancedocsoverview.htm*

*If there are none, then please state it. Leave the second sentence as a default in the document.*

*Example:*

At the time of this document creation, no Regulatory and Compliance requirements have been specified.

In addition to these requirements, the [CIS Oracle Cloud Infrastructure Foundation Benchmark, v1.2](https://www.cisecurity.org/benchmark/Oracle_Cloud) will be applied to the Customer tenancy.

### Environments

*Guide:*

*A diagram or list detailing all the required environments (e.g. development, text, live, production, etc).*

*If you like to describe a current state, you can use or add the chapter 'Current Sate Architecture' before the 'Future State Architecture'.*

Example:

Name	        | Size of Prod  | Location	  | DR    | Scope
:---		    |:---		   	|:---		  |:---   |:---
Production      | 100%        	| Malaga	  | Yes   | Not in Scope / On-prem
UAT              | 50%           | Sevilla     | No    | Workload
Dev      | 25%           | Sevilla     | No    | Workload - ${doc.config.impl.type}


### High Availability and Disaster Recovery Requirements

*Guide:*

*This section captures the resilience and recovery requirements for the Workload. Note that these may be different from the current system.*

*The Recovery Point Objective (RPO) and Recovery Time Objective (RTO) requirement of each environment should be captured in the environments section above, and wherever possible.*

- *What are the RTO and RPO requirements of the Application?*
- *What are the SLAs of the application?*
- *What are the backup requirements*

*Note that if needed, this section may also include an overview of the proposed backup and disaster recovery proposed architectures.*

*This chapter is mandatory, while there could be no requirements on HA/DR, please mention that in a short single sentence.*

*Example:*

At the time of this document creation, no Resilience or Recovery requirements have been specified.

#### High Availability (Optional)

*Guide:*

*A subsection, if cleaner separation of Resilience and Recovery into HA, DR, and Backup & Restore is needed.*

*Example:*

The following table captures the High availability requirements for the Production environment:

Service Name  	| KPI	            	| Unit	  	| Value
---		      		|---	            	|---	    	|---
Oracle DB		       		| Uptime	          | percent		| 99.98
Essbase Application	| Max Interruption	| minutes 	| 20

#### Disaster Recovery (Optional)

*Guide:*

*A subsection, if cleaner separation of Resilience and Recovery into HA, DR, and Backup & Restore is needed.*

*Example:*

Environment  |RPO   |RTO
--|---|--
PROD  | 24 Hours  |  4 Hours
UAT  | 24 Hours  |  4 Hours

#### Backup and Restore (Optional)

*Guide:*

*A subsection, if cleaner separation of Resilience and Recovery into HA, DR, and Backup & Restore is needed.*

*Example:*

Service Name	    | KPI		    | Unit		| Value
:---			   	|:---		    |:---		|:---
Database			    	| Frequency	  	| /day		| 2
Block Storage			    	| BckpTime (F)	| hours		| 4

Current Backup Schedule:

Currently, Essbase is backed up with some backup scripts once every day. MSSQL uses full backups once every week, incremental backups once every day and log backups once every hour.

OCI Backup Requirements:

Essbase backup and restore planning is required at both the application and instance level to have full flexibility to manage the life cycle of the Essbase instances, and also to provide disaster recovery.

Backups of individual applications protect you from application failures or application artifact corruption, and can easily be migrated between servers. When you restore a single application, there is no disruption to user activity with other applications in your instance. Essbase application backups are taken using LCM export and import commands.

Use Essbase instance backups to restore all applications on your instance to a common point in time. Instance backups are primarily for disaster recovery, but are also appropriate when you want to migrate or restore all applications at once. Backups of Essbase on OCI depend on some details of the Essbase stack. A complete backup must protect all information that makes your Essbase deployment unique. Items you may be instructed to back up include:

* Relational database schemas which store some application, user and configuration information.
* Essbase application and database information stored on a block volume mounted as /u01/data.
* WebLogic domain and configuration information stored** on a block volume mounted as /u01/config.

For OCI, the Backup tier will be set to Gold: The gold policy includes daily incremental backups, retained for seven days, along with weekly incremental backups, run on Sunday and retained for four weeks. Includes monthly incremental backups, run on the first day of the month, retained for twelve months. Also, include a full backup, run yearly, during the first part of January. This backup is retained for five years. The backups can be potentially done to a different cloud region as well. Refer to the documentation for more details: [Scheduling volume backups](https://docs.oracle.com/en-us/iaas/Content/Block/Tasks/schedulingvolumebackups.htm)

### Security Requirements

*Guide:*

*Capture the Non-Functional Requirements for security-related topics. The requirements can be separated into:*
- *Identity and Access Management*
- *Data Security*

*Other security topics, such as network security, application security, key management or others can be added if needed.*

*Example:*

At the time of this document creation, no Security requirements have been specified.

#### Identity and Access Management (Optional)

*Guide:*

*The requirements for identity and access control. This section describes any requirements for authentication, identity management, single-sign-on, and necessary integrations to retained customer systems (e.g. corporate directories).*
- *Is there any Single Sign On or Active Directory Integration Requirement?*
- *Is the OS hardened if so please share the hardening guideline.*

#### Data Security (Optional)

*Guide:*

*Capture any specific or special requirements for data security. This section should also describe any additional constraints such as a requirement for data to be held in a specific location or for data export restrictions.*

### Integration and Interfaces (Optional)

*Guide:*

*A list of all the interfaces into and out of the defined Workload. The list should detail the type of integration, the type of connectivity required (e.g. VPN, VPC, etc) the volumes, and the frequency.*
- *list of integrations*
- *list of user interfaces*

*Example:*

Name	                    | Source    	| Target	  | Protocol  | Function
:---		                |:---		    |:---		  |:---		  |:---
ELT	                       	| ODI		    | EBS DB	  | SQL Net	  | Data extraction
General Ledger Integration  | EBS           | ERP Cloud   | Batch     | Batch extraction


### System Configuration Control Lifecycle (Optional)

*Guide:*

*This section should detail the requirements for the development and deployment lifecycle across the Workload. This details how code will be deployed and how consistency across the environments will be maintained over future software deployment. This may include a need for CI/CD.*
- *Will a CI/CD tool need access to deploy to the target environment*
- *Does the customer require software to be delivered to a repository*
- *How will configuration and software be promoted through the environments*

Example:

Oracle recommends the below approach to automate continuous delivery onto servers running on OCI for customer’s application:

- Git version management
- Automating deployment
- Automate LCM export

### Operating Model (Optional)

*Guide:*

*This section captures requirements on how the system will be managed after implementation and migration. In the vast majority of cases, the solution will be handed back to the customer (or the customer's SI/partner), but in some cases, Oracle may also take on some sustaining responsibilities through ACS or OC.*

*Also, capture requirements for tools to monitor and manage the solution.*

### Management and Monitoring (Optional)

*Guide:*

*This subsection captures any requirements for integrations into the customer's existing management and monitoring systems - e.g. system monitoring, systems management, etc. Also, if the customer requires new management or monitor capabilities, these should be recorded.*

*Example:*

Tool		            | Task				     | Target		    | Location   	    | New   | Notes
:---			        |:---					 |:---		        |:---		        |:---	|:---
Splunk		            | Log Data Consolidation | All targets	    | On-Prem           | No	|
Enterprise Manager		| Manage DB Instances    | All Oracle DBs	| OCI	(Migration) | No	|

### Performance (Optional)

*Guide:*

*The performance requirements cover all aspects related to the time required to perform a given operation. They can be measured in different ways, for example: (1) AvrgTime: average response time that can be accepted for a given online or real interaction (data retrieve, data insert, etc.) (2) MaxTime: maximum response time for the same operations defined for AvrgRtime The operations can be online (user interactions), offline (batch execution) or (near)realtime (messaging).*

*Example:*

Type		  | Operation				       | KPI		  | Unit	| Value	| Notes
---			  |---					           |---		    |---		|---	  |---
Online		| Data Load (FDMEE) | MaxTime	| sec		| TBD	  | Compare selected data load times between the source and target environments
Online    | Run selected calculations in Essbase application (Essbase)  | MaxTime  | sec  | TBD  |  Compare selected calculation time in Essbase applications between the source and target environments

### Capacity (Optional)

*Guide:*

*Capacity is a measure of the total workload the system can bear without affecting performance. There are many KPIs to measure capacity, depending on the system's functionalities. Some of the most relevant KPIs are:*
- *MaxVol: maximum volume of data that can be stored in the system (can be different for different types of data, e.g. relational and file): 800-900GB current database size (probably with a significant waste of space)*
- *MaxFlow: maximum data flow (input/output) that can be managed by the system (can be two different numbers for each major system interface and/or operation): the current value has not been measured but is expected to be at most a few GB.*
- *MaxUser: maximum number of concurrent users (can be differentiated by user profile): up to 10 (number of registered users).*

*Example:*

The following table indicates the current sizing available on-premises and also outlines any additional capacity requested by the customer or required for the workload migration to OCI. In case of 1:1 sizing and no performance issues/growth considerations, the current capacity will be matched on OCI.

| System         | Capacity           | KPI                    | Unit | Value   | Notes                                                                                                                                 |
|:---------------|:-------------------|:-----------------------|:-----|:--------|:--------------------------------------------------------------------------------------------------------------------------------------|
| DB server      | DB size            | MaxVol                 | GB   | 11GB    | Metadata sizing stored on existing Production environment                                                                             |
| Essbase Server | Simultaneous users | Concurrent / Max Users | Nb   | 150/700 |                                                                                                                                       |
| Essbase Server | CPU                | usage                  | %    | 30      | Feedback from customer: cpu peak at 30% for evaluated period with Intel Xeon CPU E7-8870 v4@2.10GHz (2 processors - 40 virtual cores) |
| Essbase Server | Memory             | usage                  | %    | 24      | Feedback from customer for evaluated period for a total of 128GB RAM                                                                  |

## Constraints and Risks (Optional)

*Guide:*

*Constraints are limitations that will impact the resulting project or Solution Architecture. It is a technology- or project-related condition or event that prevents the project from fully delivering the ideal solution to customers and end-users. Constraints can be identified on our customer, partner, or even Oracle's side.*

*A project risk is an uncertain event that may or may not occur during a project.*

*Describe constraints and risks affecting the Workload and possible Logical Solution Architecture. These can be technical, but might also be non-technical. Consider budgets, timing, preferred technologies, skills in the customer organization, location, etc.*

*Example:*

Name                | Description                                                               | Type        | Impact               | Mitigation Approach
:---                |:---                                                                       |:---         |:---                  |:---
OCI skills          | Limited OCI skills in customers organization                              | Risk        | No Operating Model   | Involve Ops partner, for example, Oracle ACS
Team Availability   | A certain person is only available on Friday CET time zone                | Constraint  |                      | Arrange meetings to fit that person's availability
Access Restriction  | We are not allowed to access a certain tenancy without customer presence  | Constraint  |                      | Invite customer key person to implementation sessions

## Current State Architecture (Optional)

*Guide:*

*Provide a high-level logical description of the Workload's current state. Stay in the Workload scope, and show potential integrations, but do not try to create a full customer landscape. Use architecture diagrams to visualize the current state. I recommend not putting lists of technical resources or dependencies here. Refer to the attachments instead.*

## Future State Architecture

*Guide:*

*The Workload Future State Architecture can be described in various forms. In the easiest case, we describe a Logical Architecture, possibly with a System Context Diagram. A high-level physical architecture is mandatory as a description of your solution.*

*This should be the final architecture as part of the pre-sales solution, not an intermediate or draft version*

*Additional architectures, in the subsections, can be used to describe needs for specific workloads.*

This section describes the future state logical and physical deployment architecture of the Essbase application on Oracle Cloud Infrastructure and also lists the environments.

| Environment | Description                                                                                                 |
|:------------|:------------------------------------------------------------------------------------------------------------|
| PROD        | Public Load Balancer, Oracle ATP, single instance Essbase 21c MarketPlace (OEL) |

### Mandatory Security Best Practices

*Guide:*

*Use this text for every engagement. Do not change. Aligned with the Cloud Adoption Framework*

The safety of the ${doc.customer.name}'s Oracle Cloud Infrastructure (OCI) environment and data is the ${doc.customer.name}’s priority.
To following table of OCI Security Best Practices lists the recommended topics to provide a secure foundation for every OCI implementation. It applies to new and existing tenancies and should be implemented before the Workload defined in this document will be implemented.
Workload-related security requirements and settings like tenancy structure, groups, and permissions are defined in the respective chapters.
Any deviations from these recommendations needed for the scope of this document will be documented in chapters below. They must be approved by ${doc.customer.name}.

${doc.customer.name} is responsible for implementing, managing, and maintaining all listed topics.


Category  |Topic   |Details
--|---|--
| User Management          | IAM Default Domain        | Multi-factor Authentication (MFA) should be enabled and enforced for every non-federated OCI user account.                                                                                           |
|                          |                           | - For configuration details see Managing Multi-Factor Authentication.                          |
|                          |                           |                                                                                                                                                                                                      |
|                          |                           | In addition to enforce MFA for local users, Adaptive Security will be enabled to track the Risk Score of each user of the Default Domain.                                                            |
|                          |                           | - For configuration details see Managing Adaptive Security and Risk Providers.                                  |
|                          | OCI Emergency Users       | A maximum of three non-federated OCI user accounts should be present with the following requirements:                                                                                            |
|                          |                           | - Username does not match any username in the Customer’s Enterprise Identity Management System                                                                                                       |
|                          |                           | - Are real humans.                                                                                                                                                                                   |
|                          |                           | - Have a recovery email address that differs from the primary email address.                                                                                                                         |
|                          |                           | - User capabilities has Local Password enabled only.                                                                                                                                                 |
|                          |                           | - Has MFA enabled and enforced (see IAM Default Domain).                                                                                                                                             |
|                          | OCI Administrators        | Daily business OCI Administrators are managed by the Customer’s Enterprise Identity Management System .                                                                                              |
|                          |                           | This system is federated with the IAM Default Domain following these configuration steps:                                                                                                            |
|                          |                           | - Federation Setup                                                                                                                                                                                   |
|                          |                           | - User Provisioning                                                                                                                                                                                  |
|                          |                           | - For configuration guidance for major Identity Providers see the OCI IAM Identity Domain tutorials.                                                                                                 |
|                          | Application Users         | Application users like OS users, Database users, or PaaS users are not managed in the IAM Default Domain but either directly or in dedicated identity domains.                                       |
|                          |                           | These identity domains and users are covered in the Workload design.                                                                                                                                 |
|                          |                           | For additional information see Design Guidance for IAM Security Structure.                         |
| Cloud Posture Management | OCI Cloud Guard           | OCI Cloud Guard will be enabled at the root compartment of the tenancy home region. This way it covers all future extensions, like new regions or new compartments, of your tenancy automatically.   |
|                          |                           | It will use the Oracle Managed Detector and Responder recipes at the beginning and can be customized by the Customer to fulfil the Customer’s security requirements.                                 |
|                          |                           | - For configuration details see Getting Started with Cloud Guard.                                                             |
|                          |                           | Customization of the Cloud Guard Detector and Responder recipes to fit with the Customer’s requirements is highly recommended. This step requires thorough planning and decisions to make.           |
|                          |                           | - For configuration details see Customizing Cloud Guard Configuration                                                     |
|                          | OCI Vulnerability         | In addition to OCI Cloud Guard, the OCI Vulnerability Scanning Service will be enabled at the root compartment in the home region.                                                                   |
|                          | Scanning Service          | This service provides vulnerability scanning of all Compute instances once they are created.                                                                                                         |
|                          |                           | - For configuration details see Vulnerability Scanning.                                                                                      |
| Monitoring               | SIEM Integration          | Continuous monitoring of OCI resources is key for maintaining the required security level (see Regulations and Compliance for specific requirements).   |
|                          |                           | See Design Guidance for SIEM Integration to implement integration with the existing SIEM system.         |
| Additional Services      | Budget Control            | OCI Budget Control provides an easy to use and quick notification on changes of the tenancy’s budget consumption. It will be configured to quickly identify unexpected usage of the tenancy.         |
|                          |                           | - For configuration details see Managing Budgets                                                                     |

### OCI Secure Landing Zone Architecture

*Guide:*

*This chapter describes landing zone best practices and usually does not require any changes. The full landing zone needs to be described in the Solution Design by the service provider.*

*Use this template ONLY for new cloud deployments and remove it for brownfield deployments.*

The design considerations for an OCI Cloud Landing Zone have to do with OCI and industry architecture best practices, along with ${doc.customer.name} specific architecture requirements that reflect the Cloud Strategy (hybrid, multi-cloud, etc). An OCI Cloud Landing zone involves a variety of fundamental aspects that have a broad level of sophistication. A good summary of a Cloud Landing Zone has been published in the [OCI User Guide](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/landing-zone.htm).

# Naming Convention
*Guide*
*If the customer provides a resource naming convention use it. They should have it already for their on-premises compute resources.*

A naming convention is an important part of any deployment to ensure consistency as well as security within your tenancy. Hence, we jointly agree on a naming convention, matching Oracle's best practices and ${doc.customer.name} requirements.

Oracle recommends the following Resource Naming Convention:

- The name segments are separated by “-“
- Within a name segment avoid using <space> and “.”
- Where possible intuitive/standard abbreviations should be considered (e.g. “shared“ compared to "shared.cloud.team”)
- When referring to the compartment full path, use “:” as a separator, e.g. cmp-shared:cmp-security

Some examples of naming are given below:

- cmp-shared
- cmp-\<workload>
- cmp-networking

The patterns used are these:

- \<resource-type>-\<environment>-\<location>-\<purpose>
- \<resource-type>-\<environment>-\<source-location>-\<destination-location>-\<purpose>
- \<resource-type>-\<entity/sub-entity>-\<environment>-\<function/department>-\<project>-\<custom>
- \<resource-type>-\<environment>-\<location>-\<purpose>

Abbreviations per resource type are listed below. This list may not be complete.

| Resource Type | Abbreviation | Example |
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

# Security and Identity Management

This chapter covers the Security and Identity Management definitions and resources which will be implemented for ${doc.customer.name}.

## Universal Security and Identity and Access Management Principles

- Groups will be configured at the tenancy level and access will be governed by policies configured in OCI.
- Any new project deployment in OCI will start with the creation of a new compartment. Compartments follow a hierarchy, and the compartment structure will be decided as per the application requirements.
- It is also proposed to keep any shared resources, such as Object Storage, Networks, etc. in a shared services compartment. This will allow the various resources in different compartments to access and use the resources deployed in the shared services compartment and user access can be controlled by policies related to specific resource types and user roles.
- Policies will be configured in OCI to maintain the level of access/control that should exist between resources in different compartments. These will also control user access to the various resources deployed in the tenancy.
- The tenancy will include a pre-provisioned Identity Cloud Service (IDCS) instance (the primary IDCS instance) or, where applicable, the Default Identity Domain. Both provide access management across all Oracle cloud services for IaaS, PaaS, and SaaS cloud offerings.
- The primary IDCS or the Default Identity Domain will be used as the access management system for all users administrating (OCI Administrators) the OCI tenant.

## Authentication and Authorization for OCI

The provisioning of respective OCI administration users will be handled by ${doc.customer.name}.

### User Management

Only OCI Administrators are granted access to the OCI Infrastructure. As a good practice, these users are managed within the pre-provisioned and pre-integrated Oracle Identity Cloud Service (primary IDCS) or, where applicable, the OCI Default Identity Domain, of OCI tenancy. These users are members of groups. IDCS Groups can be mapped to OCI groups while Identity Domains groups do not require any mapping. Each mapped group membership will be considered during login.

**Local Users**

The usage of OCI Local Users is not recommended for the majority of users and is restricted to a few users only. These users include the initial OCI Administrator created during the tenancy setup and additional emergency administrators.

**Local Users are considered Emergency Administrators and should not be used for daily administration activities!**

**No additional users are to be, nor should be, configured as local users.**

**${doc.customer.name} is responsible to manage and maintain local users for emergency use cases.**

**Federated Users**

Unlike Local Users, Federated Users are managed in the Federated or Enterprise User Management system. In the OCI User list Federated Users may be distinguished by a prefix that consists of the name of the federated service in lower case, a '/' character followed by the user name of the federated user, for example:

`oracleidentityservicecloud/user@example.com`

Providing the same attributes (OCI API Keys, Auth Tokens, Customer Secret Keys, OAuth 2.0 Client Credentials, and SMTP Credentials) for Local and *Federated Users* federation with third-party Identity Providers should only be done in the pre-configured primary IDCS or the Default Identity Domain where applicable.

All users have the same OCI-specific attributes (OCI API Keys, Auth Tokens, Customer Secret Keys, OAuth 2.0 Client Credentials, and SMTP Credentials).

OCI Administration users should only be configured in the pre-configured primary IDCS or the Default Identity Domain where applicable.

**Note:** Any federated user can be a member of 100 groups only. The OCI Console limits the number of groups in a SAML assertion to 100 groups. User Management in the Enterprise Identity Management system will be handled by ${doc.customer.name}.

**Authorization**

In general, policies hold permissions granted to groups. Policy and Group naming follows the Resource Naming Conventions.

**Tenant Level Authorization**

The policies and groups defined at the tenant level will provide access to administrators and authorized users, to manage or view resources across the entire tenancy. The tenant-level authorization will be granted to tenant administrators only.

These policies follow the recommendations of the [CIS Oracle Cloud Infrastructure Foundations Benchmark v1.2.0, recommendations 1.1, 1.2, 1.3](https://www.cisecurity.org/cis-benchmarks).

**Service Policy**

A Service Policy is used to enable services at the tenancy level. It is not assigned to any group.

**Shared Compartment Authorization**

Compartment-level authorization for the cmp-shared compartment structure uses the following specific policies and groups.

Apart from tenant-level authorization, authorization for the cmp-shared compartment provides specific policies and groups. In general, policies will be designed so that lower-level compartments are not able to modify the resources of higher-level compartments.

Policies for the cmp-shared compartment follow the recommendations of the [CIS Oracle Cloud Infrastructure Foundations Benchmark v1.2.0, recommendations 1.1, 1.2, 1.3](https://www.cisecurity.org/cis-benchmarks).

**Compartment Level Authorization**

Apart from tenant-level authorization, compartment-level authorization provides compartment structure-specific policies and groups. In general, policies will be designed so that lower-level compartments are not able to modify the resources of higher-level compartments.

**Authentication and Authorization for Applications and Databases**

Application (including Compute Instances) and Database User management are completely separate and done outside the primary IDCS or Default Identity Domain. The management of these users is the sole responsibility of ${doc.customer.name} using the application, compute instance, and database-specific authorization.

## Security Posture Management

**Oracle Cloud Guard**

Oracle Cloud Guard Service will be enabled using the pcy-service policy and with the following default configuration. Customization of the Detector and Responder Recipes will result in clones of the default (Oracle Managed) recipes.

Cloud Guard default configuration provides several good settings. It is expected that these settings may not match ${doc.customer.name}'s requirements.

**Targets**

In accordance with the [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.2.0, Chapter 3.15](https://www.cisecurity.org/cis-benchmarks), Cloud Guard will be enabled in the root compartment.

**Detectors**

The Oracle Default Configuration Detector Recipes and Oracle Default Activity Detector Recipes are implemented. To better meet the requirements, the default detectors must be cloned and configured by ${doc.customer.name}.

**Responder Rules**

The default Cloud Guard Responders will be implemented. To better meet the requirements, the default detectors must be cloned and configured by ${doc.customer.name}.

**Vulnerability Scanning Service**

In accordance with the [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.2.0, OCI Vulnerability Scanning](https://www.cisecurity.org/cis-benchmarks) will be enabled using the pcy-service policy.

Compute instances that should be scanned *must* implement the *Oracle Cloud Agent* and enable the *Vulnerability Scanning plugin*.

**OCI OS Management Service**

Required policy statements for OCI OS Management Service are included in the pcy-service policy.

By default, the *OS Management Service Agent plugin* of the *Oracle Cloud Agent* is enabled and running on current Oracle Linux 6, 7, 8, and 9 platform images.

## Monitoring, Auditing, and Logging

In accordance with the [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.2.0, Chapter 3 Logging and Monitoring](https://www.cisecurity.org/cis-benchmarks) the following configurations will be made:

- OCI Audit log retention period set to 365 days.
- At least one notification topic and subscription to receive monitoring alerts.
- Notification for Identity Provider changes.
- Notification for IdP group mapping changes.
- Notification for IAM policy changes.
- Notification for IAM group changes.
- Notification for user changes.
- Notification for VCN changes.
- Notification for changes to route tables.
- Notification for security list changes.
- Notification for network security group changes.
- Notification for changes to network gateways.
- VCN flow logging for all subnets.
- Write level logging for all Object Storage Buckets.
- Notification for Cloud Guard detected problems.
- Notification for Cloud Guard remedied problems.

For IDCS or OCI Identity Domain Auditing events, the respective Auditing API can be used to retrieve all required information.

## Data Encryption

All data will be encrypted at rest and in transit. Encryption keys can be managed by Oracle or the customer and will be implemented for identified resources.

### Key Management

All keys for **OCI Block Volume**, **OCI Container Engine for Kubernetes**, **OCI Database**, **OCI File Storage**, **OCI Object Storage**, and **OCI Streaming** are centrally managed in a shared or a private virtual vault will be implemented and placed in the compartment cmp-security.

**Object Storage Security**

For Object Storage security the following guidelines are considered.

- **Access to Buckets** -- Assign least privileged access for IAM users and groups to resource types in the object-family (Object Storage Buckets & Object)
- **Encryption at rest** -- All data in the Object Storage is encrypted at rest using AES-256 and is on by default. This cannot be turned off and objects are encrypted with a master encryption key.

**Data Residency**

It is expected that data will be held in the respective region and additional steps will be taken when exporting the data to other regions to comply with the applicable laws and regulations. This should be reviewed for every project onboard into the tenancy.

## Operational Security

**Security Zones**

Whenever possible OCI Security Zones will be used to implement a security compartment for Compute instances or Database resources. For more information on Security Zones refer to the *Oracle Cloud Infrastructure User Guide* chapter on [Security Zones](https://docs.oracle.com/en-us/iaas/security-zone/using/security-zones.htm).

**Remote Access to Compute Instances or Private Database Endpoints**

To allow remote access to Compute Instances or Private Database Endpoints, the OCI Bastion will be implemented for defined compartments.

To be able to use OCI services for OS management, Vulnerability Scanning, Bastion Service, etc. it is highly recommended to implement the Oracle Cloud Agent as documented in the *Oracle Cloud Infrastructure User Guide* chapter [Managing Plugins with Oracle Cloud Agent](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/manage-plugins.htm).

## Network Time Protocol Configuration for Compute Instance

Synchronized clocks are a necessity for securely operating environments. OCI provides a Network Time Protocol (NTP) server using the OCI global IP number 169.254.169.254. All compute instances should be configured to use this NTP service.

## Regulations and Compliance

${doc.customer.name} is responsible for setting the access rules to services and environments that require stakeholders’ integration into the tenancy to comply with all applicable regulations. Oracle will support in accomplishing this task.


### Functional Architecture (Optional)

*Guide:*

*Provide a brief description of the functional architecture, split into two main areas: application capabilities and data.*

### Logical Architecture (Optional)


*Guide:*

*Use [System Context Diagram](https://online.visual-paradigm.com/knowledge/system-context-diagram/what-is-system-context-diagram/) to show integration for the Workload solution.*

*Provide a high-level logical Oracle solution for the complete Workload. Indicate Oracle products as abstract groups, and not as physical detailed instances. Create an architecture diagram following the latest notation and describe the solution.*

*[The Oracle Cloud Notation, OCI Architecture Diagram Toolkits](https://docs.oracle.com/en-us/iaas/Content/General/Reference/graphicsfordiagrams.htm)*

Example:

Based on the customer requirements, the future state logical architecture of Essbase on OCI is depicted below.

![Future Logical Architecture](images/essbase-architecture-logical.png)

The main building blocks that compose this cloud architecture:

* __Essbase 21c__: The targeted version of Essbase on OCI will be Essbase 21C (21.3). Essbase 21c will be deployed via Oracle Cloud Infrastructure Marketplace.

* Database for Essbase metadata: Autonomous Database using the __Autonomous Transaction Processing workload__ (ATP). ATP is proposed to evaluate exclusive functionalities for federated partitions. ATP is a managed database integrated with Object Storage and optimized for analytical queries. Federated partitions enable integration of Essbase cubes with Autonomous Data Warehouse, to combine Essbase's analytical power with the benefits of the Autonomous Database.


### Physical Architecture

*Guide:*

*The Workload Architecture is typically described in a physical form. This should include all solution components. You do not have to provide solution build or deployment details such as IP addresses.*

*Please describe the solution as a written text. If you have certain specifics you like to explain, you can also use the Solution Consideration chapter to describe the details there.*

*[The Oracle Cloud Notation, OCI Architecture Diagram Toolkits](https://docs.oracle.com/en-us/iaas/Content/General/Reference/graphicsfordiagrams.htm)*

*Example:*

Essbase sizing on OCI for **Test environment** (current Workload) is reflected in the below table "Sizing Inputs" for the Test environment.

| Description                                                     | Value                                                                      |
|-----------------------------------------------------------------|----------------------------------------------------------------------------|
| Number of Expected Concurrent Users                             | 10 peak                                                                     |
| Bastion?                                                        | **Bastion Host on Windows proposed for orchestration/integration testing** |
| Number of Planned Essbase Databases                             | 2 monthly reporting apps                                                   |
| Avg Size of Planned Essbase Database (in GB)                    | 15GB                                                                       |
| Number of Essbase Database Planned to be Loaded from Flat Files | **TBC**                                                                    |
| Number of Planned Monthly Database Backups (ATP/DBCS)           | 4                                             |
| Additional Planned Custom Object Storage (in GB)                |200                                             |
| Number of Planned Monthly Essbase Backups                       | 4                                             |
| # of Planned Essbase Instances                                  | 1                                                                 |
| Share ATP/DBCS for Essbase Instance Repository?                 | No                                                                |
| Include a Load Balancer?                                        | Yes                                                                        |
| Load Balancer Shape                                             | Flexible Shape                                                             |
| Key Management System                                           | No (Test environment)                                             |


The diagram below depicts Physical architecture.

![Future State Deployment Diagram - EBS Workload Multi-AD, DR Design Diagram](images/essbase-architecture-physical.png)

* **One instance of __Essbase 21c__** will be provisioned in a private subnet in a dedicated compartment.
* **One instance of Autonomous Database ATP** will be provisioned with a private endpoint in a dedicated compartment.
* The other OCI services are already ready to use when the tenancy was created: Oracle Cloud Infrastructure Object Storage, Oracle Cloud Infrastructure Logging, Oracle Cloud Infrastructure Monitoring, Oracle Identity Cloud Service and Identity and Access Management.

### Data Architecture (Optional)

*Guide:*

*Show how data is acquired, transported, stored, queried, and secured as in the scope of this Workload. This could include Data Ecosystem Reference Architectures, Master Data Management models, or any other data-centric model.*

## Solution Considerations

*Guide:*

*Describe certain aspects of your solution in detail. What are the security, resilience, networking, and operations decisions you have taken that are important for your customer?*

### High Availability and Disaster Recovery

*Reference:*

[High Availability: Configure Essbase Failover Cluster](https://docs.oracle.com/en/database/other-databases/essbase/21/essoa/configure-essbase-servers-failover-cluster.html)

### Security

*Guide:*

*Please describe your solution from a security point of view. Generic security guidelines are in the Annex chapter.*

Please see our security guidelines in the [Annex](#security-guidelines).

### Networking

*Reference:*

[Overview of Networking in OCI](https://docs.public.oneportal.content.oci.oraclecloud.com/en-us/iaas/Content/Network/Concepts/landing.htm)

### Operations (Optional)

*Guide:*

*In this chapter, we provide a high-level introduction to various operations-related topics around OCI. We do not design, plan or execute any detailed operations for our customers. We can provide some best practices and workload-specific recommendations.*

*Example:*

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


## Roadmap (Optional)

*Guide:*

*Explain a high-level roadmap for this Workload. Include a few easy high-level steps to success (See Business Context). Include implementation services (if possible) as a first fast step. Add other implementation partners and their work as part of your roadmap as well. Do not include details about the implementation scope or timeline. This is not about product roadmaps.*

## Sizing and Bill of Materials

*Guide:*

*Estimate and size the physically needed resources of the Workload. The information can be collected and is based upon previously gathered capacities, business user numbers, integration points, or translated existing on-premises resources. The sizing is possibly done with or even without a Physical Architecture. It is ok to make assumptions and to clearly state them!*

<!--                                                 -->
<!-- End of 3) Workload Requirements and Architecture -->
<!--                                                 -->



# Glossary (Optional)

*Guide:*

*A chapter for Product, Technology, or Concept descriptions*

*Please avoid describing products, and linking to product documentation at the first occurrence of a product.*

*Example:*

You can learn about Oracle Cloud Infrastructure terms and concepts in this [glossary](https://docs.oracle.com/en-us/iaas/Content/libraries/glossary/glossary-intro.htm). Further terms, product names, or concepts are described below in each subsection.

## 2-Factor Authentication

*Example:*

A second verification factor is required each time that a user signs in. Users can't sign in using just their username and password.

For more information please visit our documentation for [Administering Oracle Identity Cloud](https://docs.oracle.com/en/cloud/paas/identity-cloud/uaids/enable-multi-factor-authentication-security-oracle-cloud.html).

## Other

# Annex

# Security Guidelines

## Oracle Security, Identity, and Compliance

Oracle Cloud Infrastructure (OCI) is designed to protect customer workloads with a security-first approach across compute, network, and storage – down to the hardware. It’s complemented by essential security services to provide the required levels of security for your most business-critical workloads.

- [Security Strategy](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/security-strategy.htm) – To create a successful security strategy and architecture for your deployments on OCI, it's helpful to understand Oracle's security principles and the OCI security services landscape.
- The [security pillar capabilities](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/security.htm#capabilities) pillar capabilities reflect fundamental security principles for architecture, deployment, and maintenance. The best practices in the security pillar help your organization to define a secure cloud architecture, identify and implement the right security controls, and monitor and prevent issues such as configuration drift.

### References

- The Best Practices Framework for OCI provides architectural guidance about how to build OCI services in a secure fashion, based on recommendations in the [Best practices framework for Oracle Cloud Infrastructure](https://docs.oracle.com/en/solutions/oci-best-practices).
- Learn more about [Oracle Cloud Security Practices](https://www.oracle.com/corporate/security-practices/cloud/).
- For detailed information about security responsibilities in Oracle Cloud Infrastructure, see the [Oracle Cloud Infrastructure Security Guide](https://docs.oracle.com/iaas/Content/Security/Concepts/security_guide.htm).

## Compliance and Regulations

Cloud computing is fundamentally different from traditionally on-premises computing. In the traditional model, organizations are typically in full control of their technology infrastructure located on-premises (e.g., physical control of the hardware, and full control over the technology stack in production). In the cloud, organizations leverage resources and practices that are under the control of the cloud service provider, while still retaining some control and responsibility over other components of their IT solution. As a result, managing security and privacy in the cloud is often a shared responsibility between the cloud customer and the cloud service provider. The distribution of responsibilities between the cloud service provider and customer also varies based on the nature of the cloud service (IaaS, PaaS, SaaS).

# Additional Resources
- [Oracle Cloud Compliance](https://www.oracle.com/corporate/cloud-compliance/) – Oracle is committed to helping customers operate globally in a fast-changing business environment and address the challenges of an ever more complex regulatory environment. This site is a primary reference for customers on Shared Management Model with Attestations and Advisories.
- [Oracle Security Practices](https://www.oracle.com/corporate/security-practices/) – Oracle’s security practices are multidimensional, encompassing how the company develops and manages enterprise systems, and cloud and on-premises products and services.
- [Oracle Cloud Security Practices](https://www.oracle.com/corporate/security-practices/cloud/) documents.
- [Contract Documents](https://www.oracle.com/contracts/cloud-services/#online) for Oracle Cloud Services.
- [OCI Shared Security Model](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/security.htm#shared-security-model)
- [OCI Cloud Adoption Framework Security Strategy](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/security-strategy.htm)
- [OCI Security Guide](https://docs.oracle.com/en-us/iaas/Content/Security/Concepts/security_guide.htm)
- [OCI Cloud Adoption Framework Security chapter](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/security.htm)


<!--
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢠⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠸⣷⣦⣀⠀⠀⠀⠀⠀⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠙⣿⣿⣿⣦⠀⠠⠾⠿⣿⣷⠀⠀⠀⠀⠀⣠⣤⣄⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠟⢉⣠⣤⣶⡆⠀⣠⣈⠀⢀⣠⣴⣿⣿⠋⠀⠀⠀⠀
⠀⢀⡀⢀⣀⣀⣠⣤⡄⢀⣀⡘⣿⣿⣿⣷⣼⣿⣿⣷⡄⠹⣿⡿⠁⠀⠀⠀⠀⠀
⠀⠀⠻⠿⢿⣿⣿⣿⠁⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣟⣁⠀⠋⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠈⠻⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⢰⣄⣀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣠⡀⠀⣴⣿⣿⣿⣿⣿⣿⣿⡿⢿⡿⠀⣾⣿⣿⣿⣿⣶⡄⠀
⠀⠀⠀⠀⠀⢀⣾⣿⣷⡀⠻⣿⣿⡿⠻⣿⣿⣿⣿⠀⠀⠈⠉⠉⠉⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣠⣾⡿⠟⠉⠉⠀⢀⡉⠁⠀⠛⠛⢉⣠⣴⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠈⠉⠉⠀⠀⠀⠀⠀⢸⣿⣿⡿⠉⠀⠙⠿⣿⣿⣧⡀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⠁⠀⠀⠀⠀⠀⠙⠿⣷⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠟⠀⠀⠀⠀⠀⠀⠀⠀⠃⠀⠀⠀⠀⠀⠀⠀

        Have a great summer 2023!⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
-->
