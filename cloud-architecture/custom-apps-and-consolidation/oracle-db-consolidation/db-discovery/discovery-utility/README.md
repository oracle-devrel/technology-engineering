# Oracle Database Discovery Script

The Database discovery and analysis tool is a SQL utility that captures necessary details of an oracle database in order to analyse on-premises or cloud Oracle Databases for the suitability of migration/upgrades. This utility runs on Non Container or Container databases and helps in generating HTML report with detailed description.

## When to use this asset?

This script is to be executed in the discovery phase if it is identified the oracle on-premises database is to be migrated to OCI.

## How to use this asset?
```
sqlplus "/ as sysdba"  @oradb_discovery_v3_6_11_19.sql
```

### Step 1
This is a discovery utility for Oracle database compatible for 11g onwards with a below features:
1.	Current version of the script is v3.6 and it supports Oracle 11g or above database
2.	Single version script for both Oracle Multitenant and  Non-Multitenant database
3.	This is a platform independent script as we need `sqlplus "/ as sysdba" ` to execute only.

This script needs to execute on Oracle database server with a user who has `“/as sysdba” ` access.
•	Copy the oradb_discovery_v3_6_11_19.sql file to the server
•	To execute the script: `sqlplus "/ as sysdba"  @oradb_discovery_v3_6_11_19.sql`

### Step 2
The above script will generate .LST as output files on the same location.  
Convert this .LST to .HTML to view the file.

Note: This script generates dynamic files like version_not_matched.sql which gets executed and deleted automatically.


## License
Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.
