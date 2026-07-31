REM script: list_snapshots.sql
REM use DBA_HIST_SNAPSHOTS

-- format the timestamp output
ALTER SESSION SET NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH:MI';

-- list the snap ids

col begin_snap format a20
col end_snap format a20

select snap_id, begin_interval_time begin_snap, end_interval_time end_snap
from dba_hist_snapshot
order BY snap_id;
