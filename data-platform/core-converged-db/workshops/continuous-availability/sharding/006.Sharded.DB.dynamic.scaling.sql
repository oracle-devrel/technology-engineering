Elastic Scaling

Now, we will add the shard (on shd3) to the Shard Database and thus elastically scale the SDB. 
Make sure you have done all steps in the shard3 host according to the lab 2 "Shard Database Deployment" to configure the shard host, setup shard database and validate without any error.

Add the New Shard

Connect to the catalog database host. Switch to oracle user.

Switch to the GSM environment.

. ./gsm.sh

[oracle@cata ~]$ gdsctl
GDSCTL: Version 19.0.0.0.0 - Production on Thu Nov 18 11:39:03 GMT 2021

Copyright (c) 2011, 2019, Oracle.  All rights reserved.

Welcome to GDSCTL, type "help" for information.

Current GSM is set to SHARDDIRECTOR1

GDSCTL> config shard
Catalog connection is established
Name                Shard Group         Status    State       Region    Availability
----                -----------         ------    -----       ------    ------------
shd1_shdpdb1        shardgroup_primary  Ok        Deployed    region1   ONLINE
shd2_shdpdb2        shardgroup_primary  Ok        Deployed    region1   ONLINE


GDSCTL> add cdb -connect shd3:1521/shd3 -pwd Ora_DB4U
DB Unique Name: shd3
The operation completed successfully

GDSCTL> config cdb
shd1
shd2
shd3

add shard -connect shd3:1521/shdpdb3 -pwd Ora_DB4U -shardgroup shardgroup_primary -cdb shd3

GDSCTL> add shard -connect shd3:1521/shdpdb3 -pwd Ora_DB4U -shardgroup shardgroup_primary -cdb shd3
INFO: Data Guard shard validation requested.
INFO: Database role is PRIMARY.
INFO: Database name is SHD3.
INFO: Database unique name is shd3.
INFO: Database ID is 1393551348.
INFO: Database open mode is READ WRITE.
INFO: Database in archivelog mode.
INFO: Flashback is on.
INFO: Force logging is on.
INFO: Database platform is Linux x86 64-bit.
INFO: Database character set is AL32UTF8. This value must match the character set of the catalog database.
INFO: 'compatible' initialization parameter validated successfully.
INFO: Database is a multitenant container database.
INFO: Current container is SHDPDB3.
INFO: Database is using a server parameter file (spfile).
INFO: db_create_file_dest set to: '/u01/app/oracle/oradata'
INFO: db_recovery_file_dest set to: '/u01/app/oracle/fast_recovery_area'
INFO: db_files=1024. Must be greater than the number of chunks and/or tablespaces to be created in the shard.
INFO: dg_broker_start set to TRUE.
INFO: remote_login_passwordfile set to EXCLUSIVE.
INFO: db_file_name_convert set to: '/SHDSTB3/, /SHD3/'
INFO: GSMUSER account validated successfully.
INFO: DATA_PUMP_DIR is '/u01/app/oracle/admin/shd3/dpdump/D04B9ECB98A14919E05502001701C873'.
DB Unique Name: shd3_shdpdb3
The operation completed successfully

GDSCTL> config shard
Name                Shard Group         Status    State       Region    Availability
----                -----------         ------    -----       ------    ------------
shd1_shdpdb1        shardgroup_primary  Ok        Deployed    region1   ONLINE
shd2_shdpdb2        shardgroup_primary  Ok        Deployed    region1   ONLINE
shd3_shdpdb3        shardgroup_primary  U         none        region1   -

View a list of trusted hosts.

GDSCTL> config vncr
Name                          Group ID
----                          --------
10.0.1.125
10.0.1.75
10.0.1.98
127.0.0.1
cata
shd1
shd2
shd3

The host name of shard3 is already there. Manually add shard3 private IP addresses to the shard catalog metadata.

add invitednode 10.0.1.25

GDSCTL> add invitednode 10.0.1.25
GDSCTL>
GDSCTL>
GDSCTL> config vncr
Name                          Group ID
----                          --------
10.0.1.156
10.0.1.25
10.0.1.35
10.0.1.84
127.0.0.1
cata
shd1
shd2
shd3

Deploy and Verify the New Shard.


GDSCTL> deploy
Catalog connection is established
deploy: examining configuration...
deploy: requesting Data Guard configuration on shards via GSM
deploy: shards configured; background operations in progress
The operation completed successfully
GDSCTL>

GDSCTL> config shard
Name                Shard Group         Status    State       Region    Availability
----                -----------         ------    -----       ------    ------------
shd1_shdpdb1        shardgroup_primary  Ok        Deployed    region1   ONLINE
shd2_shdpdb2        shardgroup_primary  Ok        Deployed    region1   ONLINE
shd3_shdpdb3        shardgroup_primary  Ok        Deployed    region1   ONLINE

Run the following command every minute or two to see the progress of automatic rebalancing of chunks. You can see there are 4 chunks need to move to the third shard.

GDSCTL> config chunks -show_reshard
Chunks
------------------------
Database                      From      To
--------                      ----      --
shd1_shdpdb1                  1         5
shd2_shdpdb2                  7         12
shd3_shdpdb3                  6         6

