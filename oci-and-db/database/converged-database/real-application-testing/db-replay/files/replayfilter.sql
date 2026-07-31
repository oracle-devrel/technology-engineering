-- This procedure adds a filter to replay only a subset of the captured workload.

/* possible filter types: INSTANCE_NUMBER, USER, MODULE, ACTION, PROGRAM, SERVICE, PDB_NAME 

example:  
execute DBMS_WORKLOAD_REPLAY.ADD_FILTER(fname => '&filtername', fattribute => 'USER', fvalue => '&schema');

*/

execute dbms_workload_replay.add_filter(fname=>'&FILTERNAME', fattribute=>'&filtertype', fvalue=>'&filtervalue');

-- Monitor filters

set linesize window
select * from dba_workload_filters;

/* Delete filters:
execute DBMS_WORKLOAD_REPLAY.DELETE_FILTER(fname => '&filtername');
*/