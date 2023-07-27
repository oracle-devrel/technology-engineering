***********************************
Create a Non-Shard Service
***********************************


Connect to the shard3 host, switch to the oracle user.

Create a new pdb name NSPDB.

[oracle@shd3 ~]$ sqlplus / as sysdba

SQL*Plus: Release 19.0.0.0.0 - Production on Thu Nov 11 11:39:19 2021
Version 19.11.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.


Connected to:
Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
Version 19.11.0.0.0

SQL>
SQL>
SQL> CREATE PLUGGABLE DATABASE nspdb ADMIN USER admin IDENTIFIED BY Ora_DB4U
  DEFAULT TABLESPACE users DATAFILE '/u01/app/oracle/oradata/SHD3/nspdb/users01.dbf'
  SIZE 10G AUTOEXTEND ON
  FILE_NAME_CONVERT = ('/pdbseed/', '/nspdb/');

Pluggable database created.

SQL> alter pluggable database NSPDB open;



Pluggable database altered.

SQL> SQL> SQL>
SQL>
SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 SHDPDB3			  READ WRITE NO
	 4 NSPDB			  READ WRITE NO
SQL>


Create a service named GDS$CATALOG.ORADBCLOUD and start it in order to run the demo application correctly. 
(The demo application is designed for sharded database, it''s need connect to the shard catalog. The service name is hard code in the demo application).

SQL> alter session set container = nspdb;

Session altered.

SQL> BEGIN
  DBMS_SERVICE.create_service(
    service_name => 'GDS$CATALOG.ORADBCLOUD',
    network_name => 'GDS$CATALOG.ORADBCLOUD'
  );
END;
/

PL/SQL procedure successfully completed.

SQL> BEGIN
  DBMS_SERVICE.start_service(
    service_name => 'GDS$CATALOG.ORADBCLOUD'
  );
END;
/

PL/SQL procedure successfully completed.

SQL>

Create the Demo Schema
----------------------

Still in the shard3 host with oracle user. Download the SQL script nonshard-app-schema.sql.

wget https://bit.ly/3nF6jdz -O nonshard-app-schema.sql

--2022-07-04 06:19:04--  https://objectstorage.us-ashburn-1.oraclecloud.com/p/VEKec7t0mGwBkJX92Jn0nMptuXIlEpJ5XJA-A6C9PymRgY2LhKbjWqHeB5rVBbaV/n/c4u04/b/livelabsfiles/o/data-management-library-files/Oracle%20Sharding/nonshard-app-schema.sql
Resolving objectstorage.us-ashburn-1.oraclecloud.com (objectstorage.us-ashburn-1.oraclecloud.com)... 134.70.32.1, 134.70.24.1, 134.70.28.1
Connecting to objectstorage.us-ashburn-1.oraclecloud.com (objectstorage.us-ashburn-1.oraclecloud.com)|134.70.32.1|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: 2938 (2.9K) [application/octet-stream]
Saving to: ‘nonshard-app-schema.sql.1’

100%[=====================================================================================================================>] 2,938       --.-K/s   in 0.001s

2022-07-04 06:19:05 (3.14 MB/s) - ‘nonshard-app-schema.sql.1’ saved [2938/2938]
[oracle@shd3 ~]$ ls -ltr
total 8
drwxr-xr-x. 12 oracle oinstall 4096 Jul 23  2020 swingbench
-rw-r--r--.  1 oracle oinstall 2938 Jul  2 19:51 nonshard-app-schema.sql
[oracle@shd3 ~]$

[oracle@shd3 ~]$ cat nonshard-app-schema.sql
set echo on
set termout on
set time on
spool /home/oracle/nonshard_app_schema.lst
REM
REM Connect to the pdb and Create Schema
REM
connect / as sysdba
alter session set container=nspdb;
create user app_schema identified by app_schema;
grant connect, resource, alter session to app_schema;
grant execute on dbms_crypto to app_schema;
grant create table, create procedure, create tablespace, create materialized view to app_schema;
grant unlimited tablespace to app_schema;
grant select_catalog_role to app_schema;
grant all privileges to app_schema;
grant dba to app_schema;

REM
REM Create tables
REM
connect app_schema/app_schema@localhost:1521/nspdb

REM
REM Create for Customers
REM
CREATE TABLE Customers
(
  CustId      VARCHAR2(60) NOT NULL,
  FirstName   VARCHAR2(60),
  LastName    VARCHAR2(60),
  Class       VARCHAR2(10),
  Geo         VARCHAR2(8),
  CustProfile VARCHAR2(4000),
  Passwd      RAW(60),
  CONSTRAINT pk_customers PRIMARY KEY (CustId),
  CONSTRAINT json_customers CHECK (CustProfile IS JSON)
) TABLESPACE USERS
PARTITION BY HASH (CustId) PARTITIONS 12;

