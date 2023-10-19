-- User creation at CDB and PDB level

sqlplus / as sysdba
--- Common user are created from CDB$ROOT 
--- Their name must start with "C##"
CREATE USER c##user1 IDENTIFIED BY "Oracle_4U" CONTAINER=ALL; 
GRANT CREATE SESSION TO c##user1 CONTAINER=ALL;

conn / as sysdba

CREATE USER c##user2 IDENTIFIED BY "Oracle_4U"; 
GRANT CREATE SESSION TO c##user2;

-- Check status

Conn / as sysdba

select USERNAME,ACCOUNT_STATUS,PROFILE,CREATED,DEFAULT_TABLESPACE,TEMPORARY_TABLESPACE from dba_users where username like 'C##%';

-- Create local users

set echo on
show pdbs

CONN / AS SYSDBA
ALTER SESSION SET CONTAINER = ORCLPDB1;

create tablespace data_tbs;

col FILE_NAME format a60
col TABLESPACE_NAME format a50
select tablespace_name, File_name from dba_data_files where tablespace_name='DATA_TBS';

CREATE USER orclpdb1_user_local1 IDENTIFIED BY "Oracle_4U" default tablespace DATA_TBS CONTAINER=CURRENT;

GRANT CREATE SESSION TO orclpdb1_user_local1;

CONN system/"Oracle_4U"@myoracledb:1521/orclpdb1

CREATE USER orclpdb2_user_local2 IDENTIFIED BY "Oracle_4U" default tablespace DATA_TBS;
GRANT CREATE SESSION TO orclpdb2_user_local2;

set lines 999
set pages 999
col username format a20
col profile format a15
select USER_ID,USERNAME,ACCOUNT_STATUS,DEFAULT_TABLESPACE,TEMPORARY_TABLESPACE,CREATED ,PROFILE from dba_users where username like 'ORCLPDB%';

ALTER USER orclpdb2_user_local2 QUOTA UNLIMITED ON DATA_TBS; 
ALTER USER orclpdb1_user_local1 QUOTA UNLIMITED ON DATA_TBS;

grant create table to ORCLPDB1_USER_LOCAL1; 
grant create table to ORCLPDB2_USER_LOCAL2;

CONN orclpdb1_user_local1/"Oracle_4U"@myoracledb:1521/orclpdb1

CREATE TABLE Persons (
 PersonID int,
 LastName varchar(255),
 FirstName varchar(255),
 Address varchar(255),
 City varchar(255)
);

 INSERT INTO Persons (PersonID, LastName, FirstName, Address, City)
  VALUES (1, 'Garcia', 'Pedro', 'Calle Amatista, 43', 'Madrid');

commit;

Select * from Persons;