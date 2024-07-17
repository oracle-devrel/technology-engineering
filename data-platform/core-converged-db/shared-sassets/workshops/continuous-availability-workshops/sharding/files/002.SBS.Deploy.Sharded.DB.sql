Now, we have 4 database instances. We will use cata as the catalog database, shd1 and shd2 use as the shard database. The shd3 use as the third shard which will be add to the shard database in the last lab.

The 4 database instances sample information like this:

Public IP       Private IP  Hostname    CDB Name    PDB Name
<public_ip> 	<private_ip>  	cata 	    cata 	    catapdb
<public_ip>  	<private_ip> 	  shd1 	    shd1 	    shdpdb1
<public_ip>  	<private_ip> 	  shd2 	    shd2 	    shdpdb2
<public_ip>  	<private_ip> 	  shd3 	    shd3 	    shdpdb3


-- Configure the shard hosts:

-- Connect to the catalog host and each of the shard hosts with root user. edit the /etc/hosts file.

-- Edit /etc/hosts and add the private IP and name of all the 4 hosts !!!

<private_ip> cata
<private_ip> shd1
<private_ip> shd2
<private_ip> shd3

For each of the shard host(shard1, shard2, shard3), open 1521 port.

sudo firewall-cmd --add-port=1521/tcp --permanent
sudo firewall-cmd --reload
sudo firewall-cmd --list-all

[opc@shd1 ~]$ sudo firewall-cmd --add-port=1521/tcp --permanent
success
[opc@shd1 ~]$ sudo firewall-cmd --reload
success
[opc@shd1 ~]$ sudo firewall-cmd --list-all
public (active)
  target: default
  icmp-block-inversion: no
  interfaces: ens3
  sources:
  services: dhcpv6-client ssh
  ports: 1521/tcp
  protocols:
  masquerade: no
  forward-ports:
  source-ports:
  icmp-blocks:
  rich rules:

[opc@shd2 ~]$ sudo firewall-cmd --add-port=1521/tcp --permanent
success
[opc@shd2 ~]$ sudo firewall-cmd --reload
success
[opc@shd2 ~]$ sudo firewall-cmd --list-all
public (active)
  target: default
  icmp-block-inversion: no
  interfaces: ens3
  sources:
  services: dhcpv6-client ssh
  ports: 1521/tcp
  protocols:
  masquerade: no
  forward-ports:
  source-ports:
  icmp-blocks:
  rich rules:

[opc@shd3 ~]$ sudo firewall-cmd --add-port=1521/tcp --permanent
success
[opc@shd3 ~]$ sudo firewall-cmd --reload
success
[opc@shd3 ~]$ sudo firewall-cmd --list-all
public (active)
  target: default
  icmp-block-inversion: no
  interfaces: ens3
  sources:
  services: dhcpv6-client ssh
  ports: 1521/tcp
  protocols:
  masquerade: no
  forward-ports:
  source-ports:
  icmp-blocks:
  rich rules:

For the catalog host, we will install GSM in the same hosts, The default listener port of the shard director is 1522, so we need open 1522 port for gsm host. There is a demo application which need open the 8081 port.

sudo firewall-cmd --add-port=1521/tcp --permanent
sudo firewall-cmd --add-port=1522/tcp --permanent
sudo firewall-cmd --add-port=8081/tcp --permanent
sudo firewall-cmd --reload
sudo firewall-cmd --list-all

[opc@cata ~]$ sudo firewall-cmd --add-port=1521/tcp --permanent
success
[opc@cata ~]$ sudo firewall-cmd --add-port=1522/tcp --permanent
success
[opc@cata ~]$ sudo firewall-cmd --add-port=8081/tcp --permanent
success
[opc@cata ~]$ sudo firewall-cmd --reload
success
[opc@cata ~]$ sudo firewall-cmd --list-all
public (active)
  target: default
  icmp-block-inversion: no
  interfaces: ens3
  sources:
  services: dhcpv6-client ssh
  ports: 1521/tcp 1522/tcp 8081/tcp
  protocols:
  masquerade: no
  forward-ports:
  source-ports:
  icmp-blocks:
  rich rules:

On the catalog host, install Shard Director Software
****************************************************

