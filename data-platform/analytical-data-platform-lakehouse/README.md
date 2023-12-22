# Analytical Data Platform
 
Oracle's [Data Platform](https://www.oracle.com/data-platform/) delivers a complete, open, and intelligent platform to cater to all analytical workloads from the largest lakehouses to the smallest data marts, from a cloud data warehouse to a distributed data mesh; it delivers these workloads at scale and with enterprise-grade security and performance to tackle the most demanding data workloads.

Reviewed: 19.12.2023
 
# Table of Contents
 
1. [Team Publications](#team-publications)
2. [Useful Links](#useful-uinks)
3. [Reusable Assets Overview](#reusable-assets-overview)
 
# Team Publications

## Architecture Center
 
- [Data platform - data lakehouse](https://docs.oracle.com/en/solutions/data-platform-lakehouse/index.html#GUID-A328ACEF-30B8-4595-B86F-F27B512744DF)
    - This reference architecture describes a lakehouse architecture pattern, the services that are part of it, the capabilities those services deliver, and how to deploy them. It covers best practices, a deployment topology, and automated deployment with an [Oracle Resource Manager Terraform stack](https://github.com/oracle-devrel/terraform-oci-oracle-cloud-foundation/tree/main/cloud-foundation/solutions/Data-platform-data-lakehouse) (part of the [cloud-foundation Terraform solutions](https://github.com/oracle-devrel/terraform-oci-oracle-cloud-foundation/tree/main/cloud-foundation)).
- [Deploy a machine learning model close to the network edge](https://docs.oracle.com/en/solutions/deploy-ml-at-edge/#GUID-8EC86246-D724-4C16-8073-8CB5B2EA6719)
    - This reference architecture describes a deployment where data is ingested from edge locations into OCI, where it is used to build and train ML models that are deployed in the edge for low latency inferencing.
- [Monetize data with Oracle Cloud Infrastructure](https://docs.oracle.com/en/solutions/monetize-data-oci/index.html)
    - Reference Architecture depicting how to support data monetization by exposing data products via APIs and integrating with subscription and payment systems to process usage and payments.
- [Data platform - data federation](https://docs.oracle.com/en/solutions/data-platform-federation/index.html#GUID-440BB303-426C-4467-91EE-09C1BA564C84)
    - Reference Architecture depicting how to combine, correlate, and analyze lakehouse data with federated data regardless of location (third-party cloud stores, cloud, and on premises databases) without having to duplicate data.

## GitHub

- [OCI Monitoring with PLSQL SDK](https://jakubillner.github.io/2022/10/07/How-to-Get-OCI-Utilization-in-PLSQL.html)
  - Blog post showcasing how to read monitoring metrics directly from ADW to control data ingestion load.
- [Options for Storing Large JSON Documents in Autonomous Database](https://jakubillner.github.io/2022/09/30/JSON-in-autonomous-database.html)
  - Blog post showcasing options for storing large JSON documents in an Autonomous Database
- [Transforming JSON documents with OCI Data Integration](https://jakubillner.github.io/2022/10/25/Flattening-JSON-documents-with-OCI-Data-Integration.html)
  - Blog post showcasing how to process and store JSON on the Data Lake in parquet format to then use that data for analytics in the context of a lakehouse architecture
- [Event Driven Automation of OCI Data Integration Tasks](https://jakubillner.github.io/2022/11/11/automating-di-tasks-with-events.html)
  - Blog post on how to do event-driven automation of data pipelines leveraging events and functions to trigger an OCI DI task.
- [Decentralized Data Lake on OCI Object Storage](https://jakubillner.github.io/2022/12/30/data-lake-on-oci-object-storage.html)
  - Blog post describing how to organize and govern a data lake that supports several business domains in an OCI tenancy, maintaining segregation between domains while ensuring those domains have the flexibility and agility to maintain their cloud resources to produce data products.
- [Decentralized Data Lake on OCI Object Storage (Part 2)](https://jakubillner.github.io/2023/02/19/data-lake-on-oci-object-storage-2.html)
  - Blog post describing how to organize and govern a decentralized data lake domains and entities in an OCI tenancy with a design that explains 1) how to store lake data with partitions, 2) how those can be implemented, 3) governed by a Data Catalog and then 4) consumed seamlessly by ADW in a cohesive and integrated lakehouse architecture.
- [Automated Load and Export Pipelines in Autonomous Database](https://jakubillner.github.io/2023/03/27/adb-data-pipelines.html)
  - Blog post on how to ingest automatically data residing in Object Storage to make it available in ADW for further processing and curation. Covers the export of ADW data to Object Storage that can be used for several purposes, including ILM, offloading data sharing to Object Storage, or making data available via the data lake. 
- [Real Time Analytics DW DR Architecture (Part I) - DR Architecture Configuration](https://gianlucarossi06.github.io/data-organon/2023/04/20/Real-Time-Analytics-DW-DR-Architecture-(Part-I).html)
  - Blog post showcasing how to configure a DR for a DW architecture using ADW and OCI GG. 
- [Real Time Analytics DW DR Architecture (Part II) - DR Recovery Operations](https://gianlucarossi06.github.io/data-organon/2023/04/20/Real-Time-Analytics-DW-DR-Architecture-(Part-II).html)
  - Blog post showcasing a disaster simulation on the primary Region and describing the operational tasks that need to be performed to properly start the workload in the secondary Region.
- [Data Integration Operational Analytics](https://jakubillner.github.io/2023/11/10/data-integration-analytics.html)
  - Blog post describing a solution to monitor data integration pipelines at an enterprise level, potentially for several workspaces, and providing integrated monitoring capabilities as one of the key pillars to address DataOps.
- [Zero ETL Lakehouse in Oracle Cloud](https://gianlucarossi06.github.io/data-organon/2023/09/30/ZeroETL-Lakehouse-Oracle-Cloud.html)
  - Blog post describing what is ZeroETL and the different options in OCI to deploy a lakehouse that minimizes and reduces ETL to deliver information to data consumers.


## YouTube

- [Decentralized Data Platform on Oracle Cloud Infrastructure (OCI)](https://youtu.be/mHryV0K8Ciw?si=hJyOpxalMVf3bjbL)
  - Cloud Coaching session covering the concepts of a decentralized data platform, how to design such a platform with Oracle Cloud Infrastructure, and how to easily share data between data domains.
- [Data Lake Modernization](https://youtu.be/bOF3YJq4L6A?si=WgQVp9sXuZz8Em_3)
  - Cloud Coaching session covering Hadoop-based Data Lake modernizations in OCI, explaining the deployment options and migration path.
- [Architecting Analytical Data Platform](https://youtu.be/-rMUsvrXYw4?si=7Yx80VvZQYiy2qHE)
  - Cloud Coaching session covering how to architect an Analytical Data Platform in Oracle and OCI using best practices to achieve trustable business outcomes.
- [Real Time Analytics on Oracle Data Platform](https://www.youtube.com/watch?v=SVmM0CuLnU4)
  - Cloud Coaching session describing what is Real-Time Analytics and how to architect a real-time analytics workload on the Oracle Data Platform.
- [Analytics and Lakehouse for Oracle Applications](https://youtu.be/a_JsSzmz1_U)
  - Session describing how to architect analytical workloads for Oracle Applications.
- [Real Time Analytics - Cloud Customer Connect](https://community.oracle.com/customerconnect/events/604981-oci-real-time-analytics)
  - Cloud Customer Connect session describing what is Real-Time Analytics and how to architect a real-time analytics workload on the Oracle Data Platform.
- [Data Lake Modernization - Cloud Customer Connect](https://community.oracle.com/customerconnect/events/604994-oci-data-lake-modernization)
  - Cloud Customer Connect session covering Hadoop-based Data Lake modernizations in OCI, explaining the deployment options and migration path.
- [Modernize your on-premises Oracle Informatica solution to Oracle Cloud](https://youtu.be/gQ2_AztxR84?si=DyEfvgn3mk0oIP9U)
  - Cloud coaching session describing how to modernize an Oracle DW solution that uses PowerCenter for ETL into OCI and Informatica IDMC.

## LinkedIn

- [Delta Sharing with Oracle Cloud](https://www.linkedin.com/pulse/delta-sharing-oracle-cloud-jeff-richmond%3FtrackingId=kztSJVKDLRyOgQ30mH2ujQ%253D%253D/?trackingId=kztSJVKDLRyOgQ30mH2ujQ%3D%3D)
  - Article explaining Data Sharing capabilities Oracle Cloud and Autonomous Database have based on the open source Delta Share protocol, which allows sharing data between heterogeneous data platforms in a multi cloud and heterogeneous data platform.
- [Data Swamps No More!](https://www.linkedin.com/pulse/data-swamps-more-ismael-hassane/)
  - Article describing lakehouse as a natural evolution from a lambda and kappa data architecture.
- [DataOps, you data rolls!](https://www.linkedin.com/pulse/dataops-your-data-rolls-ismaël-hassane/)
  - Blog post introducing DataOps, the several aspects of a DataOps strategy in a lakehouse architecture, and how OCI services and features address those different aspects.

## Medium

- [Oracle BI Applications and migration to Fusion Applications](https://medium.com/@DoubleUP66/oracle-bi-applications-and-migration-to-fusion-applications-1ae7db1bff15)
  - Blog describing the different options to modernize OBIA when customers migrate their Oracle Unlimited Apps into Oracle Fusion SaaS.

## Podcasts

- [Data Mesh Concepts](https://digitalimpactradio.libsyn.com/s7-ep09-data-mesh-concepts-with-larry-jose-and-mike-pt-1-of-4)
  - Digital Impact Radio podcast with José Cruz, Mike Blackmore, Larry Fumagally, and Franco Ucci discussing Data Mesh concepts.
- [From a monolith approach to a Data Mesh](https://digitalimpactradio.libsyn.com/s7-ep10-from-a-monolithic-approach-to-a-data-mesh-with-larry-jose-and-mike-pt-2-of-4)
  - Digital Impact Radio podcast with José Cruz, Mike Blackmore, Larry Fumagally, and Franco Ucci discussing how to move from a monolith approach into a data mesh.
- [Data Mesh components deep dive](https://digitalimpactradio.libsyn.com/s7-ep11-data-mesh-components-deep-dive-with-larry-jose-and-mike-pt-3-of-4)
  - Digital Impact Radio podcast with José Cruz, Mike Blackmore, Larry Fumagally, and Franco Ucci discussing the components needed for a data mesh.
- [Oracle Data Mesh Components](https://digitalimpactradio.libsyn.com/s7-ep12-oracle-data-mesh-components-with-larry-jose-and-mike-pt-4-of-4)
  - Digital Impact Radio podcast with José Cruz, Mike Blackmore, Larry Fumagally, and Franco Ucci discussing the components needed for a data mesh on an OCI ecosystem.

# Useful Links
- [Oracle Modern Data Platform](https://www.oracle.com/data-platform/)
  - Oracle Modern Data Platform Homepage
- [Oracle Cloud Word 2023 - Data Strategy: From Vision to Reality](https://videohub.oracle.com/media/Oracle+Cloud+Word+2023+-+Data+StrategyA+From+Vision+to+Reality/1_0zwykatb)
  - Data Strategy session explaining what are the elements and reasoning behind defining a data strategy that is the conduit between the business strategy and requirements and a data platform architecture.

# Reusable Assets Overview

- [Workload Architecture Documents](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/analytical-data-platform-lakehouse/workload-architecture-documents)
  - [Cloud Analytics with OAC standalone](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/analytical-data-platform-lakehouse/workload-architecture-documents/cloud-analytics-with-oac-standalone)
    - In-depth guide on how to design and deploy a cloud analytics workload that uses Oracle Analytics Cloud (OAC) as the visualization tool to show data residing on a premises Data Warehouse using private connectivity.
  - [Oracle DWH Analytics for IT](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/analytical-data-platform-lakehouse/workload-architecture-documents/data-warehouse-analytics-for-IT)
    - In-depth guide on how to design and deploy a DWH Analytical workload for IT. This particular example covers a migration of an existing Oracle DW workload but the guide can be leveraged as well for net new workloads.
  - [Oracle DWH Analytics for LoB](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/analytical-data-platform-lakehouse/workload-architecture-documents/dwh-analytics-for-lob)
      - In-depth guide on how to design and deploy a DWH Analytical workload for Lines of Business (LoBs) based on the eBusiness Suite (eBS) accelerator that Oracle Consulting has for Customers.
  - [In-database Machine Learning](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/analytical-data-platform-lakehouse/workload-architecture-documents/in-database-machine-learning)
    - Machine Learning project based on the Autonomous Database Oracle Machine Learning (OML) reference architecture, useful links, and a workload deployment template. 
  - [Oracle BI Applications with Informatica PowerCenter migration to Oracle OCI with Informatica IDMC, OAC and ADW](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/analytical-data-platform-lakehouse/workload-architecture-documents/obia-with-informatica-to-oci-with-idmc)
    - An in-depth guide on how to define and design a Data Warehouse Analytical workload when migrating from an Oracle BI Applications (OBIA) with Informatica PowerCenter to Oracle OCI with Informatica IDMC, Oracle Analytics Cloud (OAC) and Autonomous Data Warehouse (ADW).
  - [Oracle BI Applications 11g with ODI migration to Oracle OCI with ODI, OAC and Oracle DB](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/analytical-data-platform-lakehouse/workload-architecture-documents/obia-with-odi-migration-to-oci)
      - In-depth guide on how to define and design a Data Warehouse Analytical workload when migrating from an Oracle BI Applications (OBIA) 11g with ODI to Oracle OCI, Oracle Analytics Cloud (OAC), and Oracle Database
  - [Oracle Database and OBIEE migration to Autonomous Data Warehouse and Oracle Analytics Cloud](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/analytical-data-platform-lakehouse/workload-architecture-documents/obiee-db-migration-to-oac-adw)
    - In-depth guide on how to define, design, and deploy a Data Warehouse Analytical workload when migrating from an on-premise OBIEE and Oracle database solution to an OCI Oracle Analytics Cloud (OAC) + Autonomous Data Warehouse (ADW) solution
  - [Serverless Lakehouse](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/analytical-data-platform-lakehouse/workload-architecture-documents/serverless-lakehouse)
    - Design for a Lakehouse Serverless solution for HR Analytics. The solution includes OCI Data Integration, Autonomous Data Warehouse, OCI Objects Storage, Oracle Analytics Cloud, OCI Data Flow, and OCI Data Science.
  - [Stand-alone Data Science](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/analytical-data-platform-lakehouse/workload-architecture-documents/stand-alone-oci-data-science)
      - Machine Learning project based on the Oracle Cloud Infrastructure Data Science service, reference architecture, useful links, and a workload deployment template.

# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
