REM Script create-spa-task.sql
REM Create a SQL Performance Analyzer task

-- enter STS name and owner of the STS
-- print task name

set serveroutput on 
declare tname varchar2(100);
begin    
   tname := dbms_sqlpa.create_analysis_task(sqlset_name => '&STSname', sqlset_owner=>'&STSOwner');
   dbms_output.put_line( 'task name: ' || tname);
end;
/
