REM Script: monitor-external-partitions.sql
REM Use ALL_XTERNAL_TAB_PARTITIONS


col table_owner format a15
col table_name format a20
col partition_name format a20

SELECT table_owner, table_name, partition_name 
FROM all_xternal_tab_partitions;
