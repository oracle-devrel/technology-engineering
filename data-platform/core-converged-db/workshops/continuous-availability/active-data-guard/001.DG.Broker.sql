-- Connect to the primary server and show the DG broker configuration:

-- Primary server: <primary_server_public_ip> - ssh -i /Users/stef/Documents/Preventa/TMP/sshkeybundle/privateKey opc@<primary_server_public_ip>
-- Standby server: <standby_server_public_ip>  - ssh -i /Users/stef/Documents/Preventa/TMP/sshkeybundle/privateKey opc@<standby_server_public_ip>

[opc@adgdb-s01-2021-11-22-170552 ~]$ sudo su - oracle
Last login: Tue Nov 23 10:44:15 UTC 2021

sqlplus / as sysdba
show parameter dg_broker

SQL> show parameter dg_broker

NAME				     TYPE	 VALUE
------------------------------------ ----------- ------------------------------
dg_broker_config_file1		     string	 +DATA/ADG_FRA383/dr1adg_fra383
						 .dat
dg_broker_config_file2		     string	 +DATA/ADG_FRA383/dr2adg_fra383
						 .dat
dg_broker_start 		     boolean	 TRUE
SQL>

SQL> show parameter log_archive_config

NAME				     TYPE	 VALUE
------------------------------------ ----------- ------------------------------
log_archive_config		     string	 dg_config=(adg_fra383,adg_fra2
						 69)

SQL> show parameter log_archive_dest_2

NAME				     TYPE	 VALUE
------------------------------------ ----------- ------------------------------
log_archive_dest_2		     string	 service="adg_fra269", ASYNC NO
						 AFFIRM delay=0 optional compre
						 ssion=disable max_failure=0 re
						 open=300 db_unique_name="adg_f
						 ra269" net_timeout=30, valid_f
						 or=(online_logfile,all_roles)

SQL> show parameter standby_file

NAME				     TYPE	 VALUE
------------------------------------ ----------- ------------------------------
standby_file_management 	     string	 AUTO

-- Show the configuration !!

dgmgrl
connect sys/"<passwd>" as sysdba

DGMGRL> connect sys/"<passwd>" as sysdba
Connected to "adg_fra383"
Connected as SYSDBA.
DGMGRL>

DGMGRL> show configuration

Configuration - adg_fra383_adg_fra269

  Protection Mode: MaxPerformance
  Members:
  adg_fra383 - Primary database
    adg_fra269 - Physical standby database

Fast-Start Failover:  Disabled

Configuration Status:
SUCCESS   (status updated 10 seconds ago)


--- Show database properties !!!

DGMGRL> show database verbose adg_fra383

Database - adg_fra383

  Role:               PRIMARY
  Intended State:     TRANSPORT-ON
  Instance(s):
    adg

  Properties:
    DGConnectIdentifier             = 'adg_fra383'
    ObserverConnectIdentifier       = ''
    FastStartFailoverTarget         = ''
    PreferredObserverHosts          = ''
    LogShipping                     = 'ON'
    RedoRoutes                      = ''
    LogXptMode                      = 'ASYNC'
    DelayMins                       = '0'
    Binding                         = 'optional'
    MaxFailure                      = '0'
    ReopenSecs                      = '300'
    NetTimeout                      = '30'
    RedoCompression                 = 'DISABLE'
    PreferredApplyInstance          = ''
    ApplyInstanceTimeout            = '0'
    ApplyLagThreshold               = '30'
    TransportLagThreshold           = '30'
    TransportDisconnectedThreshold  = '30'
    ApplyParallel                   = 'AUTO'
    ApplyInstances                  = '0'
    StandbyFileManagement           = ''
    ArchiveLagTarget                = '0'
    LogArchiveMaxProcesses          = '0'
    LogArchiveMinSucceedDest        = '0'
    DataGuardSyncLatency            = '0'
    LogArchiveTrace                 = '0'
    LogArchiveFormat                = ''
    DbFileNameConvert               = ''
    LogFileNameConvert              = ''
    ArchiveLocation                 = ''
    AlternateLocation               = ''
    StandbyArchiveLocation          = ''
    StandbyAlternateLocation        = ''
    InconsistentProperties          = '(monitor)'
    InconsistentLogXptProps         = '(monitor)'
    LogXptStatus                    = '(monitor)'
    SendQEntries                    = '(monitor)'
    RecvQEntries                    = '(monitor)'
    HostName                        = 'adgdb-s01-2021-11-22-170552'
    StaticConnectIdentifier         = '(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=adgdb-s01-2021-11-22-170552)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=adg_fra383_DGMGRL.pub.racdblab.oraclevcn.com)(INSTANCE_NAME=adg)(SERVER=DEDICATED)))'
    TopWaitEvents                   = '(monitor)'
    SidName                         = '(monitor)'

  Log file locations:
    Alert log               : /u01/app/oracle/diag/rdbms/adg_fra383/adg/trace/alert_adg.log
    Data Guard Broker log   : /u01/app/oracle/diag/rdbms/adg_fra383/adg/trace/drcadg.log

