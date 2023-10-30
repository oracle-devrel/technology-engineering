---
doc:
  author: Gianluca Rossi
  config:
    impl:
      type: Lift
      handover: ${doc.customer.name}
  cover:
    subtitle:
    - Workload Architecture Document
    - Solution Definition and Design
    title:
    - ${doc.customer.name}
    - Serverless Lakehouse
  customer:
    alias: ACME
    name: A Company Making Everything
  version: 1.3
  history:
    - version: 1.0
      date: June 21st, 2022
      authors: Gianluca Rossi
      comments:
        - Created a new Solution Definition document. To be used for iterative review and improvement.
    - version: 1.1
      date: 2nd March 2022
      authors: Gianluca Rossi
      comments: 
        - First review.
    - version: 1.2
      date: 21st July 2023
      authors: Gianluca Rossi
      comments:
        - Updated OCI Services descriptions.
    - version: 1.3
      date: 30th October 2023
      authors: Gianluca Rossi
      comments:
        - New Template
  team:
    - name: ${doc.author}
      email: gianluca.rossi@oracle.com
      role: Analytical Data Paltform Design Specialist
      company: Oracle
  acronyms:
    Dev: Development
---

# Document Control

## Version Control

| Version                | Author         | Date                 | Comment                           |
|---------               |----------------|-----------------     |-----------------------------------|
| ${doc.history.version1}| ${doc.author}  | ${doc.history.date1} | ${doc.history.comments1}          |
| ${doc.history.version2}| ${doc.author}  | ${doc.history.date2} | ${doc.history.comments2}          |
| ${doc.history.version3}| ${doc.author}  | ${doc.history.date3} | ${doc.history.comments3}          |
| ${doc.history.version4}| ${doc.author}  | ${doc.history.date4} | ${doc.history.comments4}          |

## Team

| Name             | eMail                     | Role                   | Company             |
|----------------  |---------------------------|------------------------|---------            |
| ${doc.team.name} | ${doc.team.email}         | ${doc.team.role}       | ${doc.team.company} |

## Document Purpose

This document provides a high-level solution definition for the Oracle solution and aims at describing the current state, and to-be state as well as a potential high-level project scope and timeline for ${doc.config.impl.type}.

