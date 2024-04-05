-- Primary server: <primary_server_public_ip> - ssh -i /Users/stef/Documents/Preventa/TMP/sshkeybundle/privateKey opc@<primary_server_public_ip>
-- Standby server: <standby_server_public_ip>  - ssh -i /Users/stef/Documents/Preventa/TMP/sshkeybundle/privateKey opc@<standby_server_public_ip>

--- Connect to dg broker and show the configuration:
--- From the primary site

dgmgrl
connect sys/"<passwd>" as sysdba

[oracle@adgdb-s01-2021-11-22-170552 ~]$ dgmgrl
DGMGRL for Linux: Release 19.0.0.0.0 - Production on Tue Nov 23 11:26:40 2021
Version 19.12.0.0.0

Copyright (c) 1982, 2019, Oracle and/or its affiliates.  All rights reserved.

Welcome to DGMGRL, type "help" for information.
DGMGRL> connect sys/"<passwd>" as sysdba
Connected to "adg_fra383"
Connected as SYSDBA.
DGMGRL> show configuration

Configuration - adg_fra383_adg_fra269

  Protection Mode: MaxPerformance
  Members:
  adg_fra383 - Primary database
    adg_fra269 - Physical standby database

Fast-Start Failover:  Disabled

Configuration Status:
SUCCESS   (status updated 51 seconds ago)

1. Install ACdemo app on the primary node
******************************************

cd /home/oracle
wget https://objectstorage.us-ashburn-1.oraclecloud.com/p/O8AOujhwl1dSTqhfH69f3nkV6TNZWU3KaIF4TZ-XuCaZ5w-xHEQ14ViOVhUXQjPB/n/oradbclouducm/b/LiveLabTemp/o/ACDemo_19c.zip

[oracle@adgdb-s01-2021-11-22-170552 ~]$ wget https://objectstorage.us-ashburn-1.oraclecloud.com/p/O8AOujhwl1dSTqhfH69f3nkV6TNZWU3KaIF4TZ-XuCaZ5w-xHEQ14ViOVhUXQjPB/n/oradbclouducm/b/LiveLabTemp/o/ACDemo_19c.zip
--2021-11-23 11:27:42--  https://objectstorage.us-ashburn-1.oraclecloud.com/p/O8AOujhwl1dSTqhfH69f3nkV6TNZWU3KaIF4TZ-XuCaZ5w-xHEQ14ViOVhUXQjPB/n/oradbclouducm/b/LiveLabTemp/o/ACDemo_19c.zip
Resolving objectstorage.us-ashburn-1.oraclecloud.com (objectstorage.us-ashburn-1.oraclecloud.com)... 134.70.24.1, 134.70.32.1, 134.70.28.1
Connecting to objectstorage.us-ashburn-1.oraclecloud.com (objectstorage.us-ashburn-1.oraclecloud.com)|134.70.24.1|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: 8573765 (8.2M) [application/x-zip-compressed]
Saving to: 'ACDemo_19c.zip'

100%[================================================================================================>] 8,573,765   10.3MB/s   in 0.8s

2021-11-23 11:27:43 (10.3 MB/s) - 'ACDemo_19c.zip' saved [8573765/8573765]