Database Status:
SUCCESS

--- Change the protection mode from Max Performance to Max Availability !!!

DGMGRL> EDIT DATABASE 'adg_fra383' SET PROPERTY LogXptMode='SYNC';
Property "logxptmode" updated

DGMGRL> show database 'adg_fra383' 'LogXptMode';
  LogXptMode = 'SYNC'

DGMGRL> show database 'adg_fra269' 'LogXptMode';
  LogXptMode = 'ASYNC'
DGMGRL> EDIT DATABASE 'adg_fra269' SET PROPERTY LogXptMode='SYNC';
Property "logxptmode" updated
DGMGRL> show database 'adg_fra269' 'LogXptMode';
  LogXptMode = 'SYNC'
DGMGRL>

DGMGRL> show configuration

Configuration - adg_fra383_adg_fra269

  Protection Mode: MaxPerformance
  Members:
  adg_fra383 - Primary database
    adg_fra269 - Physical standby database

Fast-Start Failover:  Disabled

Configuration Status:
SUCCESS   (status updated 55 seconds ago)

DGMGRL> EDIT CONFIGURATION SET PROTECTION MODE AS MAXAVAILABILITY;
Succeeded.

DGMGRL> show configuration

Configuration - adg_fra383_adg_fra269

  Protection Mode: MaxAvailability
  Members:
  adg_fra383 - Primary database
    adg_fra269 - Physical standby database

Fast-Start Failover:  Disabled

Configuration Status:
SUCCESS   (status updated 44 seconds ago)


--- Back in MAX PERFORMANCE !!!

DGMGRL> EDIT CONFIGURATION SET PROTECTION MODE AS MAXPERFORMANCE;
Succeeded.
DGMGRL> EDIT DATABASE 'adg_fra269' SET PROPERTY LogXptMode='ASYNC';
Property "logxptmode" updated
DGMGRL> EDIT DATABASE 'adg_fra383' SET PROPERTY LogXptMode='ASYNC';
Property "logxptmode" updated
DGMGRL> show database 'adg_fra383' 'LogXptMode';
  LogXptMode = 'ASYNC'
DGMGRL> show database 'adg_fra269' 'LogXptMode';
  LogXptMode = 'ASYNC'
DGMGRL> show configuration

Configuration - adg_fra383_adg_fra269

  Protection Mode: MaxPerformance
  Members:
  adg_fra383 - Primary database
    adg_fra269 - Physical standby database

Fast-Start Failover:  Disabled

Configuration Status:
SUCCESS   (status updated 21 seconds ago)

--- Switchover !!!
--- From the primary site !!!

DGMGRL> show configuration

Configuration - adg_fra383_adg_fra269

  Protection Mode: MaxPerformance
  Members:
  adg_fra383 - Primary database
    adg_fra269 - Physical standby database

Fast-Start Failover:  Disabled

Configuration Status:
SUCCESS   (status updated 57 seconds ago)

DGMGRL> validate database adg_fra269

  Database Role:     Physical standby database
  Primary Database:  adg_fra383

  Ready for Switchover:  Yes
  Ready for Failover:    Yes (Primary Running)

  Managed by Clusterware:
    adg_fra383:  YES
    adg_fra269:  YES

DGMGRL> switchover to adg_fra269
Performing switchover NOW, please wait...
Operation requires a connection to database "adg_fra269"
Connecting ...
Connected to "adg_fra269"
Connected as SYSDBA.
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
SUCCESS   (status updated 119 seconds ago)

DGMGRL> validate database adg_fra383

  Database Role:     Physical standby database
  Primary Database:  adg_fra269

  Ready for Switchover:  Yes
  Ready for Failover:    Yes (Primary Running)

  Managed by Clusterware:
    adg_fra269:  YES
    adg_fra383:  YES

--- Switchback !!!
--- Illustrating that a switchover can be issued from either the primary or the standby !!!

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
SUCCESS   (status updated 28 seconds ago)

DGMGRL> validate database adg_fra269

  Database Role:     Physical standby database
  Primary Database:  adg_fra383

  Ready for Switchover:  Yes
  Ready for Failover:    Yes (Primary Running)

  Managed by Clusterware:
    adg_fra383:  YES
    adg_fra269:  YES


DGMGRL> show database adg_fra269

Database - adg_fra269

  Role:               PHYSICAL STANDBY
  Intended State:     APPLY-ON
  Transport Lag:      0 seconds (computed 0 seconds ago)
  Apply Lag:          0 seconds (computed 0 seconds ago)
  Average Apply Rate: 5.00 KByte/s
  Real Time Query:    ON
  Instance(s):
    adg

Database Status:
SUCCESS

---- Failover !!!
---- We take the primary down, and perform a failover !
---- Failover must be issued from the standby !!!
---- It's a destructive operation, meaning that the former primary will need to be re-instated !!!
--- Re-instate can be performed from DG Broker, but Flashback database must be on on both DB !!!

