# SQL Performance

There are several products, tools, features, and utilities you may use when it comes to Oracle database SQL performance tuning. Graphical tools such as Oracle Enterprise Manager Cloud Control or 
SQL Developer can be helpful to monitor and tune SQL statement performance but SQL scripts can also be used to achieve the same goals. 
The following frameworks and advisors can be useful when you have to deal with SQL performance tasks:  

- SQL Tuning Sets (STS), can list and store the relevant statements for (recurring) tuning tasks. The according information about execution performance can easily be displayed. You can also use 
existing AWR reports to build SQL Tuning Sets. It provides the basis for the SQL Tuning Advisor and SQL Access Advisor and delivers the foundation for SQL Performance Advisor (known as SPA). If you want to test on a remote system, SQL Tuning Sets can be copied to a remote database system using Datapump Export or Import in case you need to test on a remote system. 

- SQL Monitoring (also known as Real-Time Monitoring) - has become important when it comes to SQL performance monitoring or database monitoring. 
Quickly and without effort you get an up-to-date and fast overview of certain - mostly long-running - operations. In contrast to AWR or STATSPACK reports, SQL Monitoring also displays statements that are 
currently active or in a queue. Especially with new applications, new techniques or features, SQL monitoring is an important step in the testing process. 

- SQL Performance Analyzer (aka SPA) as part of real application testing focuses on detailed statement analysis of a defined SQL workload made available via a SQL Tuning Set (STS). 
The workload runs twice - once BEFORE the change and then AFTER a change. The resulting reports are a detailed comparative analysis (before and after the change) of the individual statements, 
measured by different metrics such as elapsed time, cpu_time, etc. Optionally, you can automate the tuning process using SQL Tuning Advisor or SQL Plan Baselines.
In this way, statements from a SQL workload can be tested and compared and tuned if necessary.

Review Date: 03.06.2024

## Useful Links

### Documentation

- [Oracle Database 19c Performance](https://docs.oracle.com/en/database/oracle/oracle-database/19/performance.html)
- [Oracle Database 23c Performance](https://docs.oracle.com/en/database/oracle/oracle-database/23/performance.html)
- [Testing Guide 19c](https://docs.oracle.com/en/database/oracle/oracle-database/19/ratug/index.html#Oracle%C2%AE-Database)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
