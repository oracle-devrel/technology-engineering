# Oracle Database Reconciliation Utility

The Oracle Database Reconciliation tool is an utility that captures necessary details from source and target of an oracle database in order to reconcile databases post database migration. This utility runs on Non Container or Container databases and helps in generating set of reconciliation reports.


## When to use this asset?

This script is to be executed during the database migration phase.

## How to use this asset?

The solution includes two scripts. One for execution on Source and another for Target database. The Source Script needs to be executed on source before the migration process starts which captures metadata in a CSV format file. Post Migration, target script reads CSV file (generated on source) and loads it into a schema and compares with metadata of the target database and generates multiple reconciliation reports.

Script to execute on Source oracle database:
```
sqlplus "/ as sysdba"  @MF_DP_Recon_Source.sql
```
Script to execute at Target oracle database:
```
./MF_DP_Recon_Target.sh "/ as sysdba" "<<Path of source spooled files>>"
```

This is a reconciliation utility for Oracle database compatible for 11g onwards with the below features:
1.	Current version of the script is v3.0 and it supports Oracle 11g or above databases.
2.	The source script is platform independent as it requires `sqlplus "/ as sysdba"` to execute.
3.	Same script cane be used for Oracle Multitenant and Non-Multitenant databases but for Oracle Multitenant PDBs it requires the TNS alias to connect instead of using `sqlplus "/ as sysdba"`.

### Step 1
This script needs to be executed on Oracle database server with a user who has `“/as sysdba”` access.
•	Copy the MF_DP_Recon_Source.sql file to the source server.
•	To execute the source script: `sqlplus "/ as sysdba"  @MF_DP_Recon_Source.sql`.
•	The above script will generate source_data.csv which needs to be copied from source to target server.
•	Copy the MF_DP_Recon_Target.sh file to the same path of above source_data.csv at target server and provide `chmod 755` to the file.
•	To execute the target script: `./MF_DP_Recon_Target.sh "/ as sysdba" "<<Path of source spooled files>>"`.

### Step 2
This asset will generate the following key reports:
•	Schema wise objects counts Reconciliation Report.
•	Schema wise Tables wise rows counts Reconciliation Report.
•	Missing Objects Reconciliation Report.
•	Invalid Objects Status Reconciliation Report.
•	User Account Status Reconciliation Report.
•	Unusable Indexes Reconciliation Report.
•	Table wise constraints counts Reconciliation Report.
•	Disabled Referential Constraints Reconciliation Report.
•	Roles & Privileges Counts Reconciliation Report.
•	Missing Role Privileges Reconciliation Report.
•	Missing Sys Privileges Reconciliation Report.
•	Missing Table Privileges Reconciliation Report.
•	Reconciliation Mismatch Smmary Report.

Note: 
•	This script creates one temporary table like USER_TEMP at source and two tables like USER_TEMP and RECON_TABLE at target and are deleted automatically after processing reports.
•	This script generates some dynamic files like raise_exit.sql, Source_Steps_Execution.log and Target_Steps_Execution.log which gets executed and helps in generating execution log from both source and target script.
•	This scipt uses sqlldr tool and generates dynamic file like source_data.ctl and source_data_sqlldr.log at target database to load CSV date to RECON_TABLE for processing reports.


## License
Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.
