-- This procedure imports the AWR snapshots from a given replay.

-- find capture id
set serveroutput on

declare
capid number := 0;
BEGIN
capid := DBMS_WORKLOAD_CAPTURE.GET_CAPTURE_INFO(dir =>'&RATDIR');
dbms_output.put_line('capid is ' || capid);
END;
/

select dbms_workload_capture.import_awr(capture_id => &capid, staging_schema => '&User') from dual;



