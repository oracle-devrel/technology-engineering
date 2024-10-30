# Fast Ingest Lookup

The Memoptimized Rowstore enables high performance data streaming for applications, such as Internet of Things (IoT) applications, which typically stream small amounts of data in single-row inserts from a large number of clients simultaneously and also query data for clients at a very high frequency.

The Memoptimized Rowstore provides the following two functionality:

- Fast ingest optimizes the processing of high-frequency, single-row data inserts into a database. Fast ingest uses the large pool for buffering the inserts before writing them to disk, so as to improve data insert performance.


- Fast lookup enables fast retrieval of data from a database for high-frequency queries. Fast lookup uses a separate memory area in the SGA called the memoptimize pool for buffering the data queried from tables, so as to improve query performance.

Memoptimized Rowstore is available with Enterprise Edition (EE) 19.12 (onwards) On-Premises, in Oracle Base Database Service EE, in EE on Engineered Systems, and with the Oracle database 23ai FREE edition.

If you are interested in Database 23ai, [please see our page here](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/core-converged-db/database-23ai).


Reviewed Date: 29.08.2024

# Useful Links

## Documentation  
 
- [Database Performance Tuning Guide 19c](https://docs.oracle.com/en/database/oracle/oracle-database/19/tgdba/tuning-system-global-area.html#GUID-9752E93D-55A7-4584-B09B-9623B33B5CCF)
- [Database Performance Tuning Guide 23ai](https://docs.oracle.com/en/database/oracle/oracle-database/23/tgdba/tuning-system-global-area.html#GUID-9752E93D-55A7-4584-B09B-9623B33B5CCF)
- [Database Concepts 23ai](https://docs.oracle.com/en/database/oracle/oracle-database/23/cncpt/memory-architecture.html#GUID-D58DC90F-0ABB-4B1E-96C1-6094A04A5E12)
- [PL/SQL Packages and Types References 23ai](https://docs.oracle.com/en/database/oracle/oracle-database/23/arpls/DBMS_MEMOPTIMIZE.html#GUID-49F0E799-97F0-41E7-9CD3-24AE3CAA8105)
- [Database Licensing Information User Manual](https://docs.oracle.com/en/database/oracle/oracle-database/19/dblic/Licensing-Information.html#GUID-0F9EB85D-4610-4EDF-89C2-4916A0E7AC87)

## Blogs & Videos

- [Oracle Database 23ai Fast Ingest Enhancements](https://blogs.oracle.com/in-memory/post/oracle-database-23ai-fast-ingest-enhancements)
- [New in Oracle Database 19c: Memoptimized Rowstore – Fast Ingest](https://blogs.oracle.com/database/post/new-in-oracle-database-19c-memoptimized-rowstore-fast-ingest)
- [Best Practices For High Volume IoT workloads with Oracle Database 19c](https://www.oracle.com/a/tech/docs/wp-bp-for-iot-with-12c-042017-3679918.pdf)
  

# Team Publications

## Blogs

- [Fast Lookup with Memory Optimized Rowstore](https://blogs.oracle.com/coretec/post/fast-lookup-with-memoptimized-rowstore)

## Videos

- [High Performance Data Streaming with Fast Lookup and Fast Ingest](https://youtu.be/IMnbSRmFTVk)
  
# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
