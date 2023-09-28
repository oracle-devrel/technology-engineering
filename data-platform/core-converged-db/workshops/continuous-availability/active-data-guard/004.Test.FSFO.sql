--- We start from a FSFO configuration with 3 observers !!!
--- dbobs1 is running in AD1
--- dbobs2 is running in AD2
--- dbobs3 is running in AD3

[oracle@dgobserver3 ~]$ dgmgrl
DGMGRL for Linux: Release 21.0.0.0.0 - Production on Wed Nov 24 10:29:00 2021
Version 21.1.0.0.0

Copyright (c) 1982, 2020, Oracle and/or its affiliates.  All rights reserved.

Welcome to DGMGRL, type "help" for information.
DGMGRL> connect sys/"<passwd>"@adg_fra383 as sysdba
Connected to "adg_fra383"
Connected as SYSDBA.
DGMGRL> show observer

Configuration - adg_fra383_adg_fra269

  Fast-Start Failover:     ENABLED

  Primary:            adg_fra383
  Active Target:      adg_fra269

Observer "dgobs2"(21.1.0.0.0) - Master

  Host Name:                    dgobserver2
  Last Ping to Primary:         0 seconds ago
  Last Ping to Target:          2 seconds ago
  Log File:
  State File:

Observer "dgobs1"(21.1.0.0.0) - Backup

  Host Name:                    dgobserver1
  Last Ping to Primary:         0 seconds ago
  Last Ping to Target:          1 second ago
  Log File:
  State File:

Observer "dgobs3"(21.1.0.0.0) - Backup

  Host Name:                    dgobserver3
  Last Ping to Primary:         0 seconds ago
  Last Ping to Target:          1 second ago
  Log File:
  State File:

DGMGRL>

--- First test: Observer resilience
--- Kill the master observer, in this case dgobs2 !!!

[oracle@dgobserver2 wallet]$ ps -ef | grep dgmgrl
oracle   10385     1 31 10:14 ?        00:05:37 /u01/app/oracle/client/bin/dgmgrl              START OBSERVER dgobs2 FILE IS '/u01/app/oracle/client/network/admin/fsfo.dat' LOGFILE IS '/u01/app/oracle/client/network/admin/observer_dgobs2.log'
oracle   15103  2217  0 10:32 pts/0    00:00:00 grep --color=auto dgmgrl

[oracle@dgobserver2 wallet]$ kill -9 10385

-- From observer 3 machine, observe the configuration:

[oracle@dgobserver3 ~]$ dgmgrl
DGMGRL for Linux: Release 21.0.0.0.0 - Production on Wed Nov 24 10:33:29 2021
Version 21.1.0.0.0

Copyright (c) 1982, 2020, Oracle and/or its affiliates.  All rights reserved.

Welcome to DGMGRL, type "help" for information.
DGMGRL> connect sys/"<passwd>"@adg_fra383 as sysdba
Connected to "adg_fra383"
Connected as SYSDBA.
DGMGRL> show observer

Configuration - adg_fra383_adg_fra269

  Fast-Start Failover:     ENABLED

  Primary:            adg_fra383
  Active Target:      adg_fra269

Observer "dgobs1"(21.1.0.0.0) - Master

  Host Name:                    dgobserver1
  Last Ping to Primary:         0 seconds ago
  Last Ping to Target:          2 seconds ago
  Log File:
  State File:

Observer "dgobs2"(21.1.0.0.0) - Backup

  Host Name:                    dgobserver2
  Last Ping to Primary:         59 seconds ago
  Last Ping to Target:          28 seconds ago
  Log File:
  State File:

Observer "dgobs3"(21.1.0.0.0) - Backup

  Host Name:                    dgobserver3
  Last Ping to Primary:         0 seconds ago
  Last Ping to Target:          2 seconds ago
  Log File:
  State File:

DGMGRL>

