REM Script: check-sts-statements.sql
REM Use view ALL_SQLSET_STATEMENTS
 
-- check the tuning set, enter name and owner

select executions, cpu_time/1000 cpu_in_ms, elapsed_time/1000 elapsed_in_ms, sql_id, substr(sql_text,1,80) 
from all_sqlset_statements 
where sqlset_name='&name' and owner='&owner' 
order by 3 desc;