[oracle@adgdb-s01-2021-11-22-170552 ~]$ ls -ltr
total 8376
-rw-r--r-- 1 oracle oinstall 8573765 Sep 10 04:21 ACDemo_19c.zip
[oracle@adgdb-s01-2021-11-22-170552 ~]$ unzip ACDemo_19c.zip
Archive:  ACDemo_19c.zip
   creating: acdemo/
  inflating: acdemo/ac_noreplay.sbs
  inflating: acdemo/ac_replay.sbs
  inflating: acdemo/ac_setup_sql.sbs
  inflating: acdemo/build.xml
   creating: acdemo/classes/
   creating: acdemo/classes/acdemo/
  inflating: acdemo/classes/acdemo/ACDemo.class
  inflating: acdemo/classes/acdemo/PrintACStatThread.class
  inflating: acdemo/classes/acdemo/PrintStatThread.class
  inflating: acdemo/classes/acdemo/Worker.class
  inflating: acdemo/kill_session.sbs
  inflating: acdemo/lbtest.sbs
   creating: acdemo/lib/
  inflating: acdemo/lib/acdemo.jar
  inflating: acdemo/lib/ojdbc8-19.10.0.0.jar
  inflating: acdemo/lib/ons-19.10.0.0.jar
  inflating: acdemo/lib/oraclepki-19.10.0.0.jar
  inflating: acdemo/lib/orai18n-19.10.0.0.jar
  inflating: acdemo/lib/orajsoda-1.1.4.jar
  inflating: acdemo/lib/osdt_cert-19.10.0.0.jar
  inflating: acdemo/lib/osdt_core-19.10.0.0.jar
  inflating: acdemo/lib/ucp-19.10.0.0.jar
 extracting: acdemo/MANIFEST.MF
  inflating: acdemo/my_setup.sql
  inflating: acdemo/README.txt
  inflating: acdemo/runlbtest
  inflating: acdemo/runnoreplay
  inflating: acdemo/runreplay
  inflating: acdemo/runtacreplay
   creating: acdemo/src/
   creating: acdemo/src/acdemo/
  inflating: acdemo/src/acdemo/ACDemo.java
  inflating: acdemo/src/acdemo/PrintACStatsThread.java
  inflating: acdemo/src/acdemo/PrintStatThread.java
  inflating: acdemo/src/acdemo/Worker.java
  inflating: acdemo/tac_replay.sbs
   creating: acdemo/win/
  inflating: acdemo/win/ac_noreplay.install
  inflating: acdemo/win/ac_noreplay.properties
  inflating: acdemo/win/ac_replay.install
  inflating: acdemo/win/create_hr.sql
  inflating: acdemo/win/hr_tab.sql
  inflating: acdemo/win/replace.bat
  inflating: acdemo/win/replace.vbs
  inflating: acdemo/win/SETUP_AC_TEST.bat
  inflating: README.txt
  inflating: SETUP_AC_TEST.sh

--- Create a new service on the primary and the standby database !!!
--- The following commands must be run on both the primary and standby database !!!
-- On the primary !!!
--
[oracle@adgdb-s01-2021-11-22-170552 ~]$ srvctl add service -d $(srvctl config database) -s svc_tac -pdb PDB1 -role primary -replay_init_time 1000 -failoverretry 30 -failoverdelay 3 -commit_outcome TRUE -failovertype AUTO -failover_restore AUTO

[oracle@adgdb-s01-2021-11-22-170552 ~]$
[oracle@adgdb-s01-2021-11-22-170552 ~]$ srvctl start service -d $(srvctl config database) -s svc_tac
[oracle@adgdb-s01-2021-11-22-170552 ~]$ srvctl status service -d $(srvctl config database) -s svc_tac
Service svc_tac is running on instance(s) adg

[oracle@adgdb-s01-2021-11-22-170552 ~]$ srvctl config service -d $(srvctl config database) -s svc_tac
Service name: svc_tac
Server pool:
Cardinality: 1
Service role: PRIMARY
Management policy: AUTOMATIC
DTP transaction: false
AQ HA notifications: false
Global: false
Commit Outcome: true
Failover type: AUTO
Failover method:
Failover retries: 30
Failover delay: 3
Failover restore: AUTO
Connection Load Balancing Goal: LONG
Runtime Load Balancing Goal: NONE
TAF policy specification: NONE
Edition:
Pluggable database name: PDB1
Hub service:
Maximum lag time: ANY
SQL Translation Profile:
Retention: 86400 seconds
Replay Initiation Time: 1000 seconds
Drain timeout:
Stop option:
Session State Consistency: AUTO
GSM Flags: 0
Service is enabled
Preferred instances: adg
Available instances:
CSS critical: no
Service uses Java: false

