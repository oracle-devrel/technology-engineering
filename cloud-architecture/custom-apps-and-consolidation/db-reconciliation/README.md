# Oracle Database Reconciliation Utility

The Oracle Database Reconciliation tool is a utility that captures necessary details from the source and target of an Oracle database in order to reconcile databases post-database migration. This utility runs on Non-Container or Container databases and helps in generating sets of reconciliation reports.


## When to use this asset?

This script is to be executed during the database migration phase.

## How to use this asset?

The solution includes two scripts. One for execution on Source and another for Target database. The Source Script needs to be executed on source before the migration process starts which captures metadata in a CSV format file. Post Migration, the target script reads a CSV file (generated on the source) and loads it into a schema and compares it with the metadata of the target database, and generates multiple reconciliation reports.

Script to execute on Source Oracle database:
```
sqlplus "/ as sysdba"  @MF_DP_Recon_Source.sql
```
Script to execute at Target Oracle database:
```
./MF_DP_Recon_Target.sh "/ as sysdba" "<<Path of source spooled files>>"
```

This is a reconciliation utility for Oracle database compatible for 11g onwards with the below features:
1.	Current version of the script is v3.0 and it supports Oracle 11g or above databases.
2.	The source script is platform independent as it requires `sqlplus "/ as sysdba"` to execute.
3.	The same script can be used for Oracle Multitenant and Non-Multitenant databases but for Oracle Multitenant PDBs it requires the TNS alias to connect instead of using `sqlplus "/ as sysdba"`.

### Step 1
This script needs to be executed on an Oracle database server with a user who has `“/as sysdba”` access.
•	Copy the MF_DP_Recon_Source.sql file to the source server.
•	To execute the source script: `sqlplus "/ as sysdba"  @MF_DP_Recon_Source.sql`.
•	The above script will generate source_data.csv which needs to be copied from the source to the target server.
•	Copy the MF_DP_Recon_Target.sh file to the same path of the above source_data.csv at the target server and provide `chmod 755` to the file.
•	To execute the target script: `./MF_DP_Recon_Target.sh "/ as sysdba" "<<Path of source spooled files>>"`.

### Step 2
This asset will generate the following key reports:
•	Schema-wise objects counts Reconciliation Report.
•	Schema-wise Tables-wise rows counts Reconciliation Report.
•	Missing Objects Reconciliation Report.
•	Invalid Objects Status Reconciliation Report.
•	User Account Status Reconciliation Report.
•	Unusable Indexes Reconciliation Report.
•	Table-wise constraints counts Reconciliation Report.
•	Disabled Referential Constraints Reconciliation Report.
•	Roles & Privileges Counts Reconciliation Report.
•	Missing Role Privileges Reconciliation Report.
•	Missing Sys Privileges Reconciliation Report.
•	Missing Table Privileges Reconciliation Report.
•	Reconciliation Mismatch Summary Report.

Note: 
•	This script creates one temporary table like USER_TEMP at source and two tables like USER_TEMP and RECON_TABLE at target which are deleted automatically after processing reports.
•	This script generates some dynamic files like raise_exit.sql, Source_Steps_Execution.log, and Target_Steps_Execution.log which gets executed and helps in generating execution logs from both source and target script.
•	This script uses sqlldr tool and generates dynamic files like source_data.ctl and source_data_sqlldr.log at the target database to load CSV data to RECON_TABLE for processing reports.


## License
Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.
