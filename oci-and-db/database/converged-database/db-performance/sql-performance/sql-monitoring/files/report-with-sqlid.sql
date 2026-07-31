REM  Script: report-with-sqlid.sql
REM  Report generation with DBMS_SQL_MONITOR.REPORT_SQL_MONTOR 

-- optional: find SQL id with find-sqlid.sql
-- enter SQL id and type (e.g. TEXT, ACTIVE, HTML)

set trimspool on 
set trim on
set pagesize 0
set linesize 32767
set long 1000000
set longchunksize 1000000
spool sqlmon_active.html

SELECT dbms_sql_monitor.report_sql_monitor(sql_id=> '&SQLid', type => '&type', report_level => 'ALL')
FROM dual;

spool off
