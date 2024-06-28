REM Script: loadplans-for-regressed.sql
REM Load original execution plans 

-- enter STS name from create-sts-regressed.sql
DECLARE
  my_plans PLS_INTEGER;
BEGIN
  my_plans := DBMS_SPM.LOAD_PLANS_FROM_SQLSET(sqlset_name => '&STSname');
END;
/
