-- Check and use the application container

conn sys/"Oracle_4U"@myoracledb:1521/east_app_pdb as sysdba 
set sqlprompt SALES_APP_EAST>
select * from sales_app_user.zip_codes;
select * from sales_app_user.customers;
select * from sales_app_user.products;

insert into sales_app_user.zip_codes values (2, 'USA (east)'); 
commit;
select * from sales_app_user.zip_codes;

insert into sales_app_user.customers
values ('1', 'Cust1(east)', 'USA (east) address', 2);
commit;
select * from sales_app_user.customers;

-- A select against "north_app_pdb" local table fails
select * from sales_app_user.local_tbl;

-- we can create our own private table here
create table sales_app_user.local_tbl(id number); 
insert into sales_app_user.local_tbl values (2); 
commit;
select * from sales_app_user.local_tbl;

--- Now let's run some queries from the application root 
conn sys/"Oracle_4U"@myoracledb:1521/sales_app_root as sysdba 
set sqlprompt SALES_APP_ROOT>

--- Let's run a select * from sales_app_user.customers;
select * from sales_app_user.customers;

--- execute a "show pdbs" command to get the CON_ID of the application PDB 
show pdbs

--- Now we use the container clause to get a consolidated view of the customers table accross the application PDB
select * from containers(sales_app_user.customers)
where CON_ID in (5,6); -- 6,7 are the CON_ID of the application PDB

ALTER PLUGGABLE DATABASE APPLICATION sales_app begin UPGRADE '2.0' TO '2.1';
ALTER TABLE sales_app_user.customers ENABLE containers_default;
ALTER PLUGGABLE DATABASE APPLICATION sales_app end UPGRADE TO '2.1';
conn sys/"Oracle_4U"@myoracledb:1521/north_app_pdb as sysdba 
set sqlprompt NORTH_APP_PDB>
ALTER PLUGGABLE DATABASE APPLICATION sales_app SYNC;
conn sys/"Oracle_4U"@myoracledb:1521/east_app_pdb as sysdba 
ALTER PLUGGABLE DATABASE APPLICATION sales_app SYNC;
conn sys/"Oracle_4U"@myoracledb:1521/sales_app_root as sysdba 
set sqlprompt SALES_APP_ROOT>
show pdbs --- (to get the CON_ID)

select * from sales_app_user.customers;