--- On the primary and the standby, check flashback database is ON !!!

-- Primary !!!
[oracle@adgdb-s01-2021-11-22-170552 ~]$ sqlplus / as sysdba

SQL*Plus: Release 19.0.0.0.0 - Production on Tue Nov 23 11:08:51 2021
Version 19.12.0.0.0

Copyright (c) 1982, 2021, Oracle.  All rights reserved.


Connected to:
Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.12.0.0.0

SQL> select open_mode, database_role, flashback_on from v$database;

OPEN_MODE	     DATABASE_ROLE    FLASHBACK_ON
-------------------- ---------------- ------------------
READ WRITE	     PRIMARY	      YES

-- Standby !!!
[oracle@adgsby ~]$ sqlplus / as sysdba

SQL*Plus: Release 19.0.0.0.0 - Production on Tue Nov 23 11:09:59 2021
Version 19.12.0.0.0

Copyright (c) 1982, 2021, Oracle.  All rights reserved.


Connected to:
Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.12.0.0.0

SQL> select open_mode, database_role, flashback_on from v$database;

OPEN_MODE	     DATABASE_ROLE    FLASHBACK_ON
-------------------- ---------------- ------------------
READ ONLY WITH APPLY PHYSICAL STANDBY YES

--- Let's take the primary down !!!

[oracle@adgdb-s01-2021-11-22-170552 ~]$ srvctl stop database -d $(srvctl config database) -o abort
[oracle@adgdb-s01-2021-11-22-170552 ~]$ srvctl status database -d $(srvctl config database)
Instance adg is not running on node adgdb-s01-2021-11-22-170552

--- From the standby site, perform a failover !!!
[oracle@adgsby ~]$ dgmgrl
DGMGRL for Linux: Release 19.0.0.0.0 - Production on Tue Nov 23 11:12:25 2021
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
    Error: ORA-12514: TNS:listener does not currently know of service requested in connect descriptor

    adg_fra269 - Physical standby database

Fast-Start Failover:  Disabled

Configuration Status:
ERROR   (status updated 0 seconds ago)

DGMGRL> failover to adg_fra269
Performing failover NOW, please wait...
Failover succeeded, new primary is "adg_fra269"
DGMGRL> show configuration

Configuration - adg_fra383_adg_fra269

  Protection Mode: MaxPerformance
  Members:
  adg_fra269 - Primary database
    Warning: ORA-16857: member disconnected from redo source for longer than specified threshold

    adg_fra383 - Physical standby database (disabled)
      ORA-16661: the standby database needs to be reinstated

Fast-Start Failover:  Disabled

Configuration Status:
WARNING   (status updated 58 seconds ago)

DGMGRL> validate database adg_fra383
Error: ORA-16541: member is not enabled

--- The new standby needs to be re-instated !!!
--- First we start the new standby !!!
--- In a real case, we would need to restore/recover from a backup !!!

--- On the former primary server, start the database !!!

[oracle@adgdb-s01-2021-11-22-170552 ~]$ srvctl start database -d $(srvctl config database)
[oracle@adgdb-s01-2021-11-22-170552 ~]$ srvctl status database -d $(srvctl config database)
Instance adg is running on node adgdb-s01-2021-11-22-170552

--- Then we reinstate, from the new primary site !!!
DGMGRL> reinstate database adg_fra383
Reinstating database "adg_fra383", please wait...
Reinstatement of database "adg_fra383" succeeded
DGMGRL> show configuration

Configuration - adg_fra383_adg_fra269

  Protection Mode: MaxPerformance
  Members:
  adg_fra269 - Primary database
    adg_fra383 - Physical standby database

Fast-Start Failover:  Disabled

Configuration Status:
SUCCESS   (status updated 57 seconds ago)

DGMGRL> validate database adg_fra383

  Database Role:     Physical standby database
  Primary Database:  adg_fra269

  Ready for Switchover:  Yes
  Ready for Failover:    Yes (Primary Running)

  Managed by Clusterware:
    adg_fra269:  YES
    adg_fra383:  YES

DGMGRL> show database adg_fra383

Database - adg_fra383

  Role:               PHYSICAL STANDBY
  Intended State:     APPLY-ON
  Transport Lag:      0 seconds (computed 0 seconds ago)
  Apply Lag:          0 seconds (computed 0 seconds ago)
  Average Apply Rate: 21.00 KByte/s
  Real Time Query:    ON
  Instance(s):
    adg

Database Status:
SUCCESS

--- We would perform a final switchback (optionally) !!!!

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
SUCCESS   (status updated 92 seconds ago)

DGMGRL> show database adg_fra269

Database - adg_fra269

  Role:               PHYSICAL STANDBY
  Intended State:     APPLY-ON
  Transport Lag:      0 seconds (computed 0 seconds ago)
  Apply Lag:          0 seconds (computed 0 seconds ago)
  Average Apply Rate: 43.00 KByte/s
  Real Time Query:    ON
  Instance(s):
    adg

Database Status:
SUCCESS
