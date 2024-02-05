-- this script
-- presents differences in execution plans end statistisc for 
-- queries reading data from internal and external partitions

alter session set nls_language=american;
alter session set nls_territory=america;
alter session set nls_date_format='YYYY-MM-DD';
alter session set nls_timestamp_format='YYYY-MM-DD';

set autotrace on

select count(*)
from ORDERS_HPART
where order_id < 1500000;

select count(*)
from ORDERS_HPART
where order_id >= 1500000;

select count(*)
from ORDER_ITEMS_HPART
where order_id < 1500000;

select count(*)
from ORDER_ITEMS_HPART
where order_id >= 1500000;

