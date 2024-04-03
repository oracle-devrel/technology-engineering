REM Script: create-sts.sql
REM Create a new SQL Tuning Set with DBMS_SQLTUNE.CREATE_SQLSET

execute dbms_sqltune.create_sqlset(sqlset_name=>'&stsname', sqlset_owner=>'&owner');
