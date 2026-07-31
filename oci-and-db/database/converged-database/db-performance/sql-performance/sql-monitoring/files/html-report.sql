REM  Script: html-report.sql
REM  Generate HTML report with DBMS_SQL_MONITOR.REPORT_SQL_MONITOR

-- report on the last statement monitored by Oracle
-- please use the proposed SQL*Plus formats here to get the correct HTML report
  
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
