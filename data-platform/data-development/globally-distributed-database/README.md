# Globally Distributed Database (GDD)

A distributed database is a database scaling technique based on horizontal partitioning of data across multiple independent physical databases. Each physical database in such a configuration is called a shard. From the perspective of an application, a distributed database looks like a single database; the number of shards, and the distribution of data across those shards, are completely transparent to the application.

A sharded table is partitioned across all shards of the distributed database. Table partitions on each shard are not different from partitions that could be used in an Oracle database that is not sharded.

Key benefits of Oracle Globally Distributed Database:

- Linear Scalability : The Oracle Globally Distributed Database shared–nothing architecture eliminates performance bottlenecks and provides unlimited scalability (up to 1000 shards scaling support);

- Extreme Availability and Fault Isolation: The failure or slow-down of one shard does not affect the performance or availability of other shards. An unplanned outage or planned maintenance of a shard impacts only the availability of the data on that shard;

- Geographical Distribution of Data:  Globally Distributed Database enables you to deploy a global database, where a single logical db could be distributed over multiple geographies, making it possible to satisfy data privacy regulatory requirements (Data Sovreignity) as well as allows to store particular data close to its consumers (Data Proximity).

Globally Distributed Database has a flexible deployment model, embracing the Shared-Nothing architecture. Because the database shards do not share any resources, the shards can exist anywhere on a variety of on-premises and cloud systems.

You can choose to deploy all of the shards on-premises, have them all in the cloud, or you can split them up between cloud and on-premises systems to suit your needs.

Shards can be deployed on all database deployment models such as single instance, Exadata, and Oracle RAC.

Oracle Globally Distributed Database relies on replication for availability. Oracle Globally Distributed Database provides various means of replication depending on your needs:

- Shard-level Replication.

- Oracle Data Guard.

- Raft Replication.

Replication provides high availability, disaster recovery, and additional scalability for reads. A unit of replication can be a shard, a part of a shard, or a group of shards

Reviewed: 26.08.2025


# Table of Contents
 
1. [Useful Links](#useful-links)


# Useful Links

- [Globally Distributed Database in 23ai](https://docs.oracle.com/en/database/oracle/oracle-database/23/shard/changes-oracle-database-23ai.html#GUID-BDC14D70-C513-4EC3-B1A4-AA0616290800)


# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
