REM Script: monitor-external-part-tables.sql
REM Use ALL_EXTERNAL_TAB_PARTITIONS


col table_owner format a15
col table_name format a20
col partition_name format a20

SELECT table_owner, table_name, partition_name 
FROM all_xternal_tab_partitions;
