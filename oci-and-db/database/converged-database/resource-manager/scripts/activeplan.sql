-- to monitor active plans and the history of active plans

set linesize window
select * from v$rsrc_plan;

select sequence# seq, name plan_name,
to_char(start_time, 'DD-mon HH24:mi') start_time,
to_char(end_time, 'dd-mon hh24:mi') end_time
from v$rsrc_plan_history;
