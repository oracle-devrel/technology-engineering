-- This procedure adds a filter to capture a subset of the workload.

/* possible filter types: INSTANCE_NUMBER, USER, MODULE, ACTION, PROGRAM, SERVICE, PDB_NAME 

examples: 

exec dbms_workload_capture.add_filter('ORACLE MANAGEMENT SERVICE (DEFAULT)', 'Program', 'OMS');
exec dbms_workload_capture.add_filter('ORACLE MANAGEMENT AGENT (DEFAULT)', 'Program', 'emagent%');
exec dbms_workload_capture.add_filter('U_DBSNMP', 'User', 'DBSNMP');
*/

-- example 
execute dbms_workload_capture.add_filter(fname=>'&FILTERNAME', fattribute=>'&filtertype', fvalue=>'&filtervalue');

-- Monitor filters
set linesize window
select * from dba_workload_filters;

/* if you need to delete the filters
execute DBMS_WORKLOAD_CAPTURE.DELETE_FILTER(fname=>'&Filtername');
*/
