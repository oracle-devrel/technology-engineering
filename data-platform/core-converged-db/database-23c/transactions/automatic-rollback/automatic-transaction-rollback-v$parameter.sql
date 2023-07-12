REM  Script in 23c: automatic-transaction-rollback-v$parameter.sql
REM  Check the settings in V$PARAMETER for automatic transaction rollback 

-- run in 23c in your PDB session as user with DB_DEVELOPER_ROLE  
col name format a50 
col value format a10 
select name, value from v$parameter where name like 'tx%'; 
