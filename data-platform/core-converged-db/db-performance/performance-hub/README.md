# Performance Hub

This folder provides SQL scripts to generate active Performance Hub reports. The Oracle-provided script perfhubrpt.sql and the PL/SQL package DBMS_PERF especially REPORT_PERFHUB will be used.

Information on the script usage can also be found in the blog posting [Performance Hub - the database tuning gem](https://blogs.oracle.com/coretec/post/oracle-performance-hub).

Please refer to the [DBMS_PERF documentation](https://docs.oracle.com/en/database/oracle/oracle-database/21/arpls/DBMS_PERF.html#GUID-85CD8AB9-B6E0-444F-91A5-762EB92A74E9) to get detailed information on the parameters that can be used.

Before you start make sure that the user has DBA privileges.

# When to use this asset?

To present or to learn about Performance Hub.

# How to use this asset?

-  perfhubscript.sql: Use the Oracle provided script perfhubrpt.sql
-  dbmsperf_def.sql: Example for DBMS_PERF.REPORT_PERFHUB with default settings
-  dbmsperf_1.sql: Example for DBMS_PERF.REPORT_PERFHUB with parameters


# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
