# scripts-for-sts
This folder provides useful SQL scripts for SQL Tuning Sets. You may change and edit them accordingly.

## scripts
You must have the ADMINISTER SQL TUNING SET system privilege to manage SQL tuning sets that you own, or the ADMINISTER ANY SQL TUNING SET system privilege to manage any SQL tuning sets.

- create_sts.sql: Create a new SQL Tuning Set
- drop-sts.sql: Drop an existing SQL Tuning Set
- create-sts-from-cursorcache.sql: Load STS from Cursor Cache
- list_snapshots.sql: Helper script to list and find the required begin and end snap id
- create-sts-from-awr.sql: Load STS from AWR
- reduce-sts.sql: Reduce and existing STS
- check-sts-information.sql: Monitor STS
- check-sts-statements.sql: Monitor STS with statement execution
- 1-transport-sts-from-source.sql: Tasks on the source system to transport STS
- 2-transport-sts-to-target.sql: Tasks on the remote system to transport STS
