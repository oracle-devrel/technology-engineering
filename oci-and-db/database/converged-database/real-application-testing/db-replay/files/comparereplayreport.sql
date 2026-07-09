-- This procedure generates a report comparing a replay to its capture or to another replay of the same capture.

-- find replay_id
select id, awr_begin_snap, awr_end_snap 
from dba_workload_replays where name like '&replayname%';


-- replay_id2 of the workload replay whose report is requested 
-- If this is NULL, then the comparison is done with the capture

variable result clob

begin
  dbms_workload_replay.compare_period_report(replay_id1=>&replayid,replay_id2=>null,format=>'HTML',result=>:result);
end;
/

set heading off
set long 1000000
set pagesize 0
spool comparereport.html rep
print result
spool off
