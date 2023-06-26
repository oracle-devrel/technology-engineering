# Asset Name
oradb_xtts_prechecks.sql

# Introduction
XTTS Pre-check for ORACLE Database is a SQL script-based utility that captures necessary details of an oracle database in order to analyze the suitability of XTTS method.
This utility runs on Oracle 11g onwards, both on Container/Non Container databases and helps in generating a HTML report with self-contained tablespace violation status and other detailed description.

## When to use this asset?

This script is to be executed in the discovery phase if it is identified the oracle on-premises database is to be migrated using XTTS method.

## How to use this asset?

```
sqlplus "/ as sysdba"  @oradb_xtts_prechecks.sql
```

This script needs to be executed on Oracle database server with a user who has ` "/as sysdba" ` access.
•	Copy the oradb_xtts_prechecks.sql file to the server.
•	Execute the script as ```sqlplus "/ as sysdba" @oradb_xtts_prechecks.sql``` .

The above script will generate a .htm output file on the same location.

## License
Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.


