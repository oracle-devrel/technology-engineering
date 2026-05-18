-- DBA_WORKLOAD_REPLAY_DIVERGENCE displays information about data/error divergence for a user call that has been replayed.

set lines 160 pages 100  trimspool on 
col num format   999G999G999 Heading "# of Errors"
col EXPECTED_ERROR# heading "Expected|Error#"
col OBSERVED_ERROR# heading   "Observed|Error#"
col EXPECTED_ERROR_MESSAGE format a22 word wrap
col OBSERVED_ERROR_MESSAGE format a40 word wrap
col E heading "Error|Div" format a5
col Q heading "Query|Div" format a5
col D heading "DML|Div"  format a3 
col T heading "Thread|Error" format a6

break on report 
compute sum of Anzahl on report


select count(*) num,
   EXPECTED_ERROR#,
   OBSERVED_ERROR#,
   lpad(IS_ERROR_DIVERGENCE,4,' ') E,
   lpad(IS_QUERY_DATA_DIVERGENCE,3,' ') Q,
   lpad(IS_DML_DATA_DIVERGENCE,1,' ') D, 
   lpad(IS_THREAD_FAILURE,6,' ') T,
   EXPECTED_ERROR_MESSAGE,
   OBSERVED_ERROR_MESSAGE
from dba_workload_replay_divergence
group by EXPECTED_ERROR#, OBSERVED_ERROR#, IS_ERROR_DIVERGENCE,
   IS_QUERY_DATA_DIVERGENCE, IS_DML_DATA_DIVERGENCE, IS_THREAD_FAILURE,
   EXPECTED_ERROR_MESSAGE, OBSERVED_ERROR_MESSAGE
order by 1 desc,2,3,4,5,6
/
