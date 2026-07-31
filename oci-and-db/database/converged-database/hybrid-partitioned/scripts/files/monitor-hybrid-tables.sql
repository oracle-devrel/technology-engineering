REM Script: monitor-hybrid-tables.sql
REM Use ALL_TABLES

col table_name format a20
col owner format a20
col hybrid format a6

SELECT table_name, owner, hybrid
FROM all_tables 
where hybrid='YES'; 
