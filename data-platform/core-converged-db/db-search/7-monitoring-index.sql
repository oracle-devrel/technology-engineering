REM Script for 23c: 7-monitoring-index.sql

-- Query USER_INDEXES to get basic information about the created index.
col table_name format a10
col ityp_owner format a10
col table_owner format a10
  
select index_type, table_owner, table_name, table_type, status, ityp_owner
from user_indexes where index_name='SEARCH_PRODUCTS';

-- Query CTX_INDEX_VALUES to display values for each object used in the index. 
-- you need to have acces to CTXSYS user objects 

col IXV_CLASS  format a10
col IXV_OBJECT format a20
col IXV_ATTRIBUTE format a30
col IXV_VALUE format a30
  
select ixv_class, ixv_object, ixv_attribute, ixv_value
from ctxsys.CTX_INDEX_VALUES where ixv_index_owner='CO';
