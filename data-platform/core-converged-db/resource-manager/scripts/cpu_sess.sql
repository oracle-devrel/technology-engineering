-- V$RSRC_CONSUMER_GROUP displays data related to currently active resource consumer groups.

set linesize window

select inst_id,
       name,
       active_sessions,
       consumed_cpu_time,
       cpu_waits,
       cpu_wait_time
from gv$rsrc_consumer_group
order by inst_id, name;
