-- DBA_WORKLOAD_CAPTURES displays all the workload captures that have been performed in the current database.

set linesize window
select id, name, status, errors, awr_exported, duration_secs, filters_used, dbtime_total, dbtime, dbtime_total,
user_calls_total, user_calls, user_calls_unreplayable, transactions, transactions_total, capture_size/1024/1024 
from dba_workload_captures where name like '&name%';
