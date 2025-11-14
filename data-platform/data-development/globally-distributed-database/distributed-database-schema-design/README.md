# Globally Distributed Database Schema Design 

## Data Distribution Schema Design - Creating Sharded Tables

Sharded tables can be created in the following distribution methods:

- <b>System-Managed Data Distribution</b>: data is automatically distributed across the shards using partitioning by consistent hash;

- <b>User-Defined Data Distribution</b>: User explicitly maps data to individual shards. A sharded table in a user-defined distributed database can be partitioned by range or list and no tablespace sets are created;

- <b>Composite Data Distribution</b>: is a combining of the two previous methods. Composite data distribution method allows you to partition subsets of data that correspond to a range or list of key values in a table partitioned by consistent hash.



Reviewed: 2.10.2025


# Table of Contents
 
1. [Useful Links](#useful-links)


# Useful Links

- [Globally Distributed Database Schema Design](https://docs.oracle.com/en/database/oracle/oracle-database/23/shard/schema-design1.html)


# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
