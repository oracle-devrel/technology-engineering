REM Script: create-sts-from-cursorcache.sql
REM Load statements from cursor cache with SELECT_CURSOR_CACHE and LOAD_SQLSET

-- first create STS with create-sts.sql

-- enter filter criteria for parsing schema and sql text  

DECLARE
 cur dbms_sqltune.SQLSET_CURSOR;
BEGIN
 OPEN cur FOR
   SELECT VALUE(P)
   FROM dbms_sqltune.select_cursor_cache(basic_filter => 
   'parsing_schema_name = ''&schema'' and upper(sql_text) like ''SELECT%''') P;
   dbms_sqltune.load_sqlset(sqlset_name => '&stsname', sqlset_owner=>'&owner', populate_cursor => cur);
  CLOSE cur;
END;
/
