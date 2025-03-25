-- This procedure initiates workload capture on all instances.
/*
If you used filters, please review the usage of EXCLUDE and INCLUDE in the start_capture procedure.
Definition:
If EXCLUDE, no user request to the database is captured, except for the part of the workload defined by the filters. 
In this case, all the filters specified using the ADD_FILTER procedures are treated as INCLUSION filters, determining 
the workload that is captured. 
Default is INCLUDE.

-- example with user defined filter criteria 
-- execute dbms_workload_capture.start_capture (name=>'&capturename', dir=>'&dir', default_action=>'EXCLUDE');

other options:

-- with STS (not available for RAC)
-- execute dbms_workload_capture.start_capture (name=>'&capturename', dir=>'&dir', capture_sts=>TRUE);

-- with duration 
-- execute dbms_workload_capture.start_capture (name=>'&capturename', dir=>'&dir', duration=>&secs);
 
The optional plsql_mode parameter determines how PL/SQL is handled by DB Replay during capture and replays.
These two values can be set for the plsql_mode parameter:
top_level: Only top-level PL/SQL calls are captured and replayed, which is how DB Replay handled PL/SQL prior 
to Oracle Database 12c Release 2 (12.2.0.1). This is the default value.

Extended: Both top-level PL/SQL calls and SQL called from PL/SQL are captured. When the workload is replayed, 
the replay can be done at either top-level or extended level.
*/


-- Example EXCLUDE and PL/SQL mode extended
-- execute dbms_workload_capture.start_capture (name=>'&capturename', dir=>'&dir', plsql_mode => 'extended', default_action=>'EXCLUDE');


-- Example INCLUDE (default) and the PL/SQL mode extended
execute dbms_workload_capture.start_capture (name=>'&capturename', dir=>'&dir', plsql_mode => 'extended');