-- dgobs1 became the master observer
-- dgobs2 not pinging the databases because it has been killed, need to restart manually

[oracle@dgobserver2 wallet]$ dgmgrl
DGMGRL for Linux: Release 21.0.0.0.0 - Production on Wed Nov 24 10:36:48 2021
Version 21.1.0.0.0

Copyright (c) 1982, 2020, Oracle and/or its affiliates.  All rights reserved.

Welcome to DGMGRL, type "help" for information.
DGMGRL> connect sys/"<passwd>"@adg_fra383 as sysdba
Connected to "adg_fra383"
Connected as SYSDBA.
DGMGRL>
DGMGRL>
DGMGRL> start observer dgobs2 in background file is '/u01/app/oracle/client/network/admin/fsfo.dat' logfile is '/u01/app/oracle/client/network/admin/observer_dgobs2.log' connect identifier is 'adg_fra383';
Connected to "adg_fra383"
Submitted command "START OBSERVER" using connect identifier "adg_fra383"
DGMGRL> DGMGRL for Linux: Release 21.0.0.0.0 - Production on Wed Nov 24 10:37:12 2021
Version 21.1.0.0.0

Copyright (c) 1982, 2020, Oracle and/or its affiliates.  All rights reserved.

Welcome to DGMGRL, type "help" for information.
Connected to "adg_fra383"
Connected as SYSDBA.
Succeeded in opening the observer file "/u01/app/oracle/client/network/admin/fsfo.dat".
Observer 'dgobs2' started
The observer log file is '/u01/app/oracle/client/network/admin/observer_dgobs2.log'.


-- Re-check the observers from any obsever machine:

[oracle@dgobserver3 ~]$ dgmgrl
DGMGRL for Linux: Release 21.0.0.0.0 - Production on Wed Nov 24 10:38:02 2021
Version 21.1.0.0.0

Copyright (c) 1982, 2020, Oracle and/or its affiliates.  All rights reserved.

Welcome to DGMGRL, type "help" for information.
DGMGRL> connect sys/"<passwd>"@adg_fra383 as sysdba
Connected to "adg_fra383"
Connected as SYSDBA.
DGMGRL> show observer

Configuration - adg_fra383_adg_fra269

  Fast-Start Failover:     ENABLED

  Primary:            adg_fra383
  Active Target:      adg_fra269

Observer "dgobs1"(21.1.0.0.0) - Master

  Host Name:                    dgobserver1
  Last Ping to Primary:         0 seconds ago
  Last Ping to Target:          0 seconds ago
  Log File:
  State File:

Observer "dgobs2"(21.1.0.0.0) - Backup

  Host Name:                    dgobserver2
  Last Ping to Primary:         0 seconds ago
  Last Ping to Target:          2 seconds ago
  Log File:
  State File:

Observer "dgobs3"(21.1.0.0.0) - Backup

  Host Name:                    dgobserver3
  Last Ping to Primary:         0 seconds ago
  Last Ping to Target:          0 seconds ago
  Log File:
  State File:

DGMGRL>

=> OK

--- Now we will shutdown abort the primary database, and see what happens !!!

stef@stef-mac 003.DB.Resilience % ssh -i /Users/stef/Documents/Preventa/TMP/sshkeybundle/privateKey opc@130.162.51.15
Last login: Tue Nov 23 16:06:25 2021 from 92.56.97.244
[opc@adgdb-s01-2021-11-22-170552 ~]$
[opc@adgdb-s01-2021-11-22-170552 ~]$
[opc@adgdb-s01-2021-11-22-170552 ~]$
[opc@adgdb-s01-2021-11-22-170552 ~]$ sudo su - oracle
Last login: Wed Nov 24 10:39:31 UTC 2021
[oracle@adgdb-s01-2021-11-22-170552 ~]$
[oracle@adgdb-s01-2021-11-22-170552 ~]$
[oracle@adgdb-s01-2021-11-22-170552 ~]$
[oracle@adgdb-s01-2021-11-22-170552 ~]$ sqlplus / as sysdba

