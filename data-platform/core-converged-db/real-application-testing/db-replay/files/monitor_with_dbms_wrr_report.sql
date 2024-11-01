/* Database Replay monitor report (dbms_wrr_report) (Doc ID 2696765.1)

Identify percentage progress of replay, 
the slowest streams or sessions in the replay, 
waiter and blocker in the replay, 
and highest Database Wait Event during the replay 
Refer to Doc ID 2696765.1 for more information*/

-- Step 1: Identify replay id from dba_workload_replays 

select id from dba_workload_replays where status = 'IN PROGRESS';

-- step 2: Run procedure dbms_wrr_report.replay

set serveroutput on
exec dbms_wrr_report.replay(&replayid);