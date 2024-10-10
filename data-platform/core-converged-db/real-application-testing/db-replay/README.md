# Database Replay (DB Replay)

Database Replay can be used to capture a real workload on the production system and replay it on a test system with the exact timing, concurrency, and transaction characteristics of the original workload. This enables you to test the effects of a system change without affecting the production system. Database Replay supports workload capture on a system running Oracle Database 10g Release 2 and newer releases. Because the database workload capture is stored in a platform-independent format, you can capture a workload on one OS platform, e.g. Windows, and replay on a different one, e.g. Linux. Keep in mind it should be used only within the Oracle Database. Other external components like application server, middleware, or client software cannot be considered when testing with Real Application Testing. Either the graphical interface via Enterprise Manager Cloud Control or the command-line API can be used.  


Reviewed: 02.07.2024

# When to use this asset?

To learn about Database Replay using the command line API.  

# How to use this asset?

See the README in the files folder.

Please note: Database Replay for Autonomous Database (ADB) works differently. It can be used e.g. to replay a recorded (captured) workload from On-Premises or cloud installations in an Autonomous Database. 
For more details on the usage in ADB refer to the [documentation](https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/autonomous-real-application-testing.html#GUID-EB8F065E-5FBB-480D-BAF6-5A0446740073) or the posting [Autonomous Database Replay](https://blogs.oracle.com/coretec/post/adb-database-replay).
 
# Useful Links

## Documentation

- [Testing Guide](https://docs.oracle.com/en/database/oracle/oracle-database/19/ratug/database-replay.html#GUID-C5CAF3E6-0F1C-4BD6-BC03-F71744AD600E)
- [PL/SQL Packages and Types Reference - DBMS_WORKLOAD_CAPTURE](https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_WORKLOAD_CAPTURE.html#GUID-77C6507C-3DE6-4FB4-B180-530BEB840BE8)
- [PL/SQL Packages and Types Reference - DBMS_WORKLOAD_REPLAY](https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_WORKLOAD_REPLAY.html#GUID-FE03A123-2257-41FF-BA90-AD0114DC1A4F)
- [Database Replay monitor report (dbms_wrr_report) (Doc ID 2696765.1)](https://support.oracle.com/epmos/faces/SearchDocDisplay?_adf.ctrl-state=1dcdrnc7m4_53&_afrLoop=462946945372255)
- [Scripts to Debug Slow Replay (Doc ID 760402.1)](https://support.oracle.com/epmos/faces/DocumentDisplay?_afrLoop=462075676937267&id=760402.1&_adf.ctrl-state=1dcdrnc7m4_53)
- [Test Workloads with Oracle Real Application Testing - Autonomous Database](https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/autonomous-real-application-testing.html#GUID-EB8F065E-5FBB-480D-BAF6-5A0446740073)
- [PL/SQL Packages and Types Reference for Autonomous Database - DBMS_CLOUD_ADMIN](https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/dbms-cloud-admin.html#GUID-D76B229E-781E-45C0-9F14-CAF30F9E6E3B)


## LiveLabs

- [Real Application Testing: SQL Performance Analyzer and Database Replay](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=858&clear=RR,180&session=112790027738609)


# Team Publication

- [Testing with Oracle Database Replay](https://blogs.oracle.com/coretec/post/testing-with-oracle-database-replay)
- [Real Application Testing Database Replay Demo](https://blogs.oracle.com/coretec/post/rat-demo)
- [Autonomous Database Replay](https://blogs.oracle.com/coretec/post/adb-database-replay)


# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
