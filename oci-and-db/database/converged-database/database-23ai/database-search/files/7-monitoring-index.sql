REM Script for 23c: 7-monitoring-index.sql

-- Query USER_INDEXES to get basic information about the created index.
col index_type format a10
col ityp_owner format a10
col table_owner format a10
col table_name format a20

select index_type, table_owner, table_name, table_type, status, ityp_owner
from user_indexes where index_name='SEARCH_PRODUCTS';

-- Query CTX_INDEX_VALUES to display values for each object used in the index. You need to have access on CTXSYS objects. 

set linesize window

select ixv_class, ixv_object, ixv_attribute, ixv_value
from ctxsys.ctx_index_values 
where ixv_index_owner='CO';
