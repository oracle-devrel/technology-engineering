-- Add local objects in the applications PDBs

create table sales_app_user.local_tbl(id number); 
insert into sales_app_user.local_tbl values (1); 
commit;
select * from sales_app_user.local_tbl;