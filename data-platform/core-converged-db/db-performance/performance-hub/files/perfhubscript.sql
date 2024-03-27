REM  Script: perfhubscript.sql
REM  Oracle script perfhubrpt.sql
REM The Performance Hub Report can be generated in Single-Instance Database, in RAC and for PDBs and root containers.

REM Connect with DBA privileges
REM Start the perfhubrpt.sql from $ORACLE_HOME/rdbms/admin
REM You will be prompted for report level (basic, typical or all), database id, instance id and time range. 
REM An active  HTML report will be generated in the dirctory 

@?/rdbms/admin/perfhubrpt.sql
