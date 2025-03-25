-- Create a refreshable PDB from an existing PDB

-- First we connect to the CDB$ROOT, and create a common user
sqlplus / as sysdba

--- Note the C## prefix in the username (common user), and the "container=ALL" clause in the grant commands
create user C##_ADMIN_PDB identified by "Oracle_4U" container=ALL;
grant CREATE PLUGGABLE DATABASE to C##_ADMIN_PDB container=ALL;
grant create session to C##_ADMIN_PDB container=ALL;

-- Then we create a database link connected to that user. In our case, the database link is a loopback, since we only have one CDB
create database link DBL_ORCLCDB connect to C##_ADMIN_PDB identified by "Oracle_4U" using 'myoracledb:1521/ORCLCDB';

--- Check that the database link is working fine 
select * from dual@DBL_ORCLCDB;

create pluggable database PDB1_REFRESH from PDB1@DBL_ORCLCDB refresh mode manual;

--- A refreshable PDB can only be opened in read only mode. If you try to open it in read write, it will be opened in read only anyway.

alter pluggable database PDB1_REFRESH open read only; 

show pdbs

-- Create some new data in the source PDB
--- Connect to PDB1 and create a local user with a table 

sqlplus system/Oracle_4U@myoracledb:1521/PDB1

create tablespace USERS datafile size 50M;
create user TEST_REFRESH identified by "Oracle_4U" temporary tablespace TEMP default tablespace USERS;
grant connect, resource to TEST_REFRESH;
alter user TEST_REFRESH quota unlimited on USERS;

--- Connect to TEST_REFRESH schema and create a new table
sqlplus TEST_REFRESH/Oracle_4U@myoracledb:1521/PDB1 
create table TT (c1 number);
insert into TT values (999);
commit;

--- Connect to PDB1_REFRESH PDB as system, and check
sqlplus system/Oracle_4U@myoracledb:1521/PDB1_REFRESH
select username from dba_users where username = 'TEST_REFRESH';
-- We need to refresh this PDB

-- Then refresh the refreshable clone, and check the new data is there
sqlplus / as sysdba
alter pluggable database PDB1_REFRESH close immediate; 
alter pluggable database PDB1_REFRESH refresh;
show pdbs

alter pluggable database PDB1_REFRESH open read only;

sqlplus TEST_REFRESH/Oracle_4U@myoracledb:1521/PDB1_REFRESH 
select * from tt;