REM Script: compare-performance.sql
REM Compare performance of two executions
  
-- enter task name (see also monitor-tasks.ql)
-- enter name for execution 1 and execution 2 (monitor-executions.sql lists the execution names)
execute dbms_sqlpa.execute_analysis_task(task_name => '&taskname', execution_type => 'COMPARE PERFORMANCE',execution_params => DBMS_ADVISOR.ARGLIST('execution_name1', '&name1','execution_name2', '&name2'));
