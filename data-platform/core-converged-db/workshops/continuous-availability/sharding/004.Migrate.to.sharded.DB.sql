Re-Design and Create the Demo Schema
************************************

Before the existing database can be migrated to the sharded database, you must decide how to organize the sharded database. 
You must decide which tables in the application are sharded and which tables are duplicated tables. In this lab, we have already created a scripts for the sharded demo schema. 
It creates a sharded table family: Customers-->Orders-->LineItems using the sharding key CustId, and the Products is the duplicated table.

Login to the catalog database host, switch to oracle user.

Download the sharded demo schema SQL scripts sdb-app-schema.sql.


wget https://bit.ly/3yKp59X -O sdb-app-schema.sql

[oracle@cata ~]$ wget https://bit.ly/3yKp59X -O sdb-app-schema.sql

--2022-07-04 13:07:34--  https://objectstorage.us-ashburn-1.oraclecloud.com/p/VEKec7t0mGwBkJX92Jn0nMptuXIlEpJ5XJA-A6C9PymRgY2LhKbjWqHeB5rVBbaV/n/c4u04/b/livelabsfiles/o/data-management-library-files/Oracle%20Sharding/sdb-app-schema.sql
Resolving objectstorage.us-ashburn-1.oraclecloud.com (objectstorage.us-ashburn-1.oraclecloud.com)... 134.70.32.1, 134.70.24.1, 134.70.28.1
Connecting to objectstorage.us-ashburn-1.oraclecloud.com (objectstorage.us-ashburn-1.oraclecloud.com)|134.70.32.1|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: 3554 (3.5K) [application/octet-stream]
Saving to: ‘sdb-app-schema.sql.1’

100%[=====================================================================================================================>] 3,554       --.-K/s   in 0s

2022-07-04 13:07:35 (40.4 MB/s) - ‘sdb-app-schema.sql.1’ saved [3554/3554]

[oracle@cata ~]$ ls -ltr
total 955464
drwxr-xr-x.  5 oracle oinstall        90 Apr 17  2019 gsm
drwxr-xr-x. 12 oracle oinstall      4096 Jul 23  2020 swingbench
-rw-r--r--.  1 oracle oinstall      3554 Jul  2 19:51 sdb-app-schema.sql
-rw-r--r--.  1 oracle oinstall   5897389 Jul  6 19:04 sdb_demo_app.zip
-rw-r--r--.  1 oracle oinstall       166 Nov 10 10:20 cata.sh
-rw-r--r--.  1 oracle oinstall 959891519 Nov 11 08:48 GSM.19.3.V982067-01.zip
-rw-r--r--.  1 oracle oinstall       167 Nov 11 09:18 gsm.sh
drwxr-xr-x.  3 oracle oinstall        26 Nov 16 16:39 __MACOSX
drwxr-xr-x.  9 oracle oinstall      4096 Nov 16 16:46 sdb_demo_app
-rw-r-----.  1 oracle oinstall  12582912 Nov 16 17:28 original.dmp
[oracle@cata ~]$

Use SQLPLUS to run this sql scripts

[oracle@cata ~]$ sqlplus /nolog

SQL*Plus: Release 19.0.0.0.0 - Production on Wed Nov 17 09:59:48 2021
Version 19.11.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.

SQL> @sdb-app-schema.sql
SQL> set termout on
SQL> set time on
10:00:00 SQL> spool /home/oracle/sdb_app_schema.lst
10:00:00 SQL> REM
10:00:00 SQL> REM Connect to the Shard Catalog and Create Schema
10:00:00 SQL> REM
10:00:00 SQL> connect / as sysdba
Connected.
10:00:00 SQL> alter session set container=catapdb;

Session altered.

10:00:00 SQL> alter session enable shard ddl;

Session altered.

10:00:00 SQL> create user app_schema identified by app_schema;

User created.

10:00:01 SQL> grant connect, resource, alter session to app_schema;

Grant succeeded.

10:00:01 SQL> grant execute on dbms_crypto to app_schema;

Grant succeeded.

10:00:01 SQL> grant create table, create procedure, create tablespace, create materialized view to app_schema;

Grant succeeded.

10:00:01 SQL> grant unlimited tablespace to app_schema;