-- On the standby !!!
-- On the standby we don't start ths service !!

[oracle@adgsby ~]$ srvctl add service -d $(srvctl config database) -s svc_tac -pdb PDB1 -role primary -replay_init_time 1000 -failoverretry 30 -failoverdelay 3 -commit_outcome TRUE -failovertype AUTO -failover_restore AUTO
[oracle@adgsby ~]$ srvctl status service -d $(srvctl config database) -s svc_tac
Service svc_tac is not running.

-- Service is not running on the standby database, because it is associated with the primary role. Clusterware wil start it in case of switchover/failover !!!

--- On the primary database, connect to the PDB; create and populate a sample schema !!!

--- In the PDB, create schema HR and poulate some table !!!
sqlplus system/"<passwd>"@adgdb-s01-2021-11-22-170552:1521/svc_tac.pub.racdblab.oraclevcn.com

   set heading off
   set feedback off
   drop user hr cascade;
   create user hr identified by "<passwd>" default tablespace USERS temporary tablespace temp;
   grant connect, create session, resource to hr;
   alter user hr quota unlimited on USERS;

   create table HR.emp4AC(
    empno number(4) not null,
    ename varchar2(10),
    job char(9),
    mgr number(4),
    hiredate date,
    sal number(7,2),
    comm number(7,2),
    deptno number(2),
    constraint emp_primary_key primary key (empno));

   insert into hr.emp4AC values(7839,'KING','PRESIDENT',NULL,'17-NOV-81',50000,NULL,10);
   insert into hr.emp4AC values(7698,'BLAKE','MANAGER',NULL,'17-NOV-81',8000,NULL,10);
   insert into hr.emp4AC values(7782,'CLARK','MANAGER',NULL,'17-NOV-81',8000,NULL,10);
   insert into hr.emp4AC values(7566,'JONES','MANAGER',NULL,'17-NOV-81',8000,NULL,10);
   insert into hr.emp4AC values(7654,'MARTIN','SALESMAN',NULL,'17-NOV-81',7000,NULL,10);
   insert into hr.emp4AC values(7499,'ALLEN','MANAGER',NULL,'17-NOV-81',9000,NULL,10);
   insert into hr.emp4AC values(7844,'TURNER','CLERK',NULL,'17-NOV-81',5000,NULL,10);
   insert into hr.emp4AC values(7900,'JAMES','MANAGER',NULL,'17-NOV-81',9000,NULL,10);
   insert into hr.emp4AC values(7521,'WARD','PRGRMMER',NULL,'17-NOV-81',9000,NULL,10);
   insert into hr.emp4AC values(7902,'FORD','SALESMAN',NULL,'17-NOV-81',7000,NULL,10);
   insert into hr.emp4AC values(7369,'SMITH','PRGRMMER',NULL,'17-NOV-81',8000,NULL,10);
   insert into hr.emp4AC values(7788,'SCOTT','CLERK',NULL,'17-NOV-81',6000,NULL,10);
   insert into hr.emp4AC values(7876,'ADAMS','PRGRMMER',NULL,'17-NOV-81',7000,NULL,10);
   insert into hr.emp4AC values(7934,'MILLER','SALESMAN',NULL,'17-NOV-81',9000,NULL,10);
   commit;

--- Run the app !!!
--- Configure tac_replay.properties !!!
--- The connect string is formated for ADG failover !!!

[oracle@adgdb-s01-2021-11-22-170552 acdemo]$ cat /home/oracle/acdemo/tac_replay.properties
# Stub file to create tac_replay.properties
# Use replay datasource
datasource=oracle.jdbc.replay.OracleDataSourceImpl

# Set verbose mode
VERBOSE=FALSE

