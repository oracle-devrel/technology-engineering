-- Context:
--
-- 2 CDB
-- In each CDB, one Appcont + 2 App PDB
-- CDB1 is MASTER
-- CDB2 is being refreshed from CDB1, as AppCont of CDB2 has a proxy PDB inside APPCONT of CDB1 !!!
-- NB: at the end of this step by step, we setup global_names=FALSE scope=both in each CDB: better do it from the beginning !!!



--- In CDB1:
SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 PDB1 			  READ WRITE NO
SQL>

create pluggable database APPCONT as application container from PDB1 keystore identified by "YOURPASSWORD";

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 PDB1 			  READ WRITE NO
	 7 APPCONT			  MOUNTED
SQL> alter pluggable database appcont open;

Pluggable database altered.

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 PDB1 			  READ WRITE NO
	 7 APPCONT			  READ WRITE NO
SQL>

--- In APPCONT, create an APPPDB:

alter session set container=APPCONT;

CREATE PLUGGABLE DATABASE apppdb1 ADMIN USER pdb_admin IDENTIFIED BY "YOURPASSWORD" keystore identified by "YOURPASSWORD";

SQL> alter pluggable database APPPDB1 open;

Pluggable database altered.

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 4 APPPDB1			  READ WRITE NO
	 7 APPCONT			  READ WRITE NO
SQL>

sqlplus sys/"YOURPASSWORD"@dbcn01:1521/apppdb1.skynet.oraclevcn.com as sysdba

ADMINISTER KEY MANAGEMENT SET KEY FORCE KEYSTORE IDENTIFIED BY "YOURPASSWORD" WITH BACKUP;


--- En la CDB2:
--- Creo también un App Container con una App PDB:

[oracle@dbcn99 ~]$ sqlplus / as sysdba

SQL*Plus: Release 19.0.0.0.0 - Production on Tue Dec 1 09:12:49 2020
Version 19.9.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.


Connected to:
Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.9.0.0.0

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 PDB1 			  READ WRITE NO
SQL>

create pluggable database APPCONT2 as application container from PDB1 keystore identified by "YOURPASSWORD";

SQL> alter pluggable database APPCONT2 open;

Pluggable database altered.

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 PDB1 			  READ WRITE NO
	 4 APPCONT2			  READ WRITE NO
SQL>

alter session set container=APPCONT2;

ADMINISTER KEY MANAGEMENT SET KEY FORCE KEYSTORE IDENTIFIED BY "YOURPASSWORD" WITH BACKUP;

CREATE PLUGGABLE DATABASE apppdb2 ADMIN USER pdb_admin IDENTIFIED BY "YOURPASSWORD" keystore identified by "YOURPASSWORD";

SQL> alter pluggable database APPPDB2 open;

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 4 APPCONT2			  READ WRITE NO
	 5 APPPDB2			  READ WRITE NO
SQL>

sqlplus sys/"YOURPASSWORD"@dbcn99:1521/apppdb2.skynet.oraclevcn.com as sysdba

ADMINISTER KEY MANAGEMENT SET KEY FORCE KEYSTORE IDENTIFIED BY "YOURPASSWORD" WITH BACKUP;

--- Now in CDB1, create an APP PDB APPPROXY which is a proxy against APPCONT2 !!!

--- First in CDB2 create a common user:

sqlplus / as sysdba

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 PDB1 			  READ WRITE NO
	 4 APPCONT2			  READ WRITE NO
	 5 APPPDB2			  READ WRITE NO
SQL>

CREATE USER c##remote_clone_user IDENTIFIED BY "YOURPASSWORD" CONTAINER=ALL;
GRANT CREATE SESSION, CREATE PLUGGABLE DATABASE TO c##remote_clone_user CONTAINER=ALL;

--- Now in CDB1 create a dblink to PDB2 !!!
--
-- In tnsnames.ora add the following entry:

DB1130_FRA1SZ =
  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCP)(HOST = dbcn99.skynet.oraclevcn.com)(PORT = 1521))
    (CONNECT_DATA =
      (SERVER = DEDICATED)
      (SERVICE_NAME = DB1130_fra1sz.skynet.oraclevcn.com)
    )
  )

