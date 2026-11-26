# Oracle True Cache

<b>Oracle True Cache</b> is an in-memory, consistent, and automatically managed SQL and key-value (object or JSON) read-only cache in front of an Oracle AI Database.

Like Oracle Active Data Guard, True Cache is a fully functional, read-only replica of the primary database, except that it's mostly disk-less.

Modern applications often require a high number of connections and fast, low-latency access to the data. A popular approach is to place caches in front of the database because applications typically perform many more reads than updates, and they can read from the cache without affecting the database performance (business scenarios like airline reservation system).

Compared to conventional caches, True Cache automatically keeps the most frequently accessed data in the cache, and it keeps the cache consistent with the primary database, other objects in the same cache, and other caches. It caches all Oracle AI Database objects and data types, including JSON.

Oracle True Cache provides several business benefits related to application development and performance:

- Improves scalability and performance by offloading queries from the primary database.
- Reduces application response time and network latency by deploying True Cache closer to the application.
- Creates a large, in-memory storage area by dividing data across multiple True Caches making the total size of the cached data much
  larger than it would be for a single primary database or cache.
- Automatically maintains the cache contents.
- It's transparent to the applications

Oracle True Cache is available starting from Oracle AI Database 26ai release (not supported in 19c).

<b>How True Cache works</b>

Here a high-level description of how an Oracle True Cache workflow activity:

- A given application decides whether to query data from Primary Database or from True Cache depending on the [Application Usage Models](https://docs.oracle.com/en/database/oracle/oracle-database/26/odbtc/overview-oracle-true-cache.html#GUID-516B11EB-A48F-4682-A203-B80BED778CC7) in use;
- Queries to True Cache returns data that is cached in its memory. When the data isn’t in the cache, True Cache fetches the data from the primary database (Cache miss);
- When True Cache starts (ie: instance, flush buffer cache, etc) it is empty: it needs to read large chunks of data to populate the cache. Once a block is cached, it’s updated automatically through redo apply from the primary database, similarly to the update mechanism used in Oracle Active Data Guard;
- Data queried from True Cache are always consistent, hence returning committed data only;
- As in general Caching solutions, True Cache data might not be the most current data as it exists in the primary database;
- When multiple True Cache exist and serve same database service, automatic session distribution load balancing , by the listener, is performed to each cache ([Uniform Configuration](https://docs.oracle.com/en/database/oracle/oracle-database/26/tciad/tc_genarch.html)).  

<i><b>Note</i></b>: If an object is pinned as KEEP in the proper buffer pool each time new data is inserted into the object on the primary database, that new data is automatically propagated to the KEEP buffer pool on True Cache via redo apply mechanism.  

<b>Why Choose Oracle True Cache?</b>

Caching data in the app tier is an essential aspect for developers as it aims to ligthen the load in databases speeding up query responses. 
However existing conventional cache solutions in the market with more complex management to handle data caching, caching eviction policies, failures and data formatting. 

Oracle True Cache is designed to address the pressing needs of global enterprises for unparalleled performance and scalability. This solution simplifies caching against Oracle Database as it deploys a diskless True Cache instance and leave the rest to Oracle.
Oracle True Cache is ideal for a wide range of application scenarios across various industries:
- e-commerce platforms;
- Real-Time Analytics;
- Online Gaming Environments;
- Trading and more..

Oracle True Cache can be deployed in various scenarios like Mid-Tier Cache, Edge-Cache, Cross-Region to Cross-Cloud (Multicloud) Cache. 
This means that <b>Oracle True Cache is specifically designed to decouple read proximity from the physical location of the primary database</b>. 
It can be safely deployed wherever your application tiers live: whether it is an edge computing node, a remote geographic region, or across distinct cloud providers (multicloud: this proximity allows applications to service read requests locally, bypassing high-latency WAN or cross-cloud network hops while significantly offloading the primary database. 


Reviewed: 02.11.2026

# Useful Links

- [Oracle True Cache](https://www.oracle.com/database/truecache/)
- [Oracle True Cache Technical Architectures](https://docs.oracle.com/en/database/oracle/oracle-database/26/tciad/tc_genarch.html)
- [True Cache AI World 2025](https://www.oracle.com/database/truecache/)
- [True Cache - Learn about cache warmup - Oracle Blogs](https://blogs.oracle.com/database/oracle-true-cache-learn-about-cache-warmup)
- [Blog - Accelerate Your Application Performance with Oracle True Cache](https://blogs.oracle.com/database/accelerate-your-application-performance-with-oracle-true-cache)
- [Blog - True Cache and Active Data Guard Transparent JDBC Redirection](https://blogs.oracle.com/maa/true-cache-and-active-data-guard-jdbc-redirection)
- [LiveLabs-Improve application performance with True Cache](https://livelabs.oracle.com/ords/r/dbpm/livelabs/view-workshop?wid=3933&clear=RR%2C180&session=103853267931988)
- [YouTube - Application Acceleration with Oracle True Cache: Oracle DatabaseWorld 2025](https://www.youtube.com/watch?v=akCz6tskFLU)

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
