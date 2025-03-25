-- DBA_WORKLOAD_REPLAYS displays all the workload replays that have been performed in the current database.

set linesize window
alter session set nls_date_format='dd.mm.yyyy hh24:mi';

select name, id, status, user_calls, awr_exported, start_time, end_time 
from dba_workload_replays 
order by start_time;
