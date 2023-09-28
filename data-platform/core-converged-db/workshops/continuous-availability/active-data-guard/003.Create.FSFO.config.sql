-- In this lab we will create observers for FSFO !!!
--- First import a custom image from Object Storage URL:
--- https://objectstorage.eu-frankfurt-1.oraclecloud.com/p/9etVH1sO2u6HGcJgLW13j_uplBp9GhN9eQqLTTYnpjZFL4eogz-LNXuFes2AuduD/n/oractdemeabdmautodb/b/CustomImages/o/IMG_DGOBSERVER_21C

-- In your compartment, navigate to "Compute => Custom images"
--- Import the image from the URL:

-- After aprox. 10 minutes, the image is imported.
--- Create 3 compute instances from that image: dgobserver1, dgobserver2 and dgobserver3
-- Place dgobserver1 in AD1, dgobserver2 in AD2 and dgobserver3 in AD3 

-- Write down the public/private IP of your servers
-- dgobserver1: <observer1_public_ip>/<observer1_private_ip>   - ssh -i /Users/stef/Documents/Preventa/TMP/sshkeybundle/privateKey opc@<observer1_public_ip>
-- dgobserver2: <observer2_public_ip>/<observer2_private_ip>   - ssh -i /Users/stef/Documents/Preventa/TMP/sshkeybundle/privateKey opc@<observer2_public_ip>
-- dgobserver3: <observer3_public_ip>/<observer3_private_ip> - ssh -i /Users/stef/Documents/Preventa/TMP/sshkeybundle/privateKey opc@<observer3_public_ip>

--- On each server, an "oracle" OS user has been created, and the Oracle Client software has been installed.
--- Connect on any observer node and check:

[opc@dgobserver1 ~]$ sudo su - oracle
Last login: Wed Jul  7 09:42:03 GMT 2021 on pts/2
[oracle@dgobserver1 ~]$ which dgmgrl
/u01/app/oracle/client/bin/dgmgrl

--- Modify /u01/app/oracle/client/network/admin/tnsnames.ora with your own values !!!

[oracle@dgobserver1 ~]$ cat /u01/app/oracle/client/network/admin/tnsnames.ora
DBSDU_TSE=(DESCRIPTION=(SDU=65535)(SEND_BUF_SIZE=10485760)(RECV_BUF_SIZE=10485760)(ADDRESS=(PROTOCOL=TCP)(HOST=10.0.1.107)(PORT=1521))(CONNECT_DATA=(SERVER=DEDICATED)(SERVICE_NAME=DBSDU_TSE.sub06221433571.skynet.oraclevcn.com)(UR=A)))
DBSDU_FRA2BW=(DESCRIPTION=(SDU=65535)(SEND_BUF_SIZE=10485760)(RECV_BUF_SIZE=10485760)(ADDRESS=(PROTOCOL=TCP)(HOST=10.0.1.153)(PORT=1521))(CONNECT_DATA=(SERVER=DEDICATED)(SERVICE_NAME=DBSDU_fra2bw.sub06221433571.skynet.oraclevcn.com)(UR=A)))
[oracle@dgobserver1 ~]$

-- Substitute by your values on each observer node !!!
-- Use the private IP of the primary and standby DB Hosts  !!!
-- Primary Host: 10.0.0.180
-- Standby Host: 10.0.0.109

adg_fra383=(DESCRIPTION=(SDU=65535)(SEND_BUF_SIZE=10485760)(RECV_BUF_SIZE=10485760)(ADDRESS=(PROTOCOL=TCP)(HOST=10.0.0.180)(PORT=1521))(CONNECT_DATA=(SERVER=DEDICATED)(SERVICE_NAME=adg_fra383.pub.racdblab.oraclevcn.com)(UR=A)))
adg_fra269=(DESCRIPTION=(SDU=65535)(SEND_BUF_SIZE=10485760)(RECV_BUF_SIZE=10485760)(ADDRESS=(PROTOCOL=TCP)(HOST=10.0.0.109)(PORT=1521))(CONNECT_DATA=(SERVER=DEDICATED)(SERVICE_NAME=adg_fra269.pub.racdblab.oraclevcn.com)(UR=A)))


