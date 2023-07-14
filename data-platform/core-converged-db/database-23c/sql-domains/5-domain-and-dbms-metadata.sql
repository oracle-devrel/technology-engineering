REM script for 23c: 5-domain-and-dbms-metadata.sql
REM to get the DDL command we use DBMS_METADATA

-- use GET_DDL and SQL_DOMAIN as an object_type argument

set longc 1000
select dbms_metadata.get_ddl('SQL_DOMAIN', 'MYEMAIL_DOMAIN') from dual;
