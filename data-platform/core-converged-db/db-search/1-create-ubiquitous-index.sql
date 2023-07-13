REM Script for 23c: 1-create-ubiquitous-index.sql
REM Create an ubiquitous index   
 
-- prereq: install Oracle Customer order sample schema from https://github.com/oracle-samples/db-sample-schemas/tree/main/customer_orders
-- create an ubiquitous index with the name SEARCH_PRODUCTS

execute DBMS_SEARCH.CREATE_INDEX(index_name=>'SEARCH_PRODUCTS');

-- it creates the infrastructure for Oracle Text including a table SEARCH_PRODUCTS with two JSON columns DATA and METADATA.

desc SEARCH_PRODUCTS

-- if you need to drop the index first use 
-- execute DBMS_SEARCH.DROP_INDEX('SEARCH_PRODUCTS');
