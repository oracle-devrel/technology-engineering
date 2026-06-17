-- Create a PDB as Application Container !!!

create pluggable database APPCONT as application container from PDB1 keystore identified by "YOURPASSWORD";

SQL> create pluggable database APPCONT as application container from PDB1 keystore identified by "YOURPASSWORD";

Pluggable database created.

SQL>
SQL>
SQL>
SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 PDB1 			  READ WRITE NO
	 4 APPCONT			  MOUNTED
SQL> alter pluggable database APPCONT open;

Pluggable database altered.

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 PDB1 			  READ WRITE NO
	 4 APPCONT			  READ WRITE NO
SQL>

SQL> col name format a30
SQL> select CON_ID, NAME, OPEN_MODE, APPLICATION_ROOT from v$pdbs;

    CON_ID NAME 			  OPEN_MODE  APP
---------- ------------------------------ ---------- ---
	 2 PDB$SEED			  READ ONLY  NO
	 3 PDB1 			  READ WRITE NO
	 4 APPCONT			  READ WRITE YES

--- Inside the Application Container, create two Application PDB !!!

sqlplus / as sysdba
alter session set container=APPCONT;

CREATE PLUGGABLE DATABASE apppdb1 ADMIN USER pdb_admin IDENTIFIED BY "YOURPASSWORD" keystore identified by "YOURPASSWORD";
CREATE PLUGGABLE DATABASE apppdb2 ADMIN USER pdb_admin IDENTIFIED BY "YOURPASSWORD"keystore identified by "YOURPASSWORD";

SQL> CREATE PLUGGABLE DATABASE apppdb1 ADMIN USER pdb_admin IDENTIFIED BY "YOURPASSWORD";

Pluggable database created.

SQL> CREATE PLUGGABLE DATABASE apppdb2 ADMIN USER pdb_admin IDENTIFIED BY "YOURPASSWORD";

Pluggable database created.

SQL>
SQL>
SQL>
SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 4 APPCONT			  READ WRITE NO
	 5 APPPDB1			  MOUNTED
	 6 APPPDB2			  MOUNTED
SQL> alter pluggable database apppdb1 open;

Pluggable database altered.

SQL> alter pluggable database apppdb2 open;

Pluggable database altered.

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 4 APPCONT			  READ WRITE NO
	 5 APPPDB1			  READ WRITE NO
	 6 APPPDB2			  READ WRITE NO
SQL>

SQL> col name format a30
SQL> r
  1* select NAME, APPLICATION_ROOT, APPLICATION_PDB from v$pdbs

NAME			       APP APP
------------------------------ --- ---
PDB$SEED		       NO  NO
PDB1			       NO  NO
APPCONT 		       YES NO
APPPDB1 		       NO  YES
APPPDB2 		       NO  YES

SQL>

sqlplus sys/"YOURPASSWORD"@dbcn01:1521/apppdb1.skynet.oraclevcn.com as sysdba

ADMINISTER KEY MANAGEMENT SET KEY FORCE KEYSTORE IDENTIFIED BY "YOURPASSWORD" WITH BACKUP;

sqlplus sys/"YOURPASSWORD"@dbcn01:1521/apppdb2.skynet.oraclevcn.com as sysdba

ADMINISTER KEY MANAGEMENT SET KEY FORCE KEYSTORE IDENTIFIED BY "YOURPASSWORD" WITH BACKUP;


--- Inside the App Container, create a new schema:

sqlplus sys/"YOURPASSWORD"@dbcn01:1521/appcont.skynet.oraclevcn.com as sysdba
create user APPUSER identified by "YOURPASSWORD" default tablespace USERS temporary tablespace TEMP;
grant connect, resource to APPUSER;
alter user APPUSER quota unlimited on USERS;
grant create view to APPUSER;
grant create synonym to APPUSER;
grant dba to appuser;

--- This schema is a COMMON USER, because it was created in an Application Container !!!
SQL> col username format a30
SQL> r
  1* select username, common from dba_users where username = 'APPUSER'

USERNAME		       COM
------------------------------ ---
APPUSER 		       YES


--- In this schema, create tables, views and procedures !!!

sqlplus APPUSER/"YOURPASSWORD"@dbcn01:1521/appcont.skynet.oraclevcn.com

--- Fact table, each APPPDB will have its own data inside, and there is no data in it from APPCONT !!!

create table FACT_TABLE
(
   C1 number not null,
   C2 VARCHAR2(20),
   C3 varchar2(1000),
   ID_DIM_COMUN number,
   ID_DIM_SHARED number
  );
  
alter table FACT_TABLE add constraint PK1 primary key (C1);

--- This is a common dimension table, both the structure and the data belong to APPCONT, and are not modificable from the APPPDB !!!

create table DIM_COMUN
(
ID_DIM number not null,
DESC_DIM varchar2(200)
);

alter table DIM_COMUN add constraint PK2 primary key (ID_DIM);

insert into DIM_COMUN (id_dim, desc_dim) values (1,'DIMENSION COMUN 1');
insert into DIM_COMUN (id_dim, desc_dim) values (2,'DIMENSION COMUN  2');
insert into DIM_COMUN (id_dim, desc_dim) values (3,'DIMENSION COMUN  3');
insert into DIM_COMUN (id_dim, desc_dim) values (4,'DIMENSION COMUN  4');
commit;