--- Test the connections !!!
--- From the observer nodes, test the connections with dgmgrl !!!
stef@stef-mac 20211115.MT.Workshop % ssh -i /Users/stef/Documents/Preventa/TMP/sshkeybundle/privateKey opc@<observer1_public_ip>
Last login: Tue Nov 23 16:10:05 2021 from 92.56.97.244
-bash: warning: setlocale: LC_CTYPE: cannot change locale (UTF-8): No such file or directory
[opc@dgobserver1 ~]$ sudo su - oracle
Last login: Tue Nov 23 16:10:11 GMT 2021 on pts/0
[oracle@dgobserver1 ~]$
[oracle@dgobserver1 ~]$
[oracle@dgobserver1 ~]$ dgmgrl
DGMGRL for Linux: Release 21.0.0.0.0 - Production on Tue Nov 23 16:14:15 2021
Version 21.1.0.0.0

Copyright (c) 1982, 2020, Oracle and/or its affiliates.  All rights reserved.

Welcome to DGMGRL, type "help" for information.
DGMGRL> connect sys/"<passwd>"@adg_fra383 as sysdba
Connected to "adg_fra383"
Connected as SYSDBA.
DGMGRL>
DGMGRL> connect sys/"<passwd>"@adg_fra269 as sysdba
Connected to "adg_fra269"
Connected as SYSDBA.
DGMGRL>

-- Repeat that checks from dgobserver2 and dgobserver3 !!!
[opc@dgobserver2 ~]$ sudo su - oracle
Last login: Tue Nov 23 16:11:17 GMT 2021 on pts/0
[oracle@dgobserver2 ~]$ dgmgrl
DGMGRL for Linux: Release 21.0.0.0.0 - Production on Tue Nov 23 16:32:48 2021
Version 21.1.0.0.0

Copyright (c) 1982, 2020, Oracle and/or its affiliates.  All rights reserved.

Welcome to DGMGRL, type "help" for information.
DGMGRL> connect sys/"<passwd>"@adg_fra383 as sysdba
Connected to "adg_fra383"
Connected as SYSDBA.
DGMGRL> connect sys/"<passwd>"@adg_fra269 as sysdba
Connected to "adg_fra269"
Connected as SYSDBA.
DGMGRL>

[opc@dgobserver3 ~]$ sudo su - oracle
Last login: Tue Nov 23 16:12:12 GMT 2021 on pts/0
[oracle@dgobserver3 ~]$ dgmgrl
DGMGRL for Linux: Release 21.0.0.0.0 - Production on Tue Nov 23 16:31:43 2021
Version 21.1.0.0.0

Copyright (c) 1982, 2020, Oracle and/or its affiliates.  All rights reserved.

Welcome to DGMGRL, type "help" for information.
DGMGRL> connect sys/"<passwd>"@adg_fra383 as sysdba
Connected to "adg_fra383"
Connected as SYSDBA.
DGMGRL> connect sys/"<passwd>"@adg_fra269 as sysdba
Connected to "adg_fra269"
Connected as SYSDBA.
DGMGRL>

-- Now we can proceed !!

--- Enable fast-start failover !!!
--- From any machine (Observer, primary, standby) !!!

[oracle@dgobserver1 ~]$ dgmgrl
DGMGRL for Linux: Release 21.0.0.0.0 - Production on Tue Nov 23 16:14:15 2021
Version 21.1.0.0.0

Copyright (c) 1982, 2020, Oracle and/or its affiliates.  All rights reserved.