--- From CDB1 check the connectivity, after opening port 1521 in the subnet !!!

[oracle@dbcn01 admin]$ tnsping DB1130_FRA1SZ

TNS Ping Utility for Linux: Version 19.0.0.0.0 - Production on 01-DEC-2020 13:28:21

Copyright (c) 1997, 2020, Oracle.  All rights reserved.

Used parameter files:
/u01/app/oracle/product/19.0.0.0/dbhome_1/network/admin/sqlnet.ora


Used TNSNAMES adapter to resolve the alias
Attempting to contact (DESCRIPTION = (ADDRESS = (PROTOCOL = TCP)(HOST = dbcn99.skynet.oraclevcn.com)(PORT = 1521)) (CONNECT_DATA = (SERVER = DEDICATED) (SERVICE_NAME = DB1130_fra1sz.skynet.oraclevcn.com)))
OK (0 msec)

-- Check the connectivity to the remote user !!!

[oracle@dbcn01 admin]$ sqlplus c##remote_clone_user/"YOURPASSWORD"@DB1130_FRA1SZ

SQL*Plus: Release 19.0.0.0.0 - Production on Tue Dec 1 13:39:48 2020
Version 19.9.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.


Connected to:
Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.9.0.0.0

-- Create the dblink in CDB1 !!!

sqlplus / as sysdba
SQL> create database link DB1130.SKYNET.ORACLEVCN.COM connect to c##remote_clone_user identified by "YOURPASSWORD" using 'DB1130_FRA1SZ';

Database link created.

SQL> select * from dual@DB1130.SKYNET.ORACLEVCN.COM;

D
-
X

SQL>

-- Ready to create the PROXYPDB in APPCONT:

sqlplus / as sysdba
alter session set container=APPCONT;
-- The dblink MUST be created in APPCONT !!!
create database link APPCONT2.SKYNET.ORACLEVCN.COM connect to c##remote_clone_user identified by "YOURPASSWORD" using 'DB1130_FRA1SZ';

CREATE PLUGGABLE DATABASE PDBPROXY AS PROXY FROM APPCONT2@DB1130.SKYNET.ORACLEVCN.COM keystore identified by "YOURPASSWORD";

ERROR at line 1:
ORA-17628: Oracle error 46659 returned by remote Oracle server
ORA-46659: master keys for the given PDB not found

-- This is because we need to do something with CDB2 wallet !!!
--- From APPCONT2 !!!

sqlplus / as sysdba
alter session set container=APPCONT2;
ADMINISTER KEY MANAGEMENT SET KEY FORCE KEYSTORE IDENTIFIED BY "YOURPASSWORD" WITH BACKUP;

-- Then create the proxy PDB !!!

SQL> CREATE PLUGGABLE DATABASE PDBPROXY AS PROXY FROM APPCONT2@DB1130.SKYNET.ORACLEVCN.COM keystore identified by "YOURPASSWORD";

Pluggable database created.

SQL>

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 4 APPPDB1			  READ WRITE NO
	 6 PDBPROXY			  MOUNTED
	 7 APPCONT			  READ WRITE NO
SQL>

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 4 APPPDB1			  READ WRITE NO
	 6 PDBPROXY			  MOUNTED
	 7 APPCONT			  READ WRITE NO
SQL> alter pluggable database PDBPROXY open;

Pluggable database altered.

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 4 APPPDB1			  READ WRITE NO
	 6 PDBPROXY			  READ WRITE NO
	 7 APPCONT			  READ WRITE NO
SQL>

=> So far so good !!!

-- Now we have, in CDB1, an APPCONT with 2 APP PDB, one of them being a proxy pointing to APPCONT2 which is inside CDB2 !!!
--- Now we will create an application in APPCONT, and sync PDBPROXY y APPPDB1 !!!
--- Then we will sync APPPDB2 with APPCONT2 !!!

SQL> col name format a20
SQL> r
  1* select NAME, APPLICATION_ROOT, APPLICATION_PDB from v$pdbs

NAME		     APP APP
-------------------- --- ---
APPPDB1 	     NO  YES
PDBPROXY	     NO  YES
APPCONT 	     YES NO

