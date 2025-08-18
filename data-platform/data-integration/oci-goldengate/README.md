# OCI GoldenGate

Oracle Cloud Infrastructure GoldenGate is a fully managed, native cloud service that moves data in real-time, at scale. OCI GoldenGate processes data as it moves from one or more data management systems to target databases. You can also design, run, orchestrate, and monitor data replication tasks without having to allocate or manage any Compute environment.

Reviewed: 28.02.2025


# Table of Contents
 
1. [Team Publications](#team-publications)
2. [Useful Links](#useful-links)
3. [Workshops](#workshops)

 
# Team Publications


- [Sync data between DBCS and Google BigQuery using Stage and Merge](https://github.com/alexandruporcescu/Articles/blob/main/Sync%20OracleDB%20with%20Google%20BigQuery/Replicate%20data%20from%20Oracle%20DB%20to%20Google%20BigQuery%20using%20GoldenGate%20Stage%20and%20Merge%20handler.md)
    - GitHub articles that show a step-by-step guide on how to achieve replication between Oracle Database and Google BigQuery using OCI Goldengate

- [GoldenGate Data Streams - F1 Usecase](https://medium.com/@aporcescu/oracle-goldengate-data-streams-to-f1-telemetry-58532993e26a)
  - It is a step-by-step article about implementing Oracle GoldenGate Data Streams in a usecase of streaming F1 telemetry data into a web app
    

 


# Useful Links

- [OCI GoldenGate ZeroETL Mirror Pipelines](https://youtu.be/K-Qdxh4aII0?feature=shared)
    - Step-by-step Video of How to set up and use ZeroETL Mirror Pipelines in OCI GoldenGate
 
- [Install GoldenGate Microservices 21c in silent mode](https://medium.com/@eloi-lopes29/install-goldengate-microservices-21c-in-silent-mode-48a904b97dc3)
    - How to install GoldenGate in SilentMode
      
- [Migrating GoldenGate Marketplace (MySQL) to OCI GoldenGate for MySQL](https://blogs.oracle.com/dataintegration/post/migrating-goldengate-marketplace-mysql-to-oci-goldengate-for-mysql)
    - Step-by-step guide on how to move data from MySQL using OCI GoldenGate

- [Connecting GoldenGate Classic to GoldenGate Microservices and OCI GoldenGate](https://blogs.oracle.com/dataintegration/post/connecting-goldengate-classic-to-goldengate-microservices-and-oci-goldengate)
    - Blog article explaining how to connect GG Classic to OCI GoldenGate

- [Using Profiles with OCI GoldenGate](https://blogs.oracle.com/dataintegration/post/using-profiles-with-oci-goldengate)
    - Blog article explaining the process of how to control encryption in GoldenGate

- [GoldenGate monitoring and sending notifications](https://eloi-lopes29.medium.com/goldengate-monitoring-and-sending-notifications-1faead58c6bd)
    - Blog article explaining how to send notifications in a process fails

- [Configuring GoldenGate For SQL Server and loading data into Autonomous Database](https://eloi-lopes29.medium.com/configuring-goldengate-for-sql-server-and-load-data-into-autonomous-database-b8026d2d3e6f)
    - Blog article explaining how to send data from SQL Server into Autonomous Database using GoldenGate

- [Capture Kafka messages with Oracle Goldengate 21c](https://www.linkedin.com/pulse/capture-kafka-messages-oracle-goldengate-21c-juliana-a-gomes/)
    - Blog article explaining the process of capturing Kafka messages and loading them to Oracle DB in real-time

- [GoldenGate for Big Data — Replication to Oracle Object Storage](https://eloi-lopes29.medium.com/goldengate-for-big-data-replication-to-oracle-object-storage-7dfcd8d2bc63)
    - An article that explains the steps for loading data into Oracle Object Storage in real-time

- [OCI GoldenGate and VCN Peering](https://www.linkedin.com/pulse/oci-goldengate-vcn-peering-juliana-a-gomes/?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base_post_details%3Bq5ZGotyxQJq4RCBrHNn%2F0g%3D%3D)
    - An article that shows how to connect OCI GoldenGate instances that are in separate VCNs

- [OCI GoldenGate Capture data from Azure Event Hubs to Autonomous Database](https://www.youtube.com/watch?v=IEQrE7wZLXc)
    - Video that guides you through the steps of configuring replication between Azure Event Hubs and Oracle Autonomous Database using OCI GoldenGate

- [Access OCI GoldenGate Logs using OCI Logging](https://blogs.oracle.com/dataintegration/post/access-oci-goldengate-logs-using-oci-logging)
    - A blog article that explains the integration of OCI GoldenGate with OCI Logging

- [Configuring OCI GoldenGate with Data Guard-enabled databases](https://blogs.oracle.com/dataintegration/post/configuring-oci-goldengate-with-data-guard-enabled-databases)
    - This article intends to explain how to configure OCI GoldenGate connections to Data Guard and how to configure GoldenGate processes to adapt to switchover or failover changing roles

- [Configuring the GoldenGate Management Pack / Enterprise Manager with OCI GoldenGate](https://blogs.oracle.com/dataintegration/post/configuring-the-goldengate-management-pack-enterprise-manager-with-oci-goldengate)
    - Blog article explaining how to configure the GoldenGate Management Pack and Enterprise Manager

- [Clean up old OCI GoldenGate trails using Python and the OCI CLI](https://blogs.oracle.com/dataintegration/post/clean-up-old-oci-goldengate-trails-using-python-and-the-oci-cli)
    - Blog article explaining the process on how to clean OCI GoldenGate unused trail files from Oracle Cloud Infrastructure
 
- [Part-1/3: OCI PostgreSQL to OCI PostgreSQL cross-region replication with OCI GoldenGate — Introduction](https://medium.com/@devpiotrekk/oci-postgresql-to-oci-postgresql-cross-region-replication-with-oci-goldengate-introduction-e0492fc37b92)
  - This introductory post details how to establish cross-region connectivity between two OCI PostgreSQL databases using VCN peering and Dynamic Routing Gateways (DRGs) to prepare for replication with OCI GoldenGate. It covers network configuration, security lists, route tables, and DNS setup.

- [Part-2/3: OCI PostgreSQL to OCI PostgreSQL cross-region replication with OCI GoldenGate — OCI PostgreSQL](https://medium.com/@devpiotrekk/oci-postgresql-to-oci-postgresql-cross-region-replication-with-oci-goldengate-oci-postgresql-d4fcffc47498)
  - Part 2 guides you through creating primary and DR OCI PostgreSQL databases, configuring essential parameters (wal_level, max_replication_slots, etc.), establishing cross-region connectivity, and migrating the schema for cross-region replication using OCI GoldenGate. It also covers exporting and importing metadata

- [Part-3/3: OCI PostgreSQL to OCI PostgreSQL cross-region replication with OCI GoldenGate — OCI GoldenGate](https://medium.com/@devpiotrekk/oci-postgresql-to-oci-postgresql-cross-region-replication-with-oci-goldengate-oci-goldengate-4ccd5dea4d6c)
  - Part 3 guides you through setting up OCI GoldenGate for PostgreSQL to perform initial load and change data capture for cross-region replication. It covers creating deployments and connections, initial load extraction and replication, change data capture setup, monitoring, starting/stopping GoldenGate, and optimization techniques, concluding with best practices and considerations

- [Part 1/5: Get Started with OCI GoldenGate Data Transforms – Deployment Creation](https://blogs.oracle.com/dataintegration/post/get-started-with-oci-goldengate-data-transforms-deployment-creation)
  - This post guides you through creating a Data Transforms deployment in OCI GoldenGate, a new deployment type that adds batch ETL/ELT processing. It covers configuring deployment options, credentials, and enabling public access, preparing you to create Generic Connections and explore the service

- [Part 2/5: Get Started with OCI GoldenGate Data Transforms – Connectivity](https://blogs.oracle.com/dataintegration/post/get-started-with-oracle-cloud-infrastructure-oci-goldengate-data-transforms-connectivity)
  - This blog shows on how to configure connectivity within OCI GoldenGate Data Transforms, detailing how to connect to various data sources

- [Part 3/5: Get Started with OCI GoldenGate Data Transforms – Create a Data Load with Data Replication](https://blogs.oracle.com/dataintegration/post/get-started-with-oci-goldengate-data-transforms-create-a-data-load-with-data-replication)
  - Blog post guides you through creating a data load process using the data replication capabilities of OCI GoldenGate Data Transforms

- [Part 4/5: Get Started with OCI GoldenGate Data Transforms – Create a Data Flow](https://blogs.oracle.com/dataintegration/post/get-started-with-oci-goldengate-data-transforms-45-create-a-data-flow)
  - Create a data flow using OCI GoldenGate Data Transforms

- [Part 5/5: Get Started with OCI GoldenGate Data Transforms – Orchestrate and Run Processes](https://blogs.oracle.com/dataintegration/post/get-started-with-oci-goldengate-data-transforms-orchestrate-and-run-processes)
  - Orchestrate and run data transformation processes within OCI GoldenGate Data Transforms: schedule, and execute data flows for ETL/ELT workloads

- [GoldenGate 23ai is now available in OCI GoldenGate!](https://blogs.oracle.com/dataintegration/post/goldengate-23ai-is-now-available-in-oci-goldengate)
  - OCI GoldenGate now includes the 23ai release, bringing the latest features and enhancements

- [Oracle GoldenGate 23ai and Oracle Database 23ai Vectors](https://blogs.oracle.com/dataintegration/post/goldengate-database-23ai-vectors)
  - Oracle GoldenGate 23ai provides real-time, bi-directional replication of AI Vector Search in Oracle Database 23ai, enabling heterogeneous data integration and high availability across cloud data stores

- [OCI GoldenGate: Capture a topic data from Confluent Cloud to Autonomous Database](https://blogs.oracle.com/dataintegration/post/oci-goldengate-capture-a-topic-data-from-confluent-cloud-to-autonomous-database)
  - This Blog explains the details how to use OCI GoldenGate to capture data from a Confluent Cloud topic and replicate it to an Oracle Autonomous Database

- [Deriving Value from Data for Oracle Database@Azure Workloads with OCI GoldenGate](https://blogs.oracle.com/database/post/deriving-value-from-data-for-oracle-databaseazure-workloads-with-oci-goldengate)
  - OCI GoldenGate enables real-time data replication between Oracle Databases and Azure applications, supporting hybrid environments, data lakes, and real-time analytics

- [Announcing OCI GoldenGate ZeroETL Mirror - Putting the ZERO in ETL](https://blogs.oracle.com/dataintegration/post/announcing-oci-goldengate-and-zeroetl-putting-the-zero-in-etl)
  - New features and capabilities in OCI GoldenGate related to ZeroETL (Zero Extract, Transform, Load) concept

- [OCI GoldenGate Adds New Connectors for Databricks, Microsoft Fabric Lakehouse and Fabric Mirror, Snowflake, and Oracle Database@Azure, Google Cloud, and AWS](https://blogs.oracle.com/dataintegration/post/oci-goldengate-adds-new-connectors-for-databricks-microsoft-fabric-lakehouse-and-fabric-mirror-oracle-database-at-azure-google-cloud-and-aws)
  - OCI GoldenGate adds new connectors for Databricks, Microsoft Fabric Lakehouse and Fabric Mirror, and Oracle Database at Azure, Google Cloud, and AWS, expanding integration capabilities
 
- [OCI GoldenGate Real-Time Ingestion for Oracle Cloud Data Lakehouse](https://blogs.oracle.com/dataintegration/post/real-time-ingestion-for-oracle-cloud-data-lakehouse)
  - Learn how to use OCI GoldenGate for real-time data ingestion into Oracle Cloud Data Lakehouse, ensuring timely and accurate data availability for analytics and reporting.

- [OCI GoldenGate with Apache Kafka (Plain Text Authentication)](https://www.youtube.com/watch?v=cMwnT0Z60Tc)
  - This video demonstrates how to configure OCI GoldenGate to work with Apache Kafka using plain text authentication, providing a practical guide for setting up real-time data streaming.

- [Hands on with OCI GoldenGate for real-time data between two Autonomous Databases](https://www.youtube.com/watch?v=ESeukks3z70&t=10s)
  - Follow this hands-on tutorial to implement real-time data replication between two Oracle Autonomous Databases using OCI GoldenGate, ideal for maintaining synchronized environments.

- [Using Oracle Cloud Infrastructure GoldenGate with MySQL Databases](https://blogs.oracle.com/dataintegration/post/introducing-oracle-cloud-infrastructure-oci-goldengate-for-mysql)
  - Discover how to utilize OCI GoldenGate with MySQL databases for seamless data integration, offering efficient data replication and synchronization solutions.

- [OCI GoldenGate Real-Time Ingestion for Azure Data Lake Storage](https://blogs.oracle.com/dataintegration/post/ocigg-adls)
  - Explore real-time data ingestion into Azure Data Lake Storage using OCI GoldenGate, facilitating efficient data transfer and integration for Azure-based data lakes.

- [Replicate data from Amazon RDS for Oracle to Oracle Cloud Infrastructure (OCI) Object Storage using OCI GoldenGate](https://blogs.oracle.com/dataintegration/post/replicate-data-from-amazon-rds-for-oracle-to-oracle-cloud-infrastructure-oci-object-storage-using-oci-goldengate)
  - This article details how to replicate data from Amazon RDS for Oracle to OCI Object Storage with OCI GoldenGate, enabling cross-cloud data replication for backup and recovery.

- [Using Oracle Cloud Infrastructure (OCI) GoldenGate with PostgreSQL Databases](https://blogs.oracle.com/dataintegration/post/using-oracle-cloud-infrastructure-oci-goldengate-with-postgresql-databases)
  - Learn to integrate OCI GoldenGate with PostgreSQL databases, providing real-time data replication and integration capabilities for enhanced data management.

- [OCI GoldenGate Parquet format replication to OCI Object Storage](https://blogs.oracle.com/dataintegration/post/-parquet-ocios)
  - This blog post explains how to use OCI GoldenGate to replicate data in Parquet format to OCI Object Storage, optimizing data storage and retrieval for big data applications.

- [OCI GoldenGate — Collecting Diagnostics](https://medium.com/@jd.io/oci-goldengate-collecting-diagnostics-4135b4b3fb87)
  - This article provides a guide on collecting diagnostics for OCI GoldenGate, helping users troubleshoot and maintain their OCI GoldenGate deployments effectively.

- [Performance Considerations for Oracle Cloud Infrastructure GoldenGate -Data/ Delta Lakes](https://blogs.oracle.com/dataintegration/post/performance-considerations-for-oracle-cloud-infrastructure-goldengate)
  - This article discusses performance considerations for using OCI GoldenGate with Data/Delta Lakes, providing recommendations for optimal configuration settings to ensure efficient real-time data ingestion.

- [Seamlessly migrate an on-premise PostgreSQL database to OCI Database with PostgreSQL using OCI GoldenGate](https://blogs.oracle.com/dataintegration/post/seamlessly-migrate-an-onpremise-postgresql-database-to-oci-database-with-postgresql-online-with-oci-goldengate)
  - This blog post details how to seamlessly migrate an on-premise PostgreSQL database to OCI Database with PostgreSQL using OCI GoldenGate, enabling online migration with minimal downtime.

- [OCI GoldenGate Network](https://adrianotanaka.com.br/index.php/2024/03/14/network-for-oci-goldengate/)
  - A blog that explains the network configurations for OCI GoldenGate.

- [Oracle GoldenGate 21c Migration Utility](https://www.linkedin.com/pulse/oracle-goldengate-21c-migration-utility-juliana-a-gomes/)
  - An article about the Oracle GoldenGate 21c Migration Utility.

- [Using OCI GoldenGate for Multi-Region Data Replication Between Oracle Databases with Virtual Cloud Network (VCN) Peering](https://blogs.oracle.com/dataintegration/post/using-oci-goldengate-for-multi-region-data-replication-between-oracle-databases-with-virtual-cloud-network-vcn-peering)
  - This article explains how to use OCI GoldenGate for multi-region data replication between Oracle Databases using Virtual Cloud Network (VCN) Peering, ensuring high availability and disaster recovery.

- [ZeroETL Mirror Pipelines are now generally available in OCI GoldenGate!](https://docs.oracle.com/en/cloud/paas/goldengate-service/jppjs/)
   - Here is the quickstart and blog for ZeroETL Mirror Pipelines. 
  [Quickstart](https://docs.oracle.com/en/cloud/paas/goldengate-service/gzetl/) [and] 
  [Blog](https://blogs.oracle.com/dataintegration/post/oci-goldengate-zeroetl-mirror-pipelines-now-available)



# Workshops

- [Replicate Data Using Oracle Cloud Infrastructure GoldenGate](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=797&clear=RR,180&session=112005114665181)
    - Oracle GoldenGate, the industry-leading data replication and integration software, is now available as a fully-managed, cloud native service on Oracle Cloud Infrastructure. This workshop guides you through how to instantiate a target database using Oracle Data Pump and replicate data using Oracle Cloud Infrastructure GoldenGate.
 
- [Send Data from OCI GoldenGate to Oracle GoldenGate](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=881&clear=RR,180&session=131078747755230)
    - This workshop will guide you on how to start replicating data from OCI Goldengate to Oracle Goldengate on-prem.
 
- [Set up bidirectional replication in Oracle Cloud Infrastructure GoldenGate](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3503)
    - This workshop will help you to set a bi-directional replication using OCI GoldenGate

- [Replicate data from MySQL to Autonomous Database using Oracle Cloud Infrastructure GoldenGate](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3485)
    - This workshop will guide on on setting up replication between MySQL and Autonomous Database in Oracle using OCI GoldenGate
 
- [Real Time Data Streaming into OCI Object Storage with OCI GoldenGate](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3410)
    - LiveLab that will guide you through the steps of replicating data from a database to flat files in OCI Object Storage
      



# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
