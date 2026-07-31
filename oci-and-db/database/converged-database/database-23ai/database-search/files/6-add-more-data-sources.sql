REM Script for 23c: 6-add-more-data-sources.sql

-- Let's add the table CUSTOMERS

execute DBMS_SEARCH.ADD_SOURCE(index_name =>'SEARCH_PRODUCTS', source_name => 'CUSTOMERS');

-- Search for fuzzy(jon)

SELECT METADATA output from SEARCH_PRODUCTS WHERE CONTAINS(data,'fuzzy(jon)')>0;

--Let's add a row to the table CUSTOMERS und search for it again.

insert into customers values (1000,'john.johnson@oracle.com','John Johnson');

SELECT METADATA output from SEARCH_PRODUCTS WHERE CONTAINS(data,'fuzzy(jon)')>0;

-- You will find the new row when you commit the change.

commit;

-- search again
SELECT METADATA output from SEARCH_PRODUCTS WHERE CONTAINS(data,'fuzzy(jon)')>0;