REM
REM Create table for Orders
REM
CREATE TABLE Orders
(
  OrderId     INTEGER NOT NULL,
  CustId      VARCHAR2(60) NOT NULL,
  OrderDate   TIMESTAMP NOT NULL,
  SumTotal    NUMBER(19,4),
  Status      CHAR(4),
  constraint  pk_orders primary key (CustId, OrderId),
  constraint  fk_orders_parent foreign key (CustId)
    references Customers on delete cascade
) TABLESPACE USERS
partition by reference (fk_orders_parent);

REM
REM Create the sequence used for the OrderId column
REM
CREATE SEQUENCE Orders_Seq;

REM
REM Create table for LineItems
REM
CREATE TABLE LineItems
(
  OrderId     INTEGER NOT NULL,
  CustId      VARCHAR2(60) NOT NULL,
  ProductId   INTEGER NOT NULL,
  Price       NUMBER(19,4),
  Qty         NUMBER,
  constraint  pk_items primary key (CustId, OrderId, ProductId),
  constraint  fk_items_parent foreign key (CustId, OrderId)
    references Orders on delete cascade
) TABLESPACE USERS
partition by reference (fk_items_parent);

REM
REM Create table for Products
REM
CREATE TABLE Products
(
  ProductId  INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  Name       VARCHAR2(128),
  DescrUri   VARCHAR2(128),
  LastPrice  NUMBER(19,4)
) TABLESPACE USERS;

REM
REM Create functions for Password creation and checking – used by the REM demo loader application
REM

CREATE OR REPLACE FUNCTION PasswCreate(PASSW IN RAW)
  RETURN RAW
IS
  Salt RAW(8);
BEGIN
  Salt := DBMS_CRYPTO.RANDOMBYTES(8);
  RETURN UTL_RAW.CONCAT(Salt, DBMS_CRYPTO.HASH(UTL_RAW.CONCAT(Salt, PASSW), DBMS_CRYPTO.HASH_SH256));
END;
/

CREATE OR REPLACE FUNCTION PasswCheck(PASSW IN RAW, PHASH IN RAW)
  RETURN INTEGER IS
BEGIN
  RETURN UTL_RAW.COMPARE(
      DBMS_CRYPTO.HASH(UTL_RAW.CONCAT(UTL_RAW.SUBSTR(PHASH, 1, 8), PASSW), DBMS_CRYPTO.HASH_SH256),
      UTL_RAW.SUBSTR(PHASH, 9));
END;
/

REM
REM
select table_name from user_tables;
REM
REM
spool off

Use SQLPLUS to run this sql scripts.

sqlplus /nolog
@nonshard-app-schema.sql

Setup and Run the Demo Application
----------------------------------

Connect to the catalog host, switch to the oracle user.

Download the sdb_demo_app.zip file.

wget https://bit.ly/3P7Pcg3 -O sdb_demo_app.zip


--2022-07-04 06:20:12--  https://objectstorage.us-ashburn-1.oraclecloud.com/p/VEKec7t0mGwBkJX92Jn0nMptuXIlEpJ5XJA-A6C9PymRgY2LhKbjWqHeB5rVBbaV/n/c4u04/b/livelabsfiles/o/data-management-library-files/Oracle%20Sharding/sdb_demo_app.zip
Resolving objectstorage.us-ashburn-1.oraclecloud.com (objectstorage.us-ashburn-1.oraclecloud.com)... 134.70.32.1, 134.70.24.1, 134.70.28.1
Connecting to objectstorage.us-ashburn-1.oraclecloud.com (objectstorage.us-ashburn-1.oraclecloud.com)|134.70.32.1|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: 5897389 (5.6M) [application/octet-stream]
Saving to: ‘sdb_demo_app.zip.2’

100%[=====================================================================================================================>] 5,897,389   8.00MB/s   in 0.7s

2022-07-04 06:20:14 (8.00 MB/s) - ‘sdb_demo_app.zip.2’ saved [5897389/5897389]


[oracle@shd3 ~]$ ls -ltr
total 12932
drwxr-xr-x. 12 oracle oinstall    4096 Jul 23  2020 swingbench
-rw-r--r--.  1 oracle oinstall    2938 Jul  2 19:51 nonshard-app-schema.sql
-rw-r--r--.  1 oracle oinstall 5897389 Jul  6 19:04 sdb_demo_app.zip
-rw-r--r--.  1 oracle oinstall    5183 Nov 11 16:42 nonshard_app_schema.lst
-rw-r-----.  1 oracle dba      7319552 Nov 16 16:52 original.dmp
-rw-r--r--.  1 oracle dba         2360 Nov 16 16:52 original.log

