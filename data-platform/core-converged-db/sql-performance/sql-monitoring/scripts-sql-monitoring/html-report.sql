REM  Script: html-report.sql
REM  report generation in HTML with DBMS_SQL_MONITOR.REPORT_SQL_MONITOR

-- find the last monitored database operation
-- please use the proposed SQL*plus formats here to get the correct HTML report 
set trimspool on 
set trim on
set pagesize 0
set linesize 32767
set long 1000000
set longchunksize 1000000
spool sqlmon_active.html

SELECT dbms_sql_monitor.report_sql_monitor(type => 'HTML', report_level => 'ALL')
FROM dual;

spool off