Welcome to DGMGRL, type "help" for information.
DGMGRL> connect sys/"<passwd>"@adg_fra383 as sysdba
Connected to "adg_fra383"
Connected as SYSDBA.
DGMGRL>
DGMGRL> connect sys/"<passwd>"@adg_fra269 as sysdba
Connected to "adg_fra269"
Connected as SYSDBA.
DGMGRL>
DGMGRL>
DGMGRL>
DGMGRL> show configuration

Configuration - adg_fra383_adg_fra269

  Protection Mode: MaxPerformance
  Members:
  adg_fra383 - Primary database
    adg_fra269 - Physical standby database

Fast-Start Failover:  Disabled

Configuration Status:
SUCCESS   (status updated 39 seconds ago)

DGMGRL> ENABLE FAST_START FAILOVER
Enabled in Potential Data Loss Mode.

DGMGRL> show configuration

Configuration - adg_fra383_adg_fra269

  Protection Mode: MaxPerformance
  Members:
  adg_fra383 - Primary database
    Warning: ORA-16819: fast-start failover observer not started

    adg_fra269 - (*) Physical standby database

Fast-Start Failover: Enabled in Potential Data Loss Mode

Configuration Status:
WARNING   (status updated 34 seconds ago)

-- Check Observer connect string !!!

DGMGRL> show database adg_fra383 'DGConnectIdentifier'
  DGConnectIdentifier = 'adg_fra383'

DGMGRL> show database adg_fra269 'DGConnectIdentifier'
  DGConnectIdentifier = 'adg_fra269'

DGMGRL> edit database adg_fra383 set property 'ObserverConnectIdentifier'='adg_fra383';
Property "ObserverConnectIdentifier" updated
DGMGRL> edit database adg_fra269 set property 'ObserverConnectIdentifier'='adg_fra269';
Property "ObserverConnectIdentifier" updated

---- Before starting the observer in background, we need to configure a wallet, so that the observer can connect to both the primary and the standby database !!!
--- Configure Wallet from the OBSERVER host:

-- Clean-up the /u01/app/oracle/wallet/ directory:

[oracle@dgobserver1 wallet]$ rm /u01/app/oracle/wallet/*
[oracle@dgobserver1 wallet]$ cd /u01/app/oracle/wallet
[oracle@dgobserver1 wallet]$ ls -ltr
total 0
*/

-- Create a new wallet:

[oracle@dgobserver1 wallet]$ mkstore -wrl /u01/app/oracle/wallet/ -create
Oracle Secret Store Tool Release 21.0.0.0.0 - Production
Version 21.0.0.0.0
Copyright (c) 2004, 2020, Oracle and/or its affiliates. All rights reserved.

Enter password: <passwd>
Enter password again: <passwd>

[oracle@dgobserver1 wallet]$ ls -ltr
total 8
-rw-------. 1 oracle oinstall   0 Nov 23 16:55 ewallet.p12.lck
-rw-------. 1 oracle oinstall 149 Nov 23 16:55 ewallet.p12
-rw-------. 1 oracle oinstall   0 Nov 23 16:55 cwallet.sso.lck
-rw-------. 1 oracle oinstall 194 Nov 23 16:55 cwallet.sso

[oracle@dgobserver1 wallet]$ mkstore -wrl /u01/app/oracle/wallet/ -createCredential 'adg_fra383' sys <passwd>
Oracle Secret Store Tool Release 21.0.0.0.0 - Production
Version 21.0.0.0.0
Copyright (c) 2004, 2020, Oracle and/or its affiliates. All rights reserved.

Enter wallet password: <passwd>


[oracle@dgobserver1 wallet]$ mkstore -wrl /u01/app/oracle/wallet/ -createCredential 'adg_fra269' sys <passwd>
Oracle Secret Store Tool Release 21.0.0.0.0 - Production
Version 21.0.0.0.0
Copyright (c) 2004, 2020, Oracle and/or its affiliates. All rights reserved.

Enter wallet password: <passwd>

-- Check sqlnet.ora file:

cat /u01/app/oracle/client/network/admin/sqlnet.ora

