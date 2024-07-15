-- how to add capture filters

-- example 1 for inclusion
 
-- Add filters
-- The usage mode is determined by the default_action input to the START_CAPTURE Procedure.

exec DBMS_WORKLOAD_CAPTURE.ADD_FILTER (fname => 'USER_TRACK', fattribute => 'USER', fvalue => 'TRACKUSER');

-- check status in dba_workload_filters
-- check filters_used in dba_workload_captures

-- start capture (see capturestart.sql) and use EXCLUDE in DEFAULT_ACTION
  
execute dbms_workload_capture.start_capture (name=>'&Replayname', dir=>'&Reaplydir', default_action=>'EXCLUDE');

-- No user request to the database is captured, except for the part of the workload defined by the filter.

-- check status in dba_workload_filters
-- check filters_used in dba_workload_captures


-- example 2 for exclusion

-- Add filters
-- The usage mode is determined by the default_action input to the START_CAPTURE Procedure.

exec dbms_workload_capture.add_filter('ORACLE MANAGEMENT SERVICE (DEFAULT)', 'Program', 'OMS');
exec dbms_workload_capture.add_filter('ORACLE MANAGEMENT AGENT (DEFAULT)', 'Program', 'emagent%');
exec dbms_workload_capture.add_filter('U_DBSNMP', 'User', 'DBSNMP');


-- check status in dba_workload_filters
-- check filters_used dba_workload_captures


execute dbms_workload_capture.start_capture (name=>'&Replayname', dir=>'&Reaplydir', default_action=>'INCLUDE');

-- All user requests to the database are captured, except for the part of the workload defined by the filters. 