# database JDBC URL
url=jdbc:oracle:thin:@(DESCRIPTION=(CONNECT_TIMEOUT=90)(RETRY_COUNT=50)(RETRY_DELAY=3)(TRANSPORT_CONNECT_TIMEOUT=3)(ADDRESS_LIST = (FAILOVER = ON) (LOAD_BALANCE = OFF)(ADDRESS = (PROTOCOL = TCP)(HOST = adgdb-s01-2021-11-22-170552-scan.pub.racdblab.oraclevcn.com)(PORT = 1521))(ADDRESS = (PROTOCOL = TCP)(HOST = adgsby-scan.pub.racdblab.oraclevcn.com)(PORT = 1521)))(CONNECT_DATA =(SERVICE_NAME = svc_tac.pub.racdblab.oraclevcn.com)))

# database username and password:
username=hr
password=<passwd>

# Enable FAN
fastConnectionFailover=TRUE

#Disable connection tests
validateConnectionOnBorrow=TRUE

# number of connections in the UCP''s pool:
ucp_pool_size=20

#Connection Wait Timeout for busy pool
connectionWaitTimeout=5

# number of active threads (this simulates concurrent load):
number_of_threads=10

# think time is how much time the threads will sleep before looping:
thread_think_time=50

--- Run the app !!!
cd /home/oracle/acdemo
chmod +x ./runtacreplay
./runtacreplay

[oracle@adgdb-s01-2021-11-22-170552 acdemo]$ ./runtacreplay
######################################################
Connecting to jdbc:oracle:thin:@(DESCRIPTION=(CONNECT_TIMEOUT=90)(RETRY_COUNT=50)(RETRY_DELAY=3)(TRANSPORT_CONNECT_TIMEOUT=3)(ADDRESS_LIST = (FAILOVER = ON) (LOAD_BALANCE = OFF)(ADDRESS = (PROTOCOL = TCP)(HOST = adgdb-s01-2021-11-22-170552-scan.pub.racdblab.oraclevcn.com)(PORT = 1521))(ADDRESS = (PROTOCOL = TCP)(HOST = adgsby-scan.pub.racdblab.oraclevcn.com)(PORT = 1521)))(CONNECT_DATA =(SERVICE_NAME = svc_tac.pub.racdblab.oraclevcn.com)))
 # of Threads             : 10
 UCP pool size            : 20
FCF Enabled:  true
VCoB Enabled: true
ONS Configuration:  null
Enable Intensive Wload:  false
Thread think time        : 50 ms
######################################################

Starting the pool now... (please wait)
Pool is started in 12385ms
10 borrowed, 0 pending, 2ms getConnection wait, TotalBorrowed 278, avg response time from db 66ms
5 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 810, avg response time from db 38ms
4 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 1371, avg response time from db 33ms


--- Perform a switchover !!!
--- From another terminal, connect to dg broker and perform a switchover !!!

[oracle@adgsby ~]$ dgmgrl
DGMGRL for Linux: Release 19.0.0.0.0 - Production on Tue Nov 23 11:46:35 2021
Version 19.12.0.0.0

Copyright (c) 1982, 2019, Oracle and/or its affiliates.  All rights reserved.

Welcome to DGMGRL, type "help" for information.
DGMGRL> connect sys/"<passwd>" as sysdba
Connected to "adg_fra269"
Connected as SYSDBA.
DGMGRL> show configuration

Configuration - adg_fra383_adg_fra269

  Protection Mode: MaxPerformance
  Members:
  adg_fra383 - Primary database
    adg_fra269 - Physical standby database

Fast-Start Failover:  Disabled

Configuration Status:
SUCCESS   (status updated 22 seconds ago)

DGMGRL> switchover to adg_fra269
Performing switchover NOW, please wait...
New primary database "adg_fra269" is opening...
Oracle Clusterware is restarting database "adg_fra383" ...
Connected to "adg_fra383"
Connected to "adg_fra383"
Switchover succeeded, new primary is "adg_fra269"
DGMGRL> show configuration

