# Database Advisors

Oracle provides a series of advisors to analyze the database in different fields, e.g. to examine appropriate access structures, to decide on security configurations, segment compression and so on. They provide the basis for automations within the Oracle Database and support DBAs and database developers when working with the Oracle Database.
Advisors are distinguished by certain characteristics and are usually available through different methods: Graphical tools such as Oracle Enterprise Manager Cloud Control or SQL Developer, scripts through PL/SQL packages, initialization parameters or through corresponding v$ views. Most of them are available without additional installation and can be used immediately. Others can be loaded separately from My Oracle Support (MOS) or can be activated and used via Cloud Console. Unlike alerts, advisors are more resource intensive, as their analysis and suggested solutions have a greater level of detail. It is important to know how to use advisors and what advice to expect.
As the database and database offering evolves, new advisors and automations are continually made available.
 

## Useful Links

### Documentation

- [Automatic Database Diagnostic Advisor(ADDM)](https://docs.oracle.com/en/database/oracle/oracle-database/21/tgdba/automatic-performance-diagnostics.html#GUID-843A596D-2D8B-422D-9C8D-73C0EF52739D)
- [Autonomous Health Framework(AHF)](https://www.oracle.com/de/database/technologies/rac/ahf.html)
- [Automatic Indexing](https://docs.oracle.com/en/database/oracle/oracle-database/21/admin/managing-indexes.html#GUID-D1285CD5-95C0-4E74-8F26-A02018EA7999)
- [Automatic SQL Plan Management](https://docs.oracle.com/en/database/oracle/oracle-database/21/tgsql/managing-sql-plan-baselines.html#GUID-A94CFA49-910A-4237-A7BB-39BFA94E227E)
- [AutoUpgrade](https://docs.oracle.com/en/database/oracle/oracle-database/19/upgrd/about-oracle-database-autoupgrade.html#GUID-3FCFB2A6-4617-4783-828A-41BD635FC88C)
- [Cloud Premigration Advisor Tool(CPAT)](https://blogs.oracle.com/dataintegration/post/introducing-interactive-cloud-premigration-advisor-cpat-as-part-of-the-oracle-cloud-infrastructure-database-migration-dms-spring-2022-update)
- [Compression Advisor](https://docs.oracle.com/en/database/oracle/oracle-database/21/arpls/DBMS_COMPRESSION.html#GUID-9F37CAD6-C72C-407C-AFEE-CB5FD1129627)
- [Data Recovery Advisor](https://docs.oracle.com/en/database/oracle/oracle-database/21/bradv/diagnosing-repairing-failures-dra.html#GUID-8C219B50-1F7F-4F7A-95EE-5F029AE7EB2A)
- [Oracle Database Security Assessment Tool (DBSAT)](https://www.oracle.com/de/database/technologies/security/dbsat.html)
- [Oracle Data Safe](https://docs.oracle.com/en/cloud/paas/data-safe/index.html)
- [Database Replay](https://docs.oracle.com/en/database/oracle/oracle-database/21/ratug/database-replay.html#GUID-C5CAF3E6-0F1C-4BD6-BC03-F71744AD600E)
- [Memory Advisor](https://docs.oracle.com/en/database/oracle/oracle-database/21/tgdba/tuning-database-buffer-cache.html#GUID-76C5DB98-5140-469E-B23D-777EAA8564C1)
- [Oracle Database In-Memory Advisor](https://www.oracle.com/a/otn/docs/database/inmemory-advisor-tech-brief.pdf)
- [MTTR Advisor (Instance Recovery)](https://docs.oracle.com/en/database/oracle/oracle-database/19/tgdba/instance-tuning-using-performance-views.html#GUID-75455F43-DE5E-456C-BBC7-A28A782EE9D9)
- [Performance Hub](https://docs.oracle.com/en/database/oracle/oracle-database/19/admqs/monitoring-and-tuning-the-database.html#GUID-573F73E4-EF1C-46F2-9BAB-73DA08E7D364)
- [PL/SQL Hierarchical Profiler](https://docs.oracle.com/en/database/oracle/oracle-database/21/adfns/hierarchical-profiler.html#GUID-B2E3A739-08C6-4648-A65F-1D093A0DADDE)
- [Real-Time SQL Monitoring](https://www.oracle.com/a/ocom/docs/database/sql-monitor-brief.pdf)
- [Segment Advisor](https://docs.oracle.com/en/database/oracle/oracle-database/21/admin/managing-space-for-schema-objects.html#GUID-79EF8EB6-AB05-4EB0-9C72-98240BB607A8)
- [SQL Access Advisor](https://docs.oracle.com/en/database/oracle/oracle-database/21/tgsql/sql-access-advisor.html#GUID-561EC9B4-0930-4915-B5E1-17F2C5ACD261)
- [SQL Performance Analyzer (SPA)](https://docs.oracle.com/en/database/oracle/oracle-database/21/ratug/sql-performance-analyzer.html#GUID-8CE976A3-FB73-45FF-9B18-A6AB3F158A95)
- [SQL Repair Advisor](https://docs.oracle.com/en/database/oracle/oracle-database/21/admin/diagnosing-and-resolving-problems.html#GUID-D280872D-C4BF-4175-A68D-1B000E8DE868)
- [SQL Tuning Advisor](https://docs.oracle.com/en/database/oracle/oracle-database/21/tgsql/sql-tuning-advisor.html#GUID-EF47CEF3-E31A-4A2A-8BCE-19DC5F06F458)
- [Statistics Advisor](https://docs.oracle.com/en/database/oracle/oracle-database/21/tgsql/optimizer-statistics-advisor.html#GUID-054F4B76-DD57-46EE-98EA-0FF04F49D1B3)
- [Undo Advisor](https://docs.oracle.com/en/database/oracle/oracle-database/21/admin/managing-undo.html#GUID-F7D30328-A0CC-4F81-BA54-0FCFC2095F8B)

### Team Publications

- [Oracle Database Advisors](https://blogs.oracle.com/coretec/post/oracle-database-advisors-overview)
- [Advanced Compression Advisor](https://blogs.oracle.com/coretec/post/advanced-compression-advisor)
- [When and How to use Oracle Database In-Memory Advisor](https://blogs.oracle.com/coretec/post/how-to-use-oracle-database-in-memory-advisor)
- [Running Oracle Database In-Memory Advisor Offline](https://blogs.oracle.com/coretec/post/running-oracle-database-in-memory-advisor-of-one-database-on-another)
- [PL/SQL Tuning with PL/SQL Hierarchical ProfilerPL/SQL Tuning with PL/SQL Hierarchical Profiler](https://blogs.oracle.com/coretec/post/plsql-tuning-with-plsql-hierarchical-profiler)
- [Testing with Oracle Database Replay](https://blogs.oracle.com/coretec/post/testing-with-oracle-database-replay)
- [Real Application Testing Demo](https://blogs.oracle.com/coretec/post/rat-demo)
- [Autonomous Database Replay](https://blogs.oracle.com/coretec/post/adb-database-replay)
- [Smooth transition to Autonomous Database using SPA](https://blogs.oracle.com/coretec/post/spa-in-autonomous-database)

### Blogs

- [Use Compression Advisor to Estimate Compression Ratios for Data, Indexes and LOBS](https://blogs.oracle.com/datawarehousing/post/oracle-autonomous-data-warehouse-access-parquet-files-in-object-stores)
- [New Oracle Data Safe Reference Architectures to Quickly Secure Your Databases](https://blogs.oracle.com/cloudsecurity/post/oracle-data-safe-architectures-to-quickly-secure-your-databases)
- [Metrics and Performance Hub for ExaCS and DBCS](https://blogs.oracle.com/database/post/metrics-and-performance-hub-for-exacs-and-dbcs)
- [The performance report you are NOT using](https://connor-mcdonald.com/2021/04/30/the-performance-report-you-are-not-using/)

### LiveLabs Workshops

- [Automatic Indexing for Oracle Autonomous Database](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3328&clear=RR,180&session=113580025120480)
- [How do I see the current table compression ratio?](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/run-workshop?p210_wid=1019&session=113580025120480)
- [Get Started with Oracle Data Safe Fundamentals](https://apexapps.oracle.com/pls/apex/dbpm/r/livelabs/view-workshop?wid=598)
- [Real Application Testing : SQL Performance Analyzer-Database Replay](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=858&clear=RR,180&session=113580025120480)


### Video

- [Database In-Memory Advisor](https://www.youtube.com/watch?v=_qQIifPnMzA)
- [Performance Hub for Exadata Cloud Service and Database Cloud Service](https://www.youtube.com/watch?v=xj6kHFsOqFo)

# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See LICENSE for more details.
