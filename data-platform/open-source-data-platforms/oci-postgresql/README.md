# OCI PostgreSQL 

Reviewed: 11.11.2025

OCI Database with PostgreSQL is a fully managed PostgreSQL-compatible service with intelligent sizing, tuning, and high durability.

The service automatically scales storage as database tables are created and dropped, making management easier on you and optimizing storage spend. 
Data is encrypted both in transit and at rest. 

OCI Database with PostgreSQL is designed for high availability by offering durability even in the event of an availability domain (AD) failure.

# Table of Contents

1. [Team Publications](#team-publications) 
2. [Useful Links](#useful-links)
3. [Reusable Assets](#reusable-assets)

# Team Publications
- [Automate Cold Disaster Recovery for OCI Database with PostgreSQL using OCI Full Stack Disaster Recovery
](https://docs.oracle.com/en/learn/full-stack-dr-pgsql-cold-dr/#introduction)
- [Migrate to OCI PostgreSQL Database with OCI GoldenGate](https://blogs.oracle.com/dataintegration/post/seamlessly-migrate-an-onpremise-postgresql-database-to-oci-database-with-postgresql-online-with-oci-goldengate)
- [OCI PostgreSQL to OCI PostgreSQL cross-region replication with OCI GoldenGate — Part 1](https://medium.com/@devpiotrekk/oci-postgresql-to-oci-postgresql-cross-region-replication-with-oci-goldengate-introduction-e0492fc37b92)
- [OCI PostgreSQL to OCI PostgreSQL cross-region replication with OCI GoldenGate — Part 2](https://medium.com/@devpiotrekk/oci-postgresql-to-oci-postgresql-cross-region-replication-with-oci-goldengate-oci-postgresql-d4fcffc47498)
- [OCI PostgreSQL to OCI PostgreSQL cross-region replication with OCI GoldenGate — Part 3](https://medium.com/@devpiotrekk/oci-postgresql-to-oci-postgresql-cross-region-replication-with-oci-goldengate-oci-goldengate-4ccd5dea4d6c)
- [OCI PostgreSQL replication with pglogical](https://medium.com/@devpiotrekk/replicating-oci-database-with-postgresql-using-pglogical-118182ff08f9)
- [OCI PostgreSQL vector search with pgvector - Part 1](https://medium.com/@devpiotrekk/vector-search-with-pgvector-and-oci-database-with-postgresql-part-1-0915e5296148)
- [Benchmarking OCI Database with PostgreSQL](https://medium.com/@andreumdorokhinum/benchmarking-oci-database-with-postgresql-0a665e575fde)
- [Migrate PostgreSQL to OCI PostgreSQL using OCI Object Storage and Rclone](https://medium.com/@sylwekdec/migrate-postgresql-to-oci-postgresql-using-oci-object-storage-and-rclone-a61ef97c5b96)

# Useful Links

- [OCI PostgreSQL Documentation](https://docs.oracle.com/en-us/iaas/Content/postgresql/home.htm)
- [OCI PostgreSQL launch blog](https://blogs.oracle.com/cloud-infrastructure/post/oci-database-postgres)
- [OCI PostgreSQL features](https://blogs.oracle.com/cloud-infrastructure/post/first-principles-optimizing-postgresql-for-the-cloud)
- [Terraform to deploy OCI PostgreSQL database](https://blogs.oracle.com/cloud-infrastructure/post/deploy-managed-oci-database-with-postgresql-service-with-terraform)
- [Backup and Restore an OCI Database with PostgreSQL](https://docs.oracle.com/en/learn/backup-and-restore-db-with-postgresql/index.html#introduction)

# Reusable Assets

- [Create a connection between OCI PostgreSQL and Oracle Analytics Cloud](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/open-source-data-platforms/oci-postgresql/code-examples/connect-to-oac)
When you are looking to establish an OCI PostgreSQL instance, connect to it, and connect to Oracle Analytics Cloud, use these steps to guide you. The steps include using DBeaver to create a new table and load data, create an OCI PostgreSQL instance, connect to it, and connect the instance as source to Oracle Analytics Cloud.
- [Send notifications based on pg_stat_activity in OCI PostgreSQL](https://github.com/andreumdorokhinum/oci_pg_stat_activity)
- [GitLab & Standalone Managed PostgreSQL on OCI](https://github.com/andreumdorokhinum/oci_pg_with_gitlab)
- [Use CRON as scheduler for OCI PostgreSQL](https://github.com/andreumdorokhinum/oci_pg_with_unix_cron)
- [Integrate Geoserver and PostGIS using OCI Database with PostgreSQL](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/open-source-data-platforms/oci-postgresql/code-examples/postgis-geoserver)
- [Set up PgBouncer for Connection Pooling with OCI Database with PostgreSQL](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/open-source-data-platforms/oci-postgresql/code-examples/pgbouncer-setup)

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
