# OCI GoldenGate

Oracle Cloud Infrastructure GoldenGate is a fully managed, native cloud service that moves data in real-time, at scale. OCI GoldenGate processes data as it moves from one or more data management systems to target databases. You can also design, run, orchestrate, and monitor data replication tasks without having to allocate or manage any Compute environment.

Reviewed: 28.02.2025
 
# Useful Links
 
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

- [Sync data between DBCS and Google BigQuery using Stage and Merge](https://github.com/alexandruporcescu/Articles/blob/main/Sync%20OracleDB%20with%20Google%20BigQuery/Replicate%20data%20from%20Oracle%20DB%20to%20Google%20BigQuery%20using%20GoldenGate%20Stage%20and%20Merge%20handler.md)
    - GitHub articles that show a step-by-step guide on how to achieve replication between Oracle Database and Google BigQuery using OCI Goldengate

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




# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
