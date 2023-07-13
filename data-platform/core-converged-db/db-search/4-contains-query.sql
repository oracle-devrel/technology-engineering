REM Script for 23c: 4-contains-query.sql 
REM Queries using CONTAINS

-- Query using CONTAINS with FUZZY operator

select metadata output from SEARCH_PRODUCTS 
where CONTAINS(data,'fuzzy(Los)')>0;

-- check the result in table STORES

select pysical_address from stores where store_id=10;

-- check the result in table SHIPMENTS

select delivery_address from shipments where shipment_id=976;

