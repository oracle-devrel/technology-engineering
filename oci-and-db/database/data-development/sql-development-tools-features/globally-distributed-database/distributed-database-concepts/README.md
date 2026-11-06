# Globally Distributed Database Concepts
A distributed database is a collection of <b>shards</b>. It is seen as a <b>single logical Oracle Database</b> that is horizontally partitioned across a pool of physical Oracle Databases (shards) that share no hardware or software.

A <b>shard catalog</b> is a specific Oracle Database that supports automated shard deployment, centralized management of a distributed database, and multi-shard queries.

<b>Shard directors</b> are network listeners that enable high performance connection routing based on a sharding key.

A <b>global service</b> is a database service that is use to access data in an Oracle Globally Distributed AI Database.

 <b>GDSCTL</b> command-line utility is used to configure, deploy, monitor, and manage an Oracle Globally Distributed AI Database

Reviewed: 27.10.2026

# Useful Links

- [Globally Distributed Database Architecture and Components](https://docs.oracle.com/en/database/oracle/oracle-database/26/shard/architecture-components.html#GUID-3D41F762-BE04-486D-8018-C7A210D809F9)
- [Using GDSCTL for Oracle Globally Distributed AI Database](https://docs.oracle.com/en/database/oracle/oracle-database/26/shard/using-gdstl-oracle-sharding.html)

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