--- Dimension table particular to each APPPDB, with data from APPCONT. Each APPPDB can add its own data !!!

create table DIM_SHARED
(
ID_DIM number not null,
DESC_DIM varchar2(200)
);

alter table DIM_SHARED add constraint PK3 primary key (ID_DIM);

insert into DIM_SHARED (id_dim, desc_dim) values (1,'DIMENSION SHARED-APPCONT 1');
insert into DIM_SHARED (id_dim, desc_dim) values (2,'DIMENSION SHARED-APPCONT  2');
insert into DIM_SHARED (id_dim, desc_dim) values (3,'DIMENSION SHARED-APPCONT  3');
insert into DIM_SHARED (id_dim, desc_dim) values (4,'DIMENSION SHARED-APPCONT  4');
commit;

--- View on the fact table !!!

create or replace view V_HECHOS
as
select 
	FACT_TABLE.C1 as FACT_C1,
	FACT_TABLE.C2 as FACT_C2,
	DIM_COMUN.desc_dim as DIMCOMUN,
	DIM_SHARED.desc_dim as DIMSHARED
from FACT_TABLE, DIM_COMUN, DIM_SHARED
where FACT_TABLE.ID_DIM_COMUN = DIM_COMUN.ID_DIM
and FACT_TABLE.ID_DIM_SHARED = DIM_SHARED.ID_DIM;

--- Create a procedure !!!!

create or replace procedure PC_INS_FACT_TABLE (
	C1 in FACT_TABLE.C1%TYPE,
	C2 in FACT_TABLE.C2%TYPE,
	ID_DIM_COMUN in FACT_TABLE.ID_DIM_COMUN%TYPE,
	ID_DIM_SHARED in FACT_TABLE.ID_DIM_SHARED%TYPE)
AS
BEGIN
	insert into FACT_TABLE (c1,c2,ID_DIM_COMUN,ID_DIM_SHARED) values (c1,c2,ID_DIM_COMUN,ID_DIM_SHARED);
	commit;
EXCEPTION
	WHEN OTHERS THEN
		rollback;
		RAISE;
END PC_INS_FACT_TABLE;
/


SQL> select object_name, object_type, namespace from user_objects;

OBJECT_NAME		       OBJECT_TYPE	     NAMESPACE
------------------------------ -------------------- ----------
FACT_TABLE		       TABLE			     1
PK1			       INDEX			     4
DIM_COMUN		       TABLE			     1
PK2			       INDEX			     4
DIM_SHARED		       TABLE			     1
PK3			       INDEX			     4
V_HECHOS		       VIEW			     1
PC_INS_FACT_TABLE	       PROCEDURE		     1

8 rows selected.


sqlplus system/"YOURPASSWORD"@dbcn01:1521/appcont.skynet.oraclevcn.com

alter pluggable database application MYAPP BEGIN INSTALL '1.0';

---- Now we publish an application to the APPPDB !!!
--- This must be done from APPCONT !!!

-- This procedure sets a local user as an application common user in an application container.
exec dbms_pdb.set_user_explicit ('APPUSER')

--- This table can be modified only from APPCONT !!!
exec dbms_pdb.set_data_linked (schema_name => 'APPUSER',object_name=>'DIM_COMUN',namespace=>1)

--- extended Data linked => each APPPDB might add its own data !!!

exec dbms_pdb.set_ext_data_linked (schema_name => 'APPUSER',object_name=>'DIM_SHARED',namespace=>1) 
exec dbms_pdb.set_ext_data_linked (schema_name => 'APPUSER',object_name=>'V_HECHOS',namespace=>1) 
exec dbms_pdb.set_metadata_linked (schema_name => 'APPUSER',object_name=>'PC_INS_FACT_TABLE',namespace=>1) 
	
alter pluggable database application MYAPP END INSTALL '1.0';


---- Now sync the APPPDB with APPCONT !!!

sqlplus / as sysdba
alter session set container=APPPDB1;

--- First create APPUSER schema !!!

create bigfile tablespace USERS datafile size 1G;
create user APPUSER identified by "YOURPASSWORD" default tablespace USERS temporary tablespace TEMP;
grant connect, resource to APPUSER;
alter user APPUSER quota unlimited on USERS;
grant create view to APPUSER;
grant create synonym to APPUSER;

--- Then create the schema !!!

sqlplus appuser/"YOURPASSWORD"@dbcn01:1521/apppdb1.skynet.oraclevcn.com
create table FACT_TABLE
(
   C1 number not null,
   C2 VARCHAR2(20),
   C3 varchar2(1000),
   ID_DIM_COMUN number,
   ID_DIM_SHARED number
  );
  
alter table FACT_TABLE add constraint PK1 primary key (C1);

create table DIM_COMUN
(
ID_DIM number not null,
DESC_DIM varchar2(200)
);

alter table DIM_COMUN add constraint PK2 primary key (ID_DIM);