[opc@cata ~]$ sudo -i
[root@cata ~]# su - oracle
Last login: Tue Nov  9 11:36:00 GMT 2021 on pts/0

create a file named gsm.sh.

export ORACLE_BASE=/u01/app/oracle
export ORACLE_HOME=/u01/app/oracle/product/19c/gsmhome_1
export LD_LIBRARY_PATH=$ORACLE_HOME/lib
export PATH=$ORACLE_HOME/bin:$PATH

create a file named cata.sh.

export ORACLE_BASE=/u01/app/oracle
export ORACLE_HOME=/u01/app/oracle/product/19c/dbhome_1
export LD_LIBRARY_PATH=$ORACLE_HOME/lib
export PATH=$ORACLE_HOME/bin:$PATH


Switch to the GSM environment.

. ./gsm.sh

Download the GSM installation file. You can download it from OTN or edelivery using your own account. We have downloaded it and save it in the object storage. You can use the following command to get the installation file.

I got GSM 19.3 and copied it in an Object Storage bucket:

Then I download the ZIP on cata machine from the Object Storage:


wget https://bit.ly/3bNtHTy -O GSM.19.3.V982067-01.zip


[oracle@cata ~]$ ls -ltr
total 937408
drwxr-xr-x. 12 oracle oinstall      4096 Jul 23  2020 swingbench
-rw-r--r--.  1 oracle oinstall       166 Nov 10 10:20 cata.sh
-rw-r--r--.  1 oracle oinstall       167 Nov 10 16:56 gsm.sh
-rw-r--r--.  1 oracle oinstall 959891519 Nov 11 08:48 GSM.19.3.V982067-01.zip

unzip GSM.19.3.V982067-01.zip

[oracle@cata ~]$ ls -ltr
total 937408
drwxr-xr-x.  5 oracle oinstall        90 Apr 17  2019 gsm
drwxr-xr-x. 12 oracle oinstall      4096 Jul 23  2020 swingbench
-rw-r--r--.  1 oracle oinstall       166 Nov 10 10:20 cata.sh
-rw-r--r--.  1 oracle oinstall       167 Nov 10 16:56 gsm.sh
-rw-r--r--.  1 oracle oinstall 959891519 Nov 11 08:48 GSM.19.3.V982067-01.zip

Edit the ./gsm/response/gsm_install.rsp file. Specify the variables like following.

    UNIX_GROUP_NAME=oinstall
    INVENTORY_LOCATION=/u01/app/oraInventory
    ORACLE_HOME=/u01/app/oracle/product/19c/gsmhome_1
    ORACLE_BASE=/u01/app/oracle

Create the gsm home directory.

mkdir -p /u01/app/oracle/product/19c/gsmhome_1


Install the gsm

./gsm/runInstaller -silent -responseFile /home/oracle/gsm/response/gsm_install.rsp -showProgress -ignorePrereq

Starting Oracle Universal Installer...

Checking Temp space: must be greater than 551 MB.   Actual 32844 MB    Passed
Preparing to launch Oracle Universal Installer from /tmp/OraInstall2021-11-11_08-55-36AM. Please wait ...[oracle@cata ~]$
[oracle@cata ~]$ [WARNING] [INS-13014] Target environment does not meet some optional requirements.
   CAUSE: Some of the optional prerequisites are not met. See logs for details. /u01/app/oraInventory/logs/installActions2021-11-11_08-55-36AM.log
   ACTION: Identify the list of failed prerequisite checks from the log: /u01/app/oraInventory/logs/installActions2021-11-11_08-55-36AM.log. Then either from the log file or from installation manual find the appropriate configuration to meet the prerequisites and fix it manually.
The response file for this session can be found at:
 /u01/app/oracle/product/19c/gsmhome_1/install/response/gsm_2021-11-11_08-55-36AM.rsp

You can find the log of this install session at:
 /u01/app/oraInventory/logs/installActions2021-11-11_08-55-36AM.log

Prepare in progress.
..................................................   8% Done.

Prepare successful.

Copy files in progress.
..................................................   13% Done.
..................................................   19% Done.
..................................................   27% Done.
..................................................   33% Done.
..................................................   38% Done.
..................................................   43% Done.
..................................................   48% Done.
..................................................   53% Done.
..................................................   58% Done.
..................................................   64% Done.
..................................................   69% Done.
..................................................   74% Done.
..................................................   79% Done.

