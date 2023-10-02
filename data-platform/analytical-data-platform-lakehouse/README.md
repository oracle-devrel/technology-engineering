# Analytical Data Platform
 
Oracle's [Data Platform](https://www.oracle.com/data-platform/) delivers a complete, open, and intelligent platform to cater to all analytical workloads from the largest lakehouses to the smallest data marts, from a cloud data warehouse to a distributed data mesh; it delivers these workloads at scale and with enterprise-grade security and performance to tackle the most demanding data workloads. 
 
# Table of Contents
 
1. [Team Publications](#team-publications)
2. [Useful Links](#useful-uinks)
3. [Reusable Assets Overview](#reusable-assets-overview)
 
## Team Publications

### Architecture Center
 
- [Data platform - data lakehouse](https://docs.oracle.com/en/solutions/data-platform-lakehouse/index.html#GUID-A328ACEF-30B8-4595-B86F-F27B512744DF)
    - This reference architecture describes a lakehouse architecture pattern, the services that are part of it, the capabilities those services deliver, and how to deploy them. It covers best practices, a deployment topology, and automated deployment with an Oracle Resource Manager Terraform stack.
- [Deploy a machine learning model close to the network edge](https://docs.oracle.com/en/solutions/deploy-ml-at-edge/#GUID-8EC86246-D724-4C16-8073-8CB5B2EA6719)
    - This reference architecture describes a deployment where data is ingested from edge locations into OCI, where it is used to build and train ML models that are deployed in the edge for low latency inferencing.

### GitHub

- [OCI Monitoring with PLSQL SDK](https://jakubillner.github.io/2022/10/07/How-to-Get-OCI-Utilization-in-PLSQL.html)
  - Blog post showcasing how to read monitoring metrics directly from ADW to control data ingestion load.
- [Options for Storing Large JSON Documents in Autonomous Database](https://jakubillner.github.io/2022/09/30/JSON-in-autonomous-database.html)
  - Blog post showcasing options for storing large JSON documents in Autonomous Database
- [Transforming JSON documents with OCI Data Integration](https://jakubillner.github.io/2022/10/25/Flattening-JSON-documents-with-OCI-Data-Integration.html)
  - Blog post showcasing how to process and store JSON on the Data Lake in parquet format to then use that data for analytics in the context of a lakehouse architecture
- [Event Driven Automation of OCI Data Integration Tasks](https://jakubillner.github.io/2022/11/11/automating-di-tasks-with-events.html)
  - Blog post on how to do event-driven automation of data pipelines leveraging events and functions to trigger an OCI DI task.
- [Decentralized Data Lake on OCI Object Storage](https://jakubillner.github.io/2022/12/30/data-lake-on-oci-object-storage.html)
  - Blog post describing how to organize and govern a data lake that supports several business domains in an OCI tenancy, maintaining segregation between domains while ensuring those domains have the flexibility and agility to maintain their cloud resources to produce data products.
- [Decentralized Data Lake on OCI Object Storage (Part 2)](https://jakubillner.github.io/2023/02/19/data-lake-on-oci-object-storage-2.html)
  - Blog post describing how to organize and govern a decentralized data lake domains and entities in an OCI tenancy with a design that explains 1) how to store lake data with partitions, 2) how those can be implemented, 3) governed by a Data Catalog and then 4) consumed seamlessly by ADW in a cohesive and integrated lakehouse architecture.
- [Automated Load and Export Pipelines in Autonomous Database](https://jakubillner.github.io/2023/03/27/adb-data-pipelines.html)
  - Blog post on how to ingest automatically data residing in Object Storage to make it available in ADW for further processing and curation. Covers as well the export of ADW data to Object Storage that can be used for several purposes, including ILM, offloading data sharing to Object Storage, or making data available via the data lake. 
- [Real Time Analytics DW DR Architecture (Part I) - DR Architecture Configuration](https://gianlucarossi06.github.io/data-organon/2023/04/20/Real-Time-Analytics-DW-DR-Architecture-(Part-I).html)
  - Blog post showcasing how to configure a DR for a DW architecture using ADW and OCI GG. 
- [Real Time Analytics DW DR Architecture (Part II) - DR Recovery Operations](https://gianlucarossi06.github.io/data-organon/2023/04/20/Real-Time-Analytics-DW-DR-Architecture-(Part-II).html)
  - Blog post showcasing a disaster simulation on the primary Region and describing the operational tasks that need to be performed to properly start the workload in the secondary Region.

### YouTube

- [Decentralized Data Platform on Oracle Cloud Infrastructure (OCI)](https://youtu.be/mHryV0K8Ciw?si=hJyOpxalMVf3bjbL)
  - Cloud Coaching session covering the concepts of a decentralized data platform, how to design such platform with Oracle Cloud Infrastructure, and how to easily share data between data domains.
- [Data Lake Modernization](https://youtu.be/bOF3YJq4L6A?si=WgQVp9sXuZz8Em_3)
  - Cloud Coaching session covering Hadoop-based Data Lake modernizations in OCI, explaining the deployment options and migration path.
- [Architecting Analytical Data Platform](https://youtu.be/-rMUsvrXYw4?si=7Yx80VvZQYiy2qHE)
  - Cloud Coaching session covering how to architect an Analytical Data Platform in Oracle and OCI using best practices to achieve trustable business outcomes.
- [Real Time Analytics on Oracle Data Platform](https://www.youtube.com/watch?v=SVmM0CuLnU4)
  - Cloud Coaching session describing what is Real Time Analytics and how to architect a real-time analytics workload on the Oracle Data Platform.
- [Analytics and Lakehouse for Oracle Applications](https://youtu.be/a_JsSzmz1_U)
  - Session describing how to architect analytical workloads for Oracle Applications.

### LinkedIn

- [Data Swamps No More!](https://www.linkedin.com/pulse/data-swamps-more-ismael-hassane/)
  - Article describing lakehouse as a natural evolution from a lambda and kappa data architecture.
- [DataOps, you data rolls!](https://www.linkedin.com/pulse/dataops-your-data-rolls-ismaël-hassane/)
  - Blog post introducing DataOps, the several aspects of a DataOps strategy in a lakehouse architecture, and how OCI services and features address those different aspects.

### Podcasts

- [Data Mesh Concepts](https://digitalimpactradio.libsyn.com/s7-ep09-data-mesh-concepts-with-larry-jose-and-mike-pt-1-of-4)
  - Digital Impact Radio podcast with José Cruz, Mike Blackmore, Larry Fumagally, and Franco Ucci discussing Data Mesh concepts.
- [From a monolith approach to a Data Mesh](https://digitalimpactradio.libsyn.com/s7-ep10-from-a-monolithic-approach-to-a-data-mesh-with-larry-jose-and-mike-pt-2-of-4)
  - Digital Impact Radio podcast with José Cruz, Mike Blackmore, Larry Fumagally, and Franco Ucci discussing how to move from a monolith approach into a data mesh.
- [Data Mesh components deep dive](https://digitalimpactradio.libsyn.com/s7-ep11-data-mesh-components-deep-dive-with-larry-jose-and-mike-pt-3-of-4)
  - Digital Impact Radio podcast with José Cruz, Mike Blackmore, Larry Fumagally, and Franco Ucci discussing the components needed for a data mesh.
- [Oracle Data Mesh Components](https://digitalimpactradio.libsyn.com/s7-ep12-oracle-data-mesh-components-with-larry-jose-and-mike-pt-4-of-4)
  - Digital Impact Radio podcast with José Cruz, Mike Blackmore, Larry Fumagally, and Franco Ucci discussing the components needed for a data mesh on an OCI ecosystem.

## Useful Links
- [Oracle Modern Data Platform](https://www.oracle.com/data-platform/)
  - Oracle Modern Data Platform Homepage

## Reusable Assets Overview
TBD

# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/folder-structure/LICENSE) for more details.
