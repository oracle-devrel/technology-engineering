REM  Script: find-sqlid.sql
REM  Find SQL id with V$SQL_MONITOR

-- display text, sql id and cpu time
SELECT distinct s.sql_text, m.sql_id, m.cpu_time
FROM v$sql_monitor m INNER JOIN v$sql s ON s.sql_id=m.sql_id 
ORDER BY m.cpu_time;
