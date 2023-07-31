REM Script monitor-executions.sql
REM Monitor SQL Performance Analyzer executions

-- list task name and executions for advisor
-- use SQL PERFORMANCE ANALYZER in the case of SPA  
col execution_name format a25
col task_name format a25 

select task_name, execution_name, status
from dba_advisor_executions where upper(advisor_name)='&Advisorname';
