REM  Script: active-report.sql
REM  Generate active (HTML) report with DBMS_SQL_MONITOR.REPORT_SQL_MONITOR

-- report on the last statement monitored by Oracle
-- please use the proposed SQL*Plus formats here to get the correct report output

set trimspool on
set trim on
set pagesize 0
set linesize 32767
set long 1000000
set longchunksize 1000000

spool sqlmon_active.html

select dbms_sql_monitor.report_sql_monitor(report_level=>'ALL',type=>'ACTIVE')
from dual;

spool off
