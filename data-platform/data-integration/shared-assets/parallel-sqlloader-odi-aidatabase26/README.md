# Automatic Parallelism in SQL*Loader with Oracle Data Integrator and 26ai Database Client

Reviewed: 05.06.2026

Why move Teradata to Autonomous Data Warehouse on OCI?


SQL Loader is one of the most efficient ways to load large text files into Oracle Database. Starting with 26ai Oracle AI Database client releases it is possible to automate parallelism in SQL Loader jobs. Instead of manually splitting one large input file into multiple smaller files and running several SQL Loader jobs, SQL Loader can parallelize the load internally from one data file, one control file, and one command.

In Oracle Data Integrator, we can take advantage of this new capability by using a Knowledge Module and creating a basic mapping pointing to our source file and target table. ODI provides out of the box Knowledge Modules and LKM File to Oracle (SQLLDR) is commonly used when loading delimited or fixed-width files into Oracle tables, especially for high-volume loads where row-by-row JDBC loading is not ideal.

## How to use this asset?
This blog post explains steps to utilize automatic parallelism via a new custom Knowledge Module which can be downloaded from files subfolder.
[Link to full blog post in Medium](https://medium.com/@hncelebi/automatic-parallelism-in-sql-loader-with-oracle-data-integrator-and-26ai-database-client-ba4a9332a7b2)


# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
