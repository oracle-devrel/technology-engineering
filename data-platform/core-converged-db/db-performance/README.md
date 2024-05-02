# Database Performance


Effective data collection and analysis are essential for identifying and correcting performance problems. Oracle Database provides several tools that allow a performance engineer to gather information regarding database performance. In addition to gathering data, the Oracle Database provides tools to monitor performance, diagnose problems, and tune applications. 

They are usually available through different methods: Graphical tools such as Oracle Enterprise Manager Cloud Control, SQL Developer, Oracle scripts, PL/SQL packages, initialization parameters or through corresponding v$ views. Most of them are available without additional installation and can be used immediately. Others can be loaded separately from My Oracle Support (MOS) or can be activated and used via Cloud Console. 

Examples are:
- Automatic Workload Repository (AWR) collects, processes, and maintains performance statistics for problem detection and self-tuning purposes. 
- Automatic Database Diagnostic Monitor (ADDM) analyzes the information collected by AWR for possible performance problems with the Oracle database. 
- SQL Tuning Advisor allows a quick and efficient technique for optimizing SQL statements without modifying any statements.
- SQL Access Advisor provides advice on materialized views, indexes, and materialized view logs.
- SQL Performance Analyzer as part of Real Application Testing assesses the impact of system changes on the response time of SQL statements. 
- Real-time SQL Monitoring gives an up-to-date overview of operations and displays statements that are currently active or in a queue.
- Explain Plan displays execution plans chosen by the optimizer.
- Special Performance pages (aka Performance Hub) in Cloud Control or OCI Console and associated reports deliver a consolidated view of all performance data for 
  and provide summary information not only on overall IO, CPU and Memory usage by the database but also detailed SQL monitoring information.

Review Date: 03.06.2024

# Useful Links

## Documentation

- [Oracle Database 19c Performance](https://docs.oracle.com/en/database/oracle/oracle-database/19/performance.html)
- [PL/SQL Packages and Types Reference DBMS_PERF](https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_PERF.html#GUID-290C18B9-A2EF-468D-9D6E-B31D717082BB)
- [Oracle Cloud Infrastructure Documentation - Performance Hub Report](https://docs.oracle.com/en-us/iaas/autonomous-database/doc/use-perf-hub-monitor-databases.html)

## Blogs and technical briefs
- [Monitoring Database Performance Using Performance Hub Report (Doc ID 2436566.1)](https://support.oracle.com/epmos/faces/SearchDocDisplay?_afrLoop=459842075147901&_afrWindowMode=0&_adf.ctrl-state=p9nyc4tf7_4)
- [The performance report you are NOT using](https://connor-mcdonald.com/2021/04/30/the-performance-report-you-are-not-using/)

# Team Publications

- [Performance Hub - the database tuning gem](https://blogs.oracle.com/coretec/post/oracle-performance-hub)
- [Real-time SQL Monitoring on GitHub](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/core-converged-db/sql-performance/sql-monitoring)
- [SQL Performance Analyzer on GitHub](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/core-converged-db/real-application-testing/sql-performance-analyzer)


# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
