-- this script demonstrates the fast lookup usage in Oracle Database
-- database release could be before 23ai 

set feedback on
set echo on
  
-- configure memmoptimize pool in container ROOT
ALTER SYSTEM SET MEMOPTIMIZE_POOL_SIZE = 500M SCOPE=SPFILE;

-- restart the database
startup force

-- check the setting

SHOW PARAMETER MEMOPTIMIZE_POOL_SIZE

pause
-- privileges for SH to monitor execution plans 
grant select on v_$session to sh;
grant select on v_$sql_plan to sh;
grant select on v_$sql_plan_statistics_all to sh;
grant select on v_$sql to sh;
grant read on v_$sql to sh;

-- connect as SH user in PDB
connect sh/&password@&pdb

-- drop table sales_tab
drop table sales_tab;

-- create table SALES_TAB
create table sh.sales_tab (
sales_id   NUMBER(6) primary key,
prod_id       NUMBER(6) not null,
cust_id       NUMBER not null,
time_id       DATE not null,
quantity_sold NUMBER(3) not null,
amount_sold   NUMBER(10,2) not null);

-- insert data
insert into sh.sales_tab (sales_id,prod_id, cust_id, time_id, quantity_sold, amount_sold)
select rownum, PROD_ID, CUST_ID, TIME_ID, QUANTITY_SOLD,  AMOUNT_SOLD from sh.sales;

select count(*) from sales_tab;

-- Now let's enable the feature for the data stored in SH.SALES_TAB.
ALTER TABLE SH.SALES_TAB MEMOPTIMIZE FOR READ;

-- gather statistics
execute dbms_stats.gather_table_stats('SH','SALES_TAB');

-- populate
execute dbms_memoptimize.populate(schema_name=>'SH',table_name=>'SALES_TAB');

pause
-- lets check with two queries
set linesize window

-- this one will use memoptimize rowstore
select * from sh.sales_tab where sales_id=5;

-- check the execution plan
select * from dbms_xplan.display_cursor();

pause
-- this one won't work
select * from sh.sales_tab where sales_id<2;

-- check the execution plan
select * from dbms_xplan.display_cursor();
