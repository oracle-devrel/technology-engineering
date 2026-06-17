rem Script displays some information that may be helpfull to analyze slow running RAT-Replays
rem See also MOS-Note 760402.1

set echo on
set verify off
set pagesize 200

set lines 500 trimspool on pages 60
spool debug_replay.txt

col repl_id format 9999999
col capt format 9999
col "Real_Time_Repl_Capt" format a20
col filter_set_name format a30
col default_action format a20
col synchronization format a10
col connect_time_scale format 99999 heading "CONNECT|TIME|SCALE"
col think_time_scale format 999999 heading "THINK|TIME|SCALE"
col think_time_auto_correct format  a8 heading "  THINK|   TIME|   AUTO|CORRECT"
col scale_up_multiplier format 99999 heading "SCALE|UP|MULTIPLIER"
col start_time format a18
col end_time format a18

REM Replay Parameter

select id repl, to_char(start_time,'DD-Mon HH24:MI:SS') start_time, to_char( end_time,'DD-Mon HH24:MI:SS') end_time,
     duration_secs, filter_set_namE, default_action, synchronization,
     connect_time_scale, think_time_scale, think_time_auto_correct, scale_up_multiplier
-- , think_time,  elapsed_time_diff
from dba_workload_replays
where id = (select max(id)
            from dba_workload_replays)
/

col capture_id format 9999
col replay_id format 9999
col start_time format a21
col end_time format a21
col current_time format a21
col directory_path format a38
col "% replayed" format 990.00
col status format a15
col r_dbtime_sec format 999G999G990D00
col c_dbtime_sec format 999G999G990D00
col repl_user_calls format 999G999G999G999
col capt_user_calls format 999G999G999G999
col capt_calls_total format 999G999G999G999
col c_unreplayable format 999G999G999G999
col repl_id format 99999
col capt_id format 99999
col begin_snap format 999999 heading "BEGIN|SNAP"
col end_snap format   999999 heading "END|SNAP"
col status format  a15
col "#Clients" format 99999999
col Real_Time_Repl_Capture format a17 heading "Real-Time Repl/Capt"
col DB_Time_Repl_Capture format 999G999D00 heading "% DB-Time Repl/Capt"
col "%Calls repl'd"        format 9990D00 Heading "%Calls|repl'd"
col "% Replaytime"         format 99G990D00 heading "% Replay|time"
col "% Divergences"        format 990D00
col "User Calls"           format 999G999G999G999G999
col "Replay Divergences"   format 999G999G999G999G999
col max_repl_id new_value max_repl_id heading id
col id format 9999
col repl format 9999

REM Replay Progress

select r.id repl, r.capture_id capt,
   r.status,
   -- r.name,
   r.awr_begin_snap begin_snap, r.awr_end_snap end_snap, r.num_clients "#Clients" ,
lpad(trunc((nvl(r.end_time,sysdate) - r.start_time) * (24 * 60 * 60)/3600),2,'0')  ||':'|| lpad(trunc(mod((nvl(r.end_time,sysdate) - r.start_time) * (24 * 60 * 60),3600) / 60 ),2,'0') ||':'||lpad(mod((nvl(r.end_time,sysdate) - r.start_time) * (24 * 60 * 60),60),2,'0')
|| '/' ||
lpad(trunc((nvl(c.end_time,sysdate) - c.start_time) * (24 * 60 * 60)/3600),2,'0')  ||':'|| lpad(trunc(mod((nvl(c.end_time,sysdate) - c.start_time) * (24 * 60 * 60),3600) / 60 ),2,'0') ||':'||lpad(mod((nvl(c.end_time,sysdate) - c.start_time) * (24 * 60 * 60),60),2,'0') "Real_Time_Repl_Capt" ,
   round(r.user_calls / (c.user_calls) * 100,2) "%Calls repl'd",
   round(  (nvl(r.end_time,sysdate) - r.start_time) /
           (nvl(c.end_time,sysdate) - c.start_time )* 100,3) "% Replaytime",
   r.USER_CALLS repL_user_calls, c.user_calls capt_user_calls,
   c.user_calls_total capt_calls_total,
   c.user_calls_unreplayable c_unreplayable,
   round((r.dbtime / c.dbtime * 100),2) "DB_Time_Repl_Capture"
    --, elapsed_time_diff, elapsed_time_diff  / (1000 * 1000) ela_diff_sec
from dba_workload_replays r , dba_workload_captures c
where c.id =  r.capture_id
and r.id = (select max(id) from dba_workload_replays)
/

REM Query to Obtain Information on Blocking Sessions with gv$workload_replay_thread

col inst_id format 99999
col sid format 99999
col spid format a6
col blocking_session_status format a15 heading 'BS'
col blocking_instance format 99 heading 'BI'
col blocking_session format 99999 heading 'BLKSID'
col session_type format a11
col event format a31
col file_name format a21
col file_id format 9999999999999999999
col call_counter format 9999999
col wait_for_scn format 99999999999999 heading 'WAITING FOR'
col wfscn format 99999999999999 heading 'WFSCN'
col commit_wait_scn format 99999999999999 heading 'CWSCN'
col post_commit_scn format 99999999999999 heading 'PCSCN'
col clock format 99999999999999999999 heading 'CLOCK'
col next_ticker format 999999999999999999999 heading 'NEXT TICKER'

select wrt.inst_id, wrt.sid, wrt.serial#, wrt.spid,
s.BLOCKING_SESSION_STATUS, s.BLOCKING_INSTANCE,
s.blocking_session,
wrt.session_type, wrt.event,
wrt.file_name, wrt.file_id, wrt.call_counter,
wrt.wait_for_scn,
greatest(wrt.dependent_scn, wrt.statement_scn) as wfscn,
wrt.commit_wait_scn, wrt.post_commit_scn,
wrt.clock, wrt.next_ticker
from gv$workload_replay_thread wrt, gv$session s
where wrt.sid = s.sid
and wrt.serial# = s.serial#
order by inst_id, sid
/
spool off