Configuration - adg_fra383_adg_fra269

  Protection Mode: MaxPerformance
  Members:
  adg_fra269 - Primary database
    adg_fra383 - Physical standby database

Fast-Start Failover:  Disabled

Configuration Status:
SUCCESS   (status updated 124 seconds ago)

--- Observe the app output !!!

2 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 4560, avg response time from db 28ms
9 borrowed, 1 pending, 0ms getConnection wait, TotalBorrowed 5193, avg response time from db 25ms
3 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 5779, avg response time from db 30ms
1 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 6388, avg response time from db 27ms
4 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 7007, avg response time from db 26ms
10 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 7635, avg response time from db 25ms
0 borrowed, 10 pending, 0ms getConnection wait, TotalBorrowed 7718, avg response time from db 43ms
0 borrowed, 10 pending, 0ms getConnection wait, TotalBorrowed 7718
0 borrowed, 10 pending, 0ms getConnection wait, TotalBorrowed 7718
0 borrowed, 10 pending, 0ms getConnection wait, TotalBorrowed 7718
0 borrowed, 10 pending, 0ms getConnection wait, TotalBorrowed 7718
0 borrowed, 10 pending, 0ms getConnection wait, TotalBorrowed 7718
0 borrowed, 10 pending, 0ms getConnection wait, TotalBorrowed 7718
0 borrowed, 10 pending, 0ms getConnection wait, TotalBorrowed 7718
0 borrowed, 10 pending, 0ms getConnection wait, TotalBorrowed 7718
0 borrowed, 10 pending, 0ms getConnection wait, TotalBorrowed 7718
0 borrowed, 10 pending, 0ms getConnection wait, TotalBorrowed 7718
0 borrowed, 10 pending, 0ms getConnection wait, TotalBorrowed 7718
0 borrowed, 10 pending, 0ms getConnection wait, TotalBorrowed 7718
0 borrowed, 10 pending, 0ms getConnection wait, TotalBorrowed 7718
0 borrowed, 10 pending, 0ms getConnection wait, TotalBorrowed 7718
4 borrowed, 0 pending, 95ms getConnection wait, TotalBorrowed 8034, avg response time from db 28ms
3 borrowed, 0 pending, 88ms getConnection wait, TotalBorrowed 8631, avg response time from db 29ms
1 borrowed, 0 pending, 82ms getConnection wait, TotalBorrowed 9290, avg response time from db 21ms
4 borrowed, 0 pending, 77ms getConnection wait, TotalBorrowed 9856, avg response time from db 33ms
5 borrowed, 0 pending, 73ms getConnection wait, TotalBorrowed 10486, avg response time from db 25ms
1 borrowed, 0 pending, 68ms getConnection wait, TotalBorrowed 11135, avg response time from db 22ms
0 borrowed, 0 pending, 64ms getConnection wait, TotalBorrowed 11803, avg response time from db 20ms
5 borrowed, 4 pending, 61ms getConnection wait, TotalBorrowed 12443, avg response time from db 24ms
1 borrowed, 0 pending, 58ms getConnection wait, TotalBorrowed 13120, avg response time from db 19ms
0 borrowed, 0 pending, 55ms getConnection wait, TotalBorrowed 13787, avg response time from db 20ms
5 borrowed, 1 pending, 52ms getConnection wait, TotalBorrowed 14470, avg response time from db 19ms
4 borrowed, 0 pending, 50ms getConnection wait, TotalBorrowed 15141, avg response time from db 20ms
6 borrowed, 0 pending, 48ms getConnection wait, TotalBorrowed 15819, avg response time from db 19ms

-- The app freezed during the switchover, but no error was reported !!!
-- Check the service on the new primary !!!
[oracle@adgsby ~]$ srvctl status service -d $(srvctl config database) -s svc_tac
Service svc_tac is running on instance(s) adg

