REM Script create-spa-task.sql
REM Create a SQL Performance Analyzer task

-- drop existing task if required
-- execute dbms_sqlpa.drop_analysis_task(task_name => '&%taskname%');

-- create task, add STS name and owner of the STS
-- print task name

set serveroutput on 
declare tname varchar2(100);
begin    
   tname := dbms_sqlpa.create_analysis_task(sqlset_name => '&STSname', sqlset_owner=>'DWH_DATA');
   dbms_output.put_line( 'task name: ' || tname);
end;
/