Copy files successful.

Link binaries in progress.

Link binaries successful.

Setup files in progress.
........................................
Setup files successful.

Setup Inventory in progress.

Setup Inventory successful.
..........
Finish Setup in progress.
..................................................   84% Done.

Finish Setup successful.
The installation of Oracle Distributed Service and Load Management was successful.
Please check '/u01/app/oraInventory/logs/silentInstall2021-11-11_08-55-36AM.log' for more details.

Setup Oracle Base in progress.

Setup Oracle Base successful.
..................................................   95% Done.

As a root user, execute the following script(s):
	1. /u01/app/oracle/product/19c/gsmhome_1/root.sh



Successfully Setup Software with warning(s).
..................................................   100% Done.

Execute the root script:

[root@cata ~]# /u01/app/oracle/product/19c/gsmhome_1/root.sh
Check /u01/app/oracle/product/19c/gsmhome_1/install/root_cata_2021-11-11_08-58-23-323548564.log for the output of root script
[root@cata ~]#
[oracle@cata ~]$ cat /u01/app/oracle/product/19c/gsmhome_1/install/root_cata_2021-11-11_08-58-23-323548564.log
Performing root user operation.

The following environment variables are set as:
    ORACLE_OWNER= oracle
    ORACLE_HOME=  /u01/app/oracle/product/19c/gsmhome_1
   Copying dbhome to /usr/local/bin ...
   Copying oraenv to /usr/local/bin ...
   Copying coraenv to /usr/local/bin ...

Entries will be added to the /etc/oratab file as needed by
Database Configuration Assistant when a database is created
Finished running generic part of root script.
Now product-specific root actions will be performed.

***************************
Setup the catalog database:
***************************

[root@cata ~]# su - oracle
Last login: Wed Nov 10 10:18:34 GMT 2021 on pts/0
[oracle@cata ~]$ . ./cata.sh

sqlplus / as sysdba

Because the shard catalog database can run multi-shard queries which connect to shards over database links, 
the OPEN_LINKS and OPEN_LINKS_PER_INSTANCE database initialization parameter values must be greater than or equal to the number of shards that will be part of the sharded database configuration.

SQL> alter system set open_links=20 scope=spfile;

System altered.

SQL> alter system set open_links_per_instance=20 scope=spfile;

System altered.

SQL> alter system set db_files=1024 scope=spfile;

System altered.

SQL> alter system set db_create_file_dest='/u01/app/oracle/oradata' scope=spfile;

System altered.

SQL> alter user gsmcatuser account unlock;

User altered.

SQL> alter user gsmcatuser identified by Ora_DB4U;

User altered.

Connect to the catalog pdb, Unlock the gsmcatalog user and create a shard catalog administrator account.
--------------------------------------------------------------------------------------------------------
SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 CATAPDB			  READ WRITE NO
SQL> alter session set container=catapdb;

Session altered.

SQL> alter user gsmcatuser account unlock;

User altered.

SQL> create user mysdbadmin identified by Ora_DB4U;

User created.

SQL> grant gsmadmin_role to mysdbadmin;

Grant succeeded.

Connect as sysdba. Check the database archivelog mode.
------------------------------------------------------

SQL> connect / as sysdba
Connected.
SQL> archive log list
Database log mode	       No Archive Mode
Automatic archival	       Disabled
Archive destination	       /u01/app/oracle/product/19c/dbhome_1/dbs/arch
Oldest online log sequence     16
Current log sequence	       18
SQL> select flashback_on from v$database;

FLASHBACK_ON
------------------
NO

SQL> show parameter db_recovery_file

NAME				     TYPE	 VALUE
------------------------------------ ----------- ------------------------------
db_recovery_file_dest		     string
db_recovery_file_dest_size	     big integer 0
SQL>


Enable archivelog and flashback on.
-----------------------------------

SQL> !mkdir -p /u01/app/oracle/fast_recovery_area

SQL> alter system set db_recovery_file_dest_size=50G scope=both;

System altered.

SQL> alter system set db_recovery_file_dest='/u01/app/oracle/fast_recovery_area' scope=both;

System altered.

