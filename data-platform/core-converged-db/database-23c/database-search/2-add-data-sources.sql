REM Script for 23c: 2-add-data-sources.sql
REM Add two tables as data sources

-- Let's add the table SHIPMENTS and STORES as user CO

execute DBMS_SEARCH.ADD_SOURCE(index_name =>'SEARCH_PRODUCTS', source_name => 'SHIPMENTS');
execute DBMS_SEARCH.ADD_SOURCE(index_name =>'SEARCH_PRODUCTS', source_name => 'STORES');
