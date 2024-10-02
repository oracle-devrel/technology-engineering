REM Script: monitor-task.sql
REM Monitor SQL Performance Analyzer task

col owner format a15
col task_name format a30
-- check status and name of SQL Performance Analyzer task
SELECT owner, task_name, status FROM dba_advisor_tasks 
WHERE upper(advisor_name)='SQL PERFORMANCE ANALYZER'; 
