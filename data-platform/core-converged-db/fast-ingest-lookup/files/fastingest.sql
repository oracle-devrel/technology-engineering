set feedback on
set echo on
-- use 23ai environment

-- in container ROOT as privileged user
-- configure memoptimize_write_area_size
alter system set memoptimize_write_area_size=300M scope=spfile;

-- restart the database
startup force 

-- check parameters
show parameter memoptimize

-- connect to the pdb
-- change session parameter

alter session set container=&pdb;
pause

-- change memoptimize_writes parameter 
alter session set memoptimize_writes=on;

drop table sh.sales_write_tab;

-- create table with memoptimize for write attribute
create table sh.sales_write_tab (
sales_id      NUMBER(6) primary key,
prod_id       NUMBER(6) not null,
cust_id       NUMBER not null,
time_id       DATE not null,
quantity_sold NUMBER(3) not null,
amount_sold   NUMBER(10,2) not null)
segment creation immediate
memoptimize for write;

pause
-- display information about fast ingest data in the large pool
select * from v$memoptimize_write_area;

-- insert data and select
insert into sh.sales_write_tab
(sales_id, prod_id, cust_id, time_id, quantity_sold, amount_sold)
 select rownum, PROD_ID, CUST_ID, TIME_ID, QUANTITY_SOLD, AMOUNT_SOLD from sh.sales;

-- not all data is flushed yet
select count(*) from  sh.sales_write_tab;

-- display information about fast ingest data in the large pool
select * from v$memoptimize_write_area;

pause
-- flush all the fast ingest data from the large pool to disk
exec dbms_memoptimize.write_end;

pause
-- display information about fast ingest data in the large pool
select * from v$memoptimize_write_area;

-- finally all data is flushed
select count(*) from sh.sales_write_tab;

pause
-- demonstrate Lob usage
drop table sh.test_sf;

create table sh.test_sf (
id       number primary key,
test_col CLOB)
segment creation immediate
LOB (test_col) STORE AS SECUREFILE(
tablespace USERS
ENABLE STORAGE IN ROW
NOCOMPRESS
CACHE)
memoptimize for write;

pause

column table_name format a30
-- query all_tables 
select table_name, memoptimize_read memread, memoptimize_write memwrite  
from all_tables where owner='SH';
