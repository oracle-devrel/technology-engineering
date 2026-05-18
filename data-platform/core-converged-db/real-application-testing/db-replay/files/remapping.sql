-- This procedure remaps the captured connection to a new one so that the user sessions can connect to the database in a desired way during workload replay.

-- after initialize, check the connection map to get the connection_ids
select conn_id, replay_id, replay_conn from dba_workload_connection_map;

/*
examples
exec DBMS_WORKLOAD_REPLAY.REMAP_CONNECTION (connection_id => 1, replay_connection =>'PDB1');
exec DBMS_WORKLOAD_REPLAY.REMAP_CONNECTION (connection_id => 101, replay_connection => 'dlsun244:3434/bjava21');
*/
