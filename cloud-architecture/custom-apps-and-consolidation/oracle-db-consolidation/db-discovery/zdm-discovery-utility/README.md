
# ZDM Discovery Utility

ZDM Discovery Utility for ORACLE Database is a SQL script-based utility that captures the necessary details of an Oracle On-Prem database in order to analyze the suitability of logical online migration using ZDM.
This utility runs on Oracle 11g onwards Non-Container database and helps in generating HTML reports with pre-check summaries with required action and other detailed descriptions.

## When to use this asset?

This script is to be executed in the discovery phase if it is identified the Oracle on-premises database is to be migrated using Zero Downtime Migration(ZDM) Tool.

## How to use this asset?

```
sqlplus "/ as sysdba"  @oradb_zdmgg_discovery_v1_2.sql
```

This script needs to execute on an Oracle database server with a user who has `"/as sysdba"` access.
-	Copy the oradb_zdmgg_discovery_v1_2.sql file to the server.
-	Execute the script as ```sqlplus "/ as sysdba" @oradb_zdmgg_discovery_v1_2.sql ``` .


The above script will generate a .htm output file on the same location.

## License
Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.


