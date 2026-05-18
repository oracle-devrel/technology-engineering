-- Displays a history (the last one hour) of resource manager metrics, taken from V$RSRCMGRMETRIC. 
-- When a resource plan is set, this history is cleared and restarted. 
-- This view provides information about resources consumed and wait times per consumer group.

set linesize window

select inst_id,
       to_char(begin_time, 'HH:MI') time,
       consumer_group_name,
       60 * (select value from v$osstat where stat_name = 'NUM_CPUS') total,
       60 * (select value from v$parameter where name = 'cpu_count') db_total,
       cpu_consumed_time / 1000 consumed,
       cpu_consumed_time /
       (select value from v$parameter where name = 'cpu_count') / 600 cpu_utilization,
       cpu_wait_time / 1000 throttled
from gv$rsrcmgrmetric_history
order by begin_time desc, consumer_group_name;
