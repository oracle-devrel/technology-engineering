-- V$RSRC_SESSION_INFO displays Resource Manager statistics per session.

set linesize window
col username format a10
col osuser format a10
col group_name format a20
col service format a8
col state format a15

select s.inst_id            inst,
       s.username           username,
       s.osuser             osuser,
       co.name              group_name,
       s.service_name       service,
       se.state,
       se.consumed_cpu_time cpu_time,
       se.cpu_wait_time,
       se.dop/2               degree_of_parallelism
from gv$rsrc_session_info se, gv$rsrc_consumer_group co, gv$session s
where se.current_consumer_group_id = co.id
   and s.sid = se.sid
   and s.inst_id = se.inst_id
   and co.name not in ('_ORACLE_BACKGROUND_GROUP_')
 order by s.inst_id, s.username;