Unzip the file. This will create sdb_demo_app directory under the /home/oracle.

unzip sdb_demo_app.zip

Change to the sdb_demo_app/sql directory.

cd sdb_demo_app/sql

View the content of the nonshard_demo_app_ext.sql. Make sure the connect string is correct to the non-sharded instance pdb.

cat nonshard_demo_app_ext.sql

-- Create catalog monitor packages
connect sys/Ora_DB4U@shd3:1521/nspdb as sysdba;

@catalog_monitor.sql

connect app_schema/app_schema@shd3:1521/nspdb;

alter session enable shard ddl;

CREATE OR REPLACE VIEW SAMPLE_ORDERS AS
  SELECT OrderId, CustId, OrderDate, SumTotal FROM
    (SELECT * FROM ORDERS ORDER BY OrderId DESC)
      WHERE ROWNUM < 10;

alter session disable shard ddl;

-- Allow a special query for dbaview
connect sys/Ora_DB4U@shd3:1521/nspdb as sysdba;

-- For demo app purposes
grant shard_monitor_role, gsmadmin_role to app_schema;

alter session enable shard ddl;

create user dbmonuser identified by TEZiPP4MsLLL;
grant connect, alter session, shard_monitor_role, gsmadmin_role to dbmonuser;

grant all privileges on app_schema.products to dbmonuser;
grant read on app_schema.sample_orders to dbmonuser;

alter session disable shard ddl;
-- End workaround

exec dbms_global_views.create_any_view('SAMPLE_ORDERS', 'APP_SCHEMA.SAMPLE_ORDERS', 'GLOBAL_SAMPLE_ORDERS', 0, 1);

Using SQLPLUS to run the script.


[oracle@cata sql]$ sqlplus /nolog

SQL*Plus: Release 19.0.0.0.0 - Production on Tue Nov 16 16:41:37 2021
Version 19.11.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.

SQL> @nonshard_demo_app_ext.sql

The result screen like the following. Ignore the ORA-02521 error because it''s not a shard database.

Connected.
ERROR:
ORA-02521: attempted to enable shard DDL in a non-shard database



Role created.


Grant succeeded.


Grant succeeded.


Grant succeeded.


Grant succeeded.


Session altered.


Package created.

No errors.

Package body created.

No errors.

PL/SQL procedure successfully completed.


Type created.


Type created.


Package created.

No errors.

Package body created.

No errors.

Package body created.

No errors.

Grant succeeded.


Grant succeeded.


Grant succeeded.


PL/SQL procedure successfully completed.


PL/SQL procedure successfully completed.


PL/SQL procedure successfully completed.


PL/SQL procedure successfully completed.


PL/SQL procedure successfully completed.

Connected.
ERROR:
ORA-02521: attempted to enable shard DDL in a non-shard database



View created.


Session altered.

Connected.

Grant succeeded.

ERROR:
ORA-02521: attempted to enable shard DDL in a non-shard database



User created.


Grant succeeded.


Grant succeeded.


Grant succeeded.


Session altered.


PL/SQL procedure successfully completed.

SQL>

Exit the sqlplus. Then change directory to the sdb_demo_app.

cd ~/sdb_demo_app

Review the nonsharddemo.properties file content. Make sure the connect_string and service name is correct.

cat nonsharddemo.properties

[oracle@shd3 sdb_demo_app]$ cat nonsharddemo.properties
name=demo
connect_string=(ADDRESS_LIST=(LOAD_BALANCE=off)(FAILOVER=on)(ADDRESS=(HOST=shd3)(PORT=1521)(PROTOCOL=tcp)))
monitor.user=dbmonuser
monitor.pass=TEZiPP4MsLLL
app.service.write=nspdb
app.service.readonly=nspdb
app.user=app_schema
app.pass=app_schema
app.threads=7

Start the workload by executing command: ./run.sh demo nonsharddemo.properties.

./run.sh demo nonsharddemo.properties

Wait the application run several minutes and press Ctrl-C to exit the application. Remember the values of the APS(transaction per second).

RO Queries | RW Queries | RO Failed  | RW Failed  | APS
     133194        22428            0            0          819
     135368        22801            0            0          794
     137639        23162            0            0          816
     139983        23514            0            0          857
     142154        23923            0            0          791
     144423        24326            0            0          821
     146604        24720            0            0          790
     148820        25111            0            0          812
     151074        25509            0            0          809
     153302        25899            0            0          793
     155798        26347            0            0          913
     158566        26841            0            0         1013
     161386        27335            0            0         1019
     164235        27820            0            0         1031
     167050        28272            0            0         1008
     169731        28729            0            0          976
     172676        29238            0            0         1078
     175631        29737            0            0         1083
     178483        30231            0            0         1043
     181422        30730            0            0         1074