Ongoing chunk movement
------------------------
Chunk     Source                        Target                        status
-----     ------                        ------                        ------
5         shd1_shdpdb1                  shd3_shdpdb3                  scheduled
6         shd1_shdpdb1                  shd3_shdpdb3                  Running
11        shd2_shdpdb2                  shd3_shdpdb3                  scheduled
12        shd2_shdpdb2                  shd3_shdpdb3                  scheduled

GDSCTL> config chunks -show_reshard
Chunks
------------------------
Database                      From      To
--------                      ----      --
shd1_shdpdb1                  1         5
shd2_shdpdb2                  7         12
shd3_shdpdb3                  6         6

Ongoing chunk movement
------------------------
Chunk     Source                        Target                        status
-----     ------                        ------                        ------
5         shd1_shdpdb1                  shd3_shdpdb3                  Running
11        shd2_shdpdb2                  shd3_shdpdb3                  scheduled
12        shd2_shdpdb2                  shd3_shdpdb3                  scheduled

GDSCTL> config chunks -show_reshard
Chunks
------------------------
Database                      From      To
--------                      ----      --
shd1_shdpdb1                  1         4
shd2_shdpdb2                  7         12
shd3_shdpdb3                  5         6

Ongoing chunk movement
------------------------
Chunk     Source                        Target                        status
-----     ------                        ------                        ------
11        shd2_shdpdb2                  shd3_shdpdb3                  scheduled
12        shd2_shdpdb2                  shd3_shdpdb3                  Running

GDSCTL> config chunks -show_reshard
Chunks
------------------------
Database                      From      To
--------                      ----      --
shd1_shdpdb1                  1         4
shd2_shdpdb2                  7         11
shd3_shdpdb3                  5         6
shd3_shdpdb3                  12        12

Ongoing chunk movement
------------------------
Chunk     Source                        Target                        status
-----     ------                        ------                        ------
11        shd2_shdpdb2                  shd3_shdpdb3                  Running

After a few minutes, chunks end up rebalanced on the new shard !!!

GDSCTL> config chunks -show_reshard
Chunks
------------------------
Database                      From      To
--------                      ----      --
shd1_shdpdb1                  1         4
shd2_shdpdb2                  7         10
shd3_shdpdb3                  5         6
shd3_shdpdb3                  11        12

Ongoing chunk movement
------------------------
Chunk     Source                        Target                        status
-----     ------                        ------                        ------

GDSCTL>

Observe that the “databases” are automatically registered.

GDSCTL> databases
Database: "shd1_shdpdb1" Registered: Y State: Ok ONS: N. Role: PRIMARY Instances: 1 Region: region1
   Service: "oltp_rw_srvc" Globally started: Y Started: Y
            Scan: N Enabled: Y Preferred: Y
   Registered instances:
     orasdb%1
Database: "shd2_shdpdb2" Registered: Y State: Ok ONS: N. Role: PRIMARY Instances: 1 Region: region1
   Service: "oltp_rw_srvc" Globally started: Y Started: Y
            Scan: N Enabled: Y Preferred: Y
   Registered instances:
     orasdb%11
Database: "shd3_shdpdb3" Registered: Y State: Ok ONS: N. Role: PRIMARY Instances: 1 Region: region1
   Service: "oltp_rw_srvc" Globally started: Y Started: Y
            Scan: N Enabled: Y Preferred: Y
   Registered instances:
     orasdb%21

Observe that the “services” are automatically brought up on the newly added shard.

GDSCTL> services
Service "oltp_rw_srvc.orasdb.oradbcloud" has 3 instance(s). Affinity: ANYWHERE
   Instance "orasdb%1", name: "shd1", db: "shd1_shdpdb1", region: "region1", status: ready.
   Instance "orasdb%11", name: "shd2", db: "shd2_shdpdb2", region: "region1", status: ready.
   Instance "orasdb%21", name: "shd3", db: "shd3_shdpdb3", region: "region1", status: ready.


Run the Demo Application Again

. ./cata.sh

Manually update the monitored shard list. The package dbms_global_views is used by the monitor tools to monitor the status of shards. 
It will create a public shard_dblinks_view and a public dblink to each shard. If you skip this step, the monitor tools will not show the status of the latest added shard database.

[oracle@cata ~]$ sqlplus / as sysdba

SQL*Plus: Release 19.0.0.0.0 - Production on Thu Nov 18 13:06:58 2021
Version 19.11.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.


Connected to:
Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
Version 19.11.0.0.0

SQL> alter session set container=catapdb;

Session altered.

SQL> exec dbms_global_views.create_all_database_links();

PL/SQL procedure successfully completed.

SQL>

cd sdb_demo_app

[oracle@cata sdb_demo_app]$ ./run.sh demo sdbdemo.properties
 RO Queries | RW Queries | RO Failed  | RW Failed  | APS
     195539        34027            0            0         1601
     199379        34670            0            0         1587
     203113        35358            0            0         1524
     206903        36066            0            0         1548
     210737        36786            0            0         1595
     214500        37493            0            0         1544
     218492        38189            0            0         1639
     222401        38859            0            0         1613
     226386        39517            0            0         1635
     230349        40210            0            0         1614
     234115        40891            0            0         1560
     237785        41507            0            0         1536
     241644        42146            0            0         1567
     245335        42785            0            0         1556



