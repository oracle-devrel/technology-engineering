-- this script
-- presents differences in execution plans end statistisc for 
-- queries reading data from internal and external tables

alter session set nls_language=american;
alter session set nls_territory=america;
alter session set nls_date_format='YYYY-MM-DD';
alter session set nls_timestamp_format='YYYY-MM-DD';

set autotrace on

select count(*)
from ORDERS;

select count(*)
from ORDERS_EXT;

select count(*)
from ORDER_ITEMS;

select count(*)
from ORDER_ITEMS_EXT;

