REM Script: drop-sts.sql
REM Drop an existing SQL Tuning Set with DBMS_SQLTUNE.DROP_SQLSET

-- check sts first with check-sts-information.sql
-- drop sts 
execute dbms_sqltune.drop_sqlset(sqlset_name=>'&stsname', sqlset_owner=>'&owner');
