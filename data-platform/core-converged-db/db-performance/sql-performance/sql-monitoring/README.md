# Real-Time SQL Monitoring

Oracle provides a series of advisors to analyze the database in different fields, e.g. to examine appropriate access structures, to decide on security configurations, segment compression and so on. They provide the basis for automation within the Oracle Database and support DBAs and database developers when working with the Oracle Database.

Advisors are distinguished by certain characteristics and are usually available through different methods: Graphical tools such as Oracle Enterprise Manager Cloud Control or SQL Developer, scripts through PL/SQL packages, initialization parameters or corresponding v$ views. Most of them are available without additional installation and can be used immediately. Others can be loaded separately from My Oracle Support (MOS) or can be activated and used via Cloud Console. Unlike alerts, advisors are more resource-intensive, as their analysis and suggested solutions have a greater level of detail. It is important to know how to use advisors and what advice to expect.

As the database offering evolves, new advisors and automation are continually made available.
 
Reviewed: 02.04.2024

# When to use this asset?

To learn to use Real-Time SQL Monitoring functionality. 

# How to use this asset?

See the README file under the files folder.

# Useful Links

## Documentation

- [PL/SQL Packages and Types Reference DBMS_SQL_MONITOR](https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_SQL_MONITOR.html#GUID-13874A73-369E-42CD-9C43-A12F1B3BDEC6)
- [PL/SQL Packages and Types Reference DBMS_SQLTUNE](https://docs.oracle.com/en/database/oracle/oracle-database/23/arpls/DBMS_SQLTUNE.html#GUID-CFA1F851-1FC1-44D6-BB5C-76C3ADE1A483)
- [PL/SQL Packages and Types Reference DBMS_PERF](https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_PERF.html#GUID-290C18B9-A2EF-468D-9D6E-B31D717082BB)
- [Database Reference V$SQL_MONITOR](https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/V-SQL_MONITOR.html#GUID-79E97A84-9C27-4A5E-AC0D-C12CB3E748E6)

## Blogs and technical briefs

- [Getting the most out of Oracle SQL Monitor](https://sqlmaria.com/2017/08/01/getting-the-most-out-of-oracle-sql-monitor/)
- [Real-Time SQL Monitoring and Oracle Database In-Memory](https://www.oracle.com/a/ocom/docs/database/sql-monitor-brief.pdf)

# Team Publications

- [Real-Time SQL Monitoring: a MUST for SQL Tuning](https://blogs.oracle.com/coretec/post/oracle-database-real-time-sql-monitoring-one-of-the-most-important-tools)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
