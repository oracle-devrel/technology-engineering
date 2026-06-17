-- This function generates a report on the workload replay.

-- find replay_id
alter session set nls_date_format='dd.mm.yyyy hh24:mi';

select name, id, status, awr_exported,start_time, end_time
from dba_workload_replays
order by start_time;

spool replayreport.html

set pagesize 0 long 30000000 longchunksize 1000
col tt format a120
select DBMS_WORKLOAD_REPLAY.REPORT(replay_id=>&replayid, format=>'HTML') tt
from dual;

spool off
