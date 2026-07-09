REM Script: trial-execute.sql
REM Execute the trial with execution_type TEST EXECUTE

-- This is the default setting
-- It executes every SQL statement and collect its execution plans and execution statistics. 

-- enter the task name and add a user defined execution name
execute DBMS_SQLPA.EXECUTE_ANALYSIS_TASK(task_name       => '&Taskname', -
                                         execution_type  => 'test execute', -
                                         execution_name  => '&executionename');
