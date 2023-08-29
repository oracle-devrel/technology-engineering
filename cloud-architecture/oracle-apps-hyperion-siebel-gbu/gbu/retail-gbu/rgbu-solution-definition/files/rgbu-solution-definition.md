---
doc:
  author: Name Surname                  #Mandatory
  version: 1.2                          #Mandatory
  cover:                                #Mandatory
    title:                              #Mandatory
      - ${doc.customer.name}            #Mandatory
      - RGBU Applications to OCI        #Mandatory
    subtitle:                           #Mandatory
      - Solution Definition             #Mandatory
  customer:                             #Mandatory
    name: \<Customer Name\>             #Mandatory
    alias: \<Customer Alias\>           #Mandatory
  config:
    impl:
      type: \<Service Provider\>        #Mandatory: Can be 'Oracle Lift', 'Oracle Fast Start', 'Partner' etc. Use with ${doc.config.impl.type}     
      handover: ${doc.customer.name}    #Mandatory: Please specify to whom to hand over the project after implementation. eg.: The Customer, a 3rd party implementation or operations partner, etc.           
  draft: false
  history:
    - version: 1.0
      date: 1st June 2023
      authors: 
        - ${doc.author}
      comments:
        - Created a new Solution Definition document. To be used for iterative review and improvement.
    - version: 1.1
      date: 1st July 2023
      authors: ${doc.author}
      comments:
        - Update Template per feedback. Added security-templated texts and annex.
    - version: 1.2
      date: 1st August 2023
      authors: ${doc.author}
      comments:
        - Update Template per feedback.
  team:
    - name: ${doc.author}
      email: example@example.com
      role: Tech Solution Specialist
      company: AMCE
    - name: Ada Lovelace
      email: example@example.com
      role: Account Cloud Engineer
      company: ACME
  acronyms:
    Dev: Development
---

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

| Version | Authors | Date   | Comments      |
|---------|---------|--------|---------------|
| 0.1     | Name    | Aug 23 | initial draft |

## Team

*Guide:*

*A section describing the Oracle team.*

*Example:*

| Name  | Email | Role | Company |
|-------|-------|------|---------|
| Ada Lovelace  | ada@example.com | Account Cloud Engineer | ACME |


## Abbreviations and Acronyms (Optional)

*Guide:*

*If needed, maintain a list of:*
- *Abbreviation: a shortened form of a word or phrase.*
- *Acronyms: an abbreviation formed from the initial letters of other words and pronounced as a word (e.g. ASCII, NASA ).*

*Example:*

| Term    | Meaning                              |
|---------|--------------------------------------|
|RMS      | Retail Merchandising System          |
|ReIM     | Retail Invoice Matching              |
|ReSA     | Retail Sales Audit                   |
|RTM      | Retail Trade Management              |
|RPM      | Retail Price Management              |
|RIB      | Retail Integration Bus               |
|RFI      | Retail Financials Integration        |
|RPAS     | Retail Predictive Application Server |
|SIM      | Store Inventory Management           |
|RWMS     | Warehouse Management System          |


## Document Purpose

*Guide:*

*Describe the purpose of this document and the Oracle-specific terminology, specifically around 'Workload'.*

*Example:*


This document provides a high-level solution definition for the Oracle solution and aims at describing the current state and to-be state

The document may refer to a 'Workload', which summarizes the full technical solution for a customer (You) during a single engagement. The Workload is described in chapter [Workload Requirements and Architecture](#workload-requirements-and-architecture). 

This is a living document, additional sections will be added as the engagement progresses resulting in a final workload architecture to be handed over at the end of the customer engagement. Where Oracle Lift is involved, certain sections will only be completed after customer acceptance of the content of the Workload Architecture document as it stands at the time acceptance is requested.


<!--                            -->
<!-- End of 1) Document Control -->
<!--                            -->

# Business Context

*Guide:*

*Describe the customer's business and background. What is the context of the customer's industry and LoB? What are the business needs and goals which this Workload is an enabler for? How does this technical solution impact and support the customer's business goals? Does this solution support a specific customer strategy, or maybe certain customer values? How does this solution help our customers to either generate more revenue or save costs?*

## Executive Summary

*Guide:*

*A section describing the Oracle differentiator and key values of the solution of our solution for the customer, allowing the customer to make decisions quickly.*

*Example:*

 - Brief history of the Customer
 - Current Solution and Rationale for moving to Oracle Cloud Infrastructure (OCI)

## Workload Business Value

*Guide:*

