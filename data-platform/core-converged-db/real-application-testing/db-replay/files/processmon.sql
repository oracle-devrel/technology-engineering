set serveroutput on

declare
p number;
z number;
begin

p:=dbms_workload_replay.process_capture_completion;
z:=dbms_workload_replay.process_capture_remaining_time;
dbms_output.put_line('percentage ' ||p);
dbms_output.put_line('Remaining time '||z);
end;
/