The document may refer to a ‘Workload’, which summarizes the full technical solution for a customer (You) during a single engagement. The Workload is described in the chapter [Workload Requirements and Architecture](#workload-requirements-and-architecture).

This is a living document, additional sections will be added as the engagement progresses resulting in a final Document to be handed over to the ${doc.config.impl.type}.

# Business Context

${doc.customer.name} has more than two thousand employees and is looking for a solution that supports the analysis, monitoring and prediction of personnel costs and helps in the main decision-making processes concerning HR management.

## Executive Summary

This Oracle Analytical Data Platform for HR provides the customer with a complete solution to discover, ingest, process, analyze, and analyze HR data. Its easily scalable, flexible, and cost-effective architecture is built with services fully managed by Oracle, allowing ${doc.customer.name} to focus on their core HR competencies while leaving the technical complexities of managing IT infrastructure to Oracle.

## Workload Business Value

The solution will allow ${doc.customer.name} to make data-driven decisions, enabling HR professionals to identify trends, patterns, and areas for improvement within the workforce.
The solution provides a competitive advantage by ensuring that ${doc.customer.name} has the right talent, engaged employees, and efficient processes, positioning the company for long-term success.
Finally, with predictive analytics in HR ${doc.customer.name} will be able to forecast trends such as skills shortages or potential turnover, enabling proactive measures to address these issues before they impact the organization.

# Workload Requirements and Architecture

## Overview

The Workload includes a new analytical application that allows ${doc.customer.name} to produce analyzes on human resources data and in particular on typical indicators of cost of labor. The application will:

-   Store data into Oracle's Cloud systems and platforms
-   Manage metadata and business glossaries for the included data domains.
-   Integrate, transform and enrich data according to the Business rules for calculating cost of labor.
-   Model data with the goal of enabling analysis with advanced visualization.
-   Enable data scientists to develop and execute Machine Learning models by leveraging in a self-service way all the typical features of a ML process: data discovery, data preparation, data processing, ...

The application will have two environments based on Oracle Cloud infrastructure and platforms:

-   Development/Test
-   Production

## Non Functional Requirements

### Integration and Interfaces

The new system extracts data from on-premises application (HR System on Oracle DB, some master data on MS SQL Server System, some accounting information on EBS) and stores them on OCI Object Storage. Integrations with on-premises source system have to be done to extract data on daily bases through batch processes.

| Name                       | Source        | Target         | Protocol | Function        | Connection      |
|----------------------------|---------------|----------------|----------|-----------------|-----------------|
| HR System Integration      | HR System     | Object Storage | Batch    | Data extraction | VPN/FastConnect |
| General Ledger Integration | EBS           | Object Storage | Batch    | Data extraction | VPN/FastConnect |
| HR Master Data Integration | MS SQL Server | Object Storage | Batch    | Data Extraction | VPN/FastConnect |

### Regulations and Compliances

The HR reporting data for ${doc.customer.name} uses personal data. 'Personal data’ means any information relating to an identified or identifiable natural person (‘data subject’); an identifiable natural person is one who can be identified, directly or indirectly, in particular by reference to an identifier such as a name, an identification number, location data, an online identifier or to one or more factors specific to the physical, physiological, genetic, mental, economic, cultural or social identity of that natural person. Furthermore, under GDPR, this only applies to personal data processed in one of two ways:

-   Personal data processed wholly or partly by automated means (or, information in electronic form); and
-   Personal data processed in a non-automated manner which forms part of, or is intended to form part of, a ‘filing system’ (or, written records in a manual filing system).

**In relation to this Workload, all HR data will be anonymized (masked/pseudonymized to make data not attributable to a single employee) by ${doc.customer.name} prior to being uploaded in the Oracle Cloud.**

### Environments

The new workload includes two environment, Development/Test and Production.

Name	        | Size of Prod  | Location	  | DR    | Scope
:---		      |:---		   	    |:---		      |:---   |:---
Production    | 100%          | Frankfurt	  | No    | Workload
Dev & Test    | 25%           | Frankfurt   | No    | Workload - ${doc.config.impl.type}

### High Availability and Disaster Recovery Requirements

At the time of this document creation, no Resilience or Recovery requirements have been specified. Anyhow, resilience is achieved by the intrinsic capabilities of Autonomous Data Warehouse, Oracle Analytics Cloud, OCI Data Integration and OCI Compute services, and providing Service Level Objectives as described in ["Oracle PaaS and IaaS Public Cloud Services Pillar Document"](https://www.oracle.com/assets/paas-iaas-pub-cld-srvs-pillar-4021422.pdf "Oracle PaaS and IaaS Public Cloud Services Pillar Document")

Furthermore, resilience and recovery and can be achieved by leveraging:

-   **ADW automated backups**: by default the Automatic Backup feature for the Autonomous Data Warehouse is enabled. Backups have a retention period of 60 days and that allow to restore and recover the ADW database to any point-in-time in this retention period.
-   **OAC Snapshots** that can be used to perform full or partial backups of OAC content and that can be either restored on the same or a different OAC instance.
-   **OCI Object Storage objects replication**: stored objects are automatically replicated across fault domains or across availability domains. Object Storage offers also automatic self-healing: when a data integrity issue is identified, corrupt data is automatically ‘healed’ from redundant copies.
-   **OCI Data Flow serverless Spark environment** (without infrastructure to deploy or manage) and its code persisted on Object Storage.
-   **OCI Data Science Block Volume built-in redundancy**: block storage of the compute instances of the OCI Data Science Notebooks are automatically replicated to protect against data loss. Multiple copies of data are stored redundantly across storage servers with built-in repair mechanisms. In addition, Block Volumes are persistent and durable beyond the lifespan of a virtual machine.

### Security Requirement

Authentication and authorization of users done by enterprise-grade identity and access management services of OCI.

To facilitate identity and access management the solution will make use of the standard Oracle OCI IAM with IDCS foundation integration. Oracle Cloud Infrastructure Identity and Access Management (IAM) lets ${doc.customer.name} control who has access to the subscribed OCI cloud resources. After ${doc.customer.name} signs up for an Oracle account and Identity Domain, Oracle sets up a default administrator for the account. This ${doc.customer.name} tenancy also automatically has a policy that gives the Administrators group access to all of the Oracle Cloud resources in the tenancy. ${doc.customer.name} can control what type of access a group of users have and to which specific resources. The different Groups and associated policies for ${doc.customer.name} will consider the different type of ${doc.customer.name}'s user and the different type of service they will use to perform their job. ${doc.customer.name}'s main type of users are:

-   **Business Analysts** (HR Manager, HR Specialists): must have the possibility to visualize data, to create report and dashboard with OAC.
-   **Data Scientists**: must have the possibility to run data processing (with Data Flow, Data Integration), to access to the different type of data (raw data in Object Storage, enriched/transformed data in ADW), to analyze and discover data (with Data Science projects, OAC self-service analytics) and to train and test AI models (with Data Science projects).
-   **BI Developer**: must have the possibility to create visualization, report and dashboard with OAC and to administer OAC applications.
-   **ETL Developer**: must have the possibility to create Data Set, Data Flows and Pipelines with OCI Data Integrator.
-   **IT Administrators**: must have the possibility to administer the Oracle Cloud Infrastructure (Networks, Compartments, Groups, Policies,...) and Oracle Cloud Platforms (ADW, OAC, ...).

Currently, for this workload, there isn't a requirement to federate users with ${doc.customer.name} on-premises identity and access management system.

#### Data Security

There is a specific requirement regarding data security in Dev/Test environment. Data managed by this workload includes personal data of ${doc.customer.name} employees (e.g: Name, Surname, Fiscal Code) associated to their salary and retribution details. ${doc.customer.name} will perform the masking process on-premises before loading source data files on Object Storage buckets. That masking process will make impossible to attribute data to a single employee.

For the Production environment of this workload the pseudonymization of personal data is under discussion. Anyhow, as per the data masking process, the pseudonymization process will be developed by ${doc.customer.name} and will be executed on the on-premises data prior to load them in Oracle Cloud.

### Networking Requirements

A connection to the ${doc.customer.name} network is required to extract data from the data sources on-premises. ${doc.customer.name} requires all the services to be deployed with private endpoints.

### Capacity

The following tables shows the main capacity metrics collected for this Workload:

| System     | Capacity                 | KPI      | Unit   | Value     | Notes              |
|:-----------|:-------------------------|:---------|:-------|:----------|:-------------------|
| DB server  | DB size                  | MaxVol   | TB     | 1         |                    |
| ETL Server | Data processed daily     | MaxFlow  | GB/day | 20        |                    |
| OAC        | Users                    | Users    | Users  | 1200-1400 |                    |
| OAC        | Simultaneous users       | MaxUsers | Users  | 120-140   | 10% of total users |
| OAC        | Data Visualization users | MaxUsers | Users  | 240-280   | 20% of total users |


## Functional Requirements

${doc.customer.name} needs a solution to manage Human Resource data from an analytical perspective. They need to monitor the current values of salary, retribution, cost of labor, presences/absences in current and past ${doc.customer.name}'s organizational structure for different employee types. They also need to understand historical trends of the main KPIs and predict possible future scenarios.

### Use cases

Different type of users will leverage the new analytic platform capabilities:

-   **Analysts** in ${doc.customer.name} will profile and analyze data to identify and prototype KPIs, visualizations, dashboards and other outputs useful for ${doc.customer.name}s's business users.
-   **Report Developers** in ${doc.customer.name} will prepare and publish KPIs, visualizations and dashboards, that will be used by ${doc.customer.name}'s business users to understand history and trends of various data sets managed by ${doc.customer.name}.
-   **Data Scientists** in ${doc.customer.name} need an environment to load and prepare data, develop, and test ML models, so that they can create new insights from data in the new analytic platform.
-   ${doc.customer.name}'s **Business Users** (HR Managers, HR Specialists, etc...), need interactive dashboards and visualizations, to analyze HR management KPIs values (cost of labor, salaries, absences/presences) and other characteristics of the service they are responsible for. They also need a Graphical User Interface to manage some master data updates ("D_SOURCE_TABLE1 voci di retribuzione" - i.e. "Payslip items grouping" and "Categoria di Storno" - i.e. "Reversal Category").
-   **All ${doc.customer.name}'s users** needs a supporting tool to manage metadata and main business glossaries of the data included in the analytic solution.

### Requirement Matrix

| Requirements                                      | OAC[^1] | ADW | Data Science | Data Flow | OCI DI | Data Catalog | APEX |
|---------------------------------------------------|---------|-----|--------------|-----------|--------|--------------|------|
| Access report and advanced visualization          | Y       |     |              |           |        |              |      |
| Self-Service reporting and advanced visualization | Y       |     |              |           |        |              |      |
| Profile and analyze data and KPIs                 | Y       | Y   | Y            |           |        |              |      |
| Develop and test ML models                        |         |     | Y            |           |        |              |      |
| Data Loading and processing                       |         |     |              | Y         | Y      |              |      |
| Self Service data Loading and processing          | Y       | Y   |              | Y         | Y      |              |      |
| Manage metadata and business glossaries           |         |     |              |           |        | Y            |      |
| Web GUI to update data                            |         |     |              |           |        |              | Y    |

## Constraints, Challenges and other Requirements

Two of the datasets used by the workload as data sources will come as results of data manipulation done by Business Users through dedicated new Web Applications. Those applications are not already available, they will be developed by ${doc.customer.name} using Oracle APEX in Oracle Cloud. For the solution definition and the Lift implementation we need to share with ${doc.customer.name} the expected data set structure - tables output of the APEX Applications - that will be used as data sources.

## Future State Architecture

### Mandatory Security Best Practices

The safety of the ${doc.customer.name}'s Oracle Cloud Infrastructure (OCI) environment and data is the ${doc.customer.name}’s priority.

To following table of OCI Security Best Practices lists the recommended topics to provide a secure foundation for every OCI implementation. It applies to new and existing tenancies and should be implemented before the Workload defined in this document will be implemented.

Workload-related security requirements and settings like tenancy structure, groups, and permissions are defined in the respective chapters.

Any deviations from these recommendations needed for the scope of this document will be documented in the chapters below. They must be approved by ${doc.customer.name}.

${doc.customer.name} is responsible for implementing, managing, and maintaining all listed topics.

+--------------------------+---------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| CATEGORY                 | TOPIC                     | DETAILS                                                                                                                                                                                              |
+==========================+===========================+======================================================================================================================================================================================================+
| User Management          | IAM Default Domain        | Multi-factor Authentication (MFA) should be enabled and enforced for every non-federated OCI user account.                                                                                           |
|                          |                           | - For configuration details see [Managing Multi-Factor Authentication](https://docs.oracle.com/en-us/iaas/Content/Identity/mfa/understand-multi-factor-authentication.htm).                          |
|                          |                           |                                                                                                                                                                                                      |
|                          |                           | In addition to enforcing MFA for local users, Adaptive Security will be enabled to track the Risk Score of each user of the Default Domain.                                                          |
|                          |                           | - For configuration details see [Managing Adaptive Security and Risk Providers](https://docs.oracle.com/en-us/iaas/Content/Identity/adaptivesecurity/overview.htm).                                  |
+--------------------------+---------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                          | OCI Emergency Users       | A maximum of **three** non-federated OCI user accounts should be present with the following requirements:                                                                                            |
|                          |                           | - Username does not match any username in the Customer’s Enterprise Identity Management System                                                                                                       |
|                          |                           | - Are real humans.                                                                                                                                                                                   |
|                          |                           | - Have a recovery email address that differs from the primary email address.                                                                                                                         |
|                          |                           | - User capabilities have Local Password enabled only.                                                                                                                                                |
|                          |                           | - Has MFA enabled and enforced (see IAM Default Domain).                                                                                                                                             |
+--------------------------+---------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                          | OCI Administrators        | Daily business OCI Administrators are managed by the Customer’s Enterprise Identity Management System.                                                                                               |
|                          |                           | This system is federated with the IAM Default Domain following these configuration steps:                                                                                                            |
|                          |                           | - Federation Setup                                                                                                                                                                                   |
|                          |                           | - User Provisioning                                                                                                                                                                                  |
|                          |                           | - For configuration guidance for major Identity Providers see the OCI IAM Identity Domain tutorials.                                                                                                 |
+--------------------------+---------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                          | Application Users         | Application users like OS users, Database users, or PaaS users are not managed in the IAM Default Domain but either directly or in dedicated identity domains.                                       |
|                          |                           | These identity domains and users are covered in the Workload design.                                                                                                                                 |
|                          |                           | For additional information see [Design Guidance for IAM Security Structure](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/iam-security-structure.htm).                         |
+--------------------------+---------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Cloud Posture Management | OCI Cloud Guard           | OCI Cloud Guard will be enabled at the root compartment of the tenancy home region. This way it covers all future extensions, like new regions or new compartments, of your tenancy automatically.   |
|                          |                           | It will use the Oracle Managed Detector and Responder recipes at the beginning and can be customized by the Customer to fulfill the Customer’s security requirements.                                |
|                          |                           | - For configuration details see [Getting Started with Cloud Guard](https://docs.oracle.com/en-us/iaas/cloud-guard/using/part-start.htm).                                                             |
|                          |                           | Customization of the Cloud Guard Detector and Responder recipes to fit the Customer’s requirements is highly recommended. This step requires thorough planning and decisions to make.                |
|                          |                           | - For configuration details see [Customizing Cloud Guard Configuration](https://docs.oracle.com/en-us/iaas/cloud-guard/using/part-customize.htm)                                                     |
+--------------------------+---------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                          | OCI Vulnerability         | In addition to OCI Cloud Guard, the OCI Vulnerability Scanning Service will be enabled at the root compartment in the home region.                                                                   |
|                          | Scanning Service          | This service provides vulnerability scanning of all Compute instances once they are created.                                                                                                         |
|                          |                           | - For configuration details see [Vulnerability Scanning](https://docs.oracle.com/en-us/iaas/scanning/home.htm).                                                                                      |
+--------------------------+---------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Monitoring               | SIEM Integration          | Continuous monitoring of OCI resources is key for maintaining the required security level (see [Regulations and Compliance](#regulations-and-compliances-requirements) for specific requirements).   |
|                          |                           | See [Design Guidance for SIEM Integration](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/siem-integration.htm) to implement integration with the existing SIEM system.         |
+--------------------------+---------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Additional Services      | Budget Control            | OCI Budget Control provides an easy-to-use and quick notification on changes in the tenancy’s budget consumption. It will be configured to quickly identify unexpected usage of the tenancy.         |
|                          |                           | - For configuration details see [Managing Budgets](https://docs.oracle.com/en-us/iaas/Content/Billing/Tasks/managingbudgets.htm)                                                                     |
+--------------------------+---------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

### Naming Conventions

*Guide:*

*This chapter describes naming convention best practices and usually does not require any changes. If changes are required please refer to [Landing Zone GitHub](https://github.com/oracle-devrel/technology-engineering/tree/main/landing-zones). The naming convention zone needs to be described in the Solution Design by the service provider.*

*Use this template ONLY for new cloud deployments and remove it for brownfield deployments.*

<!--
    Owner: Olaf Heimburger / Jose Palmeiro
    Last Change: 26th of September 2023
    Review Status: Live
    Review Notes: -
-->

A naming convention is an important part of any deployment to ensure consistency, governance, and security within your tenancy. Find [here](https://github.com/oracle-devrel/technology-engineering/blob/main/landing-zones/commons/resource_naming_conventions.md) Oracle's recommended best practices.

### OCI Landing Zone Solution Definition

An OCI Landing Zone sets the foundations for a secure tenancy, providing design best practices and operational control over OCI resources. A Landing Zone also simplifies the onboarding of workloads and teams, with clear patterns for network isolation and segregation of duties in the organization, which sets the cloud operating model for day two operations.

Oracle highly recommends the use of an OCI Landing Zone for any deployment. Use these [guidelines](https://github.com/oracle-devrel/technology-engineering/blob/main/landing-zones/commons/lz_solution_definition.md) to set up your OCI Landing Zone, including design considerations, approaches, and solutions to use.

Note that all workloads in a tenancy should sit on top of a Landing Zone, meaning that the workload architecture defined in the next section can be subject to adjustments (e.g., network structure) towards the landing zone model, along with other future workloads.  

### Logical Architecture

![Future State - Logical Architecture](images/e-HRAnalytics-diagrams-FutureState.jpg)

The following are the main building blocks that compose this cloud architecture.

**Data Persistence and Data Governance**:

-   **OCI Object Storage**: is a cloud native, highly scalable and resilient storage that will be used to support the Data Lake to store any type of data, be it relational or non-relational. Object Storage can be leveraged by a variety of clients and processing engines. It is a managed, durable, scalable, and cost-effective cloud storage for Data Lake and many other use cases. Data in Object Storage is organized in buckets. Object name prefix may be used to group data into logical entities and partitions.
-   **Autonomous Data Warehouse (ADW)**: Oracle Autonomous Data Warehouse (ADW) is a fully managed, preconfigured data warehouse environment. After provisioning, you can scale the number of CPU cores or the storage capacity of the database at any time without impacting availability or performance. ADW can also virtualize data that resides on Object Storage as external tables and hybrid partitioned tables so data consumption derived from other data sources can seamlessly be consumed and joined with the warehouse data. Furthermore one can also leverage Object Storage as a tier of cold storage, if needed, and move part of the historical data from the warehouse into object storage and then consume it seamlessly via Hybrid Partitioned Tables. ADW can also take advantage of the metadata stored on the Data Catalog, meaning, it can consume metadata previously harvested, in order to support external tables creation without the need to explicitly define manually all metadata needed for creating those tables; it even synchs automatically the metadata updates in the Data Catalog with the external tables definition to keep consistency overtime, simplify management and reduce effort. Furthermore, ADW offers solutions to enable data sharing without duplicating or propagating data to all recipients, significantly reducing storage and bandwidth requirements: Delta Sharing and Cloud Links. **Delta Sharing**, a modern open data sharing protocol introduced by Databricks, enables secure and efficient data sharing across organizations. It provides a unified, high-performance, and cost-effective solution for sharing large datasets without the need for data duplication or complex ETL processes. **Cloud Links** are a cutting-edge data sharing solution native to Oracle Autonomous Databases. Leveraging the Oracle Cloud Infrastructure and its metadata Cloud Links enable secure and efficient data sharing between single databases or groups of databases, for example, on a compartmental level. The ${doc.customer.name} instance will be used to support the HR Management Data Lake to be analyzed by all the tools and services of this new OCI analytical system. The built in **APEX** platform will support the development of the Web Application that Business User will use to modify specific HR data that will be used as data input by the HR data-mart.
-   **OCI Data Catalog**: provides metadata describing data sets in the Data Lake. Metadata includes technical metadata such as location, type and format of data sets; and business metadata defining the logical categories and terms. In ${doc.customer.name}, Data Catalog can be used by users for searching and understanding available data (metadata of files in Object Storage and tables in ADW) and also to map data to **ADW external tables** (from source files). In addition, Data Catalog Metastore also provides a highly available and scalable central repository of metadata for a Hive cluster. It stores metadata for data structures such as databases, tables, and partitions in a relational database, backed by files maintained in Object Storage. OCI Data Flow jobs with Apache Spark can makes use of Data Catalog Metastore for this purpose.

**Analytics and Data Science**:

-   **Oracle Analytics Cloud (OAC)**: managed BI service supporting reports, dashboards, self-service, and augmented analytics. With OAC, users can prepare data and run self-service data transformations, they can discover and visualize data, collaborate in teams and share analysis, and develop dashboards and rich visualizations for consumers. In this workload, it will support the reporting to provide visibility on the overall HR Management KPIs (cost of labor, salaries, retribution) as well as to drill down on detailed employee information.
-   **OCI Data Science**: provides infrastructure, open source technologies, libraries, and packages, and data science tools for data science teams to build, train, and manage machine learning (ML) models in Oracle Cloud Infrastructure. The collaborative and project-driven workspace provides an end-to-end cohesive user experience and supports the lifecycle of predictive models. Data Science Model Deployment feature allows data scientists to deploy trained models as fully managed HTTP endpoints that serve predictions in real time infusing intelligence into processes and applications and allowing the business to react to events of relevance as they occur. For long running machine learning process, the results can be also stored in Autonomous Data Base or files in Object Storage to be consumed by external applications. ${doc.customer.name} will implement a ML model to predict cost of labour by leveraging OCI Data Science capabilities.

**Batch Ingestion and Processing**:

-   **OCI Data Integration (DI)**: is a serverless, no code, fully managed ETL service to integrate, transform, move data in the OCI ecosystem. It will be used to develop and execute the data integration pipelines that ingest data from data sources as micro batches or batches, transform that data leveraging Spark and persists the data on the targets, on this case, Autonomous Data Warehouse. It will support data extract, transformation and loading to build the analytical data layer in ADW. ${doc.customer.name}'s data analysts and data scientists can leverage its graphical no-code interface for operations that require self-service ETL.
-   **OCI Data Flow**: managed service for running Apache Spark applications. Data Flow applications are reusable templates consisting of a Spark application, its dependencies, default parameters, and a default runtime resource specification. Since it's a perfectly elastic pay-as-you-go service, Data Flow can be used by ${doc.customer.name} Data Engineers and Data Scientists whenever they need to perform scalable and large scale data processing on Data Lake. Furthermore, OCI Data lows offers Data Flow SQL Endpoints that are designed for developers, data scientists, and advanced analysts to interactively query data directly where it lives in the data lake. Using Data Flow SQL Endpoints, you can economically process large amounts of raw data, with cloud native security used to control access.

**Identity and Access Management**:

-   **Identity Cloud Service (IDCS)** manages user identities, access and entitlements across a wide range of cloud and on-premises applications and services, such as OCI, OAC, and many other Oracle and non-Oracle services. IDCS may be federated with external identity systems such as Active Directory, both for SSO and user and group provisioning. For this workload ${doc.customer.name} can use IDCS to authenticate users and define users/groups memberships. In future ${doc.customer.name} can leverage IDCS federation capabilities to enable a hybrid Cloud/on-premises security model.
-   **OCI Identity and Access Management (IAM)** control who can access OCI resources in Data Lake. Access control rules are described in flexible and powerful policy statements, using service types, compartments, tags, locations, and other attributes to allow access to OCI. Access is granted either to Groups (for humans as principals) or to Dynamic Groups (for VMs or Functions as principals).

### Physical Architecture

Below is a high level deployment architecture to show how the OCI services would be deployed to deliver the logical architecture above. This architecture supports different environments of solution.

![Future State - Deployment](images/e-HRAnalytics-diagrams-PhysicalDeployment.jpg)

Below there is a brief explanation of each architecture component.

-   **OCI Region** An Oracle Cloud Infrastructure region is a localized geographic area that contains one or more data centers, called availability domains.
-   **IDCS** - Identity Cloud Service is the service that allows to manage identities and permissions for the various OCI services users and can be integrated/federated with external Identity Providers, on this case, ${doc.customer.name}'s (Azure) Active Directory.
-   **IAM** - OCI Identity and Access Management allows controlling who has access to cloud resources. It can control what type of access a group of users have and to which specific cloud resources. It is a key component of segregating resources and restricting access only to authorized groups and users. OCI IAM, and in fact, OCI as a whole implements a [Zero Trust Security](https://www.oracle.com/security/what-is-zero-trust/#link1model) of which one of the guiding principles is least privilege access; in fact, a user by default doesn’t have access to any resources and policies need to be created explicitly to grant groups of users access to cloud resources.
-   **Cloud Guard** - Cloud Guard continuously collects and analyses configuration, audit logs and other information in a customer’s tenancy and reports its findings as “Problems” based on its Detector Recipes. When Cloud Guard triggers detects a problem, transform and send the problem data to an external SIEM system, leveraging OCI Event and OCI Functions.
-   **Vault** - OCI Vault allows to centrally manage the encryption keys that protect your data and the secret credentials that you use to securely access resources. Vault allows to import customer key in order to own and manage the key material outside Oracle Cloud infrastructure for additional durability, and for recovery purpose.
-   **Logging** - Logging provides access to logs from Oracle Cloud Infrastructure resources. These logs include critical diagnostic information that describes how resources are performing and being accessed.
-   **Networking**: the OCI network architecture will be provisioned as hub-and-spoke network. the OCI network architecture will be provisioned as hub-and-spoke network. This architecture uses a DRG as the hub, and enables communication between on-premises network and multiple VCNs (associated to the same DRG) in the same region, over a single FastConnect private virtual circuit or Site-to-Site VPN:
    -   **OCI Site-to-Site VPN** provides a site-to-site IPSec connection between on-premises network and the virtual cloud network (VCN) on OCI. The IPSec protocol suite encrypts IP traffic before the packets are transferred from the source to the destination and decrypts the traffic when it arrives. OCI Site-to-Site VPN it's free of charge and provides secure and reliable connections between on-premises network and OCI VCNs. Customers who prefer alternative solutions, may also install and configure third party software in OCI to manage VPN connections. The configuration of the CPE (the customer-premises equipment at end of Site-to-Site VPN) is needed for traffic to flow between your on-premises network and virtual cloud network (VCN). CPE can be any equipment (router, firewall, etc.) that the customer uses to manage IPsec connections. Oracle provides configuration instructions for the CPE verified devices (e.g. Checkpoint, Cisco ASA, Cisco IOS,...). For details and best practice refers to the [CPE configuration documentation](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/configuringCPE.htm)
    -   **OCI FastConnect** - FastConnect provides an easy way to create a dedicated, private connection between on-premises data center and Oracle Cloud Infrastructure. FastConnect provides higher-bandwidth options, and a more reliable and consistent networking experience compared to internet-based connections.
    -   **VCN and Subnets** A VCN is a software-defined network that you set up in the Oracle Cloud Infrastructure data centers in a particular region. A subnet is a subdivision of a VCN.
    -   **Dynamic routing gateway (DRG)**- The DRG is a virtual router that provides a path for private network traffic between VCNs in the same OCI Regions but also between a VCN and a network outside the region, such as a VCN in another Oracle Cloud Infrastructure region, an on-premises network, or a network in another cloud provider.
    -   **Security list**- For each subnet, you can create security rules that specify the source, destination, and type of traffic that must be allowed in and out of the subnet.
    -   **Route table**- Virtual route tables contain rules to route traffic from subnets to destinations outside a VCN, typically through gateways.
-   **Data Lakehouse Platform** - A data lakehouse is a modern, open architecture that enables you to store, understand, and analyze all your data. It combines the power and richness of data warehouses with the breadth and flexibility of the most popular open source data lake technologies. Main Lakehouse components for this workload:
    -   **Autonomous Data Warehouse** - Oracle Autonomous Data Warehouse (ADW) is a fully managed, preconfigured data warehouse environment. After provisioning, you can scale the number of CPU cores or the storage capacity of the database at any time without impacting availability or performance. ADW can also virtualize data that resides on Object Storage as external tables and hybrid partitioned tables so data consumption derived from other data sources can seamlessly be consumed and joined with the warehouse data. Furthermore one can also leverage Object Storage as a tier of cold storage, if needed, and move part of the historical data from the warehouse into object storage and then consume it seamlessly via Hybrid Partitioned Tables. ADW can also take advantage of the metadata stored on the Data Catalog, meaning, it can consume metadata previously harvested, in order to support external tables creation without the need to explicitly define manually all metadata needed for creating those tables; it even synchs automatically the metadata updates in the Data Catalog with the external tables definition to keep consistency overtime, simplify management and reduce effort. For ${doc.customer.name} two ADW instances will be provisioned one for Production and the other for Dev/Test environment, both will have private end-points.
    -   **Object Storage** - is a cloud native, highly scalable and resilient storage that will be used to support the data lake to store any type of data, be it relational or non-relational. Object Storage can be leveraged by a variety of clients and processing engines and effectively.
-   **OCI Data Integration** - is a serverless, no code, fully managed ETL service that will be used to develop and execute the data integration pipelines that ingest data from data sources as micro batches or batches, transform that data leveraging Spark and persists the data on the targets, on this case, Autonomous Data Warehouse. It will be used to support any ETL needed on the data platform and to capture data from the majority of the systems based on Oracle DB and MS SQL, recent versions. OCI Data Integration is used in ${doc.customer.name} for data ingestion processes that load the HR Analytics data model. There will be two OCI DI workspaces, one for each environment.
-   **Oracle Analytics Cloud** - OAC is a scalable and secure cloud service that provides a full set of capabilities to explore and perform collaborative analytics for you, your workgroup, and your enterprise. With Oracle Analytics Cloud you also get flexible service management capabilities, including fast setup, easy scaling and patching, and automated lifecycle management. There will be two OAC instances, one for each environment, both with private end-points.
-   **Data Catalog**, ready to use when the tenancy is created.
-   **OCI Data Flow** and **OCI Data Science** are available to ${doc.customer.name}'s data scientists and data analysts. They will create Data Science projects or Data Flow applications whenever they need.

### Management and Monitoring

Management of the system will be done via:

-   **OCI console** - to get access to the service instances supporting the architecture and be able to manage them, for instance, start/stop instances, configure backups, ...
-   **ADW console** - to start/stop the ADW instance, create a clone, download and rotate the ADW wallet, restore from a backup, change admin password or set resource management rules
-   **OAC console** - to manage OAC settings, create and restore snapshots and manage ADW connection settings amongst other admin tasks
-   **IDCS console** - to manage users and perform role assignment for those users
-   **OCI SDK** and **OCI CLI** provide the capability to interact with services programmatically (e.g. launch OCI Data Integration tasks, OCI Data Science jobs)

Monitoring will be performed leveraging OCI base capabilities as well as the specific services capabilities and will be done via:

-   **OCI console** - to see and monitor the OAC, ADW, OCI DI and OCI Compute metrics; can also be used to trigger alarms and notifications based on those metrics
-   **ADW console and Performance Monitor** - monitor performance, CPU utilization, consumed storage, running SQL statements and sessions amongst other metrics exposed
-   **OAC console** - to monitor user sessions and cache status
-   **OCI Data Integrator Monitor Application** - to see and monitor workspaces and application runs.
-   **OCI Data Flow** - simplifies common operational tasks like log management and access to operational UIs. It offers simple debugging and diagnostics with a consolidated view of log output. Administrators can easily discover and stop live Spark jobs that are running for too long or consuming too many resources.
-   **OCI Data Science** - Data Science monitors running notebook sessions, collects and reports metrics including: CPU Utilization, Memory Utilization, Network Bytes In, Network Bytes Out. You can view the default metric charts for all the notebook sessions in a compartment using the OCI Monitoring service.

### High Availability and Disaster Recovery

Please see documentation reference:

- [Resilliance on OCI](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/era-resiliency.htm)


### Security

Please see our security guidelines in the [Annex](#security-guidelines).

### Networking

A list of possible Oracle solutions can be found in the [Annex](#networking-solutions).*

## Sizing and Bill of Materials

The following table includes a Bill of Materials and sizing estimates for the workload environments:

| Product                                | Metric      | Env.     | Quantity | Notes     |
|:---------------------------------------|:------------|:---------|:---------|:----------|
| Autonomous Data Warehouse              | OCPU/h      | DEV      | 2        |           |
| Autonomous Data Warehouse              | OCPU/h      | PROD     | 8        |           |
| Autonomous Data Warehouse Storage      | TB/month    | DEV      | 1        |           |
| Autonomous Data Warehouse Storage      | TB/month    | PROD     | 1        |           |
| OCI Data Integration - Workspace       | Workspace/h | DEV      | 1        |           |
| OCI Data Integration - Workspace       | Workspace/h | PROD     | 1        |           |
| OCI Data Integration - Data Processing | GB/h        | DEV      | 20       | 20 Gb/day |
| OCI Data Integration - Data Processing | GB/h        | PROD     | 20       | 20 Gb/day |
| Oracle Analytics Cloud                 | OCPU/h      | PROD     | 6        |           |
| Oracle Analytics Cloud                 | OCPU/h      | DEV/PROD | 2        |           |

# Project Implementation

## Solution Scope

### Disclaimer

As part of the Oracle Lift Project, any scope needs to be agreed by both the customer and Oracle. A scope can change, but must be confirmed again by both parties. Oracle can reject scope changes for any reason and may only design and implement a previously agreed scope. A change of scope can change any agreed times or deadlines, and needs to be technical feasible.

### Overview

The Lift project will provision and configure the Oracle Cloud Environments. Using DEV environment, a complete analytics workflow will be implemented focusing on "Cost of labor" data. Source data will be read form Object Storage buckets and then transformed in the Oracle Data Warehouse database to provide analytical capabilities both to Business Users/BI Developers who creates reports with Oracle Analytics Cloud and to Data Scientists/Data Engineers who develops ML models with Data Science notebooks. In addition, sample OAC reports and dashboards will be developed using OAC visualizations.


### Business Value

The Oracle ${doc.config.impl.type} service brings several benefits to this project. All the activities mentioned within the scope will ensure the deployment of workload as per Oracle's best practices. As a tried and tested methodology by many customers, Oracle ${doc.config.impl.type} brings the speed of deployment resulting in successful projects without any setbacks. Oracle ${doc.config.impl.type} services will bring value to the overall project provisioning OCI environments for the application workload.

Oracle Cloud ${doc.config.impl.type} services provide guidance from cloud engineers and project managers on planning, project management, architecting, deploying, and managing cloud migrations.

### Success Criteria

The following project success criteria have been defined:

| \#  | Success Criteria                   | Description                                                                                                                                                                                                                      |
|:----|:-----------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1   | Deployment of technical components | Technical and network components have been deployed as described in the physical architecture (Compartments, VCNs, Subnets - ADW, OAC, OCI DI instances)                                                                         |
| 2   | User Access                        | Users have been created the appropriate user groups and policies in an OCI IDCS stripe for the analytics environments. Users are able to access the OAC environment and see the reports and dashboard for the selected use cases |
| 3   | Data Mart creation                 | Creating the database objects and perform the initial data load from the source files into the target ADW                                                                                                                        |
| 4   | Daily data loading                 | Daily batch data loading processes successfully updates the data access layers in ADW (full loading, not incremental)                                                                                                            |
| 5   | Report creation                    | The required report runs successfully (with no errors). Sample reports are created and runs successfully                                                                                                                         |
| 6   | Logical model in OAC               | Building 1 Subject Area (OAC repository logical model) in OAC                                                                                                                                                                    |
## Workplan

## Deliverables

The Lift implementation project will have the following main deliverables:

-   1 OAC instance.
-   2 ADW instances.
-   OCI Data Integration Workspaces and artifacts.
-   OAC Subject Area, reports and visualizations

## Included Activities

Main implementation activities as part of the Lift service are:

-   Provisioning and configuration of Oracle Cloud Infrastructure Components for two environments as per Deployment Architecture (Compartments, VCNs, Subnets).
-   Provisioning and configuration of Oracle Cloud Platforms for two environments as per Deployment Architecture (ADW, OAC, OCI DI instances).
-   Harvesting in the Data Catalog of the data source files metadata (used as external tables by ADW).
-   Creation of data loading process with OCI Data Integration (Data Assets, Task, Data Flows, Data Pipelines). There are maximum 7 source datasets (5 txt files and 2 database tables in ADW).
-   Creation of a relational data-mart model (expected 2 Fact Tables and 4 dimensions table)
-   Implementation of batch data loading process for the relational data mart model (full loading for all the target tables).
-   Implementation of 1 OAC Subject Area
-   Creation of OAC reports and visualizations. Only one report is strictly required. Other OAC sample reports will be provided (max 15 visualizations).
-   Creation of users/groups/policies with OCI IDCS/IAM.
-   Association of OAC users to OAC Application Roles (standard and custom roles).
-   Unit test of the data loading processes.
-   Unit test of the OAC reports and visualizations.
-   Deployment in Production environment.
-   Handover sessions to ${doc.customer.name}'s System Integrator partner and to ${doc.customer.name}'s IT Department.

## Recommended Activities

-   SAML Federation for Single-Sign-On and synchronization of users/group with on-premises identity management system.
-   The development of processes that access directly to on-premises data source to extract data.
-   The development of the Web Application with APEX.
-   The management of the data source tables (output of APEX applications).
-   Data quality process or discarded records management.
-   Row-level security implementation.
-   OAC customizations
-   The creation of other metadata with OCI Data Catalog. Data Catalog metadata will be created only for the data source files.
-   Performance testing & tuning of any component in the solution.
-   Vulnerability Assessment and Penetration Testing.
-   Trainings on deployed products and Cloud services.

## Timeline

High-level project timeline definition

![High-level Project Timeline\*](images/implementation_plan.png)

'\*' The above timeline shows a representative timeline and is intended for planning purposes only

## Specific Requirements and Constraints

### Reporting and Visualization Requirements

There is a specific requirement only for the implementation of one report. That report is shown in the figure below:

![Required Report](images/e-ReportExampleMain.jpg)

${doc.customer.name} has provided other reports as examples to be considered when implementing additional OAC visualization for the "Cost of labor":

![Sample Report](images/e-ReportExample2.jpg)

![Sample Report](images/e-ReportExample3.jpg)

### Specific Non Functional Requirements

${doc.customer.name} team (members of ${doc.customer.name} IT department and ${doc.customer.name} Partners) needs to be involved during the execution of the Lift implementation. The handover sessions will be scheduled accordingly with the project progress and not only at the end of the project. ${doc.customer.name}'s requirement is to be ready to design extensions of the workload before the end of the Lift implementation project.

Main handover session will be focused on:

-   OCI DI data loading applications
-   ADW data models
-   OAC reports and dashboards
-   Administering OCI (infrastructure, platforms, security, monitoring)

## Implementation RACI

Find below the RACI matrix for the high level tasks:

| **Activity**                                                                                            | **Oracle** | **Customer** | **Notes**                                                                           |
|---------------------------------------------------------------------------------------------------------|------------|--------------|-------------------------------------------------------------------------------------|
| Create new OCI IAM users for named Oracle consultants                                                   | I,C        | R,A          |                                                                                     |
| Provisioning and configuration of Oracle Cloud Infrastructure Components as per Deployment Architecture | A,R        | I,C          | Compartments, Networking (VCN, Security Lists, Route Tables, ...)                   |
| Provisioning and configuration of Oracle Cloud Platforms as per Deployment Architecture                 | A,R        | C,I          |                                                                                     |
| Harvesting in the Data Catalog the data source files metadata                                           | A,R        | I,C          |                                                                                     |
| Creation of data loading process with OCI Data Integration                                              | A,R        | I,C          |                                                                                     |
| Implementation of 1 OAC Subject Area                                                                    | A,R        | I,C          |                                                                                     |
| Provide OAC Subject Area (Presentation Layer) columns names/comments                                    | I,C        | R,A          |                                                                                     |
| Creation of OAC reports and visualizations                                                              | A,R        | I,C          |                                                                                     |
| Provide OAC users details (usernames, roles)                                                            | I,C        | A,R          | Key users to be created in the new OAC environments and related OAC Roles to assign |
| Creation of OAC users with IDCS and associations to OAC Roles                                           | A,R        | I            |                                                                                     |
| Unit test of the data loading processes                                                                 | A,R        | C,I          |                                                                                     |
| Unit test of the OAC reports and visualizations                                                         | A,R        | C,I          |                                                                                     |
| Deployment in Production environment                                                                    | A,R        | C,I          |                                                                                     |
| Testing by ${doc.customer.name}                                                                  | I          | R,A          |                                                                                     |

R:Responsible A:Accountable C:Consulted I:Informed

### Assumptions

-   Data is assumed to be already masked/pseudonymized by ${doc.customer.name} managed processes (executed on-premises).
-   Data sources will be:
    -   maximum 5 text files (csv), uploaded by ${doc.customer.name} on OCI Object Storage buckets
    -   maximum 2 Oracle tables in Oracle Autonomous Data Warehouse. Those tables are the output of the APEX applications that HR Business users will use to modify some master data related to the payslip items. The APEX application will be developed by ${doc.customer.name} in parallel with the Lift project.
-   Data prepared in the sources files and source tables is considered "ready to be loaded" (no quality checks or discarded records management)
-   Batch loading processes will perform a full data loading (no incremental loading).
-   Batch loading process will run on monthly bases (only consolidated monthly data will be loaded).
-   OAC reports/dashboards/visualizations will be implemented using the standard OAC theme (Redwood)
-   It is assumed that all work will be done remotely and within either central European time or India standard time normal office working hours.

### Obligations

-   ${doc.customer.name} Application team will be available for the Testing Phase and will be completed within the agreed testing window.
-   ${doc.customer.name} to provide lists of Users and related IAM/IDCS Groups membership (max 20 users)
-   ${doc.customer.name} to provide lists OAC Application Roles and related users associations (max 2 custom OAC Application Roles)
-   ${doc.customer.name} to provides the tables structures output of the APEX web applications (that are source tables for this workload) before the beginning of the project implementation.

### Transition Plan

#### Introduction

Following the deployment of the solution to Oracle Cloud Infrastructure by the ${doc.config.impl.type} team, it is important to ensure a smooth handover to a technical team, or a partner. ${doc.config.impl.type} values the continuation of the cloud journey and we focus our efforts to ensure you start with the best possible foundation, to set you up for success in OCI.

When ${doc.config.impl.type} completes the deliverables as described in the [Workplan](#workplan) section of this document, ${doc.config.impl.type} will hand over the controls of the new OCI environment.

${doc.customer.name}, or a partner of your choice, will assume the ownership of the OCI tenancy and responsibility for further development of the OCI environment. From that moment forward, having completed the [Solution Scope](#solution-scope), ${doc.config.impl.type} will disengage. For post-implementation support, Oracle provides you with three distinct resources:

1.	Oracle Account Cloud Engineer (ACE) – This is your first point of contact and will provide technical leadership and support for Oracle cloud technologies and your cloud transformation.
2.	Cloud Adoption Manager (CAM) - Introduces and plans operation monitoring and optimization advisory activities, and continues working with you on the next milestones. Please contact your ACE for further information.
3.	[My Oracle Support](https://support.oracle.com/portal/)

#### Transition Acceptance

When ${doc.config.impl.type} completes the deliverables as specified in the [Workplan](#workplan) section of this document, a closure session will be scheduled within 1-2 weeks to recap the project and to hand it over to the accepting party. In the case of this project, the accepting party is ${doc.config.impl.handover}. ${doc.config.impl.handover} is now responsible for the OCI tenancy.

From this moment forward, the Oracle ${doc.config.impl.type} team will fully remove their access from your OCI tenancy and provide the access credentials to the accepting party. This marks the completion of the ${doc.config.impl.type} project. There is no sign-off signature required.

# Oracle Lift Implementation

## Approach

Preparation of Oracle Cloud tenancy:

-   Preparation of the OCI tenancy and provisioning all networks components including gateways

Provisioning of Oracle Cloud services:

-   Provisioning and configuration of 1 OAC instance.
-   Provisioning and configuration of 2 ADW instances.
-   Configuration of 2 OCI Data Integration Workspaces.

Implementation of the solution:

-   ADW Data Model creation
-   Implementation of data loading process (from source file in Object Storage to data model in ADW)
-   Implementation of OAC report and visualizations

## Deployment Build

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

The value for \<prefix\> or the full names **must be agreed** with customer.

### Compartments

Compartments are logical collections of OCI resources, used for isolating the resources, managing access, and monitoring usage and billing. Typically, compartments correspond to projects, application domains or departments. For the CAP solution, we will create the compartments as defined below:

| Compartment Name    | Description                                                              | Parent |
|:--------------------|:-------------------------------------------------------------------------|:-------|
| datalakeDev         | Compartment for all the development resources for Lakehouse applications | root   |
| DatalakeProd        | Compartment for all the production resources for Lakehouse applications  | root   |
| network-compartment | Compartment for all OCI network resources                                | root   |
| DatalakeMetadata    | Compartment for all the metadata for Lakehouse                           | root   |

### Groups

OCI group is a collection of users who all need the same type of access to a particular set of OCI resources or compartment. All access controls in OCI are managed on the level of groups; it is not possible to assign access to individual users.

| OCI Group Name  | IDCS Group Name      | Description                                                           |
|:----------------|:---------------------|:----------------------------------------------------------------------|
| catalog-admin   | IDCS_Catalog-Admin   | OCI Data Catalog administrators                                       |
| analytics-admin | IDCS_AnalyticsAdmins | Administrators responsible for the usage of analytics resources (OAC) |
| di-admin        | di-admin             | OCI Data Integration administrators                                   |
| data-scientists | idcs-data-scientists | OCI Data Science administrators who can manage all OCI DS resources   |

### Dynamic Groups

OCI dynamic group Dynamic groups allow to group Oracle Cloud Infrastructure instances as "principal" actors (similar to user groups). The following policies may be considered for the initial setup of the tenancy.

| Dynamic Group Name          | Description                                                                                                     | Matching Rule                                                                                                                                                       |
|:----------------------------|:----------------------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| lakehouse-adw-dynamic-group | Dynamic group for Autonomous Data Warehouse instance to manage OCI Data Catalog and read Object Storage buckets | resource.id = 'ocid1.autonomousdatabase.oc1.eu-frankfurt-1.xyz'                                            |
| dcatalog-dg                 | dynamic group for data catalog                                                                                  | Any {resource.id = 'ocid1.datacatalog.oc1.eu-frankfurt-1.xyz'}                                             |
|                             |                                                                                                                 | Any {resource.id = 'ocid1.datacatalog.oc1.eu-frankfurt-1.xyz'}                                             |
| data-science-dynamic-group  | Dynamic group to enable ResourcePrincipal for DataScience                                                       | ALL {resource.type = 'datasciencenotebooksession', resource.compartment.id = 'ocid1.compartment.oc1..xyz'} |

### Policies

Policy documents define which groups or services can access which OCI resource and what level of access they are allowed. The following policies may be considered for the initial setup of the tenancy.

| Policy Name              | Compartment | Description                                                                                        | Statements                                                                                                     |
|:-------------------------|:------------|:---------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------|
| datacatalog-policy-root  | root        | Grant access to all resources in any compartment in the tenancy                                    | allow service datacatalog to read object-family in tenancy                                                     |
|                          |             |                                                                                                    | allow dynamic-group dcatalog-dg to read object-family in tenancy                                               |
| di-policies-root         | root        | Grant admin access to all OCI DI workspaces in the tenancy                                         | allow group di-admin to manage dis-family in tenancy                                                           |
|                          |             |                                                                                                    | allow group di-admin to inspect compartments in tenancy                                                        |
| analytics-admin-policy   | root        | Policies for Analytics Administrators                                                              | allow group analytics-admin to manage analytics-instances in tenancy                                           |
|                          |             |                                                                                                    | allow group analytics-admin to manage analytics-instance-work-requests in tenancy                              |
| data-science-policies2   | root        | Grant admin access to all OCI Data Science resources in the tenancy                                | allow dynamic-group data-science-dynamic-group to read compartments in tenancy                                 |
|                          |             |                                                                                                    | allow dynamic-group data-science-dynamic-group to read users in tenancy                                        |
|                          |             |                                                                                                    | allow dynamic-group data-science-dynamic-group to manage object-family in compartment datalakeDev              |
|                          |             |                                                                                                    | allow any-user to use log-content in tenancy where ALL {request.principal.type = 'datasciencemodeldeployment'} |
| adw-objectstorage-policy | root        | Policy per consentire di leggere oggetti dell'Object Storage al gruppo lakehouse-adw-dynamic-group | allow dynamic-group lakehouse-adw-dynamic-group to read objects in tenancy                                     |
| adw-datacatalog-policy   | root        | Policy per consentire la gestione del Data Catalog al gruppo lakehouse-adw-dynamic-group           | allow dynamic-group lakehouse-adw-dynamic-group to manage data-catalog-family in tenancy                       |

In the future, you can create additional new Policy Names or add policies to the existing ones.

### Tags

Tags are key/value metadata added to OCI resources, that are used to organize and list resources based on your needs. Defined tags may be automatically populated based on tag variables. For the initial use case, you might consider the following tag namespaces:

| Tag Namespace           | Namespace Description                                    |
|:------------------------|:---------------------------------------------------------|
| operation-tag-namespace | Tags related to provisioning and operating OCI resources |

The *operation-tag-namespace* namespace might have the following tag key definitions. Tag environment is used to classify environment types, while *Project* may be used to identify the project associated to the resources.

| Tag Namespace           | Tag Keys    | Tag Description   | Cost Tracking | Tag Values (Examples) |
|:------------------------|:------------|:------------------|:--------------|:----------------------|
| operation-tag-namespace | Project     | Id of the project | No            | Lakehouse             |
| operation-tag-namespace | Environment | Environment       | No            | Prod, Test, Dev       |

You can add additional tag namespaces and tag keys in the future.

### Users

To be Defined

| Name | Email | Group | Description |
|:-----|:------|:------|:------------|
|      |       |       |             |

### Virtual Cloud Networks

| Compartment         | VCN Name           | CIDR Block      | DNS Label        |
|:--------------------|:-------------------|:----------------|:-----------------|
| network-compartment | vcn-lakehouse-prod | 10.50.82.128/25 | vcnlakehouseprod |
| network-compartment | vcn-lakehouse-dev  | 10.50.80.128/25 | vcnlakehousedev  |

### Subnets

| Compartment         | VCN Name           | Subnet Name                  | CIDR Block      | Subnet Span | Type    | Route Tables                | Security Lists                |
|:--------------------|:-------------------|:-----------------------------|:----------------|:------------|:--------|:----------------------------|:------------------------------|
| network-compartment | vcn-lakehouse-prod | sn-lkh-prod-analytics-priv   | 10.50.82.128/27 | Regional    | Private | lakehouse-fra-route-table-1 | lakehouse-fra-security-list-1 |
| network-compartment | vcn-lakehouse-prod | sn-lkh-prod-data-priv        | 10.50.82.160/27 | Regional    | Private | lakehouse-fra-route-table-1 | lakehouse-fra-security-list-1 |
| network-compartment | vcn-lakehouse-prod | sn-lkh-prod-integration-priv | 10.50.82.192/27 | Regional    | Private | lakehouse-fra-route-table-1 | lakehouse-fra-security-list-1 |
| network-compartment | vcn-lakehouse-dev  | sn-lkh-dev-analytics-priv    | 10.50.80.128/27 | Regional    | Private | lakehouse-fra-route-table-2 | lakehouse-fra-security-list-2 |
| network-compartment | vcn-lakehouse-dev  | sn-lkh-dev-data-priv         | 10.50.80.160/27 | Regional    | Private | lakehouse-fra-route-table-2 | lakehouse-fra-security-list-2 |
| network-compartment | vcn-lakehouse-dev  | sn-lkh-dev-analytics-priv    | 10.50.80.128/27 | Regional    | Private | lakehouse-fra-route-table-2 | lakehouse-fra-security-list-2 |

### Route Tables

We create Route Tables:

-   To grant resources in private subnet to access to the public internet through the NAT Gateway.
-   To grant resources in private subnet to access the endpoints of Oracle Services in the Oracle Service Network (Object Storage, ADW, ...)

| Compartment         | Route Table Name            | Target Type     | Destination CIDR/Service                   | NAT/Service Gateway Name |
|:--------------------|:----------------------------|:----------------|:-------------------------------------------|:-------------------------|
| network-compartment | lakehouse-fra-route-table-1 | Service Gateway | All FRA Services in Oracle Service Network | lakehouse-fra-sgw-1      |
| network-compartment | lakehouse-fra-route-table-2 | Service Gateway | All FRA Services in Oracle Service Network | lakehouse-fra-sgw-2      |

### Security Lists (Egress)

We create Security List egress rules (stateful) to allow the resources in subnets to reach the endpoints of the services in the Oracle Service Network.

| Compartment         | Security List Name            | Rule Type | Dest. Type | Rule CIDR                                  | IP Protocol | Source Port | Dest. Port |
|:--------------------|:------------------------------|:----------|:-----------|:-------------------------------------------|:------------|:------------|:-----------|
| network-compartment | lakehouse-fra-security-list-1 | Egress    | Service    | All FRA Services in Oracle Service Network | TCP         | All         | All        |
| network-compartment | lakehouse-fra-security-list-2 | Egress    | Service    | All FRA Services in Oracle Service Network | TCP         | All         | All        |

### Object Storage Buckets

Object Storage buckets to store the datasource files uploaded in OCI by ${doc.customer.name}. We create two buckets (one for Development), one for Production) that will store the HR costs source files.

| Compartment  | Bucket       | Visibility | Region | Description                              | Tags                                  |
|:-------------|:-------------|:-----------|:-------|:-----------------------------------------|:--------------------------------------|
| datalakeDev  | HRCosts-dev  | Private    | FRA    | Dev Bucket for source files of HR Costs  | Project: Lakehouse, Environment: Dev  |
| DatalakeProd | HRCosts-prod | Private    | FRA    | Prod Bucket for source files of HR Costs | Project: Lakehouse, Environment: Prod |

### Databases

### Autonomous Databases

#### Autonomous Database Information

We create two Autonomous Data Warehouse instances one for Development environment and the other for Production environment:

| Compartment  | Display name             | DB Name    | Workl. Type | Infr. Type | DB Version | OCPU Count | Storage (TB) | Region | Tags                                  |
|:-------------|:-------------------------|:-----------|:------------|:-----------|:-----------|:-----------|:-------------|:-------|:--------------------------------------|
| datalakeDev  | lakehouse-dev-fra-adw-1  | LHDEVADW1  | ADW         | Shared     | 19c        | 2          | 1            | FRA    | Project: Lakehouse, Environment: Dev  |
| DatalakeProd | lakehouse-prod-fra-adw-1 | LHPRODADW1 | ADW         | Shared     | 19c        | 8          | 1            | FRA    | Project: Lakehouse, Environment: Prod |

#### Automation Database Network

| Displayname              | Auto Scaling | Network Access | Access Control Rules          | License Type |
|:-------------------------|:-------------|:---------------|:------------------------------|:-------------|
| lakehouse-prod-fra-adw-1 | No           | Shared         | Secure Access from everywhere | BYOL         |
| lakehouse-dev-fra-adw-1  | No           | Shared         | Secure Access from everywhere | BYOL         |

### Oracle Analytics Cloud

We create an Oracle Analytics Cloud instance (Enterprise) with public end-point.

| Compartment  | OAC Instance Name | Feature Set          | Capacity | OCPU | License  | Network Access | Tags                                  |
|:-------------|:------------------|:---------------------|:---------|:-----|:---------|:---------------|:--------------------------------------|
| DatalakeProd | lakehouseprodoac1 | Enterprise Analytics | OCPU     | 6    | Included | Private        | Project: Lakehouse, Environment: Prod |
| DatalakeProd | lakehousedevoac1  | Enterprise Analytics | OCPU     | 2    | Included | Private        | Project: Lakehouse, Environment: Dev  |

### OCI Data Catalog

We create an OCI Data Catalog instance to harvest data source files. ${doc.customer.name} can then use the same Data Catalog instance to harvest other data assets (e.g: lakehouse data models tables in ADW) as needed.

| Compartment      | Data Catalog Instance Name | Tags               |
|:-----------------|:---------------------------|:-------------------|
| DatalakeMetadata | lakehouse-data-catalog     | Project: Lakehouse |

We have to add a data asset using the Object Storage buckets that contains data source files.

| Data Asset Name                           | Description                            | Type                  | URL                                 | Namespace                                 |
|:------------------------------------------|:---------------------------------------|:----------------------|:------------------------------------|:------------------------------------------|
| Lakehouse-Source Files Object Storage-Dev | Data Asset to harvest dev source files | Oracle Object Storage | *\<uri of the bucket HRCosts-dev\>* | *\<namespace of the bucket HRCosts-dev\>* |

We need also to add a connection to the data *asset*:

| Data Asset Name                           | Connection Name               | Description                      | Region         | Compartment OCID                          | Default |
|:------------------------------------------|:------------------------------|:---------------------------------|:---------------|:------------------------------------------|:--------|
| Lakehouse-Source Files Object Storage-Dev | Object Storage Connection Dev | Connessione a Object Storage Dev | eu-frankfurt-1 | *\<OCID of the compartment datalakeDev\>* | Yes     |

## Solution Build

### Data Processing

The figure below shows the high level data processing to load the HR analytics data model in ADW:

![High-level Data Processing](images/e-HRAnalytics-diagrams-Logical-Data-Processing.jpg)

-   **Data Sources**: data sources are 4 text files loaded by ${doc.customer.name} in Object Storage buckets and 2 ADW tables (output of APEX application)
-   **Working Tables**: tables to calculate intermediate results to be loaded then to the final target schemas
-   **Target Tables and Views**: lakehouse HR target tables and Views (accessed by OAC for dashboards and visualizations)
-   **Aggregated views**: aggregated views created to run ML Model

#### ADW Users/Schemas

Two users/schemas will be created to manage the ADW data model and the ADW data sources:

-   LHHR: user/schema for working tables and target tables.
-   LHAPP: user/schema for the application tables that are the data sources for the HR analytics workload.

#### Data Sources

Data sources files will be stored by ${doc.customer.name} in the reserved specific Object Storage buckets:

-   **HRCosts-Dev** for development data source files
-   **HRCosts-Prod** for production data source files

Source files are:

-   **filename1.txt**: csv files with ";" as separator. It contains historical data regarding ${doc.customer.name}'s employees and their organizational units. Repeated for every month you can find the organizational units to which employees belong.
-   **filename2.txt**: csv files with ";" as separator. It contains historical data regarding ${doc.customer.name}'s salary slip items. Each item may have additional rows with related reference month, in case change to the item description occurs.
-   **filename3.txt**: csv files with ";" as separator. It contains historical data regarding ${doc.customer.name}'s employee retributions. Level of detail for the amounts is: month, salary slip item, employee.
-   **filename4.txt**: csv files with ";" as separator. It contains historical data regarding ${doc.customer.name}'s employees salary as per accounting information (EBS). Level of detail for the amounts is: month, salary slip item, employee category (manager/employee).

For detailed descriptions of the source file structure including columns name, columns type and columns description refer to the sheet "Source Files" in the attached Excel file "\_${doc.customer.name}*HRAnalytics_DataMapping.xlsx*"

Source tables are:

-   **D_SOURCE_TABLE1**: it contains the hierarchy levels for the salary slip items.
-   **D_SOURCE_TABLE2**: it contains information of the reversals of the salary that have to be considered to calculate values in the target fact table **F_TABLE1**.

#### Working Tables

We create two working tables:

-   **W_TABLE1**: used to elaborate the validity interval period for the salary slip items (included in the source file **filename2.txt**. To optimize the loading of **W_TABLE1** with OCI Data Integration two additional temporary/working table are used (**T_TABLE1**, **W_TABLE2**)
-   **W_TABLE3**: with the data of the TABLE2 table filtered by type of "*column1*" and with the calculation of the amounts of reversals and funds ("*column2*" and "*column3*").
-   **W_TABLE3** with the data of the filename3.txt file filtered for the last five years.

For detailed descriptions of the table structures and related mapping to load them refer to the sheet "Working Tables" in the attached Excel file "\_${doc.customer.name}*HRAnalytics_DataMapping.xlsx*"

#### Target Tables and Views

The logical data model that includes the target table is shown in the figure below:

![Logical Data Model](images/e-Relational_DM.png)

Target Tables and Views are:

-   Table **D_TABLE1**: It contains all the attributes regarding the salary payslip items. It Includes master-data coming from the **FILENAME1.txt** source file and the related hierarchy as per the information stored in the **D_SOURCE_TABLE1** source table. A consolidated validity period is calculated for each salary item.
-   View **V_D_VIEW1**: Using the group of salary items present in **D_TABLE1** it calculates a high level categorization ("*Category1*": "*Category1*", "*Category1*", "*Category4*", "*Category5*", "*Category6*"). This view is then used to calculate the aggregated view **V_W_VIEW2**.
-   Table **D_TABLE2**: It contains all the information regarding ${doc.customer.name}'s organizational unit. It includes the information coming from the **FILENAME2.txt** source files.
-   View **V_D_TABLE2**: Starting from the data in the dimension **D_TABLE2** and in the fact table **F_TABLE3** we create also this database view that contains some additional records. The added records are the ones related to those employees that are still present in the SourceFile3.txt files but not in the SourceFile2.txt file anymore. This case happens after an employee resigned and, even if he/she is not part of ${doc.customer.name} organizational units anymore, he/she still receives last salaries from ${doc.customer.name} (then is present in the system and in SourceFile3.txt file)
-   **D_TIME**: Time dimension. The level of detail is month.
-   **D_TABLE4**: table manually loaded with the only two values for "accounting employee category" that are: "Impiegato" and "Dirigente". It is used as conformed dimension to compare values of the salary coming from HR System (stored in **F_TABLE3** target table) with the values for the salary coming from accounting systems (stored in **F_TABLE5** target table)
-   **F_TABLE3**: It contains the values of the employee salary and, eventually, the values of related reversals. Level of details are: month, employee, salary item.
-   **F_TABLE5**: It contains the values of the employee salary as managed in the accounting system. Level of details are: month, employee, employee accounting category.

For detailed descriptions of the table structures and related mapping to load them refer to the sheet "Target - Data Mart" in the attached Excel file "\_${doc.customer.name}*HRAnalytics_DataMapping.xlsx*"

#### Aggregated Views

We create an aggregated view:

-   **V_W_VIEW3**: it's built with the data of **F_TABLE3**, **D_TABLE1** and **V_D_VIEW1**. It calculates all the values needed for an existing ML Model developed during a previous POC.

#### OAC Workbook

We create an OAC Workbook using the Subject Area "*HR Analysis*". The workbook contains a canvas with the report required by ${doc.customer.name} (see par. 4.2.1 - Fig.4). In addition the workbook will contain other visualizations as sample analyses with Cost of Labour data.

#### OAC security

There is no specific implementation required for OAC security. As starting point, we create for ${doc.customer.name} the users listed below (will be assigned to **BI Service Administrator** OAC role):

-   John Smith: john.smith@${doc.customer.name}.com
-   Tom Scott : tom.scott@${doc.customer.name}.com

${doc.customer.name} will add further OAC users in the future.

[^1]: **OAC**:Oracle Analytics Cloud, **ADW**: Autonomous Data Warehouse, **OCI DI**: Data Integration, **APEX**: Oracle Application Express

# Annex


## Security Guidelines

<!--
    Owner: Srihari and olaf
    Last Change: 04 July 2023
    Review Status: Live
    Review Notes: -
-->

### Oracle Security, Identity, and Compliance

Oracle Cloud Infrastructure (OCI) is designed to protect customer workloads with a security-first approach across compute, network, and storage – down to the hardware. It’s complemented by essential security services to provide the required levels of security for your most business-critical workloads.

- [Security Strategy](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/security-strategy.htm) – To create a successful security strategy and architecture for your deployments on OCI, it's helpful to understand Oracle's security principles and the OCI security services landscape.
- The [security pillar capabilities](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/security.htm#capabilities) reflect fundamental security principles for architecture, deployment, and maintenance. The best practices in the security pillar, help your organization to define a secure cloud architecture, identify and implement the right security controls, and monitor and prevent issues such as configuration drift.

### References

- The Best Practices Framework for OCI provides architectural guidance about how to build OCI services in a secure fashion, based on recommendations in the [Best practices framework for Oracle Cloud Infrastructure](https://docs.oracle.com/en/solutions/oci-best-practices).
- Learn more about [Oracle Cloud Security Practices](https://www.oracle.com/corporate/security-practices/cloud/).
- For detailed information about security responsibilities in Oracle Cloud Infrastructure, see the [Oracle Cloud Infrastructure Security Guide](https://docs.oracle.com/iaas/Content/Security/Concepts/security_guide.htm).

### Compliance and Regulations

Cloud computing is fundamentally different from traditionally on-premises computing. In the traditional model, organizations are typically in full control of their technology infrastructure located on-premises (e.g., physical control of the hardware, and full control over the technology stack in production). In the cloud, organizations leverage resources and practices that are under the control of the cloud service provider, while still retaining some control and responsibility over other components of their IT solution. As a result, managing security and privacy in the cloud is often a shared responsibility between the cloud customer and the cloud service provider. The distribution of responsibilities between the cloud service provider and the customer also varies based on the nature of the cloud service (IaaS, PaaS, SaaS).

### Additional Resources
- [Oracle Cloud Compliance](https://www.oracle.com/corporate/cloud-compliance/) – Oracle is committed to helping customers operate globally in a fast-changing business environment and address the challenges of an ever more complex regulatory environment. This site is a primary reference for customers on the Shared Management Model with Attestations and Advisories.
- [Oracle Security Practices](https://www.oracle.com/corporate/security-practices/) – Oracle’s security practices are multidimensional, encompassing how the company develops and manages enterprise systems, and cloud and on-premises products and services.
- [Oracle Cloud Security Practices](https://www.oracle.com/corporate/security-practices/cloud/) documents.
- [Contract Documents](https://www.oracle.com/contracts/cloud-services/#online) for Oracle Cloud Services.
- [OCI Shared Security Model](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/security.htm#shared-security-model)
- [OCI Cloud Adoption Framework Security Strategy](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/security-strategy.htm)
- [OCI Security Guide](https://docs.oracle.com/en-us/iaas/Content/Security/Concepts/security_guide.htm)
- [OCI Cloud Adoption Framework Security chapter](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/security.htm)

## Networking Requirement Considerations

<!--
    Owner: Luis Catalan
    Last Change: 1st of September 2023
    Review Status: Live
    Review Notes: -
-->

The below questions help to identify networking requirements.

### Application Connectivity

- Does your application need to be exposed to the internet?
- Does your solution on DC (on-prem) need to be connected 24x7 to OCI in a Hybrid model?
  - Site-to-Site IPSEC (Y/N)
  - Dedicated Lines (FC) (Y/N)
- Are there any specific network security requirements for your application? (No internet, encryption, etc, etc)
- Will your application require connectivity to other cloud providers?
  - Site-to-Site IPSEC (Y/N)
  - Dedicated Lines (FC)  (Y/N)
- Will your application require inter-region connectivity?
- Are you planning to reuse IP addresses from your on-premises environment in OCI?
- If yes, what steps have you taken to ensure IP address compatibility and avoid conflicts?
- How will you handle network address translation (NAT) for IP reuse in OCI?
- Will you bring your own public IPs to OCI?

### DR and Business Continuity

- Does your organization need a Business Continuity/DR Plan to address potential disruptions?
  - Network Requirements (min latency, bandwidth, etc)
  - RPO/RTO values
- What are your requirements regarding Data Replication and Geo-Redundancy (different regions, restrictions, etc.)?
- Are you planning to distribute incoming traffic across multiple instances or regions to achieve business continuity?
- What strategies do you require to guarantee minimal downtime and data loss, and to swiftly recover from any unforeseen incidents?

### High Availability and Scalability

- Does your application require load balancing for high availability and scalability? (y/n)
  - Does your application span around the globe or is regionally located?
  - How do you intend to ensure seamless user experiences and consistent connections in your application (session persistence, affinity, etc.)?
  - What are the network Security requirements for traffic management (SSL offloading, X509 certificates management, etc.)?
  - Does your application use name resolutions and traffic steering across multiple regions (Public DNS steering)?

### Security and Access Control

- Are you familiar with the concept of Next-Generation Firewalls (NGFW) and their benefits over traditional firewalls?
- Have you considered the importance of protecting your web applications from potential cyber threats using a Web Application Firewall (WAF)?

### Monitoring and Troubleshooting

- How do you plan to monitor your application's network performance in OCI?
- How can you proactively address and resolve any potential network connectivity challenges your company might face?
- How do you plan to troubleshoot your network connectivity?

## Networking Solutions

<!--
    Owner: Luis Catalan
    Last Change: 1st of September 2023
    Review Status: Live
    Review Notes: -
-->

### OCI Network Firewall

Oracle Cloud Infrastructure Network Firewall is a next-generation managed network firewall and intrusion detection and prevention service for your Oracle Cloud Infrastructure VCN, powered by Palo Alto Networks®.

- [Overview](https://docs.oracle.com/en-us/iaas/Content/network-firewall/overview.htm)
- [OCI Network Firewall](https://docs.oracle.com/en/solutions/oci-network-firewall/index.html#GUID-875E911C-8D7D-4205-952B-5E8FAAD6C6D3)

### OCI Load Balancer

The Load Balancer service provides automated traffic distribution from one entry point to multiple servers reachable from your virtual cloud network (VCN). The service offers a load balancer with your choice of a public or private IP address and provisioned bandwidth.

- [Load Balancing](https://www.oracle.com/es/cloud/networking/load-balancing/)
- [Overview](https://docs.oracle.com/en-us/iaas/Content/NetworkLoadBalancer/overview.htm)
- [Concept Overview](https://docs.oracle.com/en-us/iaas/Content/Balance/Concepts/balanceoverview.htm)

### OCI DNS Traffic Management

Traffic Management helps you guide traffic to endpoints based on various conditions, including endpoint health and the geographic origins of DNS requests.

- [Concept Overview](https://docs.oracle.com/en-us/iaas/Content/TrafficManagement/Concepts/overview.htm)
- [DNS](https://docs.oracle.com/en-us/iaas/Content/DNS/home.htm)

### OCI WAF

Protect applications from malicious and unwanted internet traffic with a cloud-based, PCI-compliant, global web application firewall service.

- [Cloud Security Web Application Firewall](https://www.oracle.com/security/cloud-security/web-application-firewall/)
- [Add WAF to a load balancer](https://docs.oracle.com/en/learn/oci-waf-flex-lbaas/index.html#add-oracle-cloud-infrastructure-web-application-firewall-protection-to-a-flexible-load-balancer)

### OCI IGW

An internet gateway is an optional virtual router that connects the edge of the VCN with the internet. To use the gateway, the hosts on both ends of the connection must have public IP addresses for routing

- [Managing IGW](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/managingIGs.htm)

### OCI Site-to-Site VPN

Site-to-site VPN provides a site-to-site IPSec connection between your on-premises network and your virtual cloud network (VCN). The IPSec protocol suite encrypts IP traffic before the packets are transferred from the source to the destination and decrypts the traffic when it arrives. Site-to-Site VPN was previously referred to as VPN Connect and IPSec VPN.

- [Overview IPSec](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/overviewIPsec.htm)
- [Setup IPSec](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/settingupIPsec.htm)

### OCI Fast Connect

FastConnect allows customers to connect directly to their Oracle Cloud Infrastructure (OCI) virtual cloud network via dedicated, private, high-bandwidth connections.

- [FastConnect](https://www.oracle.com/cloud/networking/fastconnect/)
- [Concept Overview](https://docs.public.oneportal.content.oci.oraclecloud.com/en-us/iaas/Content/Network/Concepts/fastconnect.htm)

### OCI VTAP

A Virtual Test Access Point (VTAP) provides a way to mirror traffic from a designated source to a selected target to facilitate troubleshooting, security analysis, and data monitoring

- [VTAP](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/vtap.htm)
- [Network VTAP Wireshark](https://docs.oracle.com/en/solutions/oci-network-vtap-wireshark/index.html#GUID-3196621D-12EB-470A-982C-4F7F6F3723EC)

### OCI NPA

Network Path Analyzer (NPA) provides a unified and intuitive capability you can use to identify virtual network configuration issues that impact connectivity. NPA collects and analyzes the network configuration to determine how the paths between the source and the destination function or fail.

- [Path Analyzer](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/path_analyzer.htm)

### OCI DRG (Connectivity Options)

A DRG acts as a virtual router, providing a path for traffic between your on-premises networks and VCNs, and can also be used to route traffic between VCNs. Using different types of attachments, custom network topologies can be constructed using components in different regions and tenancies.

- [Managing DRGs](https://docs.oracle.com/es-ww/iaas/Content/Network/Tasks/managingDRGs.htm)
- [OCI Pilot Light DR](https://docs.oracle.com/en/solutions/oci-pilot-light-dr/index.html#GUID-3C1F7B6B-0195-4166-A38C-8B7AD53F0B79)
- [Peering VCNs in different regions through a DRG](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/scenario_e.htm)

### OCI Oracle Cloud Infrastructure Certificates

Easily create, deploy, and manage Secure Sockets Layer/Transport Layer Security (SSL/TLS) certificates available in Oracle Cloud. In a flexible Certificate Authority (CA) hierarchy, Oracle Cloud Infrastructure Certificates help create private CAs to provide granular security controls for each CA.

- [SSL TLS Certificates](https://www.oracle.com/security/cloud-security/ssl-tls-certificates/)

### OCI Monitoring

You can monitor the health, capacity, and performance of your Oracle Cloud Infrastructure resources by using metrics, alarms, and notifications. For more information, see [Monitoring](https://docs.oracle.com/iaas/Content/Monitoring/home.htm) and [Notifications](https://docs.oracle.com/en-us/iaas/Content/Notification/home.htm#top).

- [Networking Metrics](https://docs.oracle.com/en-us/iaas/Content/Network/Reference/networkmetrics.htm)