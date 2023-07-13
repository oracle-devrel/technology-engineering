REM Script for 23c: 3-review-virtual-document.sql
REM Review the virtual document

-- GET_DOCUMENT returns a virtual indexed document that is created after populating it with the two tables. 

set long 1000 longc 500
select DBMS_SEARCH.GET_DOCUMENT (INDEX_NAME=>'SEARCH_PRODUCTS', DOCUMENT_METADATA=>METADATA) output 
from SEARCH_PRODUCTS;

