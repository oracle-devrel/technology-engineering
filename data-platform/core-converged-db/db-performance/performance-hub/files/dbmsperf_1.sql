REM  Script: dbmsperf_1.sql
REM  example for DBMS_PERF.REPORT_PERFHUB with parameters
 
REM REPORT_PERFHUB generates an active performance report of the entire database system for a specified time period.
REM Arguments in this example define the report mode (historical or real-time) and start and end time for the time selection and outer time.
REM Different tabs are available in the Performance Hub, depending on whether is_real-time is 1 for real-time mode or 0 for historical mode.
REM When real-time data is selected, more granular data is presented because data points are available every minute.
REM If historical data is chosen, more detailed data is presented, but the data points are averaged out to the AWR interval (usually an hour). 


set pages 0 linesize 32767 trimspool on trim on long 1000000 longchunksize 10000000

spool sql_details_1.html

select dbms_perf.report_perfhub (
is_realtime         => &realtime,  
outer_start_time    => to_date('&outerstart','dd-MON-YYYY hh24:mi:ss'), 
outer_end_time      => to_date('&outerend','dd-MON-YYYY hh24:mi:ss'), 
selected_start_time => to_date('&starttime','dd-MON-YYYY hh24:mi:ss'), 
selected_end_time   => to_date('&endtime','dd-MON-YYYY hh24:mi:ss')) 
from dual; 

spool off