Grant succeeded.

10:00:01 SQL> grant select_catalog_role to app_schema;

Grant succeeded.

10:00:01 SQL> grant all privileges to app_schema;

Grant succeeded.

10:00:01 SQL> grant gsmadmin_role to app_schema;

Grant succeeded.

10:00:01 SQL> grant dba to app_schema;

Grant succeeded.

10:00:01 SQL>
10:00:01 SQL>
10:00:01 SQL> REM
10:00:01 SQL> REM Create a tablespace set for SHARDED tables
10:00:01 SQL> REM
10:00:01 SQL> CREATE TABLESPACE SET  TSP_SET_1 using template (datafile size 100m autoextend on next 10M maxsize unlimited extent management	local segment space management auto );

Tablespace created.

10:00:02 SQL>
10:00:02 SQL> REM
10:00:02 SQL> REM Create a tablespace for DUPLICATED tables
10:00:02 SQL> REM
10:00:02 SQL> CREATE TABLESPACE products_tsp datafile size 100m autoextend on next 10M maxsize unlimited extent management local uniform size 1m;

Tablespace created.

10:00:03 SQL>
10:00:03 SQL> REM
10:00:03 SQL> REM Create Sharded and Duplicated tables
10:00:03 SQL> REM
10:00:03 SQL> connect app_schema/app_schema@catapdb
Connected.
10:00:03 SQL> alter session enable shard ddl;

Session altered.

10:00:03 SQL> REM
10:00:03 SQL> REM Create a Sharded table for Customers	(Root table)
10:00:03 SQL> REM
10:00:03 SQL> CREATE SHARDED TABLE Customers
10:00:03   2  (
10:00:03   3  	CustId	    VARCHAR2(60) NOT NULL,
10:00:03   4  	FirstName   VARCHAR2(60),
10:00:03   5  	LastName    VARCHAR2(60),
10:00:03   6  	Class	    VARCHAR2(10),
10:00:03   7  	Geo	    VARCHAR2(8),
10:00:03   8  	CustProfile VARCHAR2(4000),
10:00:03   9  	Passwd	    RAW(60),
10:00:03  10  	CONSTRAINT pk_customers PRIMARY KEY (CustId),
10:00:03  11  	CONSTRAINT json_customers CHECK (CustProfile IS JSON)
10:00:03  12  ) TABLESPACE SET TSP_SET_1
10:00:03  13  PARTITION BY CONSISTENT HASH (CustId) PARTITIONS AUTO;

Table created.

10:00:04 SQL>
10:00:04 SQL> REM
10:00:04 SQL> REM Create a Sharded table for Orders
10:00:04 SQL> REM
10:00:04 SQL> CREATE SHARDED TABLE Orders
10:00:04   2  (
10:00:04   3  	OrderId     INTEGER NOT NULL,
10:00:04   4  	CustId	    VARCHAR2(60) NOT NULL,
10:00:04   5  	OrderDate   TIMESTAMP NOT NULL,
10:00:04   6  	SumTotal    NUMBER(19,4),
10:00:04   7  	Status	    CHAR(4),
10:00:04   8  	constraint  pk_orders primary key (CustId, OrderId),
10:00:04   9  	constraint  fk_orders_parent foreign key (CustId)
10:00:04  10  	  references Customers on delete cascade
10:00:04  11  ) partition by reference (fk_orders_parent);

Table created.

10:00:04 SQL>
10:00:04 SQL> REM
10:00:04 SQL> REM Create the sequence used for the OrderId column
10:00:04 SQL> REM
10:00:04 SQL> CREATE SEQUENCE Orders_Seq;

Sequence created.

10:00:04 SQL>
10:00:04 SQL> REM
10:00:04 SQL> REM Create a Sharded table for LineItems
10:00:04 SQL> REM
10:00:04 SQL> CREATE SHARDED TABLE LineItems
10:00:04   2  (
10:00:04   3  	OrderId     INTEGER NOT NULL,
10:00:04   4  	CustId	    VARCHAR2(60) NOT NULL,
10:00:04   5  	ProductId   INTEGER NOT NULL,
10:00:04   6  	Price	    NUMBER(19,4),
10:00:04   7  	Qty	    NUMBER,
10:00:04   8  	constraint  pk_items primary key (CustId, OrderId, ProductId),
10:00:04   9  	constraint  fk_items_parent foreign key (CustId, OrderId)
10:00:04  10  	  references Orders on delete cascade
10:00:04  11  ) partition by reference (fk_items_parent);

