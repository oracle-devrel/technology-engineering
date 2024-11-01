REM Script: create-sts-regressed.sql
REM Generate STS for regressed statements

-- create SQL Tuning Set for regressed statements
execute DBMS_SQLTUNE.CREATE_SQLSET(sqlset_name => '&stsname', description=> 'Regressed Statements');

-- use task and execution name from compare-performance.sql or check with monitor-executions.sql
DECLARE
  sqlset_cur  DBMS_SQLTUNE.SQLSET_CURSOR;
BEGIN  
  OPEN sqlset_cur FOR
    SELECT value(p)
    FROM table(
      DBMS_SQLTUNE.SELECT_SQLPA_TASK('&taskname', '&STSowner','&execution_name', 'REGRESSED')) p;
      DBMS_SQLTUNE.LOAD_SQLSET(sqlset_name => '&STSname', populate_cursor => sqlset_cur);
  CLOSE sqlset_cur;
END;
/
