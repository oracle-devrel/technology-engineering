REM  Script: session-longops.sql
REM  Example for V$SESSION_LONGOPS


-- V$SESSION_LONGOPS displays the status of various operations that run for longer than 6 seconds (in absolute time)

SELECT opname, username, sql_fulltext, to_char(start_time,'DD-MON-YYYY HH24:MI:SS'),
(sofar/totalwork)*100 "%_complete", time_remaining, s. con_id
FROM v$session_longops s INNER JOIN v$sql sl USING (sql_id) 
WHERE time_remaining > 0;