-- Now let's try the same with an Sql*Plus session !!!

[oracle@adgsby ~]$ dgmgrl
DGMGRL for Linux: Release 19.0.0.0.0 - Production on Tue Nov 23 13:19:44 2021
Version 19.12.0.0.0

Copyright (c) 1982, 2019, Oracle and/or its affiliates.  All rights reserved.

Welcome to DGMGRL, type "help" for information.
DGMGRL> connect sys/"<passwd>" as sysdba
Connected to "adg_fra269"
Connected as SYSDBA.
DGMGRL> show configuration

Configuration - adg_fra383_adg_fra269

  Protection Mode: MaxPerformance
  Members:
  adg_fra269 - Primary database
    adg_fra383 - Physical standby database

Fast-Start Failover:  Disabled

Configuration Status:
SUCCESS   (status updated 11 seconds ago)

-- From any server, connect to the primary database with Sql*Plus, using the TAC service !!!

[oracle@adgdb-s01-2021-11-22-170552 acdemo]$ sqlplus hr/"<passwd>"@"(DESCRIPTION=(CONNECT_TIMEOUT=90)(RETRY_COUNT=50)(RETRY_DELAY=3)(TRANSPORT_CONNECT_TIMEOUT=3)(ADDRESS_LIST = (FAILOVER = ON) (LOAD_BALANCE = OFF)(ADDRESS = (PROTOCOL = TCP)(HOST = adgdb-s01-2021-11-22-170552-scan.pub.racdblab.oraclevcn.com)(PORT = 1521))(ADDRESS = (PROTOCOL = TCP)(HOST = adgsby-scan.pub.racdblab.oraclevcn.com)(PORT = 1521)))(CONNECT_DATA =(SERVICE_NAME = svc_tac.pub.racdblab.oraclevcn.com)))"

SQL*Plus: Release 19.0.0.0.0 - Production on Tue Nov 23 13:21:35 2021
Version 19.12.0.0.0

Copyright (c) 1982, 2021, Oracle.  All rights reserved.

Last Successful login time: Tue Nov 23 2021 13:16:29 +00:00

Connected to:
Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.12.0.0.0

SQL>
SQL> select SYS_CONTEXT('USERENV','DB_UNIQUE_NAME') from dual;

SYS_CONTEXT('USERENV','DB_UNIQUE_NAME')
--------------------------------------------------------------------------------
adg_fra269

=> We are connected to the primary database !!!

--- Initiate a transaction, but don't commit .... will commit that after the coffee break !!!

SQL> update emp4ac set sal=sal*1.1 where ename like 'Bob%';

17811 rows updated.

SQL>

--- From another terminal, perform a switchover !!!

DGMGRL> switchover to adg_fra383
Performing switchover NOW, please wait...
Operation requires a connection to database "adg_fra383"
Connecting ...
Connected to "adg_fra383"
Connected as SYSDBA.
New primary database "adg_fra383" is opening...
Oracle Clusterware is restarting database "adg_fra269" ...
Connected to "adg_fra269"
Connected to "adg_fra269"
Switchover succeeded, new primary is "adg_fra383"
DGMGRL> show configuration

Configuration - adg_fra383_adg_fra269

  Protection Mode: MaxPerformance
  Members:
  adg_fra383 - Primary database
    adg_fra269 - Physical standby database

Fast-Start Failover:  Disabled

Configuration Status:
SUCCESS   (status updated 102 seconds ago)

DGMGRL>

---- No error reported on the Sql*Plus session !!!
---- Coming back from the coffee break, and committing !!!

SQL> commit;

Commit complete.

SQL> select SYS_CONTEXT('USERENV','DB_UNIQUE_NAME') from dual;

SYS_CONTEXT('USERENV','DB_UNIQUE_NAME')
--------------------------------------------------------------------------------
adg_fra383