SQL> shutdown immediate
Database closed.
Database dismounted.
ORACLE instance shut down.
SQL>
SQL>
SQL>
SQL> startup mount
ORACLE instance started.

Total System Global Area 4630509232 bytes
Fixed Size		    9143984 bytes
Variable Size		  855638016 bytes
Database Buffers	 3758096384 bytes
Redo Buffers		    7630848 bytes
Database mounted.
SQL> alter database archivelog;

Database altered.

SQL> alter database flashback on;

Database altered.

SQL> alter database open;

Database altered.

SQL>

**********************
Setup Shard Databases
**********************

[oracle@shd1 ~]$ sqlplus / as sysdba

SQL*Plus: Release 19.0.0.0.0 - Production on Wed Nov 10 11:44:28 2021
Version 19.11.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.


Connected to:
Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
Version 19.11.0.0.0

SQL> alter user gsmrootuser account unlock;

User altered.

SQL> alter user gsmrootuser identified by Ora_DB4U;

User altered.

SQL> grant SYSDG, SYSBACKUP to gsmrootuser;

Grant succeeded.

SQL>

A directory object named DATA_PUMP_DIR must be created and accessible in the shard database from the GSMADMIN_INTERNAL account.

SQL> select directory_path from dba_directories where directory_name='DATA_PUMP_DIR';

DIRECTORY_PATH
--------------------------------------------------------------------------------
/u01/app/oracle/admin/shd1/dpdump/

SQL> grant read, write on directory DATA_PUMP_DIR to gsmadmin_internal;

Grant succeeded.

SQL>

Unlock the gsmuser.

SQL> alter user gsmuser account unlock;

User altered.

SQL> alter user gsmuser identified by Ora_DB4U;

User altered.

SQL> grant SYSDG, SYSBACKUP to gsmuser;

Grant succeeded.

SQL> alter system set db_files=1024 scope=spfile;

System altered.

SQL> alter system set dg_broker_start=true scope=both;

System altered.

SQL> alter system set db_file_name_convert='/SHDSTB1/','/SHD1/' scope=spfile;

System altered.

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 SHDPDB1			  READ WRITE NO
SQL> alter session set container=shdpdb1;

Session altered.

SQL> alter user gsmuser account unlock;

User altered.

SQL> grant SYSDG, SYSBACKUP to gsmuser;

Grant succeeded.

SQL> show parameter db_create_file_dest

NAME				     TYPE	 VALUE
------------------------------------ ----------- ------------------------------
db_create_file_dest		     string
SQL> alter system set db_create_file_dest='/u01/app/oracle/oradata' scope=both;

System altered.

SQL> grant read, write on directory DATA_PUMP_DIR to gsmadmin_internal;

Grant succeeded.



Connect to the CDB. Enable achivelog and flashback on
-----------------------------------------------------

SQL> connect / as sysdba
Connected.
SQL> !mkdir -p /u01/app/oracle/fast_recovery_area

SQL> alter system set db_recovery_file_dest_size=50G scope=both;

System altered.

SQL> alter system set db_recovery_file_dest='/u01/app/oracle/fast_recovery_area' scope=both;

System altered.

SQL> shutdown immediate
Database closed.
Database dismounted.
ORACLE instance shut down.
SQL> startup mount
ORACLE instance started.

Total System Global Area 4630509232 bytes
Fixed Size		    9143984 bytes
Variable Size		  855638016 bytes
Database Buffers	 3758096384 bytes
Redo Buffers		    7630848 bytes
Database mounted.
SQL> alter database archivelog;

Database altered.

SQL> alter database flashback on;

Database altered.

SQL> alter database open;

Database altered.


(Optional) If your shard database will use standby shard databases, you must enable the FORCE LOGGING mode.
----------------------------------------------------------------------------------------------------------

SQL> alter database force logging;

Database altered.


Connect to the shard pdb and validate the shard. 
The validateShard procedure can and should be run against primary, mounted (unopened) standby, and Active Data Guard standby databases that are part of the sharded database configuration. 

SQL> alter session set container=shdpdb1;

Session altered.

