--  V$RSRC_SESSION_INFO displays Resource Manager statistics per session.

set linesize window
col username format a20
col osuser format a15
col gruppe format a15

select s.username username,s.osuser osuser, co.name gruppe,
se.state, se.consumed_cpu_time cpu_time, se.cpu_wait_time
from v$rsrc_session_info se, v$rsrc_consumer_group co , v$session s
where se.current_consumer_group_id = co.id and  s.sid=se.sid and se.state!='NOT MANAGED';
