# Real Application Testing
Real Application Testing comes in two flavors - Database Replay (DB Replay) and SQL Performance Analyzer (SPA). Both can be used independently of each other but are also a good complement. 
With SQL Performance Analyzer you can check the SQL performance. It focuses on detailed statement analysis of a defined SQL workload made available via a SQL Tuning Set (STS).
Statements from a SQL workload can be tested and compared and tuned if necessary.

Database Replay can be used to capture a real workload on the production system and replay it on a test system with the exact timing, concurrency, and transaction characteristics of the original workload. This enables you to test the effects of a system change without affecting the production system. 

Review Date: 03.06.2024
## Useful Links

### Documentation

- [Testing Guide 19c](https://docs.oracle.com/en/database/oracle/oracle-database/19/ratug/index.html#Oracle%C2%AE-Database)
- [PL/SQL Packages and Types Reference](https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/index.html#Oracle%C2%AE-Database)


### Team Publications

- [Testing with Oracle Database Replay](https://blogs.oracle.com/coretec/post/testing-with-oracle-database-replay)
- [Autonomous Database Replay](https://blogs.oracle.com/coretec/post/adb-database-replay)
- [Real Application Testing Database Replay Demo](https://blogs.oracle.com/coretec/post/rat-demo)
- [Smooth transition to Autonomous Database using SPA](https://blogs.oracle.com/coretec/post/spa-in-autonomous-database)
- [Oracle SQL Tuning Sets (STS) - The foundation for SQL Tuning](https://blogs.oracle.com/coretec/post/oracle-sql-tuning-sets-the-basis-for-sql-tuning)


### LiveLabs Workshops

- [Real Application Testing : SQL Performance Analyzer and Database Replay](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=858&clear=RR,180&session=112790027738609)



# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
