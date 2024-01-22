REM Script: dbresource-manager.sql
REM Database Resource Manager and Real-Time SQL Monitoring

-- query columns with rm_ prefix to get database resource manager information 
  
SELECT username, elapsed_time, plsql_exec_time, sql_text, cpu_time,
rm_last_action, rm_last_action_reason, rm_last_action_time, rm_consumer_group
FROM v$sql_monitor WHERE username is not null;
