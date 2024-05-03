# Scripts for Hybrid Partitioned Tables

As the name implies the partitions of hybrid partitioned tables can exist in both – inside the Oracle database in tablespaces and outside in external sources, such as Linux files, files on Hadoop Distributed File System (HDFS), and files in Cloud Object Storage. Hybrid Partitioned Tables enhance the functionality of partitioning for mixed Big Data scenarios where large portions of a table can reside in external partitions.

Reviewed: 27.03.2024

# When to use this asset?

To present the basic Hybrid Partitioned Tables functionality. 

# How to use this asset?

This folder provides a step-by-step instruction to create a hybrid partitioned table. The example uses the table EMPLOYEES from schema HR.  

- 1-create-partitioned-table.sql: create a partitioned table and add rows

- 2-add-external-attribute.sql: Use ALTER TABLE to add external partition attribute 

- 3-create-external-data.sql: Create an external (helper) table with ORACLE_DATAPUMP

- 4-add-external-partition-data.sql: Use EXCHANGE PARTITION to provide data for the external partition

- monitor-external-part-tables.sql: Use ALL_XTERNAL_TAB_PARTITIONS

- monitor-hybrid-tables.sql. Use ALL_TABLES with column hybrid

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
