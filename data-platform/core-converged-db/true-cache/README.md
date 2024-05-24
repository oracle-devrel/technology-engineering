# True Cache

Today, many Oracle users place a cache in front of the Oracle Database to speed up query response time and improve overall scalability. True Cache is a new way to have a cache in front of the Oracle Database. True Cache is an in-memory, consistent, and automatically managed cache for Oracle Database. It operates similarly to an Active Data Guard readers farm, except True Cache is mostly diskless and designed for performance and scalability, as opposed to disaster recovery. An application can connect to True Cache directly for read-only workloads. A general read-write Java application can also mark some sections of the code as read-only, and the 23ai JDBC Thin driver can automatically send read-only workloads to configured True Caches.
True Cache has many advantages including ease of use, consistent data, more recent data, and automatically managed cache.

True Cache is available with Oracle Database 23ai and later versions. It is not supported in earlier releases. True Cache is available in Oracle Database 23ai Free and Oracle Base Database Service Enterprise Edition (please read the limitations in the Licensing Guide).

Reviewed: 06.05.2024

# Useful Links

## Documentation  
 
- [True Cache on oracle.com](https://www.oracle.com/database/truecache/)
- [True Cache FAQ](https://www.oracle.com/database/truecache/faq/)
- [Oracle True Cache User's Guide](https://docs.oracle.com/en/database/oracle/oracle-database/23/odbtc/index.html)
- [Java Support for True Cache](https://docs.oracle.com/en/database/oracle/oracle-database/23/jjdbc/JDBC-getting-started.html#GUID-B4CFD064-76D7-4384-B4A9-6E8725968D9B)
- [Oracle True Cache Technical Architecture](https://docs.oracle.com/en/database/oracle/oracle-database/23/tciad/tc_genarch.html)
- [Database Licensing Information User Manual](https://docs.oracle.com/en/database/oracle/oracle-database/23/dblic/Licensing-Information.html#GUID-F796455D-C7EF-4836-9F69-2BCCDA49B7BD)

## Blogs

- [Introducing Oracle True Cache: In-memory, consistent, and automatically managed SQL cache (Oracle Database 23ai)](https://blogs.oracle.com/database/post/introducing-oracle-true-cache)
  
# Team Publications

- [Getting started with True Cache in Oracle Database 23ai FREE](https://blogs.oracle.com/coretec/post/true-cache-in-23ai-free)


# License

Copyright (c) 2024 Oracle and/or its affiliates.