create table DIM_SHARED
(
ID_DIM number not null,
DESC_DIM varchar2(200)
);

alter table DIM_SHARED add constraint PK3 primary key (ID_DIM);

create or replace view V_HECHOS
as
select 
	FACT_TABLE.C1 as FACT_C1,
	FACT_TABLE.C2 as FACT_C2,
	DIM_COMUN.desc_dim as DIMCOMUN,
	DIM_SHARED.desc_dim as DIMSHARED
from FACT_TABLE, DIM_COMUN, DIM_SHARED
where FACT_TABLE.ID_DIM_COMUN = DIM_COMUN.ID_DIM
and FACT_TABLE.ID_DIM_SHARED = DIM_SHARED.ID_DIM;

create or replace procedure PC_INS_FACT_TABLE (
	C1 in FACT_TABLE.C1%TYPE,
	C2 in FACT_TABLE.C2%TYPE,
	ID_DIM_COMUN in FACT_TABLE.ID_DIM_COMUN%TYPE,
	ID_DIM_SHARED in FACT_TABLE.ID_DIM_SHARED%TYPE)
AS
BEGIN
	insert into FACT_TABLE (c1,c2,ID_DIM_COMUN,ID_DIM_SHARED) values (c1,c2,ID_DIM_COMUN,ID_DIM_SHARED);
	commit;
EXCEPTION
	WHEN OTHERS THEN
		rollback;
		RAISE;
END PC_INS_FACT_TABLE;
/

sqlplus / as sysdba
alter session set container=APPPDB1;
ALTER PLUGGABLE DATABASE APPLICATION MYAPP SYNC;

SQL> ALTER PLUGGABLE DATABASE APPLICATION MYAPP SYNC;

Pluggable database altered.


COLUMN app_name FORMAT A20
COLUMN app_version FORMAT A10

SELECT app_name,
       app_version,
       app_status
FROM   dba_applications
WHERE  app_name = 'MYAPP';

APP_NAME	     APP_VERSIO APP_STATUS
-------------------- ---------- ------------
MYAPP		     1.0	NORMAL

---- From APPPDB1: 

---- We can query DIM_COMUN, but not run DML:

sqlplus appuser/"YOURPASSWORD"@dbcn01:1521/apppdb1.skynet.oraclevcn.com
SQL> delete dim_comun;
delete dim_comun
       *
ERROR at line 1:
ORA-65097: DML into a data link table is outside an application action


SQL> insert into dim_comun values (5,'DDDD');
insert into dim_comun values (5,'DDDD')
            *
ERROR at line 1:
ORA-65097: DML into a data link table is outside an application action

---- We can query DIM_SHARED, and also add data !!!

SQL> insert into dim_shared values (1,'CCCP');
insert into dim_shared values (1,'CCCP')
*
ERROR at line 1:
ORA-00001: unique constraint (APPUSER.PK3) violated


SQL> insert into dim_shared values (5,'CCCP');

1 row created.

SQL> commit;

Commit complete.

insert into dim_shared values (6,'Valor insertado en APPPDB1');
commit;

SQL> select * from dim_shared where id_dim = 1;

    ID_DIM
----------
DESC_DIM
--------------------------------------------------------------------------------
	 1
DIMENSION SHARED-APPCONT 1



SQL> delete dim_shared where id_dim = 1;

0 rows deleted.

SQL>

update DIM_SHARED set desc_dim = 'CCCP' where id_dim = 1;

SQL> update DIM_SHARED set desc_dim = 'CCCP' where id_dim = 1;

0 rows updated.

delete DIM_SHARED where id_dim = 5;

SQL> delete DIM_SHARED where id_dim = 5;

1 row deleted.

SQL> commit;

Commit complete.

---- Use the procedure !!!

BEGIN
PC_INS_FACT_TABLE(
C1=> 1,
C2=> 'Desde APPPDB1',
ID_DIM_COMUN => 1,
ID_DIM_SHARED => 1);
END;
/

PL/SQL procedure successfully completed.

SQL>
SQL> select * from fact_table;

	C1 C2
---------- --------------------
C3
--------------------------------------------------------------------------------
ID_DIM_COMUN ID_DIM_SHARED
------------ -------------
	 1 Desde APPPDB1

	   1		 1

--- As the procedure lacks a C3 parameter, try to create your own version of the procedure in APPPDB1:

create or replace procedure PC_INS_FACT_TABLE (
	C1 in FACT_TABLE.C1%TYPE,
	C2 in FACT_TABLE.C2%TYPE,
	ID_DIM_COMUN in FACT_TABLE.ID_DIM_COMUN%TYPE,
	ID_DIM_SHARED in FACT_TABLE.ID_DIM_SHARED%TYPE)
AS
BEGIN
	insert into FACT_TABLE (c1,c2,c3,ID_DIM_COMUN,ID_DIM_SHARED) values (c1,c2,'Esto es C3',ID_DIM_COMUN,ID_DIM_SHARED);
	commit;
EXCEPTION
	WHEN OTHERS THEN
		rollback;
		RAISE;
END PC_INS_FACT_TABLE;
/

*
ERROR at line 1:
ORA-65274: operation not allowed from outside an application action

