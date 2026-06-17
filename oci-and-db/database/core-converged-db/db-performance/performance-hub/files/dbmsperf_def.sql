REM  Script: dbmsperf_def.sql
REM  example for DBMS_PERF.REPORT_PERFHUB with defaults 
REM REPORT_PERFHUB generates an active performance report of the entire database system for a specified time period.
REM If you choose the defaults, report mode is historical, selected time is 1 hour before latest AWR and outer time period starts 24 hours before. 


set pages 0 linesize 32767 trimspool on trim on long 1000000 longchunksize 10000000

spool sql_details_def.html

select dbms_perf.report_perfhub() 
from dual; 

spool off
