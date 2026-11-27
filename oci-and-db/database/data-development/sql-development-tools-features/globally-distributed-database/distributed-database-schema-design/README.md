# Globally Distributed Database Schema Design - Data Distribution and Creating Sharded Tables

Sharded tables can be created in the following distribution methods:

- <b>System-Managed Data Distribution</b>: data is automatically distributed across the shards using partitioning by consistent hash;

- <b>User-Defined Data Distribution</b>: User explicitly maps data to individual shards. A sharded table in a user-defined distributed database can be partitioned by range or list and no table space sets are created;

- <b>Composite Data Distribution</b>: is a combining of the two previous methods. Composite data distribution method allows you to partition subsets of data that correspond to a range or list of key values in a table partitioned by consistent hash.

## Data Distribution Method 
System-Managed Data Distribution does not require the user to specify mapping of data to shards as data is automatically mapped across shards using <b><i>Partitioning by Consistent</i></b> Hash method. The data is randomly and evenly distributed, via a partitioning algorithm, across shards. 

Note that Consistent hash is a partitioning strategy commonly used in scalable distributed systems. It is different from traditional hash partitioning.

The implementation of consistent hashing used in Oracle Globally Distributed AI Database avoids reshuffle limitations of traditional hash partitioning: it divides the possible range of values of the hash function (for example. from 0 to 2^32) into a set of N adjacent intervals, and assigning each interval to a <i>chunk</i>.

In the event of resharding, when shards are added to or removed from a distributed database, some of the chunks are relocated among the shards to maintain an even distribution of chunks across the shards, and the  contents of the chunks do not change during this process.

The number of chunks in a distributed database with system-managed data distribution can be specified when the shard catalog is created (default: 120 chunks per shard).

User-Defined Data Distribution let the user explicitly specify the mapping of data to individual shards. Due to performance, regulatory, or other reasons:
- Data would need to be stored on a particular shard;
- Administrator needs to have full control over moving data between shards.

## User-Defined Data Distribution Method
This method lets the user to explicitly specify the mapping of data to individual shards. Scenarios in which this kind of distribution method is can be appropriate:

- <b>Performance</b> reasons: specific business data on specific shards with highly-access rate);
- <b>Regulatory</b> reasons: certain data need to be retained in a specific country (in which the shard database containing them is created);
- <b>Management</b> reasons: Administrators need to  have full control over moving data between shards. 

Other advantages and disadvantages of adopting this method :
- In case of a shard planned/unplanned outage, administrators and users know perfectly which data are not available;
- Database administrators activity "burned" in monitoring and managing balancing data and workload distribution across shards.  

With user-defined data distribution, a sharded table can be partitioned by <b>range</b> or <b>list</b>. The CREATE TABLE syntax for a sharded table is not very different from the syntax for a regular table, except for the requirement that each partition should be stored in a separate tablespace.

In this data distribution method the concept of <b>Shardspace</b> is defined: 
- A set of shards that store data corresponding to a range or list of key values;
- a shardspace consists of a shard or a set of fully replicated shards

Note: User-defined data distribution does not support Raft replication: Data Guard/Active DataGuard is supported.

## Composite Data Distribution
System-managed data distribution uses partitioning by consistent hash to randomly distribute data across shards. This provides better load balancing compared to user-defined distribution that uses partitioning by range or list. However, system-managed distribution does not give the user any control on assignment of data to shards.

Composite distribution is a combination of user-defined and system-managed distribution which, when required, provides benefits of both methods.
With composite distribution, you to use two levels of partitioning: first the data is <b>partitioned by range or list</b> and then it is partitioned further by <b>consistent hash</b>.

The two levels of distribution make it possible to automatically <u>maintain balanced distribution of data across shards</u> in each shardspace, and, at the same time, <u>partition data across shardspaces</u>.

Globally Distributed AI Database is based on table partitioning: all of the subpartitioning methods provided by Oracle Database are also supported by Oracle Globally Distributed AI Database.


## Directory-Based Data Distribution
This data distribution method comes advantageous in the following scenarios:
- System-managed data distribution results in <b>uneven data distribution</b>: the number of distinct key values are not large enough (B2B application scenarios managing data for a large number of business customer accounts and Dealers application managing data for many dealers resulting in uneven distribution of data with hashing);
- Grouping certain key values together into the <b>same location or chunk</b>: useful when needed to group certain key values together into the same location or chunk for affinity purposes;
- Implement <b>custom policy-based</b> data distribution round-robin, random, least data and others.

Directory-Based Data Distribution can be considered as an <b>enhancement of the user-defined method</b>, whereby the location of data records associated with any sharding key is specified dynamically at runtime based on user preferences. 

Main properties:
- Mapping of key values to partitions and shards is stored in a <b>directory table</b>;
- Directory table is <b>automatically created</b> in the shard catalog and shards when a table sharded by directory is created;
- Shard director (GSM) and client-side connection pools cache the directory for routing purposes.
- The directory is <b>automatically updated</b> when rows are inserted into or deleted from the sharded table for inserts with an auto-assignment rule enabled (Deletes do not auto-delete the mapping in the directory).
- A <b>virtual column</b> with partitioning information is included in a directory-sharded table, utilized for <b>partition pruning</b> purposes.

Reviewed: 27.10.2026

# Useful Links

- [Globally Distributed Database Schema Design](https://docs.oracle.com/en/database/oracle/oracle-database/23/shard/schema-design1.html)

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
