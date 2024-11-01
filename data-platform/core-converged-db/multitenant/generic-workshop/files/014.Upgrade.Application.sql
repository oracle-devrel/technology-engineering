-- Upgrade the application

conn sys/"Oracle_4U"@myoracledb:1521/sales_app_root as sysdba 
set sqlprompt SALES_APP_ROOT>

ALTER PLUGGABLE DATABASE APPLICATION sales_app BEGIN UPGRADE '1.0' TO '2.0';

alter user SALES_APP_USER quota 50m on system;

select app_name, app_version, app_id, app_status, app_implicit implicit
from dba_applications
where app_name = 'SALES_APP';

--- Create an "extended data" table
create table SALES_APP_USER.zip_codes
sharing=extended data
(zip_code number, country varchar2(20));

insert into sales_app_user.zip_codes values (1, 'Spain(root)'); 
commit;

-- Create a data shared table
create table SALES_APP_USER.products sharing=data
(prod_id number, prod_name varchar2(20), price number);

insert into SALES_APP_USER.products values (1, 'prod1 (root)', 111); 
commit;

ALTER PLUGGABLE DATABASE APPLICATION sales_app END UPGRADE TO '2.0';

