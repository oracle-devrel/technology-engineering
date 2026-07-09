-- Install an application in the application root

sqlplus sys/"Oracle_4U"@myoracledb:1521/sales_app_root as sysdba
set sqlprompt SALES_APP_ROOT>
select app_name, app_version, app_id, app_status,
app_implicit implicit from dba_applications;

select CON_ID, name, CON_UID, Guid from v$containers;

---- Begin the installation of application sales_app
ALTER PLUGGABLE DATABASE APPLICATION sales_app BEGIN INSTALL '1.0';
col app_name format a40
select app_name, app_version, app_id, app_status, app_implicit implicit from dba_applications;

-- Create a common user
CREATE USER sales_app_user IDENTIFIED BY "Oracle_4U" CONTAINER=ALL;
GRANT CREATE SESSION, create procedure, CREATE TABLE, unlimited tablespace TO sales_app_user;

CREATE TABLE sales_app_user.customers SHARING=METADATA
( cust_id NUMBER constraint cust_pk primary key,
cust_name varchar2(30), cust_add varchar2(30), cust_zip NUMBER
);

ALTER PLUGGABLE DATABASE APPLICATION sales_app END INSTALL '1.0';
select app_name, app_version, app_id, app_status, app_implicit implicit from dba_applications;

