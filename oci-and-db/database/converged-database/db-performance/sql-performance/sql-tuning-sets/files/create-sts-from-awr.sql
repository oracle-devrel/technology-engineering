REM Script: create-sts-from-awr.sql
REM Load STS from AWR with SELECT_WORKLOAD_REPOSITORY and LOAD_SQLSET

-- first create a STS with create-sts.sql
-- find snap ids with list-snapshots.sql
-- load statements in the SQL Tuning Set and enter two snap ids 
 
DECLARE
 cur dbms_sqltune.sqlset_cursor;
BEGIN
 OPEN cur FOR
SELECT VALUE(P) 
  FROM dbms_sqltune.select_workload_repository(begin_snap=>&startid, end_snap=>&endid) P; 
  dbms_sqltune.load_sqlset (sqlset_name => '&name', sqlset_owner=>'&schema', populate_cursor => cur); 
END;
/