SQL*Plus: Release 19.0.0.0.0 - Production on Wed Nov 24 10:40:06 2021
Version 19.12.0.0.0

Copyright (c) 1982, 2021, Oracle.  All rights reserved.


Connected to:
Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.12.0.0.0

SQL> select open_mode, database_role from v$database;

OPEN_MODE	     DATABASE_ROLE
-------------------- ----------------
READ WRITE	     PRIMARY

srvctl stop database -d $(srvctl config database) -o abort
[oracle@adgdb-s01-2021-11-22-170552 ~]$ srvctl status database -d $(srvctl config database)
Instance adg is not running on node adgdb-s01-2021-11-22-170552


DGMGRL> show observer
ORA-03113: end-of-file on communication channel
Process ID: 18645
Session ID: 209 Serial number: 28128

Configuration details cannot be determined by DGMGRL

--- Need to connect to the standby !!!

[oracle@dgobserver3 ~]$ dgmgrl
DGMGRL for Linux: Release 21.0.0.0.0 - Production on Wed Nov 24 10:51:10 2021
Version 21.1.0.0.0

Copyright (c) 1982, 2020, Oracle and/or its affiliates.  All rights reserved.

Welcome to DGMGRL, type "help" for information.
DGMGRL> connect sys/"<passwd>"@adg_fra269 as sysdba
Connected to "ADG_FRA269"
Connected as SYSDBA.
DGMGRL> show observer

Configuration - adg_fra383_adg_fra269

  Fast-Start Failover:     ENABLED

  Primary:            adg_fra269
  Active Target:      adg_fra383

Observer "dgobs1"(21.1.0.0.0) - Master

  Host Name:                    dgobserver1
  Last Ping to Primary:         0 seconds ago
  Last Ping to Target:          594 seconds ago
  Log File:
  State File:

Observer "dgobs2"(21.1.0.0.0) - Backup

  Host Name:                    dgobserver2
  Last Ping to Primary:         0 seconds ago
  Last Ping to Target:          594 seconds ago
  Log File:
  State File:

Observer "dgobs3"(21.1.0.0.0) - Backup

  Host Name:                    dgobserver3
  Last Ping to Primary:         0 seconds ago
  Last Ping to Target:          594 seconds ago
  Log File:
  State File:

DGMGRL> show configuration

Configuration - adg_fra383_adg_fra269

  Protection Mode: MaxPerformance
  Members:
  adg_fra269 - Primary database
    Warning: ORA-16824: multiple warnings, including fast-start failover-related warnings, detected for the database

    adg_fra383 - (*) Physical standby database (disabled)
      ORA-16661: the standby database needs to be reinstated

Fast-Start Failover: Enabled in Potential Data Loss Mode

Configuration Status:
WARNING   (status updated 13 seconds ago)


DGMGRL> show database adg_fra383

Database - adg_fra383

  Role:                PHYSICAL STANDBY
  Intended State:      APPLY-ON
  Transport Lag:       (unknown)
  Apply Lag:           (unknown)
  Average Apply Rate:  (unknown)
  Real Time Query:     OFF
  Instance(s):
    adg

Database Status:
DISABLED - ORA-16661: the standby database needs to be reinstated

DGMGRL> show database adg_fra269

Database - adg_fra269

  Role:                PRIMARY
  Intended State:      TRANSPORT-ON
  Instance(s):
    adg

  Database Warning(s):
    ORA-16829: fast-start failover configuration is lagging
    ORA-16869: fast-start failover target not initialized

Database Status:
WARNING

DGMGRL>

--- FSFO performed an automatic failover

---- After a while we start the former primary again ...
---  Hoping that an automatic re-instate will occur !!!
--- In a real case we would restore from backup !!!

