-- This procedure puts the database state in INIT for REPLAY mode, and loads data into the replay system that is required before preparing for the replay 

execute dbms_workload_replay.initialize_replay(replay_name=>'&NAME', replay_dir=>'&DIR', plsql_mode=>'extended');
