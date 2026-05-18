-- debug slow replay in alert

set linesize 9999
col object_name format a20
col reason format a100
col creation_time format a20

select object_name, reason, to_char(creation_time,'MM-DD-YYYY HH24:MM:SS') as creation_time
from dba_alert_history
where  reason_id between 160 and 165
order by creation_time
/

