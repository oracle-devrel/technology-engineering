# Oracle True Cache

<b>Oracle True Cache</b> is an in-memory, consistent, and automatically managed SQL and key-value (object or JSON) read-only cache in front of an Oracle AI Database.

Like Oracle Active Data Guard, True Cache is a fully functional, read-only replica of the primary database, except that it's mostly diskless.

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

Reviewed: 24.04.2026


# Table of Contents
 
1. [Team Publications](#team-publications)
2. [Useful Links](#useful-links)


# Team Publications
N/A

# Useful Links
- [Oracle True Cache](https://www.oracle.com/database/truecache/)
- [Documentation](https://docs.oracle.com/en/database/oracle/oracle-database/26/odbtc/index.html)
- [Oracle True Cache Users Guide](https://docs.oracle.com/en/database/oracle/oracle-database/26/odbtc/oracle-true-cache-users-guide.pdf)
- [Blog - Accelerate Your Application Performance with Oracle True Cache](https://blogs.oracle.com/database/accelerate-your-application-performance-with-oracle-true-cache)
- [Oracle True Cache Technical Architectures](https://docs.oracle.com/en/database/oracle/oracle-database/26/tciad/tc_genarch.html)
- [Blog - True Cache and Active Data Guard Transparent JDBC Redirection](https://blogs.oracle.com/maa/true-cache-and-active-data-guard-jdbc-redirection)
- [LiveLabs-Improve application performance with True Cache](https://livelabs.oracle.com/ords/r/dbpm/livelabs/view-workshop?wid=3933&clear=RR%2C180&session=103853267931988)
- [YouTube - Application Acceleration with Oracle True Cache: Oracle DatabaseWorld 2025](https://www.youtube.com/watch?v=akCz6tskFLU)

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