Export the Demo Data and Copy DMP File
**************************************

In this step, you will export the demo application data and copy the dmp file to the catalog and each of the shard hosts. You will import the data to the shard database in the next lab.

Connect to the shard3 host, switch to the oracle user.

Connect to the non-sharded database as app_schema user with SQLPLUS.



sqlplus app_schema/app_schema@shd3:1521/nspdb

Create a dump directory and exit the SQLPLUS.

create directory demo_pump_dir as '/home/oracle';
exit

Run the following command to export the demo data.

GROUP_PARTITION_TABLE_DATA: Unloads all partitions as a single operation producing a single partition of data in the dump file. 
Subsequent imports will not know this was originally made up of multiple partitions.

expdp app_schema/app_schema@shd3:1521/nspdb directory=demo_pump_dir \
  dumpfile=original.dmp logfile=original.log \
  schemas=app_schema data_options=group_partition_table_data

[...]
Dump file set for APP_SCHEMA.SYS_EXPORT_SCHEMA_01 is:
  /home/oracle/original.dmp
Job "APP_SCHEMA"."SYS_EXPORT_SCHEMA_01" successfully completed at Tue Nov 16 17:06:36 2021 elapsed 0 00:01:27


From the shard3 host, create a ssh key pair. Press Enter to accept all the default values.

[oracle@shd3 sdb_demo_app]$ ssh-keygen -t rsa
Generating public/private rsa key pair.
Enter file in which to save the key (/home/oracle/.ssh/id_rsa):
Created directory '/home/oracle/.ssh'.
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /home/oracle/.ssh/id_rsa.
Your public key has been saved in /home/oracle/.ssh/id_rsa.pub.
The key fingerprint is:
SHA256:BakV9l9zcUn/FuS8evQKNoE7WhrEsFc9/74QxUGVfmE oracle@shd3
The key''s randomart image is:
+---[RSA 2048]----+
|        +o    o**|
|       .oo .  =E=|
|      .o  + o =*+|
|      .+ o o +.+=|
|      . S . o..o+|
|       o   . .+o.|
|        . + +o .o|
|         = o ooo |
|        o     ..o|
+----[SHA256]-----+

[oracle@shd3 sdb_demo_app]$ cat /home/oracle/.ssh/id_rsa.pub
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDC2EjG8bsTKnvQpjlnDtbDKFUb9X0ik3PRnW99BbDfR0vAiYp2rojcBMCed2YKzcZr5UX8x7p8HpB3u8Bp/J1wJxW/OVuww3oaSkQ8QRL60tX6KdyTbwVGwxK0YoUaCbgYemXVHGa/TjuRY/csSesTBIRuCSL1SPYBBGLCOpOnl84+PDhVsf+TxfeIFK+b0zcevr3y++1Yz96+EwS66h1RSs9d6QQ/Uf0dx4WQnbxWM5lyXdwyJKInDoBxRgoDgv/+Zo+RCOk2n0SCqqaXwTb6cA8Vimup7dmd+9e8wPX9Wo0rDIlCfdEjBStBhK2sDTtq+8ju9tXDhguiTZ53LD4f oracle@shd3
[oracle@shd3 sdb_demo_app]$

Open another terminal to connect to the cata host. Switch to oracle user.


Make a .ssh directory and edit the authorized_keys file.

[oracle@cata ~]$ mkdir .ssh
[oracle@cata ~]$ vi .ssh/authorized_keys

Copy all the content of the SSH public key from Shard3 host. Save the file and chmod the file.

[oracle@cata ~]$ chmod 600 .ssh/authorized_keys
[oracle@cata ~]$

Repeat the same steps from previous steps 8 - 10. This time connect to the shard1 and shard2 host. Create authorized_keys in each of the shard hosts.

From shard3 host side. Copy the dmp file to the catalog, shard1 and shard2 host. Press yes when prompt ask if you want to continue.

[oracle@shd3 ~]$ scp original.dmp oracle@cata:/home/oracle
original.dmp                                                                                        100%   12MB  47.6MB/s   00:00
[oracle@shd3 ~]$ scp original.dmp oracle@shd1:/home/oracle
original.dmp                                                                                        100%   12MB  49.5MB/s   00:00
[oracle@shd3 ~]$ scp original.dmp oracle@shd2:/home/oracle
original.dmp                                                                                        100%   12MB  51.4MB/s   00:00
[oracle@shd3 ~]$

    








