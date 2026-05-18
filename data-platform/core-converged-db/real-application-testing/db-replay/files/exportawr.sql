-- This procedure exports the AWR snapshots associated with a given capture ID.

-- find the capture_id
select id, name 
from dba_workload_captures where name like '%&capturename%';

-- export AWR
execute dbms_workload_capture.export_awr(capture_id =>&captureid);

-- please check the status with capturemon.sql