SQL>

SQL> COLUMN target_host FORMAT A20
COLUMN target_service FORMAT A32
COLUMN target_user FORMAT A20

SELECT con_id,
       target_port,
       target_host,
       target_service,
       target_user
FROM   v$proxy_pdb_targets;SQL> SQL> SQL> SQL>   2    3    4    5    6

    CON_ID TARGET_PORT TARGET_HOST	    TARGET_SERVICE
---------- ----------- -------------------- --------------------------------
TARGET_USER
--------------------
	 6	  1521 dbcn99		    b5648b05f725cccee0530500000a05a9
					    .skynet.oraclevcn
					    .com


--- Install the application in APPCONT !!!

-- In CDB1, create TBS USERS in APPPDB1 !!!
-- In APPCONT, TBS USERS already exists, as APPCONT was created from PDB$SEED !!
-- In PDBPROXY we cannot create a TBS, we need to do it in the remote PDB !!!

sqlplus / as sysdba
alter session set container=APPPDB1;
create bigfile tablespace USERS datafile size 1G;

sqlplus / as sysdba
create user C##APPUSER identified by "YOURPASSWORD" default tablespace USERS temporary tablespace TEMP;
grant connect, resource to C##APPUSER container=ALL;
alter user C##APPUSER quota unlimited on USERS container=ALL;
grant create view to C##APPUSER container=ALL;
grant create synonym to C##APPUSER container=ALL;
grant dba to C##APPUSER container=ALL;

--- Same in CDB2 !!!

[oracle@dbcn99 admin]$ sqlplus / as sysdba

SQL*Plus: Release 19.0.0.0.0 - Production on Tue Dec 1 15:43:51 2020
Version 19.9.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.


Connected to:
Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.9.0.0.0

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 PDB1 			  READ WRITE NO
	 4 APPPDB2			  READ WRITE NO
	 5 APPCONT2			  READ WRITE NO
SQL> alter session set container = APPPDB2;

Session altered.

SQL> create bigfile tablespace USERS datafile size 1G;

Tablespace created.

SQL> exit
Disconnected from Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.9.0.0.0
[oracle@dbcn99 admin]$ sqlplus / as sysdba

SQL*Plus: Release 19.0.0.0.0 - Production on Tue Dec 1 15:44:29 2020
Version 19.9.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.


Connected to:
Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.9.0.0.0

SQL> create user C##APPUSER identified by "YOURPASSWORD" default tablespace USERS temporary tablespace TEMP;

User created.

grant connect, resource to C##APPUSER container=ALL;
alter user C##APPUSER quota unlimited on USERS container=ALL;
grant create view to C##APPUSER container=ALL;
grant create synonym to C##APPUSER container=ALL;
grant dba to C##APPUSER container=ALL;
Grant succeeded.

SQL>
User altered.

SQL>
Grant succeeded.

SQL>
Grant succeeded.

SQL>
Grant succeeded.


--- Now install the application in APPCONT !!!
sqlplus system/"YOURPASSWORD"@dbcn01:1521/appcont.skynet.oraclevcn.com

alter pluggable database application MYAPP BEGIN INSTALL '1.0';

--- Fact table, each APPPDB will have its own data inside !!!

create table C##APPUSER.FACT_TABLE sharing=metadata
(
   C1 number not null,
   C2 VARCHAR2(20),
   C3 varchar2(1000),
   ID_DIM_COMUN number,
   ID_DIM_SHARED number
  );
  
alter table C##APPUSER.FACT_TABLE add constraint PK1 primary key (C1);

--- Common dimension table

create table C##APPUSER.DIM_COMUN sharing=data
(
ID_DIM number not null,
DESC_DIM varchar2(200)
);

alter table C##APPUSER.DIM_COMUN add constraint PK2 primary key (ID_DIM);

insert into C##APPUSER.DIM_COMUN (id_dim, desc_dim) values (1,'DIMENSION COMUN 1');
insert into C##APPUSER.DIM_COMUN (id_dim, desc_dim) values (2,'DIMENSION COMUN  2');
insert into C##APPUSER.DIM_COMUN (id_dim, desc_dim) values (3,'DIMENSION COMUN  3');
insert into C##APPUSER.DIM_COMUN (id_dim, desc_dim) values (4,'DIMENSION COMUN  4');
commit;