[oracle@adgdb-s01-2021-11-22-170552 ~]$ srvctl start database -d $(srvctl config database)
[oracle@adgdb-s01-2021-11-22-170552 ~]$ srvctl status database -d $(srvctl config database)
Instance adg is running on node adgdb-s01-2021-11-22-170552
[oracle@adgdb-s01-2021-11-22-170552 ~]$

--- Let's observe the configuration !!!

DGMGRL> show configuration

Configuration - adg_fra383_adg_fra269

  Protection Mode: MaxPerformance
  Members:
  adg_fra269 - Primary database
    Warning: ORA-16824: multiple warnings, including fast-start failover-related warnings, detected for the database

    adg_fra383 - (*) Physical standby database
      Warning: ORA-16657: reinstatement of database in progress

Fast-Start Failover: Enabled in Potential Data Loss Mode

Configuration Status:
WARNING   (status updated 102 seconds ago)

-- FSFO is currently reinstating the former primary !!!
--- After some minutes ....

DGMGRL> show configuration

Configuration - adg_fra383_adg_fra269

  Protection Mode: MaxPerformance
  Members:
  adg_fra269 - Primary database
    adg_fra383 - (*) Physical standby database

Fast-Start Failover: Enabled in Potential Data Loss Mode

Configuration Status:
SUCCESS   (status updated 46 seconds ago)


DGMGRL> show database adg_fra269

Database - adg_fra269

  Role:                PRIMARY
  Intended State:      TRANSPORT-ON
  Instance(s):
    adg

Database Status:
SUCCESS

DGMGRL> show database adg_fra383

Database - adg_fra383

  Role:                PHYSICAL STANDBY
  Intended State:      APPLY-ON
  Transport Lag:       0 seconds (computed 1 second ago)
  Apply Lag:           0 seconds (computed 1 second ago)
  Average Apply Rate:  17.00 KByte/s
  Real Time Query:     ON
  Instance(s):
    adg

Database Status:
SUCCESS


DGMGRL> validate database adg_fra383

  Database Role:     Physical standby database
  Primary Database:  adg_fra269

  Ready for Switchover:  Yes
  Ready for Failover:    Yes (Primary Running)

  Managed by Clusterware:
    adg_fra269:  YES
    adg_fra383:  YES

=> OK

--- Optionnally, we can run a switchback to go back to the original configuration !!!
--- From any observer, run the switchover command !!!

DGMGRL> switchover to adg_fra383
2021-11-24T11:01:36.994+00:00
Performing switchover NOW, please wait...

2021-11-24T11:01:41.317+00:00
Operation requires a connection to database "adg_fra383"
Connecting ...
Connected to "adg_fra383"
Connected as SYSDBA.

2021-11-24T11:01:41.823+00:00
Continuing with the switchover...

2021-11-24T11:02:28.676+00:00
New primary database "adg_fra383" is opening...

2021-11-24T11:02:28.676+00:00
Oracle Clusterware is restarting database "adg_fra269" ...
Connected to "adg_fra269"
Connected to "adg_fra269"
2021-11-24T11:03:44.657+00:00
Switchover succeeded, new primary is "adg_fra383"

2021-11-24T11:03:44.659+00:00
Switchover processing complete, broker ready.

--- After a while, we are back to the initial configuration

DGMGRL> show configuration

Configuration - adg_fra383_adg_fra269

  Protection Mode: MaxPerformance
  Members:
  adg_fra383 - Primary database
    adg_fra269 - (*) Physical standby database

Fast-Start Failover: Enabled in Potential Data Loss Mode

Configuration Status:
SUCCESS   (status updated 18 seconds ago)


DGMGRL> validate database adg_fra269

  Database Role:     Physical standby database
  Primary Database:  adg_fra383

  Ready for Switchover:  Yes
  Ready for Failover:    Yes (Primary Running)

  Managed by Clusterware:
    adg_fra383:  YES
    adg_fra269:  YES

-- This concludes the ADG lab !!!



