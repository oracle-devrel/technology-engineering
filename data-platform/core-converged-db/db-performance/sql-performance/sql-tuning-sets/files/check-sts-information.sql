REM Script: check-sts-information.sql
REM Use view ALL_SQLSET
 
-- check all sts 

col name format a20
col owner format a20

select name, owner, created, statement_count 
from all_sqlset
where owner= '&owner';
