-- This function generates a report on the workload capture.


-- Find report_id 
select id, name, status, start_time, end_time, awr_exported, connects, user_calls, dir_path 
from dba_workload_captures where id = (select max(id) from dba_workload_captures);

-- Generate capture report
spool capturereport.txt

set pagesize 0 long 30000000 longchunksize 1000
select dbms_workload_capture.report(&report_id, 'TEXT') from dual;

spool off