--- Dimension table particular to each APPPDB, with data from APPCONT. Each APPPDB can add its own data !!!

create table C##APPUSER.DIM_SHARED sharing=EXTENDED DATA
(
ID_DIM number not null,
DESC_DIM varchar2(200)
);

alter table C##APPUSER.DIM_SHARED add constraint PK3 primary key (ID_DIM);

insert into C##APPUSER.DIM_SHARED (id_dim, desc_dim) values (1,'DIMENSION SHARED-APPCONT 1');
insert into C##APPUSER.DIM_SHARED (id_dim, desc_dim) values (2,'DIMENSION SHARED-APPCONT  2');
insert into C##APPUSER.DIM_SHARED (id_dim, desc_dim) values (3,'DIMENSION SHARED-APPCONT  3');
insert into C##APPUSER.DIM_SHARED (id_dim, desc_dim) values (4,'DIMENSION SHARED-APPCONT  4');
commit;

--- View on the fact table !!!

create or replace view C##APPUSER.V_HECHOS sharing=extended data
as
select 
	FACT_TABLE.C1 as FACT_C1,
	FACT_TABLE.C2 as FACT_C2,
	DIM_COMUN.desc_dim as DIMCOMUN,
	DIM_SHARED.desc_dim as DIMSHARED
from C##APPUSER.FACT_TABLE, C##APPUSER.DIM_COMUN, C##APPUSER.DIM_SHARED
where FACT_TABLE.ID_DIM_COMUN = DIM_COMUN.ID_DIM
and FACT_TABLE.ID_DIM_SHARED = DIM_SHARED.ID_DIM;

--- Create a procedure !!!!

