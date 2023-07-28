REM Script: report-for-developers.sql
REM DBMS_SQLTUNE for database developers

-- DBMS_SQLTUNE contains the REPORT_SQL_MONITOR and REPORT_SQL_MONITOR_LIST functions
-- list last monitored statement excuted by the user with REPORT_SQL_MONITOR
-- enter value for type (e.g. TEXT, HTML, ACTIVE)
-- please use the proposed SQL*Plus formats

set trimspool on 
set trim on
set pagesize 0
set linesize 32767
set long 1000000
set longchunksize 1000000

SELECT dbms_sqltune.report_sql_monitor(type => '&type') FROM dual;