SQL> set serveroutput on
SQL> execute dbms_gsm_fix.validateShard
INFO: Data Guard shard validation requested.
INFO: Database role is PRIMARY.
INFO: Database name is SHD1.
INFO: Database unique name is shd1.
INFO: Database ID is 785208895.
INFO: Database open mode is READ WRITE.
INFO: Database in archivelog mode.
INFO: Flashback is on.
INFO: Force logging is on.
INFO: Database platform is Linux x86 64-bit.
INFO: Database character set is AL32UTF8. This value must match the character
set of the catalog database.
INFO: 'compatible' initialization parameter validated successfully.
INFO: Database is a multitenant container database.
INFO: Current container is SHDPDB1.
INFO: Database is using a server parameter file (spfile).
INFO: db_create_file_dest set to: '/u01/app/oracle/oradata'
INFO: db_recovery_file_dest set to: '/u01/app/oracle/fast_recovery_area'
INFO: db_files=1024. Must be greater than the number of chunks and/or
tablespaces to be created in the shard.
INFO: dg_broker_start set to TRUE.
INFO: remote_login_passwordfile set to EXCLUSIVE.
INFO: db_file_name_convert set to: '/SHDSTB1/, /SHD1/'
INFO: GSMUSER account validated successfully.
INFO: DATA_PUMP_DIR is
'/u01/app/oracle/admin/shd1/dpdump/D04B91BB4408489EE055000017074120'.

PL/SQL procedure successfully completed.

SQL>

Repeat previous steps to set up all shard databases. You can only setup shard1 and shard2 if you don t want add the third shard in the workshop.
------------------------------------------------------------------------------------------------------------------------------------------------

**************************************
Configure the Shard Database Topology
**************************************

Connect to the catalog database host. Switch to oracle user.

Switch to the GSM environment.

[oracle@cata ~]$ . ./gsm.sh
[oracle@cata ~]$ gdsctl
GDSCTL: Version 19.0.0.0.0 - Production on Thu Nov 11 09:18:26 GMT 2021

Copyright (c) 2011, 2019, Oracle.  All rights reserved.

Welcome to GDSCTL, type "help" for information.

Warning:  GSM  is not set automatically because gsm.ora does not contain GSM entries. Use "set  gsm" command to set GSM for the session.
Current GSM is set to GSMORA
GDSCTL>

Create the shard catalog using the System-Managed sharding method. In this workshop, we have no data guard environment, so just set one region. 
In this workshop, we set the chunks to 12, the default value is 120 for each of the shard database.

create shardcatalog -database cata:1521/catapdb -user mysdbadmin/Ora_DB4U -chunks 12 -region region1 -SHARDING system

GDSCTL> create shardcatalog -database cata:1521/catapdb -user mysdbadmin/Ora_DB4U -chunks 12 -region region1 -SHARDING system
Catalog is created
GDSCTL>

Add and start the shard director.
---------------------------------

GDSCTL> connect mysdbadmin/Ora_DB4U@cata:1521/catapdb
Catalog connection is established
GDSCTL> add gsm -gsm sharddirector1 -catalog cata:1521/catapdb -pwd Ora_DB4U -region region1
GSM successfully added
GDSCTL> start gsm -gsm sharddirector1
GSM is started successfully
GDSCTL> set gsm -gsm sharddirector1

Add shard group, each shardspace must contain at least one primary shardgroup and may contain any number or type of standby shardgroups. 
In this workshop, we have only one primary shardgroup.

GDSCTL> add shardgroup -shardgroup shardgroup_primary -deploy_as primary -region region1
The operation completed successfully

Verify the Sharding Topology. Before adding information about your shard databases to the catalog, 
verify that your sharding topology is correct before proceeding by using the various GDSCTL CONFIG commands.

GDSCTL> config

Regions
------------------------
region1

GSMs
------------------------
sharddirector1

Sharded Database
------------------------
orasdb

Databases
------------------------

Shard Groups
------------------------
shardgroup_primary

Shard spaces
------------------------
shardspaceora

Services
------------------------

GDSCTL pending requests
------------------------
Command                       Object                        Status
-------                       ------                        ------

Global properties
------------------------
Name: oradbcloud
Master GSM: sharddirector1
DDL sequence #: 0

Add shard CDB. Repeat the ADD CDB command for all of the CDBs that contain a shard PDB in the configuration. In this lab, we only add shd1 and shd2.

