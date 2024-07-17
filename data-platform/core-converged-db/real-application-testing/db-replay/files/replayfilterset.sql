-- This procedure creates a new filter set for the replays at replay_dir 

/* It includes all the replay filters that have already been added by the ADD_FILTER Procedure.
Once all workload replay filters are added, you can create a replay filter set that can be used when replaying the workload. 
Default_action can be either INCLUDE or EXCLUDE. */

execute DBMS_WORKLOAD_REPLAY.CREATE_FILTER_SET(replay_dir=> '&REPLAY_DIR', filter_set => '&FILTERSET_NAME', default_action => 'EXCLUDE');

-- check all filters
select * from dba_workload_filters;