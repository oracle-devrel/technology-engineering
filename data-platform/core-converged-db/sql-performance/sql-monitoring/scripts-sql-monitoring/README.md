#scripts-for-sql-tuning-monitoring

These scripts can be used to generate Real-Time SQL monitoring reports in HTML or ACTIVE HTML. 

##scripts

- active-report.sql: Generate an active html report with DBMS_SQL_MONITOR.REPORT_SQL_MONITOR
  
- dbresource-manager.sql: Real-Time SQL Monitoring when Database Resource Manager is in use

- find-sqlid.sql: Find SQL id with V$SQL_MONITOR

- html-report.sql: Generate a report in HTML with DBMS_SQL_MONITOR.REPORT_SQL_MONITOR

- report-for-devs.sql: DBMS_SQLTUNE for database developers to view the last monitored statement executed by the user

- report-summary-for-devs.sql: DBMS_SQLTUNE for database developers to get a list of all statements executed by the user
  
- report-with-sqlid.sql: Generate a report with DBMS_SQL_MONITOR.REPORT_SQL_MONITOR for a specific statement
  
- session-longops.sql: Example for V$SESSION_LONGOPS usage

