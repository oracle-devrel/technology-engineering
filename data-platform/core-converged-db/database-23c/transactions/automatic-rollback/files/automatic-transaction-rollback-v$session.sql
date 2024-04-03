REM  Script for 23c: automatic-transaction-rollback-v$session.sql
REM  Check transactions in V$SESSION with columns EVENT, SECONDS_IN_WAIT and BLOCKING_SESSION to analyze the locking situation. 

col event format a35
select sid, event, seconds_in_wait, blocking_session      
from v$session where  event like '%enq%';
