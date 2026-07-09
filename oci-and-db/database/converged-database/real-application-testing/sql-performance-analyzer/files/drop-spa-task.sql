REM Script: drop-spa-task.sql
REM drop SQL Performance Analyzer task 

-- enter SPA task name  
execute dbms_sqlpa.drop_analysis_task(task_name => '&taskname');
-- check SPA tasks with monitor_task.sql