[oracle@dgobserver1 wallet]$ cat /u01/app/oracle/client/network/admin/sqlnet.ora
NAMES.DIRECTORY_PATH= (TNSNAMES, ONAMES, HOSTNAME,EZCONNECT)
WALLET_LOCATION=(SOURCE=(METHOD=FILE)(METHOD_DATA=(DIRECTORY=/u01/app/oracle/wallet/)))
SQLNET.WALLET_OVERRIDE=TRUE

---- From Observer machine, start the observer in background !!!

dgmgrl
connect sys/"<passwd>"@adg_fra383 as sysdba

start observer dgobs1 in background file is '/u01/app/oracle/client/network/admin/fsfo.dat' logfile is '/u01/app/oracle/client/network/admin/observer_dgobs1.log' connect identifier is 'adg_fra383';

[oracle@dgobserver1 wallet]$ dgmgrl
DGMGRL for Linux: Release 21.0.0.0.0 - Production on Tue Nov 23 17:23:46 2021
Version 21.1.0.0.0

Copyright (c) 1982, 2020, Oracle and/or its affiliates.  All rights reserved.

Welcome to DGMGRL, type "help" for information.
DGMGRL> connect sys/"<passwd>"@adg_fra383 as sysdba
Connected to "adg_fra383"
Connected as SYSDBA.
DGMGRL> show observer

Configuration - adg_fra383_adg_fra269

  Fast-Start Failover:     ENABLED

No observers.

DGMGRL> start observer dgobs1 in background file is '/u01/app/oracle/client/network/admin/fsfo.dat' logfile is '/u01/app/oracle/client/network/admin/observer_dgobs1.log' connect identifier is 'adg_fra383';
Connected to "adg_fra383"
Submitted command "START OBSERVER" using connect identifier "adg_fra383"
DGMGRL> DGMGRL for Linux: Release 21.0.0.0.0 - Production on Tue Nov 23 17:24:09 2021
Version 21.1.0.0.0

Copyright (c) 1982, 2020, Oracle and/or its affiliates.  All rights reserved.

Welcome to DGMGRL, type "help" for information.
Connected to "adg_fra383"
Connected as SYSDBA.
Succeeded in opening the observer file "/u01/app/oracle/client/network/admin/fsfo.dat".
[W000 2021-11-23T17:24:12.314+00:00] Observer could not validate the contents of the observer file.
[W000 2021-11-23T17:24:12.476+00:00] FSFO target standby is adg_fra269
Observer 'dgobs1' started
The observer log file is '/u01/app/oracle/client/network/admin/observer_dgobs1.log'.

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


-- Repeat the setps on dgobserver2 and dgobserver3 !!

  start observer dgobs2 in background file is '/u01/app/oracle/client/network/admin/fsfo.dat' logfile is '/u01/app/oracle/client/network/admin/observer_dgobs2.log' connect identifier is 'adg_fra383';

[oracle@dgobserver2 wallet]$ dgmgrl
DGMGRL for Linux: Release 21.0.0.0.0 - Production on Wed Nov 24 09:48:41 2021
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
  Last Ping to Primary:         0 seconds ago
  Last Ping to Target:          2 seconds ago
  Log File:
  State File:


start observer dgobs3 in background file is '/u01/app/oracle/client/network/admin/fsfo.dat' logfile is '/u01/app/oracle/client/network/admin/observer_dgobs3.log' connect identifier is 'adg_fra383';

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
  Last Ping to Primary:         0 seconds ago
  Last Ping to Target:          2 seconds ago
  Log File:
  State File:

Observer "dgobs3"(21.1.0.0.0) - Backup

  Host Name:                    dgobserver3
  Last Ping to Primary:         0 seconds ago
  Last Ping to Target:          2 seconds ago
  Log File:
  State File:

=> We end-up with 3 observers, one Master and 2 backups

--- You can change the master !!!
--- From any observer !!!

DGMGRL> set masterobserver to dgobs2
Succeeded.

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