*A clear statement of specific business value as part of the full workload scope. Try to keep it SMART: Specific, Measurable, Assignable, Realistic, and Time-Related - Agree on the business value with the customer. Keep it business-focused, and speak the language of the LoB which benefits from this Workload: "Increase Customer Retention by 3% in the next year" or "Grow Customer Base with Executive Decision-Making from our Sales and Support Data". Avoid technical success criteria such as "Migrate App X to Oracle Cloud" or "Provision 5 Compute Instances". Avoid Oracle success criteria and language "Get Workload Consuming on OCI".*

Oracle Retail's solution portfolio allows retailers to drive performance, deliver critical insights, fuel growth across all channels, and deliver what customers want most: empowered commerce.


<!--                            -->
<!-- End of 2) Business Context -->
<!--                            -->

# Workload Requirements and Architecture

## Overview

*Guide:*

*Describe the Workload: What applications and environments are part of this Workload migration or new implementation project, and what are their names? The implementation will be scoped later and can be a subset of the Solution Definition and proposed overall solution. For example, a Workload could exist of two applications, but the implementer would only include one environment of one application. The workload chapter is about the whole Workload and the implementation scope will be described late in the chapter [Solution Scope](#solution-scope).*

## Functional Requirements (Optional)

*Guide:*

*Provide a brief overview of the functional requirements, the functional area they belong to, the impacted business processes, etc.*

*Provide a formal description of the requirements as 1. a set of Use Cases or 2. a description of Functional Capabilities or 3. a Requirement Matrix. The three descriptions are not mutually exclusive.*

*Some Workload teams, especially the Analytics and Merging Tech teams, will create new applications based on functional requirements, some Workload teams will not touch the functional requirements at all and just change the platform under an application. But it is important to understand who is using the system and for what reason.*

### Use Cases (Optional)

*Guide:*

*A Use Case (UC) can be represented in a table as the following one. See https://www.visual-paradigm.com/guide/use-case/what-is-use-case-specification/ for a quick introduction to the concept of UC. See https://www.usability.gov/how-to-and-tools/methods/use-cases.html for more examples and detailed instructions.*

All use cases are listed in the **Oracle Retail Reference Model (RRM)** available on My Oracle Support website [(Doc ID 2058843.2)](https://support.oracle.com/epmos/faces/DocumentDisplay?id=2058843.2).


### Functional Capabilities (Optional)

*Guide:*

*In specific cases, a set of Functional Capabilities can be represented in a functional decomposition diagram. This is typical of functional analysis in the System Engineering domain. For more information on Functional Analysis see, e.g. https://spacese.spacegrant.org/functional-analysis/.*

All functional capabilities are listed in the **Oracle Retail Reference Model (RRM)** available on My Oracle Support website [(Doc ID 2058843.2)](https://support.oracle.com/epmos/faces/DocumentDisplay?id=2058843.2).

### Requirement Matrix (Optional)

*Guide:*

*A Requirement Matrix can be used when the solution will be based on software capabilities already available in existing components (either custom or vendor provided). The Requirements Matrix is a matrix that is used to capture client requirements for software selection and to evaluate the initial functional “fit” of a vendor’s software solution to the business needs
of the client.*

*Example:*

For example, rows can list required functional capabilities and columns can list available software components. Cells can contain a simple Y/N or provide more detail. The Requirements Matrix also is used to identify initial functional gaps or special software enhancements needed to enable each vendor’s software to fulfill the client’s desired system capabilities.

Please refer to the ["Oracle Retail Certification Matrix (Doc ID 857142.1)"](https://support.oracle.com/epmos/faces/DocumentDisplay?id=857142.1) on My Oracle Support website.


## Non-Functional Requirements

*Guide:*

*Describe the high-level technical requirements for the Workload. Consider all sub-chapters, but decide and choose which Non-Functional Requirements are necessary for your engagement. You might not need to capture all requirements for all sub-chapters.*

*This chapter is for describing customer-specific requirements (needs), not to explain Oracle solutions or capabilities.*

### Regulations and Compliances Requirements

*Guide:*

*This section captures specific regulatory or compliance requirements for the Workload. These may limit the types of technologies that can be used and may drive some architectural decisions.*

*The Oracle Cloud Infrastructure Compliance Documents service lets you view and download compliance documents:
https://docs.oracle.com/en-us/iaas/Content/ComplianceDocuments/Concepts/compliancedocsoverview.htm*

*If there are none, then please state it. Leave the second sentance as a default in the document.*

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
DR              | 50%           | London      | No    | Workload
Dev & Test      | 25%           | Frankfurt   | No    | Workload - ${doc.config.impl.type}


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

*A subsubsection, if cleaner separation of Resilience and Recovery into HA, DR, and Backup & Restore is needed.*

*Example:*

Service Name  	| KPI	            | Unit	  	| Value
:---		    |:---	            |:---	    |:---
DB		       	| Uptime	        | percent	| 99.98
Web Application	| Max Interruption	| minutes 	| 20


*Reference:*

[Case Study: Creating a High Availability Environment for Oracle Retail](https://support.oracle.com/epmos/faces/DocumentDisplay?id=2151366.1) on My Oracle Support website.

#### Disaster Recovery (Optional)

*Guide:*

*A subsubsection, if cleaner separation of Resilience and Recovery into HA, DR, and Backup & Restore is needed.*

*Example:*

Service Name   	| KPI		| Unit		| Value
:---		    |:---		|:---	    |:---
RMS	| RTO		| minutes	| 180
RMS	| RPO		| minutes	| 30
RPM	| RTO		| minutes	| 120
RPM	| RPO		| minutes	| 10
SIM	| RTO		| minutes	| 120
SIM	| RPO		| minutes	| 10
RPM	| RTO		| minutes	| 240
RPM	| RPO		| minutes	| 5

#### Backup and Restore (Optional)

*Guide:*

*A subsubsection, if cleaner separation of Resilience and Recovery into HA, DR, and Backup & Restore is needed.*

*Example:*

Service Name	    | KPI		    | Unit		| Value
:---			   	|:---		    |:---		|:---
RMS			    	| Frequency	  	| /day		| 2
RMS			    	| BckpTime (F)	| hours		| 4
RMS			    	| BckpTime (I)	| hours		| 1

### Security Requirements

*Guide:*

*Capture the Non-Functional Requirements for security-related topics. Security is a mandatory subsection that is to be reviewed by the x-workload security team. The requirements can be separated into:*
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

Name         | Source  | Target    | Protocol   | Function
:---         |:---     |:---       |:---        |:---
Financials   | EBS     | RMS       | RFI        | Data collection
Price tags   | SIM     | printers  | file based | Data extraction


### System Configuration Control Lifecycle (Optional)

*Guide:*

*This section should detail the requirements for the development and deployment lifecycle across the Workload. This details how code will be deployed and how consistency across the environments will be maintained over future software deployment. This may include a need for CI/CD.*
- *Will a CI/CD tool need access to deploy to the target environment*
- *Does the customer require software to be delivered to a repository*
- *How will configuration and software be promoted through the environments*


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

Type		| Operation				 | KPI		| Unit	| Value	  | Notes
:---		|:---					 |:---	    |:---	|:---	  |:---
Online		| Retrieve customer data | MaxTime	| sec	| 3		  |
Online		| Retrieve customer data | AvrgTime	| sec	| 0.2	  |
Realtime	| Receive MQTT message	 | AvrgTime	| msec	| 100	  | From arrival at Internet router

### Capacity (Optional)

*Guide:*

*Capacity is a measure of the total workload the system can bear without affecting performance. There are many KPIs to measure capacity, depending on the system's functionalities. Some of the most relevant KPIs are:*
- *MaxVol: maximum volume of data that can be stored in the system (can be different for different types of data, e.g. relational and file): 800-900GB current database size (probably with a significant waste of space)*
- *MaxFlow: maximum data flow (input/output) that can be managed by the system (can be two different numbers for each major system interface and/or operation): the current value has not been measured but is expected to be at most a few GB.*
- *MaxUser: maximum number of concurrent users (can be differentiated by user profile): up to 10 (number of registered users).*

*Example:*

System      | Capacity                | KPI		  | Unit   | Value    | Notes
:---		|:---					  |:---		  |:---	   |:---	  |:---
DB server	| DB size                 | MaxVol	  | GB     | 2000	  |
ETL Server  | Data processed nightly  | MaxFlow	  | GB/h   | 100	  |
OAC Server  | Simultaneous users      | MaxUsers  | -	   | 10	      |

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

### Mandatory Security Best Practices

*Guide:*

*Use this text for every engagament. Do not change. Aligned with the Cloud Adoption Framework*

### OCI Secure Landing Zone Architecture

*Guide:*

*This chapter describes landing zone best practices and usually does not require any changes. The full landing Zone needs to be described in the Solution Design by the service provider.*

*Use this section ONLY for new cloud deployments and remove for brown field deployments.*

The design considerations for an OCI Cloud Landing Zone have to do with OCI and industry architecture best practices, along with customer-specific architecture requirements that reflect the Cloud Strategy (hybrid, multi-cloud, etc). An OCI Cloud Landing zone involves a variety of fundamental aspects that have a broad level of sophistication. Oracle Cloud Infrastructure (OCI) provides multiple landing zone implementations that you can choose from [link](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/technology-implementation.htm).

### Functional Architecture (Optional)

*Guide:*

*Provide a brief description of the functional architecture, split into two main areas: application capabilities and data.*

### Logical Architecture (Optional)

*Guide:*

*Use [System Context Diagram](https://online.visual-paradigm.com/knowledge/system-context-diagram/what-is-system-context-diagram/) to show integration for the Workload solution.*

*Provide a high-level logical Oracle solution for the complete Workload. Indicate Oracle products as abstract groups, and not as physical detailed instances. Create an architecture diagram following the latest notation and describe the solution.*

*[The Oracle Cloud Notation, OCI Architecture Diagram Toolkits](https://docs.oracle.com/en-us/iaas/Content/General/Reference/graphicsfordiagrams.htm)*


*Example:*

![Future State Logical Architecture](images/rgbu-logical-arch.drawio.png)

### Physical Architecture

*Guide:*

*The Workload Architecture is typically described in a physical form. This should include all solution components. You do not have to provide solution build or deployment details such as IP addresses.*

*Please describe the solution as a written text. If you have certain specifics you like to explain, you can also use the Solution Consideration chapter to describe the details there.*

*[The Oracle Cloud Notation, OCI Architecture Diagram Toolkits](https://docs.oracle.com/en-us/iaas/Content/General/Reference/graphicsfordiagrams.htm)*


*Example:*

![Future State Deployment Diagram - RGBU Workload Multi-AD](images/rgbu-physical-arch.drawio.png)

### Data Architecture (Optional)

*Guide:*

*Show how data is acquired, transported, stored, queried, and secured as in the scope of this Workload. This could include Data Ecosystem Reference Architectures, Master Data Management models, or any other data-centric model.*

## Solution Considerations

*Guide:*

*Describe certain aspects of your solution in detail. What are the security, resilience, networking, and operations decisions you have taken that are important for your customer?*

### High Availability and Disaster Recovery 


*Reference:*

[Case Study: Creating a High Availability Environment for Oracle Retail](https://support.oracle.com/epmos/faces/DocumentDisplay?id=2151366.1) on My Oracle Support website.

### Security

*Guide:*

*Please describe your solution from a security point of view. Generic security guidelines are in the Annex chapter.*

*Example:*

Please see our security guidelines in the [Annex](#security-guidelines).

### Networking

*Reference:*

[Networking public repository](https://github.com/oracle-devrel/technology-engineering/tree/main/cloud-infrastructure/networking)

### Operations (Optional)

*Guide:*

*In this chapter, we provide a high-level introduction to various operations-related topics around OCI. We do not design, plan or execute any detailed operations for our customers. We can provide some best practices and workload-specific recommendations.*


*The below example text represents the first asset from this catalog PCO#01. Please consider including other assets as well. You can find MD text snippets within each asset.*

## Roadmap (Optional)

*Guide:*

*Explain a high-level roadmap for this Workload. Include a few easy high-level steps to success (See Business Context). Include implementation services (if possible) as a first fast step. Add other implementation partners and their work as part of your roadmap as well. Do not include details about the implementation scope or timeline. This is not about product roadmaps.*

## Sizing and Bill of Materials

*Guide:*

*Estimate and size the physically needed resources of the Workload. The information can be collected and is based upon previously gathered capacities, business user numbers, integration points, or translated existing on-premises resources. The sizing is possibly done with or even without a Physical Architecture. It is ok to make assumptions and to clearly state them!*

*Clarify with sales your assumptions and your sizing. Get your sales to finalize the BoM with discounts or other sales calculations. Review the final BoM and ensure the sales are using the correct product SKUs / Part Number.*

*Even if the BoM and sizing were done with the help of Excel between the different teams, ensure that this chapter includes or links to the final BoM as well.*

*WIP*
- *Revision of existing discovery templates*
- *Consolidated data gathering sheet (sizing focused)*
- *Workload-specific sizing process/methodology*

<!--                                                 -->
<!-- End of 3) Workload Requirements and Architecture -->
<!--                                                 -->

# Glossary (Optional)


*Guide:*

*A chapter for Product, Technology, or Concept descriptions*

*Please avoid describing products, and linking to product documentation at the first occurrence of a product.*

*Example:*

You can learn about Oracle Cloud Infrastructure terms and concepts in this [glossary](https://docs.oracle.com/en-us/iaas/Content/libraries/glossary/glossary-intro.htm). Further terms, product names, or concepts are described below in each subsection.