GDSCTL> add cdb -connect shd1:1521/shd1 -pwd Ora_DB4U
DB Unique Name: shd1
The operation completed successfully

GDSCTL> add cdb -connect shd2:1521/shd2 -pwd Ora_DB4U
DB Unique Name: shd2
The operation completed successfully

GDSCTL> config cdb
shd1
shd2

Add the primary shard information to the shard catalog. The shard group is shardgroup_primary.

GDSCTL> add shard -connect shd1:1521/shdpdb1 -pwd Ora_DB4U -shardgroup shardgroup_primary -cdb shd1
INFO: Data Guard shard validation requested.
INFO: Database role is PRIMARY.
INFO: Database name is SHD1.
INFO: Database unique name is shd1.
INFO: Database ID is 785208895.
INFO: Database open mode is READ WRITE.
INFO: Database in archivelog mode.
INFO: Flashback is on.
INFO: Force logging is on.
INFO: Database platform is Linux x86 64-bit.
INFO: Database character set is AL32UTF8. This value must match the character set of the catalog database.
INFO: 'compatible' initialization parameter validated successfully.
INFO: Database is a multitenant container database.
INFO: Current container is SHDPDB1.
INFO: Database is using a server parameter file (spfile).
INFO: db_create_file_dest set to: '/u01/app/oracle/oradata'
INFO: db_recovery_file_dest set to: '/u01/app/oracle/fast_recovery_area'
INFO: db_files=1024. Must be greater than the number of chunks and/or tablespaces to be created in the shard.
INFO: dg_broker_start set to TRUE.
INFO: remote_login_passwordfile set to EXCLUSIVE.
INFO: db_file_name_convert set to: '/SHDSTB1/, /SHD1/'
INFO: GSMUSER account validated successfully.
INFO: DATA_PUMP_DIR is '/u01/app/oracle/admin/shd1/dpdump/D04B91BB4408489EE055000017074120'.
DB Unique Name: shd1_shdpdb1
The operation completed successfully

GDSCTL> add shard -connect shd2:1521/shdpdb2 -pwd Ora_DB4U -shardgroup shardgroup_primary -cdb shd2
INFO: Data Guard shard validation requested.
INFO: Database role is PRIMARY.
INFO: Database name is SHD2.
INFO: Database unique name is shd2.
INFO: Database ID is 1343741747.
INFO: Database open mode is READ WRITE.
INFO: Database in archivelog mode.
INFO: Flashback is on.
INFO: Force logging is on.
INFO: Database platform is Linux x86 64-bit.
INFO: Database character set is AL32UTF8. This value must match the character set of the catalog database.
INFO: 'compatible' initialization parameter validated successfully.
INFO: Database is a multitenant container database.
INFO: Current container is SHDPDB2.
INFO: Database is using a server parameter file (spfile).
INFO: db_create_file_dest set to: '/u01/app/oracle/oradata'
INFO: db_recovery_file_dest set to: '/u01/app/oracle/fast_recovery_area'
INFO: db_files=1024. Must be greater than the number of chunks and/or tablespaces to be created in the shard.
INFO: dg_broker_start set to TRUE.
INFO: remote_login_passwordfile set to EXCLUSIVE.
INFO: db_file_name_convert set to: '/SHDSTB2/, /SHD2/'
INFO: GSMUSER account validated successfully.
INFO: DATA_PUMP_DIR is '/u01/app/oracle/admin/shd2/dpdump/D04B984A766F48D6E055000017017509'.
DB Unique Name: shd2_shdpdb2
The operation completed successfully

Run CONFIG SHARD to view the shard metadata on the shard catalog.

GDSCTL> config shard
Name                Shard Group         Status    State       Region    Availability
----                -----------         ------    -----       ------    ------------
shd1_shdpdb1        shardgroup_primary  U         none        region1   -
shd2_shdpdb2        shardgroup_primary  U         none        region1   -


Add all of the host names and IP addresses of your shard hosts to the shard catalog. First, View a list of trusted hosts.

GDSCTL> config vncr
Name                          Group ID
----                          --------
10.0.1.125
shd1
shd2

Run the ADD INVITEDNODE command to manually add all host names and IP addresses of your shard hosts to the shard catalog metadata.

