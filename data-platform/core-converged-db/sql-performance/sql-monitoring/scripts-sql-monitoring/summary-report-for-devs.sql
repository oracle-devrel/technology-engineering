REM Script: summary-report-for-devs.sql
REM DBMS_SQLTUNE for database developers for all statements executed by the user

-- list all monitored statement executed by the user
-- enter value for type (e.g. TEXT, HTML, ACTIVE)
-- use the proposed SQL*Plus formats to get a correct report output  
  
set trimspool on 
set trim on
set pagesize 0
set linesize 32767
set long 1000000
set longchunksize 1000000

select DBMS_SQLTUNE.REPORT_SQL_MONITOR_LIST(type=>'TEXT') from dual;
