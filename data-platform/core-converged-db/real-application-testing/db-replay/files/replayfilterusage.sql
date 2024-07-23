-- How to use replay filters

-- First step: Adding new filters (see replayfilter.sql).

-- Adding filters
exec DBMS_WORKLOAD_REPLAY.add_filter('ORACLE_MANAGEMENT_SERVICE', 'PROGRAM', 'OMS'); 
exec DBMS_WORKLOAD_REPLAY.add_filter('DBSNMP_USER', 'USER', 'DBSNMP');  
exec DBMS_WORKLOAD_REPLAY.add_filter('ORACLE_MANAGEMENT_AGENT', 'PROGRAM', 'emagent%'); 
exec DBMS_WORKLOAD_REPLAY.add_filter('RMAN_MODULE', 'MODULE', 'rman%');  

-- check dba_workload_filters, filter status is now "NEW".


-- Second step: Creating a Replay Filter Set (see replayfilterset.sql). 
exec DBMS_WORKLOAD_REPLAY.CREATE_FILTER_SET (replay_dir => '&DIR', filter_set => 'MyReplayFilter', default_action => 'INCLUDE');

-- INCLUDE: CREATE_FILTER_SET creates a replay filter set named MyReplayFilter, which will replay all captured calls except for the part of the workload defined by the replay filters.
-- See capturefilterusage.sql for EXCLUDE example.

-- Initialize replay (see replayinitialize.sql)

execute DBMS_WORKLOAD_REPLAY.initialize_replay(replay_name=>'&NAME', replay_dir=>'&DIR', plsql_mode=>'extended');

-- check dba_workload_filters: status is now "IN SET

-- Third step: Using a Replay Filter Set (see replayusefilterset.sql).
exec DBMS_WORKLOAD_REPLAY.USE_FILTER_SET (filter_set => 'MyReplayFilter');

-- check dba_workload_filters: status is now "IN USE"

-- now proceed with replayprepare.sql, wrc starts and replaystart.sql