GDSCTL> add invitednode 127.0.0.1
GDSCTL> add invitednode cata
GDSCTL> add invitednode 10.0.1.75
GDSCTL> add invitednode 10.0.1.98
GDSCTL>

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

************************************
Deploy the Sharding Configuration
************************************

When the sharded database topology has been fully configured, run the GDSCTL DEPLOY command to deploy the sharded database configuration.

GDSCTL> deploy
deploy: examining configuration...
deploy: requesting Data Guard configuration on shards via GSM
deploy: shards configured successfully
The operation completed successfully

Check the shard status, It''s may look similar to the following.

GDSCTL> config shard
Name                Shard Group         Status    State       Region    Availability
----                -----------         ------    -----       ------    ------------
shd1_shdpdb1        shardgroup_primary  Ok        Deployed    region1   ONLINE
shd2_shdpdb2        shardgroup_primary  Ok        Deployed    region1   ONLINE

Observe all shard are registered.

GDSCTL> databases
Database: "shd1_shdpdb1" Registered: Y State: Ok ONS: N. Role: PRIMARY Instances: 1 Region: region1
   Registered instances:
     orasdb%1
Database: "shd2_shdpdb2" Registered: Y State: Ok ONS: N. Role: PRIMARY Instances: 1 Region: region1
   Registered instances:
     orasdb%11

Create and start a global service named oltp_rw_srvc that a client can use to connect to the sharded database. 
The oltp_rw_srvc service runs read/write transactions on the primary shards.

GDSCTL> add service -service oltp_rw_srvc -role primary
The operation completed successfully

GDSCTL> start service -service oltp_rw_srvc
The operation completed successfully

Check the status of the service.

GDSCTL> config service


Name           Network name                  Pool           Started Preferred all
----           ------------                  ----           ------- -------------
oltp_rw_srvc   oltp_rw_srvc.orasdb.oradbclou orasdb         Yes     Yes
               d


Exit the GDSCTL.

GDSCTL> exit
[oracle@cata ~]$

Check the shard director listener status. You can see listening on 1522 port there is a service named oltp_rw_srvc.orasdb.oradbcloud 
which we create previously and a service named GDS$CATALOG.oradbcloud which connect to the catalog instance.

[oracle@cata ~]$ lsnrctl status SHARDDIRECTOR1

LSNRCTL for Linux: Version 19.0.0.0.0 - Production on 11-NOV-2021 10:24:26

Copyright (c) 1991, 2019, Oracle.  All rights reserved.

Connecting to (DESCRIPTION=(ADDRESS=(HOST=cata)(PORT=1522)(PROTOCOL=tcp))(CONNECT_DATA=(SERVICE_NAME=GDS$CATALOG.oradbcloud)))
STATUS of the LISTENER
------------------------
Alias                     SHARDDIRECTOR1
Version                   TNSLSNR for Linux: Version 19.0.0.0.0 - Production
Start Date                11-NOV-2021 10:05:22
Uptime                    0 days 0 hr. 19 min. 4 sec
Trace Level               off
Security                  ON: Local OS Authentication
SNMP                      OFF
Listener Parameter File   /u01/app/oracle/product/19c/gsmhome_1/network/admin/gsm.ora
Listener Log File         /u01/app/oracle/diag/gsm/cata/sharddirector1/alert/log.xml
Listening Endpoints Summary...
  (DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)(HOST=cata)(PORT=1522)))
Services Summary...
Service "GDS$CATALOG.oradbcloud" has 1 instance(s).
  Instance "cata", status READY, has 1 handler(s) for this service...
Service "GDS$COORDINATOR.oradbcloud" has 1 instance(s).
  Instance "cata", status READY, has 1 handler(s) for this service...
Service "_MONITOR" has 1 instance(s).
  Instance "SHARDDIRECTOR1", status READY, has 1 handler(s) for this service...
Service "_PINGER" has 1 instance(s).
  Instance "SHARDDIRECTOR1", status READY, has 1 handler(s) for this service...
Service "oltp_rw_srvc.orasdb.oradbcloud" has 2 instance(s).
  Instance "orasdb%1", status READY, has 1 handler(s) for this service...
  Instance "orasdb%11", status READY, has 1 handler(s) for this service...
The command completed successfully













