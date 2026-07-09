REM Script for 23c: 5-json-textcontains-query.sql 
REM Query using JSON_TEXTCONTAINS

-- JSON_TEXTCONTAINS checks if a specified string exists in JSON property values or not.  
select metadata from SEARCH_PRODUCTS
where JSON_TEXTCONTAINS(data,'$.CO.STORES.PHYSICAL_ADDRESS','fuzzy(LOS)');
