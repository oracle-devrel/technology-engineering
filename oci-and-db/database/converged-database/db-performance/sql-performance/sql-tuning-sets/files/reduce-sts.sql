REM Script: reduce-sts.sql
REM Use SELECT_SQLSET and LOAD_SQLSET

-- first create a new SQL Tuning Set with create-sts.sql
-- enter values for ranking and limit criteria

DECLARE cur dbms_sqltune.sqlset_cursor; 
BEGIN 
OPEN cur FOR
     SELECT VALUE (P)
     FROM table(DBMS_SQLTUNE.SELECT_SQLSET(sqlset_name =>'&name_sts',    
            ranking_measure1 =>'ELAPSED_TIME', result_limit=>&limit)) P;
  DBMS_SQLTUNE.LOAD_SQLSET(sqlset_name => '&name_reducedsts', populate_cursor => cur);
CLOSE cur;
END;
/
