-- SYNC the changes in the application PDBs

conn sys/"Oracle_4U"@myoracledb:1521/east_app_pdb as sysdba 
set sqlprompt SALES_APP_EAST>
alter pluggable database application sales_app sync;

conn sys/"Oracle_4U"@myoracledb:1521/north_app_pdb as sysdba 
set sqlprompt SALES_APP_NORTH>
alter pluggable database application sales_app sync;
select * from sales_app_user.zip_codes;

select * from sales_app_user.products;

insert into sales_app_user.products values (2, 'prod2(north)', 111); 
insert into sales_app_user.products values (2, 'prod2(north)', 111);

ERROR at line 1:
ORA-65097: DML into a data link table is outside an application action

insert into sales_app_user.zip_codes values (2, 'USA (north)'); 
commit;

select * from sales_app_user.zip_codes;

insert into sales_app_user.customers
values ('1', 'Cust1(north)', 'USA (north) address', 2);
commit;
select * from sales_app_user.customers;

insert into sales_app_user.customers values ('1', 'Another Cust1(north)', 'USA (north) address', 2);

ERROR at line 1:
ORA-00001: unique constraint (SALES_APP_USER.CUST_PK) violated