set lines 180 pages 100  trimspool on 
col num format   999G999G999
col EXPECTED_ERROR_MESSAGE format a32 trunc
col OBSERVED_ERROR_MESSAGE format a32 trunc
col E heading Error_div format a7
col Q heading Query format a5
col D heading DML format a3
col T heading Thread_Error format a13

col spool_file new_value spool_file

select 'divergences' || '_by_sql_id.log' spool_file
from dual;


break on sql_id skip 2 dup
compute sum of Anzahl on sql_id 

spool &spool_file
select sql_id,  count(*) num,
   EXPECTED_ERROR#,
   OBSERVED_ERROR#,
   lpad(IS_ERROR_DIVERGENCE,4,' ') E,
   lpad(IS_QUERY_DATA_DIVERGENCE,3,' ') Q,
   lpad(IS_DML_DATA_DIVERGENCE,1,' ') D, 
   lpad(IS_THREAD_FAILURE,6,' ') T,
   EXPECTED_ERROR_MESSAGE,
   OBSERVED_ERROR_MESSAGE
from dba_workload_replay_divergence
group by sql_id,  EXPECTED_ERROR#, OBSERVED_ERROR#, IS_ERROR_DIVERGENCE,
   IS_QUERY_DATA_DIVERGENCE, IS_DML_DATA_DIVERGENCE, IS_THREAD_FAILURE,
   EXPECTED_ERROR_MESSAGE, OBSERVED_ERROR_MESSAGE
order by 3, 2 desc,1,4,5,6,7
/

spool off 
select sql_id,  count(*) Anzahl,
   EXPECTED_ERROR#,
   OBSERVED_ERROR#,
   lpad(IS_ERROR_DIVERGENCE,4,' ') E,
   lpad(IS_QUERY_DATA_DIVERGENCE,3,' ') Q,
   lpad(IS_DML_DATA_DIVERGENCE,1,' ') D,
   lpad(IS_THREAD_FAILURE,6,' ') T,
   EXPECTED_ERROR_MESSAGE,
   OBSERVED_ERROR_MESSAGE
from dba_workload_replay_divergence
where EXPECTED_ERROR_MESSAGE is not null or OBSERVED_ERROR_MESSAGE is not null
group by sql_id,  EXPECTED_ERROR#, OBSERVED_ERROR#, IS_ERROR_DIVERGENCE,
   IS_QUERY_DATA_DIVERGENCE, IS_DML_DATA_DIVERGENCE, IS_THREAD_FAILURE,
   EXPECTED_ERROR_MESSAGE, OBSERVED_ERROR_MESSAGE
order by 3, 2 desc,1,4,5,6,7
/

