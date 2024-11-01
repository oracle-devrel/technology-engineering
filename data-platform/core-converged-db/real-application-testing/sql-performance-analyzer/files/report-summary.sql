REM Script: report-summary.sql
REM Generate summary report in HTML

-- please use the following SQL*Plus formats
set long 1000000 longchunksize 1000000 linesize 200 head off feedback off echo off

-- enter task name
variable result clob
execute :result := dbms_sqlpa.report_analysis_task(task_name => '&Taskname', -
                                                     type      => 'HTML', -
                                                     section   => 'SUMMARY');
-- spool the HTML report
spool rep_summary.html
print result
spool off 
