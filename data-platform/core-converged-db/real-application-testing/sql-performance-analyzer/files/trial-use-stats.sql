REM Script: trial-use-stats.sql
REM Use imported execution statistics from STS with execution_type CONVERT SQLSET


-- enter the task name, STS name and STS owner and add a user defined execution name
execute dbms_sqlpa.execute_analysis_task(task_name => '&Taskname', -
                                         execution_type => 'convert sqlset',- 
                                         execution_name => '&executionname', -
                                         execution_params => DBMS_ADVISOR.ARGLIST('sqlset_name', '&STSname', 'sqlset_owner', '&STSowner')); 
