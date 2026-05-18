-- This procedure processes the workload capture found in capture_dir in place.

execute dbms_workload_replay.process_capture(capture_dir=>'&dir', parallel_level=>&parallel, plsql_mode=>'extended');