--- Cannot compile, because the procedure is owned by APPCONT !!!

--- Let's try to overload it !!!

create or replace procedure PC_INS_FACT_TABLE (
	C1 in FACT_TABLE.C1%TYPE,
	C2 in FACT_TABLE.C2%TYPE,
	C3 in FACT_TABLE.C3%TYPE,
	ID_DIM_COMUN in FACT_TABLE.ID_DIM_COMUN%TYPE,
	ID_DIM_SHARED in FACT_TABLE.ID_DIM_SHARED%TYPE)
AS
BEGIN
	insert into FACT_TABLE (c1,c2,c3,ID_DIM_COMUN,ID_DIM_SHARED) values (c1,c2,'Esto es C3',ID_DIM_COMUN,ID_DIM_SHARED);
	commit;
EXCEPTION
	WHEN OTHERS THEN
		rollback;
		RAISE;
END PC_INS_FACT_TABLE;
/

create or replace procedure PC_INS_FACT_TABLE (
*
ERROR at line 1:
ORA-65274: operation not allowed from outside an application action


--- With the view !!!

select * from V_HECHOS;

   FACT_C1 FACT_C2
---------- --------------------
DIMCOMUN
--------------------------------------------------------------------------------
DIMSHARED
--------------------------------------------------------------------------------
	 1 Desde APPPDB1
DIMENSION COMUN 1
DIMENSION SHARED-APPCONT 1

--- Try to compile the view !!!

create or replace view V_HECHOS
as
select 
	FACT_TABLE.C1 as FACT_C1,
	FACT_TABLE.C2 as FACT_C2,
	FACT_TABLE.C3 as FACT_C3,
	DIM_COMUN.desc_dim as DIMCOMUN,
	DIM_SHARED.desc_dim as DIMSHARED
from FACT_TABLE, DIM_COMUN, DIM_SHARED
where FACT_TABLE.ID_DIM_COMUN = DIM_COMUN.ID_DIM
and FACT_TABLE.ID_DIM_SHARED = DIM_SHARED.ID_DIM;

     *
ERROR at line 9:
ORA-65274: operation not allowed from outside an application action

create or replace view V_HECHOS2
as
select 
	FACT_TABLE.C1 as FACT_C1,
	FACT_TABLE.C2 as FACT_C2,
	FACT_TABLE.C3 as FACT_C3,
	DIM_COMUN.desc_dim as DIMCOMUN,
	DIM_SHARED.desc_dim as DIMSHARED
from FACT_TABLE, DIM_COMUN, DIM_SHARED
where FACT_TABLE.ID_DIM_COMUN = DIM_COMUN.ID_DIM
and FACT_TABLE.ID_DIM_SHARED = DIM_SHARED.ID_DIM;

SQL> select * from v_hechos2;

   FACT_C1 FACT_C2
---------- --------------------
FACT_C3
--------------------------------------------------------------------------------
DIMCOMUN
--------------------------------------------------------------------------------
DIMSHARED
--------------------------------------------------------------------------------
	 1 Desde APPPDB1

DIMENSION COMUN 1
DIMENSION SHARED-APPCONT 1

create synonym V_HECHOS for V_HECHOS2;

--- This fails because synonyms and views belong to the same namespace !!!

--- Now we configure APPPDB2 !!!

sqlplus / as sysdba
alter session set container=APPPDB2;

--- Create APPUSER !!!

create bigfile tablespace USERS datafile size 1G;
create user APPUSER identified by "YOURPASSWORD" default tablespace USERS temporary tablespace TEMP;
grant connect, resource to APPUSER;
alter user APPUSER quota unlimited on USERS;
grant create view to APPUSER;
grant create synonym to APPUSER;

--- Create the schema !!!

sqlplus appuser/"YOURPASSWORD"@dbcn01:1521/apppdb2.skynet.oraclevcn.com
create table FACT_TABLE
(
   C1 number not null,
   C2 VARCHAR2(20),
   C3 varchar2(1000),
   ID_DIM_COMUN number,
   ID_DIM_SHARED number
  );
  
alter table FACT_TABLE add constraint PK1 primary key (C1);

create table DIM_COMUN
(
ID_DIM number not null,
DESC_DIM varchar2(200)
);

alter table DIM_COMUN add constraint PK2 primary key (ID_DIM);

create table DIM_SHARED
(
ID_DIM number not null,
DESC_DIM varchar2(200)
);

alter table DIM_SHARED add constraint PK3 primary key (ID_DIM);

create or replace view V_HECHOS
as
select 
	FACT_TABLE.C1 as FACT_C1,
	FACT_TABLE.C2 as FACT_C2,
	DIM_COMUN.desc_dim as DIMCOMUN,
	DIM_SHARED.desc_dim as DIMSHARED
from FACT_TABLE, DIM_COMUN, DIM_SHARED
where FACT_TABLE.ID_DIM_COMUN = DIM_COMUN.ID_DIM
and FACT_TABLE.ID_DIM_SHARED = DIM_SHARED.ID_DIM;

create or replace procedure PC_INS_FACT_TABLE (
	C1 in FACT_TABLE.C1%TYPE,
	C2 in FACT_TABLE.C2%TYPE,
	ID_DIM_COMUN in FACT_TABLE.ID_DIM_COMUN%TYPE,
	ID_DIM_SHARED in FACT_TABLE.ID_DIM_SHARED%TYPE)
AS
BEGIN
	insert into FACT_TABLE (c1,c2,ID_DIM_COMUN,ID_DIM_SHARED) values (c1,c2,ID_DIM_COMUN,ID_DIM_SHARED);
	commit;
EXCEPTION
	WHEN OTHERS THEN
		rollback;
		RAISE;
END PC_INS_FACT_TABLE;
/

sqlplus / as sysdba
alter session set container=APPPDB2;
ALTER PLUGGABLE DATABASE APPLICATION MYAPP SYNC;

SQL> ALTER PLUGGABLE DATABASE APPLICATION MYAPP SYNC;

Pluggable database altered.


COLUMN app_name FORMAT A20
COLUMN app_version FORMAT A10

SELECT app_name,
       app_version,
       app_status
FROM   dba_applications
WHERE  app_name = 'MYAPP';

APP_NAME	     APP_VERSIO APP_STATUS
-------------------- ---------- ------------
MYAPP		     1.0	NORMAL

---- From APPPDB2: 

---- Can query DIM_COMUN, but no DML:

sqlplus appuser/"YOURPASSWORD"@dbcn01:1521/apppdb2.skynet.oraclevcn.com
SQL> delete dim_comun;
delete dim_comun
       *
ERROR at line 1:
ORA-65097: DML into a data link table is outside an application action


SQL> insert into dim_comun values (5,'DDDD');
insert into dim_comun values (5,'DDDD')
            *
ERROR at line 1:
ORA-65097: DML into a data link table is outside an application action

---- Can query DIM_SHARED, and also add data !!!

SQL> insert into dim_shared values (1,'CCCP');
insert into dim_shared values (1,'CCCP')
*
ERROR at line 1:
ORA-00001: unique constraint (APPUSER.PK3) violated


SQL> insert into dim_shared values (5,'CCCP');

1 row created.

SQL> commit;

Commit complete.

insert into dim_shared values (6,'Valor insertado en APPPDB2');
commit;

SQL> select * from dim_shared;

    ID_DIM
----------
DESC_DIM
--------------------------------------------------------------------------------
	 1
DIMENSION SHARED-APPCONT 1

	 2
DIMENSION SHARED-APPCONT  2

	 3
DIMENSION SHARED-APPCONT  3


    ID_DIM
----------
DESC_DIM
--------------------------------------------------------------------------------
	 4
DIMENSION SHARED-APPCONT  4

	 5
CCCP

	 6
Valor insertado en APPPDB2


6 rows selected.

SQL>


SQL> select * from dim_shared where id_dim = 1;

    ID_DIM
----------
DESC_DIM
--------------------------------------------------------------------------------
	 1
DIMENSION SHARED-APPCONT 1



SQL> delete dim_shared where id_dim = 1;

0 rows deleted.

SQL>

update DIM_SHARED set desc_dim = 'CCCP' where id_dim = 1;

SQL> update DIM_SHARED set desc_dim = 'CCCP' where id_dim = 1;

0 rows updated.

delete DIM_SHARED where id_dim = 5;

SQL> delete DIM_SHARED where id_dim = 5;

1 row deleted.

SQL> commit;

Commit complete.

---- Use the procedure !!!

BEGIN
PC_INS_FACT_TABLE(
C1=> 1,
C2=> 'Desde APPPDB2',
ID_DIM_COMUN => 1,
ID_DIM_SHARED => 1);
END;
/

PL/SQL procedure successfully completed.

SQL>
SQL> select * from fact_table;

	C1 C2
---------- --------------------
C3
--------------------------------------------------------------------------------
ID_DIM_COMUN ID_DIM_SHARED
------------ -------------
	 1 Desde APPPDB2

	   1		 1


--- Try to create a new version of the procedure:

create or replace procedure PC_INS_FACT_TABLE (
	C1 in FACT_TABLE.C1%TYPE,
	C2 in FACT_TABLE.C2%TYPE,
	ID_DIM_COMUN in FACT_TABLE.ID_DIM_COMUN%TYPE,
	ID_DIM_SHARED in FACT_TABLE.ID_DIM_SHARED%TYPE)
AS
BEGIN
	insert into FACT_TABLE (c1,c2,c3,ID_DIM_COMUN,ID_DIM_SHARED) values (c1,c2,'Esto es C3',ID_DIM_COMUN,ID_DIM_SHARED);
	commit;
EXCEPTION
	WHEN OTHERS THEN
		rollback;
		RAISE;
END PC_INS_FACT_TABLE;
/

*
ERROR at line 1:
ORA-65274: operation not allowed from outside an application action

--- Cannot compile, because the procedure belongs to APPCONT !!!

--- Try to overload !!!

create or replace procedure PC_INS_FACT_TABLE (
	C1 in FACT_TABLE.C1%TYPE,
	C2 in FACT_TABLE.C2%TYPE,
	C3 in FACT_TABLE.C3%TYPE,
	ID_DIM_COMUN in FACT_TABLE.ID_DIM_COMUN%TYPE,
	ID_DIM_SHARED in FACT_TABLE.ID_DIM_SHARED%TYPE)
AS
BEGIN
	insert into FACT_TABLE (c1,c2,c3,ID_DIM_COMUN,ID_DIM_SHARED) values (c1,c2,'Esto es C3',ID_DIM_COMUN,ID_DIM_SHARED);
	commit;
EXCEPTION
	WHEN OTHERS THEN
		rollback;
		RAISE;
END PC_INS_FACT_TABLE;
/

create or replace procedure PC_INS_FACT_TABLE (
*
ERROR at line 1:
ORA-65274: operation not allowed from outside an application action


--- With the view !!!

select * from V_HECHOS;

SQL> select * from V_HECHOS;

   FACT_C1 FACT_C2
---------- --------------------
DIMCOMUN
--------------------------------------------------------------------------------
DIMSHARED
--------------------------------------------------------------------------------
	 1 Desde APPPDB2
DIMENSION COMUN 1
DIMENSION SHARED-APPCONT 1

--- try to compile the view !!!

create or replace view V_HECHOS
as
select 
	FACT_TABLE.C1 as FACT_C1,
	FACT_TABLE.C2 as FACT_C2,
	FACT_TABLE.C3 as FACT_C3,
	DIM_COMUN.desc_dim as DIMCOMUN,
	DIM_SHARED.desc_dim as DIMSHARED
from FACT_TABLE, DIM_COMUN, DIM_SHARED
where FACT_TABLE.ID_DIM_COMUN = DIM_COMUN.ID_DIM
and FACT_TABLE.ID_DIM_SHARED = DIM_SHARED.ID_DIM;

     *
ERROR at line 9:
ORA-65274: operation not allowed from outside an application action

create or replace view V_HECHOS2
as
select 
	FACT_TABLE.C1 as FACT_C1,
	FACT_TABLE.C2 as FACT_C2,
	FACT_TABLE.C3 as FACT_C3,
	DIM_COMUN.desc_dim as DIMCOMUN,
	DIM_SHARED.desc_dim as DIMSHARED
from FACT_TABLE, DIM_COMUN, DIM_SHARED
where FACT_TABLE.ID_DIM_COMUN = DIM_COMUN.ID_DIM
and FACT_TABLE.ID_DIM_SHARED = DIM_SHARED.ID_DIM;

SQL> select * from v_hechos2;

   FACT_C1 FACT_C2
---------- --------------------
FACT_C3
--------------------------------------------------------------------------------
DIMCOMUN
--------------------------------------------------------------------------------
DIMSHARED
--------------------------------------------------------------------------------
	 1 Desde APPPDB1

DIMENSION COMUN 1
DIMENSION SHARED-APPCONT 1

create synonym V_HECHOS for V_HECHOS2;

--- This fails because synonyms and views belong to the same namespace !!!

---- Generate a new version of the application:
--- From APPCONT !!!

-- Compile the procedure and the view after changing them !!!

sqlplus / as sysdba
alter session set container=APPCONT;


ALTER PLUGGABLE DATABASE APPLICATION MYAPP BEGIN UPGRADE '1.0' TO '1.1';

create or replace procedure APPUSER.PC_INS_FACT_TABLE (
	C1 in FACT_TABLE.C1%TYPE,
	C2 in FACT_TABLE.C2%TYPE,
	C3 in FACT_TABLE.C3%TYPE,
	ID_DIM_COMUN in FACT_TABLE.ID_DIM_COMUN%TYPE,
	ID_DIM_SHARED in FACT_TABLE.ID_DIM_SHARED%TYPE)
AS
BEGIN
	insert into FACT_TABLE (c1,c2,c3,ID_DIM_COMUN,ID_DIM_SHARED) values (c1,c2,'Esto es C3',ID_DIM_COMUN,ID_DIM_SHARED);
	commit;
EXCEPTION
	WHEN OTHERS THEN
		rollback;
		RAISE;
END PC_INS_FACT_TABLE;
/

create or replace view APPUSER.V_HECHOS
as
select 
	FACT_TABLE.C1 as FACT_C1,
	FACT_TABLE.C2 as FACT_C2,
	FACT_TABLE.C3 as FACT_C3,
	DIM_COMUN.desc_dim as DIMCOMUN,
	DIM_SHARED.desc_dim as DIMSHARED
from FACT_TABLE, DIM_COMUN, DIM_SHARED
where FACT_TABLE.ID_DIM_COMUN = DIM_COMUN.ID_DIM
and FACT_TABLE.ID_DIM_SHARED = DIM_SHARED.ID_DIM;
	
ALTER PLUGGABLE DATABASE APPLICATION MYAPP END UPGRADE;

COLUMN app_name FORMAT A20
COLUMN app_version FORMAT A10

SELECT app_name,
       app_version,
       app_status
FROM   dba_applications
WHERE  app_name = 'MYAPP';

APP_NAME	     APP_VERSIO APP_STATUS
-------------------- ---------- ------------
MYAPP		     1.1	NORMAL

--- Let's sync APPPDB1 !!!

sqlplus / as sysdba
alter session set container=APPPDB1;

COLUMN app_name FORMAT A20
COLUMN app_version FORMAT A10

SELECT app_name,
       app_version,
       app_status
FROM   dba_applications
WHERE  app_name = 'MYAPP';

APP_NAME	     APP_VERSIO APP_STATUS
-------------------- ---------- ------------
MYAPP		     1.0	NORMAL

-- Still in 1.0 !!!

SQL> ALTER PLUGGABLE DATABASE APPLICATION MYAPP SYNC;

Pluggable database altered.

SQL> COLUMN app_name FORMAT A20
COLUMN app_version FORMAT A10

SELECT app_name,
       app_version,
       app_status
FROM   dba_applications
WHERE  app_name = 'MYAPP';

APP_NAME	     APP_VERSIO APP_STATUS
-------------------- ---------- ------------
MYAPP		     1.1	NORMAL

--- Now we have APPPDB1 in 1.1 and APPPDB2 in 1.0 !!!

[oracle@dbcn01 ~]$ sqlplus appuser/"YOURPASSWORD"@dbcn01:1521/apppdb1.skynet.oraclevcn.com

SQL*Plus: Release 19.0.0.0.0 - Production on Mon Nov 23 18:52:09 2020
Version 19.9.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.

Last Successful login time: Mon Nov 23 2020 18:40:41 +01:00

Connected to:
Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.9.0.0.0

SQL> desc PC_INS_FACT_TABLE
PROCEDURE PC_INS_FACT_TABLE
 Argument Name			Type			In/Out Default?
 ------------------------------ ----------------------- ------ --------
 C1				NUMBER			IN
 C2				VARCHAR2(20)		IN
 C3				VARCHAR2(1000)		IN
 ID_DIM_COMUN			NUMBER			IN
 ID_DIM_SHARED			NUMBER			IN

SQL>

SQL> desc v_hechos
 Name					   Null?    Type
 ----------------------------------------- -------- ----------------------------
 FACT_C1				   NOT NULL NUMBER
 FACT_C2					    VARCHAR2(20)
 FACT_C3					    VARCHAR2(1000)
 DIMCOMUN					    VARCHAR2(200)
 DIMSHARED					    VARCHAR2(200)

SQL>

[oracle@dbcn01 ~]$ sqlplus appuser/"YOURPASSWORD"@dbcn01:1521/apppdb2.skynet.oraclevcn.com

SQL*Plus: Release 19.0.0.0.0 - Production on Mon Nov 23 18:53:27 2020
Version 19.9.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.

Last Successful login time: Mon Nov 23 2020 18:42:22 +01:00

Connected to:
Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.9.0.0.0

SQL> desc PC_INS_FACT_TABLE
PROCEDURE PC_INS_FACT_TABLE
 Argument Name			Type			In/Out Default?
 ------------------------------ ----------------------- ------ --------
 C1				NUMBER			IN
 C2				VARCHAR2(20)		IN
 ID_DIM_COMUN			NUMBER			IN
 ID_DIM_SHARED			NUMBER			IN

SQL> desc v_hechos
 Name					   Null?    Type
 ----------------------------------------- -------- ----------------------------
 FACT_C1				   NOT NULL NUMBER
 FACT_C2					    VARCHAR2(20)
 DIMCOMUN					    VARCHAR2(200)
 DIMSHARED					    VARCHAR2(200)

SQL>


--- Now execute the procedure from APPPDB1 !!!!

sqlplus appuser/"YOURPASSWORD"@dbcn01:1521/apppdb1.skynet.oraclevcn.com

BEGIN
PC_INS_FACT_TABLE(
C1=> 1,
C2=> 'Desde APPPDB1 v1.1',
C3=> 'Valor de C3',
ID_DIM_COMUN => 1,
ID_DIM_SHARED => 1);
END;
/

SQL> select * from v_hechos;

   FACT_C1 FACT_C2
---------- --------------------
FACT_C3
--------------------------------------------------------------------------------
DIMCOMUN
--------------------------------------------------------------------------------
DIMSHARED
--------------------------------------------------------------------------------
	 1 Desde APPPDB1 v1.1
Esto es C3
DIMENSION COMUN 1
DIMENSION SHARED-APPCONT 1

--- And from APPPDB2 !!!

sqlplus appuser/"YOURPASSWORD"@dbcn01:1521/apppdb2.skynet.oraclevcn.com

BEGIN
PC_INS_FACT_TABLE(
C1=> 1,
C2=> 'Desde APPPDB2 v1.0',
ID_DIM_COMUN => 1,
ID_DIM_SHARED => 1);
END;
/

SQL> select * from v_hechos;

   FACT_C1 FACT_C2
---------- --------------------
DIMCOMUN
--------------------------------------------------------------------------------
DIMSHARED
--------------------------------------------------------------------------------
	 1 Desde APPPDB2 v1.0
DIMENSION COMUN 1
DIMENSION SHARED-APPCONT 1


--- At any time we can upgrade APPPDB2 to version 1.1 !!!

sqlplus / a sysdba
alter session set container = APPPDB2;

ALTER PLUGGABLE DATABASE APPLICATION MYAPP SYNC;

[oracle@dbcn01 ~]$ sqlplus appuser/"YOURPASSWORD"@dbcn01:1521/apppdb2.skynet.oraclevcn.com

SQL*Plus: Release 19.0.0.0.0 - Production on Tue Nov 24 14:23:29 2020
Version 19.9.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.

Last Successful login time: Tue Nov 24 2020 14:12:07 +01:00

Connected to:
Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.9.0.0.0

SQL> desc v_hechos
 Name					   Null?    Type
 ----------------------------------------- -------- ----------------------------
 FACT_C1				   NOT NULL NUMBER
 FACT_C2					    VARCHAR2(20)
 FACT_C3					    VARCHAR2(1000)
 DIMCOMUN					    VARCHAR2(200)
 DIMSHARED					    VARCHAR2(200)

SQL> desc PC_INS_FACT_TABLE
PROCEDURE PC_INS_FACT_TABLE
 Argument Name			Type			In/Out Default?
 ------------------------------ ----------------------- ------ --------
 C1				NUMBER			IN
 C2				VARCHAR2(20)		IN
 C3				VARCHAR2(1000)		IN
 ID_DIM_COMUN			NUMBER			IN
 ID_DIM_SHARED			NUMBER			IN

SQL>

BEGIN
PC_INS_FACT_TABLE(
C1=> 2,
C2=> 'Desde APPPDB2 v1.1',
C3=> 'Valor de C3',
ID_DIM_COMUN => 1,
ID_DIM_SHARED => 1);
END;
/

SQL> select * from v_hechos;

   FACT_C1 FACT_C2
---------- --------------------
FACT_C3
--------------------------------------------------------------------------------
DIMCOMUN
--------------------------------------------------------------------------------
DIMSHARED
--------------------------------------------------------------------------------
	 1 Desde APPPDB2 v1.0

DIMENSION COMUN 1
DIMENSION SHARED-APPCONT 1


   FACT_C1 FACT_C2
---------- --------------------
FACT_C3
--------------------------------------------------------------------------------
DIMCOMUN
--------------------------------------------------------------------------------
DIMSHARED
--------------------------------------------------------------------------------
	 2 Desde APPPDB2 v1.1
Esto es C3
DIMENSION COMUN 1
DIMENSION SHARED-APPCONT 1


SQL>


---- We can create a SEED database !!!

sqlplus / a sysdba
alter session set container=APPCONT;
SQL> CREATE PLUGGABLE DATABASE AS SEED FROM APPCONT  keystore identified by "YOURPASSWORD";


Pluggable database created.

SQL> SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 4 APPPDB1			  READ WRITE NO
	 5 APPCONT			  READ WRITE NO
	 6 APPPDB2			  READ WRITE NO
	 9 APPCONT$SEED 		  MOUNTED
SQL> alter pluggable database APPCONT$SEED open;

Warning: PDB altered with errors.

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 4 APPPDB1			  READ WRITE NO
	 5 APPCONT			  READ WRITE NO
	 6 APPPDB2			  READ WRITE NO
	 9 APPCONT$SEED 		  READ WRITE YES
	 
SQL> alter session set container=APPCONT$SEED;

Session altered.


@$ORACLE_HOME/rdbms/admin/pdb_to_apppdb.sql
alter pluggable database APPCONT$SEED close immediate;
alter pluggable database APPCONT$SEED open read only;

SQL> alter session set container=APPCONT;

Session altered.

SQL> show pdbs

    CON_ID CON_NAME                       OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
         4 APPPDB1                        READ WRITE NO
         5 APPCONT                        READ WRITE NO
         6 APPPDB2                        READ WRITE NO
         9 APPCONT$SEED                   READ ONLY  NO
SQL>

[oracle@dbcn01 ~]$ sqlplus appuser/"YOURPASSWORD"@dbcn01:1521/appcont$seed.skynet.oraclevcn.com

SQL*Plus: Release 19.0.0.0.0 - Production on Tue Nov 24 14:49:14 2020
Version 19.9.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.

Last Successful login time: Tue Nov 24 2020 14:23:30 +01:00

Connected to:
Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.9.0.0.0

SQL> select * from v_hechos;

no rows selected

SQL> desc v_hechos
 Name					   Null?    Type
 ----------------------------------------- -------- ----------------------------
 FACT_C1				   NOT NULL NUMBER
 FACT_C2					    VARCHAR2(20)
 FACT_C3					    VARCHAR2(1000)
 DIMCOMUN					    VARCHAR2(200)
 DIMSHARED					    VARCHAR2(200)

SQL> desc PC_INS_FACT_TABLE
PROCEDURE PC_INS_FACT_TABLE
 Argument Name			Type			In/Out Default?
 ------------------------------ ----------------------- ------ --------
 C1				NUMBER			IN
 C2				VARCHAR2(20)		IN
 C3				VARCHAR2(1000)		IN
 ID_DIM_COMUN			NUMBER			IN
 ID_DIM_SHARED			NUMBER			IN

SQL>