Table created.

10:00:04 SQL>
10:00:04 SQL> REM
10:00:04 SQL> REM Create Duplicated table for Products
10:00:04 SQL> REM
10:00:04 SQL> CREATE DUPLICATED TABLE Products
10:00:04   2  (
10:00:04   3  	ProductId  INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
10:00:04   4  	Name	   VARCHAR2(128),
10:00:04   5  	DescrUri   VARCHAR2(128),
10:00:04   6  	LastPrice  NUMBER(19,4)
10:00:04   7  ) TABLESPACE products_tsp;

Table created.

10:00:05 SQL>
10:00:05 SQL> REM
10:00:05 SQL> REM Create functions for Password creation and checking – used by the REM demo loader application
10:00:05 SQL> REM
10:00:05 SQL>
10:00:05 SQL> CREATE OR REPLACE FUNCTION PasswCreate(PASSW IN RAW)
10:00:05   2  	RETURN RAW
10:00:05   3  IS
10:00:05   4  	Salt RAW(8);
10:00:05   5  BEGIN
10:00:05   6  	Salt := DBMS_CRYPTO.RANDOMBYTES(8);
10:00:05   7  	RETURN UTL_RAW.CONCAT(Salt, DBMS_CRYPTO.HASH(UTL_RAW.CONCAT(Salt, PASSW), DBMS_CRYPTO.HASH_SH256));
10:00:05   8  END;
10:00:05   9  /

Function created.

10:00:05 SQL>
10:00:05 SQL> CREATE OR REPLACE FUNCTION PasswCheck(PASSW IN RAW, PHASH IN RAW)
10:00:05   2  	RETURN INTEGER IS
10:00:05   3  BEGIN
10:00:05   4  	RETURN UTL_RAW.COMPARE(
10:00:05   5  	    DBMS_CRYPTO.HASH(UTL_RAW.CONCAT(UTL_RAW.SUBSTR(PHASH, 1, 8), PASSW), DBMS_CRYPTO.HASH_SH256),
10:00:05   6  	    UTL_RAW.SUBSTR(PHASH, 9));
10:00:05   7  END;
10:00:05   8  /

Function created.

10:00:05 SQL>
10:00:05 SQL> REM
10:00:05 SQL> REM
10:00:05 SQL> select table_name from user_tables;

TABLE_NAME
--------------------------------------------------------------------------------
CUSTOMERS
ORDERS
LINEITEMS
PRODUCTS
MLOG$_PRODUCTS
RUPD$_PRODUCTS

6 rows selected.

10:00:05 SQL> REM
10:00:05 SQL> REM
10:00:05 SQL> spool off
10:00:05 SQL>

Verify the Sharded Demo Schema
******************************

Switch to the GSM environment, run GDSCTL.

. ./gsm.sh
gdsctl

[oracle@cata ~]$ . ./gsm.sh
[oracle@cata ~]$
[oracle@cata ~]$
[oracle@cata ~]$ gdsctl
GDSCTL: Version 19.0.0.0.0 - Production on Wed Nov 17 11:17:51 GMT 2021

Copyright (c) 2011, 2019, Oracle.  All rights reserved.

Welcome to GDSCTL, type "help" for information.

