
# ZDM Discovery Utility

ZDM Discovery Utility for ORACLE Database is a SQL script-based utility that captures necessary details of an oracle On-Prem database in order to analyze the suitability of logical online migration using ZDM.
This utility runs on Oracle 11g onwards Non Container database and helps in generating HTML report with pre-check summary with required action and other detailed description.

## When to use this asset?

This script is to be executed in the discovery phase if it is identified the oracle on-premises database is to be migrated using Zero Downtime Migration(ZDM) Tool.

## How to use this asset?

```
sqlplus "/ as sysdba"  @oradb_zdmgg_discovery_v1_2.sql
```

This script needs to execute on Oracle database server with a user who has `"/as sysdba"` access.
-	Copy the oradb_zdmgg_discovery_v1_2.sql file to the server.
-	Execute the script as ```sqlplus "/ as sysdba" @oradb_zdmgg_discovery_v1_2.sql ``` .


The above script will generate .htm output file on the same location.

## License
Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.


