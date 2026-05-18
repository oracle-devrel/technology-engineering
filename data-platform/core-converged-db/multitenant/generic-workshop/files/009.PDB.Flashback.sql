-- PDB Flashback

-- Connect to ORCLPDB1 PDB, and create a local user 
sqlplus system/"Oracle_4U"@myoracledb:1521/ORCLPDB1

create user TEST_FLASHBACK identified by "Oracle_4U" default tablespace USERS temporary tablespace TEMP;
grant connect, resource to TEST_FLASHBACK;
alter user TEST_FLASHBACK quota unlimited on USERS;
exit

-- Connect to TEST_FASHBACK schema and create a table
sqlplus TEST_FLASHBACK/"Oracle_4U"@myoracledb:1521/ORCLPDB1 

create table tt (c1 number);
insert into tt values (1);
insert into tt values (2);
commit; 
exit

-- Now we create a restore point
sqlplus sys/Oracle_4U@myoracledb:1521/ORCLPDB1 as sysdba 
create restore point RP_1 guarantee flashback database; 
exit

-- Now connect to TEST_FLASHBACK schema and drop the table 
sqlplus TEST_FLASHBACK/"Oracle_4U"@myoracledb:1521/ORCLPDB1 
drop table tt;
exit

-- Now connect to the CDB and flashback the PDB to the restore point
sqlplus / as sysdba
alter pluggable database ORCLPDB1 close immediate; 
flashback pluggable database ORCLPDB1 to restore point RP_1;

show pdbs

alter pluggable database ORCLPDB1 open resetlogs;

show pdbs

-- Now connect to TEST_FLASHBACK schema and check the table is back 
sqlplus TEST_FLASHBACK/"Oracle_4U"@myoracledb:1521/ORCLPDB1
select * from tt;