Current GSM is set to SHARDDIRECTOR1
GDSCTL> show ddl
Catalog connection is established
id      DDL Text                                 Failed shards
--      --------                                 -------------
9       grant dba to app_schema
10      CREATE TABLESPACE SET  TSP_SET_1 usin...
11      CREATE TABLESPACE products_tsp datafi...
12      CREATE SHARDED TABLE Customers (   Cu...
13      CREATE SHARDED TABLE Orders (   Order...
14      CREATE SEQUENCE Orders_Seq
15      CREATE SHARDED TABLE LineItems (   Or...
16      CREATE MATERIALIZED VIEW "APP_SCHEMA"...
17      CREATE OR REPLACE FUNCTION PasswCreat...
18      CREATE OR REPLACE FUNCTION PasswCheck...

GDSCTL>

Run the config commands as shown below for each of the shards and verify if there are any DDL error.

GDSCTL> config shard -shard shd1_shdpdb1
Name: shd1_shdpdb1
Shard Group: shardgroup_primary
Status: Ok
State: Deployed
Region: region1
Connection string: shd1:1521/shdpdb1
SCAN address:
ONS remote port: 0
Disk Threshold, ms: 20
CPU Threshold, %: 75
Version: 19.0.0.0
Failed DDL:
DDL Error: ---
Failed DDL id:
Availability: ONLINE
Rack:


Supported services
------------------------
Name                                                            Preferred Status
----                                                            --------- ------
oltp_rw_srvc                                                    Yes       Enabled


Show the created chunks.

GDSCTL> config chunks
Chunks
------------------------
Database                      From      To
--------                      ----      --
shd1_shdpdb1                  1         6
shd2_shdpdb2                  7         12


Connect to the shard pdb1.

Check the created tablespace set.

[oracle@cata ~]$ sqlplus sys/Ora_DB4U@shd1:1521/shdpdb1 as sysdba

SQL*Plus: Release 19.0.0.0.0 - Production on Wed Nov 17 13:02:08 2021
Version 19.3.0.0.0

Copyright (c) 1982, 2019, Oracle.  All rights reserved.


Connected to:
Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
Version 19.11.0.0.0

SQL> select TABLESPACE_NAME, BYTES/1024/1024 MB from sys.dba_data_files order by tablespace_name;

TABLESPACE_NAME 		       MB
------------------------------ ----------
C001TSP_SET_1			      100
C002TSP_SET_1			      100
C003TSP_SET_1			      100
C004TSP_SET_1			      100
C005TSP_SET_1			      100
C006TSP_SET_1			      100
PRODUCTS_TSP			      100
SYSAUX				      520
SYSTEM				      350
TSP_SET_1			      100
UNDOTBS1			      215

TABLESPACE_NAME 		       MB
------------------------------ ----------
USERS					5

12 rows selected.

Verify that the chunks and chunk tablespaces are created.

set linesize 140
column table_name format a20
column tablespace_name format a20
column partition_name format a20
select table_name, partition_name, tablespace_name from dba_tab_partitions where tablespace_name like 'C%TSP_SET_1' order by tablespace_name;

TABLE_NAME	     PARTITION_NAME	  TABLESPACE_NAME
-------------------- -------------------- --------------------
LINEITEMS	     CUSTOMERS_P1	  C001TSP_SET_1
CUSTOMERS	     CUSTOMERS_P1	  C001TSP_SET_1
ORDERS		     CUSTOMERS_P1	  C001TSP_SET_1
CUSTOMERS	     CUSTOMERS_P2	  C002TSP_SET_1
ORDERS		     CUSTOMERS_P2	  C002TSP_SET_1
LINEITEMS	     CUSTOMERS_P2	  C002TSP_SET_1
CUSTOMERS	     CUSTOMERS_P3	  C003TSP_SET_1
LINEITEMS	     CUSTOMERS_P3	  C003TSP_SET_1
ORDERS		     CUSTOMERS_P3	  C003TSP_SET_1
LINEITEMS	     CUSTOMERS_P4	  C004TSP_SET_1
CUSTOMERS	     CUSTOMERS_P4	  C004TSP_SET_1

TABLE_NAME	     PARTITION_NAME	  TABLESPACE_NAME
-------------------- -------------------- --------------------
ORDERS		     CUSTOMERS_P4	  C004TSP_SET_1
CUSTOMERS	     CUSTOMERS_P5	  C005TSP_SET_1
ORDERS		     CUSTOMERS_P5	  C005TSP_SET_1
LINEITEMS	     CUSTOMERS_P5	  C005TSP_SET_1
CUSTOMERS	     CUSTOMERS_P6	  C006TSP_SET_1
ORDERS		     CUSTOMERS_P6	  C006TSP_SET_1
LINEITEMS	     CUSTOMERS_P6	  C006TSP_SET_1

18 rows selected.

Connect to the shard pdb2.

SQL> connect sys/Ora_DB4U@shd2:1521/shdpdb2 as sysdba
Connected.
SQL> select TABLESPACE_NAME, BYTES/1024/1024 MB from sys.dba_data_files order by tablespace_name;

TABLESPACE_NAME 	     MB
-------------------- ----------
C007TSP_SET_1		    100
C008TSP_SET_1		    100
C009TSP_SET_1		    100
C00ATSP_SET_1		    100
C00BTSP_SET_1		    100
C00CTSP_SET_1		    100
PRODUCTS_TSP		    100
SYSAUX			    530
SYSTEM			    350
TSP_SET_1		    100
UNDOTBS1		    215

TABLESPACE_NAME 	     MB
-------------------- ----------
USERS			      5

12 rows selected.

SQL> select table_name, partition_name, tablespace_name from dba_tab_partitions where tablespace_name like 'C%TSP_SET_1' order by tablespace_name;

TABLE_NAME	     PARTITION_NAME	  TABLESPACE_NAME
-------------------- -------------------- --------------------
ORDERS		     CUSTOMERS_P7	  C007TSP_SET_1
LINEITEMS	     CUSTOMERS_P7	  C007TSP_SET_1
CUSTOMERS	     CUSTOMERS_P7	  C007TSP_SET_1
ORDERS		     CUSTOMERS_P8	  C008TSP_SET_1
CUSTOMERS	     CUSTOMERS_P8	  C008TSP_SET_1
LINEITEMS	     CUSTOMERS_P8	  C008TSP_SET_1
LINEITEMS	     CUSTOMERS_P9	  C009TSP_SET_1
ORDERS		     CUSTOMERS_P9	  C009TSP_SET_1
CUSTOMERS	     CUSTOMERS_P9	  C009TSP_SET_1
LINEITEMS	     CUSTOMERS_P10	  C00ATSP_SET_1
ORDERS		     CUSTOMERS_P10	  C00ATSP_SET_1

TABLE_NAME	     PARTITION_NAME	  TABLESPACE_NAME
-------------------- -------------------- --------------------
CUSTOMERS	     CUSTOMERS_P10	  C00ATSP_SET_1
ORDERS		     CUSTOMERS_P11	  C00BTSP_SET_1
LINEITEMS	     CUSTOMERS_P11	  C00BTSP_SET_1
CUSTOMERS	     CUSTOMERS_P11	  C00BTSP_SET_1
LINEITEMS	     CUSTOMERS_P12	  C00CTSP_SET_1
CUSTOMERS	     CUSTOMERS_P12	  C00CTSP_SET_1
ORDERS		     CUSTOMERS_P12	  C00CTSP_SET_1

18 rows selected.


Connect to the shardcatalog.

Query the gsmadmin_internal.chunk_loc table to observe that the chunks are uniformly distributed.

connect sys/Ora_DB4U@cata:1521/catapdb as sysdba

column shard format a40

select a.name Shard,count( b.chunk_number) Number_of_Chunks from gsmadmin_internal.database a, gsmadmin_internal.chunk_loc b where a.database_num=b.database_num group by a.name;

SHARD					 NUMBER_OF_CHUNKS
---------------------------------------- ----------------
shd1_shdpdb1						6
shd2_shdpdb2						6


Connect into the appschema/appschema on the catadb, shard1, shard2 databases and verify that the sharded and duplicated tables are created.

SQL> connect app_schema/app_schema@cata:1521/catapdb
Connected.
SQL> select table_name from user_tables;

TABLE_NAME
--------------------
CUSTOMERS
ORDERS
LINEITEMS
PRODUCTS
MLOG$_PRODUCTS
RUPD$_PRODUCTS

6 rows selected.

SQL> connect app_schema/app_schema@shd1:1521/shdpdb1
Connected.
SQL> select table_name from user_tables;

TABLE_NAME
--------------------
CUSTOMERS
ORDERS
LINEITEMS
PRODUCTS
USLOG$_PRODUCTS

SQL> connect app_schema/app_schema@shd2:1521/shdpdb2
Connected.
SQL> select table_name from user_tables;

TABLE_NAME
--------------------
CUSTOMERS
ORDERS
LINEITEMS
PRODUCTS
USLOG$_PRODUCTS

Migrate Data to the Sharded Tables
**********************************

Now, we will load data into sharded database using the dump file which created in the previous lab. 
The duplicated tables reside in the shard catalog, they are always loaded into the shard catalog database using any of available data loading utilities, or plain SQL.
When loading a sharded table, each database shard accommodates a distinct subset of the data set, so the data in each table must be split (partitioned) across shards during the load. 
You can use the Oracle Data Pump utility to load the data across database shards in subsets. 
Data from the source database can be exported into a Data Pump dump file. Then Data Pump import can be run on each shard concurrently by using the same dump file.
Loading the data directly into the database shards is much faster, because each shard is loaded separately. 
The Data Pump Import detects that you are importing into a shard and only load rows that belong to that shard. 

Use SQLPLUS, connect to the catalog pdb with app_schema user.

Create a data pump directory. When shard ddl enabled, it will be created in catalog db and each of the sharded db. Exit the SQLPLUS.

. ./cata.sh
sqlplus app_schema/app_schema@cata:1521/catapdb
alter session enable shard ddl;
create directory demo_pump_dir as '/home/oracle';
exit



From the catalog host, run the following command to import the public table data.

[oracle@cata ~]$ impdp app_schema/app_schema@cata:1521/catapdb directory=demo_pump_dir \
dumpfile=original.dmp logfile=imp.log \
tables=Products \
content=DATA_ONLY

Import: Release 19.0.0.0.0 - Production on Thu Nov 18 10:27:58 2021
Version 19.11.0.0.0

Copyright (c) 1982, 2019, Oracle and/or its affiliates.  All rights reserved.

Connected to: Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
Master table "APP_SCHEMA"."SYS_IMPORT_TABLE_01" successfully loaded/unloaded
Starting "APP_SCHEMA"."SYS_IMPORT_TABLE_01":  app_schema/********@cata:1521/catapdb directory=demo_pump_dir dumpfile=original.dmp logfile=imp.log tables=Products content=DATA_ONLY
*/
Processing object type SCHEMA_EXPORT/TABLE/TABLE_DATA
. . imported "APP_SCHEMA"."PRODUCTS"                     27.25 KB     480 rows
Job "APP_SCHEMA"."SYS_IMPORT_TABLE_01" successfully completed at Thu Nov 18 10:28:13 2021 elapsed 0 00:00:10


Run the following command to import data into the shard1 tables.

impdp app_schema/app_schema@shd1:1521/shdpdb1 directory=demo_pump_dir \
      dumpfile=original.dmp logfile=imp.log \
      tables=Customers, Orders, LineItems \
      content=DATA_ONLY

Import: Release 19.0.0.0.0 - Production on Thu Nov 18 10:29:46 2021
Version 19.11.0.0.0

Copyright (c) 1982, 2019, Oracle and/or its affiliates.  All rights reserved.

Connected to: Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
Master table "APP_SCHEMA"."SYS_IMPORT_TABLE_01" successfully loaded/unloaded
Starting "APP_SCHEMA"."SYS_IMPORT_TABLE_01":  app_schema/********@shd1:1521/shdpdb1 directory=demo_pump_dir dumpfile=original.dmp logfile=imp.log tables=Customers, Orders, LineItems content=DATA_ONLY
*/
Processing object type SCHEMA_EXPORT/TABLE/TABLE_DATA
. . imported "APP_SCHEMA"."CUSTOMERS"                    6.169 MB   13717 out of 27430 rows   <====== Roughly half of the rows are loaded into shard1
. . imported "APP_SCHEMA"."ORDERS"                       2.118 MB   21188 out of 42386 rows
. . imported "APP_SCHEMA"."LINEITEMS"                    3.027 MB   38011 out of 76034 rows
Job "APP_SCHEMA"."SYS_IMPORT_TABLE_01" successfully completed at Thu Nov 18 10:30:19 2021 elapsed 0 00:00:28

Run the following command to load data into shard2 tables.

[oracle@cata ~]$ impdp app_schema/app_schema@shd2:1521/shdpdb2 directory=demo_pump_dir \
dumpfile=original.dmp logfile=imp.log \
tables=Customers, Orders, LineItems \
content=DATA_ONLY

Import: Release 19.0.0.0.0 - Production on Thu Nov 18 10:31:03 2021
Version 19.11.0.0.0

Copyright (c) 1982, 2019, Oracle and/or its affiliates.  All rights reserved.

Connected to: Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
Master table "APP_SCHEMA"."SYS_IMPORT_TABLE_01" successfully loaded/unloaded
Starting "APP_SCHEMA"."SYS_IMPORT_TABLE_01":  app_schema/********@shd2:1521/shdpdb2 directory=demo_pump_dir dumpfile=original.dmp logfile=imp.log tables=Customers, Orders, LineItems content=DATA_ONLY
*/
Processing object type SCHEMA_EXPORT/TABLE/TABLE_DATA
. . imported "APP_SCHEMA"."CUSTOMERS"                    6.169 MB   13713 out of 27430 rows   <====== Roughly half of the rows are loaded into shard2
. . imported "APP_SCHEMA"."ORDERS"                       2.118 MB   21198 out of 42386 rows
. . imported "APP_SCHEMA"."LINEITEMS"                    3.027 MB   38023 out of 76034 rows
Job "APP_SCHEMA"."SYS_IMPORT_TABLE_01" successfully completed at Thu Nov 18 10:31:37 2021 elapsed 0 00:00:30

Setup and Run the Demo Application

Migrate application to the sharded database a slight change to the application code. 
In this workshop, the demo application is designed for sharded database. You need to create additional objects needed by the demo application.

From the catalog host, make sure your are in the catalog environment.

. ./cata.sh
cd ~/sdb_demo_app/sql

View the content of the sdb_demo_app_ext.sql. Make sure the connect string is correct.

cat sdb_demo_app_ext.sql

-- Create catalog monitor packages
connect / as sysdba
alter session set container=catapdb;

@catalog_monitor.sql

connect app_schema/app_schema@cata:1521/catapdb;

alter session enable shard ddl;

CREATE OR REPLACE VIEW SAMPLE_ORDERS AS
  SELECT OrderId, CustId, OrderDate, SumTotal FROM
    (SELECT * FROM ORDERS ORDER BY OrderId DESC)
      WHERE ROWNUM < 10;

alter session disable shard ddl;

-- Allow a special query for dbaview
connect / as sysdba
alter session set container=catapdb;

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

sqlplus /nolog
@sdb_demo_app_ext.sql

Exit the sqlplus. Change directory to the sdb_demo_app.

cd ~/sdb_demo_app

[oracle@cata sdb_demo_app]$ cat sdbdemo.properties
name=demo
connect_string=(ADDRESS_LIST=(LOAD_BALANCE=off)(FAILOVER=on)(ADDRESS=(HOST=localhost)(PORT=1522)(PROTOCOL=tcp)))
monitor.user=dbmonuser
monitor.pass=TEZiPP4MsLLL
#app.service.write=oltp_rw_srvc.cust_sdb.oradbcloud
app.service.write=oltp_rw_srvc.orasdb.oradbcloud
#app.service.readonly=oltp_rw_srvc.cust_sdb.oradbcloud
app.service.readonly=oltp_rw_srvc.orasdb.oradbcloud
app.user=app_schema
app.pass=app_schema
app.threads=7

Start the workload by executing the command.

./run.sh demo sdbdemo.properties

RO Queries | RW Queries | RO Failed  | RW Failed  | APS
     217471        37038            0            0         1338
     221685        37782            0            0         1573
     226016        38510            0            0         1620
     230522        39264            0            0         1697
     235169        39980            0            0         1749
     239513        40703            0            0         1653
     243503        41472            0            0         1488
     247781        42238            0            0         1617
     252090        43001            0            0         1628
     256371        43791            0            0         1635
     260649        44523            0            0         1604
     264750        45230            0            0         1540
     268903        45943            0            0         1587
     273267        46659            0            0         1689
     277461        47343            0            0         1591
     281727        48096            0            0         1619
     286116        48777            0            0         1651

Open another terminal, connect to the catalog host, switch to oracle user. Change the directory to sdb_demo_app.

Start the monitoring tool via the following command. Ignore the FileNotFoundException message. 
(Note: due to the resource limit, start monitor may impact the demo application performance).

cd ~/sdb_demo_app
./run.sh monitor sdbdemo.properties

http://130.61.44.229:8081/