create or replace procedure C##APPUSER.PC_INS_FACT_TABLE SHARING=METADATA
(
	C1 in C##APPUSER.FACT_TABLE.C1%TYPE,
	C2 in C##APPUSER.FACT_TABLE.C2%TYPE,
	ID_DIM_COMUN in C##APPUSER.FACT_TABLE.ID_DIM_COMUN%TYPE,
	ID_DIM_SHARED in C##APPUSER.FACT_TABLE.ID_DIM_SHARED%TYPE)
AS
BEGIN
	insert into C##APPUSER.FACT_TABLE (c1,c2,ID_DIM_COMUN,ID_DIM_SHARED) values (c1,c2,ID_DIM_COMUN,ID_DIM_SHARED);
	commit;
EXCEPTION
	WHEN OTHERS THEN
		rollback;
		RAISE;
END PC_INS_FACT_TABLE;
/

alter pluggable database application MYAPP END INSTALL '1.0';

--- Now sync APPPDB1 !!!

sqlplus / as sysdba
alter session set container=APPPDB1;
ALTER PLUGGABLE DATABASE APPLICATION MYAPP SYNC;

Pluggable database altered.

SQL>

--- If I connect to APPPDB1, I can use the app !!!

sqlplus appuser/"YOURPASSWORD"@dbcn01:1521/apppdb1.skynet.oraclevcn.com

SQL> select * from dim_comun;

    ID_DIM
----------
DESC_DIM
--------------------------------------------------------------------------------
	 1
DIMENSION COMUN 1

	 2
DIMENSION COMUN  2

	 3
DIMENSION COMUN  3


    ID_DIM
----------
DESC_DIM
--------------------------------------------------------------------------------
	 4
DIMENSION COMUN  4


SQL>
-- => OK !!!

-- Now sync PDBPROXY !!!!
-- NB: connection to PDBPROXY needs to be with password !!!

sqlplus sys/"YOURPASSWORD"@dbcn01:1521/pdbproxy.skynet.oraclevcn.com as sysdba

ALTER PLUGGABLE DATABASE APPLICATION MYAPP SYNC;

ALTER PLUGGABLE DATABASE APPLICATION MYAPP SYNC
*
ERROR at line 1:
ORA-12545: Connect failed because target host or object does not exist

--- This fails because SYNC is intented with PROXYPDB$DBLINK.SKYNET.ORACLEVCN.COM
-- looking at the alert.log, we observe a connection tentative with:

"(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=dbcn99)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=b569c8fe8b022c37e0530500000ad9c6.skynet.oraclevcn.com)(CID=(PROGRAM=oracle)(HOST=dbcn01)(USER=oracle))))"



[oracle@dbcn01 ~]$ sqlplus c##appuser/"YOURPASSWORD"@dbcn01:1521/pdbproxy.skynet.oraclevcn.com

SQL*Plus: Release 19.0.0.0.0 - Production on Tue Dec 1 17:05:33 2020
Version 19.9.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.

ERROR:
ORA-06550: line 1, column 7:
PLS-00352: Unable to access another database
'PROXYPDB$DBLINK.SKYNET.ORACLEVCN.COM'
ORA-06550: line 1, column 7:
PLS-00201: identifier 'DBMS_APPLICATION_INFO' must be declared
ORA-06550: line 1, column 7:
PL/SQL: Statement ignored


Error accessing package DBMS_APPLICATION_INFO
Last Successful login time: Tue Dec 01 2020 16:55:13 +01:00

Connected to:
Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.9.0.0.0

SQL> exit


-- This fails because dbcn99 is not being resolved by DNS:

[oracle@dbcn01 trace]$ nslookup dbcn99
Server:		169.254.169.254
Address:	169.254.169.254#53
server cannot find dbcn99: NXDOMAIN

[oracle@dbcn01 trace]$

-- The following connection string works:
"(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=dbcn99.skynet.oraclevcn.com)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=b569c8fe8b022c37e0530500000ad9c6.skynet.oraclevcn.com)(CID=(PROGRAM=oracle)(HOST=dbcn01)(USER=oracle))))"

[oracle@dbcn01 trace]$ nslookup dbcn99.skynet.oraclevcn.com
Server:		169.254.169.254
Address:	169.254.169.254#53

Non-authoritative answer:
Name:	dbcn99.skynet.oraclevcn.com
Address: 10.0.0.5

[oracle@dbcn01 trace]$

--- Add an entry to /etc/hosts !!!
10.0.0.5 dbcn99.skynet.oraclevcn.com dbcn99

SQL> ALTER PLUGGABLE DATABASE APPLICATION MYAPP SYNC;
ALTER PLUGGABLE DATABASE APPLICATION MYAPP SYNC
*
ERROR at line 1:
ORA-02085: database link PROXYPDB$DBLINK connects to
APPCONT2.SKYNET.ORACLEVCN.COM

Ahora falla por el nombre del DBLINK !!!!
-- Now it fails because of the global_names !!!

sqlplus / as sysdba
SQL> show parameter global_names

NAME				     TYPE	 VALUE
------------------------------------ ----------- ------------------------------
global_names			     boolean	 TRUE
SQL> alter system set global_names=FALSE scope=both;

System altered.

SQL>

-- Try to SYNC en la PDBPROXY !!!

sqlplus sys/"YOURPASSWORD"@dbcn01:1521/pdbproxy.skynet.oraclevcn.com as sysdba

ALTER PLUGGABLE DATABASE APPLICATION MYAPP SYNC;

SQL> ALTER PLUGGABLE DATABASE APPLICATION MYAPP SYNC;

Pluggable database altered.

SQL>

-- => Working now !!!

-- Check things PDBPROXY !!!

sqlplus c##appuser/"YOURPASSWORD"@dbcn01:1521/pdbproxy.skynet.oraclevcn.com
select * from dim_comun;

SQL> select * from dim_comun;

    ID_DIM
----------
DESC_DIM
--------------------------------------------------------------------------------
	 1
DIMENSION COMUN 1

	 2
DIMENSION COMUN  2

	 3
DIMENSION COMUN  3


    ID_DIM
----------
DESC_DIM
--------------------------------------------------------------------------------
	 4
DIMENSION COMUN  4


SQL>

SQL> desc v_hechos
 Name					   Null?    Type
 ----------------------------------------- -------- ----------------------------
 FACT_C1				   NOT NULL NUMBER
 FACT_C2					    VARCHAR2(20)
 DIMCOMUN					    VARCHAR2(200)
 DIMSHARED					    VARCHAR2(200)

SQL> desc pc_ins_fact_table
PROCEDURE pc_ins_fact_table
 Argument Name			Type			In/Out Default?
 ------------------------------ ----------------------- ------ --------
 C1				NUMBER			IN
 C2				VARCHAR2(20)		IN
 ID_DIM_COMUN			NUMBER			IN
 ID_DIM_SHARED			NUMBER			IN

SQL>

-- Check CDB2 -> APPCONT2 !!!

sqlplus c##appuser/"YOURPASSWORD"@dbcn99:1521/appcont2.skynet.oraclevcn.com

SQL> select * from dim_comun;

    ID_DIM
----------
DESC_DIM
--------------------------------------------------------------------------------
	 1
DIMENSION COMUN 1

	 2
DIMENSION COMUN  2

	 3
DIMENSION COMUN  3


    ID_DIM
----------
DESC_DIM
--------------------------------------------------------------------------------
	 4
DIMENSION COMUN  4


SQL> desc v_hechos
 Name					   Null?    Type
 ----------------------------------------- -------- ----------------------------
 FACT_C1				   NOT NULL NUMBER
 FACT_C2					    VARCHAR2(20)
 DIMCOMUN					    VARCHAR2(200)
 DIMSHARED					    VARCHAR2(200)

SQL> desc pc_ins_fact_table
PROCEDURE pc_ins_fact_table
 Argument Name			Type			In/Out Default?
 ------------------------------ ----------------------- ------ --------
 C1				NUMBER			IN
 C2				VARCHAR2(20)		IN
 ID_DIM_COMUN			NUMBER			IN
 ID_DIM_SHARED			NUMBER			IN

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

-- => So far so good !!!

--- Now sync APPPDB2 from APPCONT2 !!!

sqlplus sys/"YOURPASSWORD"@dbcn99:1521/apppdb2.skynet.oraclevcn.com as sysdba

ALTER PLUGGABLE DATABASE APPLICATION MYAPP SYNC;

SQL> ALTER PLUGGABLE DATABASE APPLICATION MYAPP SYNC;

Pluggable database altered.

SQL>

--- Check APPPDB2 !!!

[oracle@dbcn99 ~]$ sqlplus c##appuser/"YOURPASSWORD"@dbcn99:1521/apppdb2.skynet.oraclevcn.com

SQL*Plus: Release 19.0.0.0.0 - Production on Wed Dec 2 10:04:40 2020
Version 19.9.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.

Last Successful login time: Wed Dec 02 2020 10:01:27 +00:00

Connected to:
Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.9.0.0.0

SQL> select * from dim_comun;

    ID_DIM
----------
DESC_DIM
--------------------------------------------------------------------------------
	 1
DIMENSION COMUN 1

	 2
DIMENSION COMUN  2

	 3
DIMENSION COMUN  3


    ID_DIM
----------
DESC_DIM
--------------------------------------------------------------------------------
	 4
DIMENSION COMUN  4


SQL> desc v_hechos
 Name					   Null?    Type
 ----------------------------------------- -------- ----------------------------
 FACT_C1				   NOT NULL NUMBER
 FACT_C2					    VARCHAR2(20)
 DIMCOMUN					    VARCHAR2(200)
 DIMSHARED					    VARCHAR2(200)

SQL> desc pc_ins_fact_table
PROCEDURE pc_ins_fact_table
 Argument Name			Type			In/Out Default?
 ------------------------------ ----------------------- ------ --------
 C1				NUMBER			IN
 C2				VARCHAR2(20)		IN
 ID_DIM_COMUN			NUMBER			IN
 ID_DIM_SHARED			NUMBER			IN

SQL>


--- This is a killer feature !!!

--- Bonus track !!!
--- In CDB1, try to clone APPPDB1, to check if we can clone outside of APPCONT1 !!!
-- 

SQL> create pluggable database PDB2 from APPPDB1 keystore identified by "YOURPASSWORD";
create pluggable database PDB2 from APPPDB1 keystore identified by "YOURPASSWORD"
*
ERROR at line 1:
ORA-65240: not connected to an application root

-- It logically fails !!!

 