#scripts-for-sql-monitoring

This scripts can be used to monitor real-time SQL performance with sql scripts. 

##scripts

- session-longops.sql: Example for V$SESSION_LONGOPS usage

- find-sqlid.sql: Find SQL id with V$SQL_MONITOR

- html-report.sql: Generate report in HTML with DBMS_SQL_MONITOR.REPORT_SQL_MONITOR

- active-report.sql: Generate active report with DBMS_SQL_MONITOR.REPORT_SQL_MONITOR
 
- sql-monitoring-with-sqlid.sql: generate report with DBMS_SQL_MONITOR.REPORT for a specific sqlid 

- dbresource-manager.sql: Real-Time SQL Monitoring with Database Resource Manager

- report-for-devs.sql: DBMS_SQLTUNE for database developers for the last monitored statement executed by the user   

- summary-report-for-devs.sql: DBMS_SQLTUNE for database developers for all statements executed by the user
