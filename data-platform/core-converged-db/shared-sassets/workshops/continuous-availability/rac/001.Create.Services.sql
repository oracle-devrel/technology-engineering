Login and Identify Database and Instance names
**********************************************

Node1: ssh -i /Users/stef/Documents/Preventa/TMP/sshkeybundle/privateKey opc@<node1_public_ip>
Node2: ssh -i /Users/stef/Documents/Preventa/TMP/sshkeybundle/privateKey opc@<node2_public_ip>


List cluster resources:
***********************
Run the command to determine your database name and additional information about your cluster on node 1. Run this as the grid user.

ssh -i /Users/stef/Documents/Preventa/TMP/sshkeybundle/privateKey opc@<node1_public_ip>
sudo su - grid

/u01/app/19.0.0.0/grid/bin/crsctl stat res -t

Find your database name in the Cluster Resources section with the .db. Jot this information down, you will need it for this lab.

ora.lvrac_fra3md.db
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17Open,HOME=/u01/app/o
                                    18421                    racle/product/19.0.0
                                                             .0/dbhome_1,STABLE
      2        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17Open,HOME=/u01/app/o
                                    18422                    racle/product/19.0.0
                                                             .0/dbhome_1,STABLE

=> Database name is lvrac_fra3md



Create services:
****************

sudo su - oracle

Get the name of the instances:

[oracle@lvracdb-s01-2021-11-18-1718422 ~]$ ps -ef | grep pmon | grep lvrac
oracle   72990     1  0 Nov18 ?        00:00:04 ora_pmon_lvrac2

Instances are named lvrac1 and lvrac2

-- Create a new service called svctest !!!

srvctl add service -d lvrac_fra3md -s svctest -preferred lvrac1 -available lvrac2 -pdb pdb1
srvctl start service -d lvrac_fra3md -s svctest
[oracle@lvracdb-s01-2021-11-18-1718422 ~]$ srvctl status service -d lvrac_fra3md -s svctest
Service svctest is running on instance(s) lvrac1

Use the lsnrctl utility to list the services on both node 1 and node 2 as the grid user.

export ORACLE_HOME=/u01/app/19.0.0.0/grid
$ORACLE_HOME/bin/lsnrctl services

[grid@lvracdb-s01-2021-11-18-1718422 ~]$ $ORACLE_HOME/bin/lsnrctl services

LSNRCTL for Linux: Version 19.0.0.0.0 - Production on 19-NOV-2021 09:57:17

Copyright (c) 1991, 2021, Oracle.  All rights reserved.

Connecting to (DESCRIPTION=(ADDRESS=(PROTOCOL=IPC)(KEY=LISTENER)))
Services Summary...
Service "+APX" has 1 instance(s).
  Instance "+APX2", status READY, has 1 handler(s) for this service...
    Handler(s):
      "DEDICATED" established:0 refused:0 state:ready
         LOCAL SERVER
Service "+ASM" has 1 instance(s).
  Instance "+ASM2", status READY, has 1 handler(s) for this service...
    Handler(s):
      "DEDICATED" established:0 refused:0 state:ready
         LOCAL SERVER
Service "+ASM_DATA" has 1 instance(s).
  Instance "+ASM2", status READY, has 1 handler(s) for this service...
    Handler(s):
      "DEDICATED" established:0 refused:0 state:ready
         LOCAL SERVER
Service "+ASM_RECO" has 1 instance(s).
  Instance "+ASM2", status READY, has 1 handler(s) for this service...
    Handler(s):
      "DEDICATED" established:0 refused:0 state:ready
         LOCAL SERVER
Service "c9a7e2196ee27681e0531f02640a18c1.pub.racdblab.oraclevcn.com" has 1 instance(s).
  Instance "lvrac2", status READY, has 1 handler(s) for this service...
    Handler(s):
      "DEDICATED" established:0 refused:0 state:ready
         LOCAL SERVER
Service "d11546103f6d7831e0538100000a30ea.pub.racdblab.oraclevcn.com" has 1 instance(s).
  Instance "lvrac2", status READY, has 1 handler(s) for this service...
    Handler(s):
      "DEDICATED" established:0 refused:0 state:ready
         LOCAL SERVER
Service "lvracXDB.pub.racdblab.oraclevcn.com" has 1 instance(s).
  Instance "lvrac2", status READY, has 1 handler(s) for this service...
    Handler(s):
      "D000" established:0 refused:0 current:0 max:1022 state:ready
         DISPATCHER <machine: lvracdb-s01-2021-11-18-1718422, pid: 73364>
         (ADDRESS=(PROTOCOL=tcp)(HOST=lvracdb-s01-2021-11-18-1718422.pub.racdblab.oraclevcn.com)(PORT=58310))
Service "lvrac_fra3md.pub.racdblab.oraclevcn.com" has 1 instance(s).
  Instance "lvrac2", status READY, has 1 handler(s) for this service...
    Handler(s):
      "DEDICATED" established:0 refused:0 state:ready
         LOCAL SERVER
Service "pdb1.pub.racdblab.oraclevcn.com" has 1 instance(s).
  Instance "lvrac2", status READY, has 1 handler(s) for this service...
    Handler(s):
      "DEDICATED" established:0 refused:0 state:ready
         LOCAL SERVER
The command completed successfully
[grid@lvracdb-s01-2021-11-18-1718422 ~]$ $ORACLE_HOME/bin/lsnrctl status LISTENER

LSNRCTL for Linux: Version 19.0.0.0.0 - Production on 19-NOV-2021 09:57:54

Copyright (c) 1991, 2021, Oracle.  All rights reserved.

Connecting to (DESCRIPTION=(ADDRESS=(PROTOCOL=IPC)(KEY=LISTENER)))
STATUS of the LISTENER
------------------------
Alias                     LISTENER
Version                   TNSLSNR for Linux: Version 19.0.0.0.0 - Production
Start Date                18-NOV-2021 17:56:30
Uptime                    0 days 16 hr. 1 min. 24 sec
Trace Level               off
Security                  ON: Local OS Authentication
SNMP                      OFF
Listener Parameter File   /u01/app/19.0.0.0/grid/network/admin/listener.ora
Listener Log File         /u01/app/grid/diag/tnslsnr/lvracdb-s01-2021-11-18-1718422/listener/alert/log.xml
Listening Endpoints Summary...
  (DESCRIPTION=(ADDRESS=(PROTOCOL=ipc)(KEY=LISTENER)))
  (DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)(HOST=10.0.0.146)(PORT=1521)))
  (DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)(HOST=10.0.0.139)(PORT=1521)))
Services Summary...
Service "+APX" has 1 instance(s).
  Instance "+APX2", status READY, has 1 handler(s) for this service...
Service "+ASM" has 1 instance(s).
  Instance "+ASM2", status READY, has 1 handler(s) for this service...
Service "+ASM_DATA" has 1 instance(s).
  Instance "+ASM2", status READY, has 1 handler(s) for this service...
Service "+ASM_RECO" has 1 instance(s).
  Instance "+ASM2", status READY, has 1 handler(s) for this service...
Service "c9a7e2196ee27681e0531f02640a18c1.pub.racdblab.oraclevcn.com" has 1 instance(s).
  Instance "lvrac2", status READY, has 1 handler(s) for this service...
Service "d11546103f6d7831e0538100000a30ea.pub.racdblab.oraclevcn.com" has 1 instance(s).
  Instance "lvrac2", status READY, has 1 handler(s) for this service...
Service "lvracXDB.pub.racdblab.oraclevcn.com" has 1 instance(s).
  Instance "lvrac2", status READY, has 1 handler(s) for this service...
Service "lvrac_fra3md.pub.racdblab.oraclevcn.com" has 1 instance(s).
  Instance "lvrac2", status READY, has 1 handler(s) for this service...
Service "pdb1.pub.racdblab.oraclevcn.com" has 1 instance(s).
  Instance "lvrac2", status READY, has 1 handler(s) for this service...
The command completed successfully

=> Note that this service is only active on one instance at a time, so both local listeners will not include an entry for this service. 
In the example shown here, the listener on racnode2 would not have an entry for *Service "svctest.pub.racdblab.oraclevcn.com"

On node 1:

[grid@lvracdb-s01-2021-11-18-1718421 ~]$ $ORACLE_HOME/bin/lsnrctl services

LSNRCTL for Linux: Version 19.0.0.0.0 - Production on 19-NOV-2021 10:06:51

Copyright (c) 1991, 2021, Oracle.  All rights reserved.

Connecting to (DESCRIPTION=(ADDRESS=(PROTOCOL=IPC)(KEY=LISTENER)))
Services Summary...
Service "+APX" has 1 instance(s).
  Instance "+APX1", status READY, has 1 handler(s) for this service...
    Handler(s):
      "DEDICATED" established:0 refused:0 state:ready
         LOCAL SERVER
Service "+ASM" has 1 instance(s).
  Instance "+ASM1", status READY, has 1 handler(s) for this service...
    Handler(s):
      "DEDICATED" established:0 refused:0 state:ready
         LOCAL SERVER
Service "+ASM_DATA" has 1 instance(s).
  Instance "+ASM1", status READY, has 1 handler(s) for this service...
    Handler(s):
      "DEDICATED" established:0 refused:0 state:ready
         LOCAL SERVER
Service "+ASM_RECO" has 1 instance(s).
  Instance "+ASM1", status READY, has 1 handler(s) for this service...
    Handler(s):
      "DEDICATED" established:0 refused:0 state:ready
         LOCAL SERVER
Service "c9a7e2196ee27681e0531f02640a18c1.pub.racdblab.oraclevcn.com" has 1 instance(s).
  Instance "lvrac1", status READY, has 1 handler(s) for this service...
    Handler(s):
      "DEDICATED" established:0 refused:0 state:ready
         LOCAL SERVER
Service "d11546103f6d7831e0538100000a30ea.pub.racdblab.oraclevcn.com" has 1 instance(s).
  Instance "lvrac1", status READY, has 1 handler(s) for this service...
    Handler(s):
      "DEDICATED" established:0 refused:0 state:ready
         LOCAL SERVER
Service "lvracXDB.pub.racdblab.oraclevcn.com" has 1 instance(s).
  Instance "lvrac1", status READY, has 1 handler(s) for this service...
    Handler(s):
      "D000" established:0 refused:0 current:0 max:1022 state:ready
         DISPATCHER <machine: lvracdb-s01-2021-11-18-1718421, pid: 8733>
         (ADDRESS=(PROTOCOL=tcp)(HOST=lvracdb-s01-2021-11-18-1718421.pub.racdblab.oraclevcn.com)(PORT=57366))
Service "lvrac_fra3md.pub.racdblab.oraclevcn.com" has 1 instance(s).
  Instance "lvrac1", status READY, has 1 handler(s) for this service...
    Handler(s):
      "DEDICATED" established:0 refused:0 state:ready
         LOCAL SERVER
Service "pdb1.pub.racdblab.oraclevcn.com" has 1 instance(s).
  Instance "lvrac1", status READY, has 1 handler(s) for this service...
    Handler(s):
      "DEDICATED" established:0 refused:0 state:ready
         LOCAL SERVER
Service "svctest.pub.racdblab.oraclevcn.com" has 1 instance(s).
  Instance "lvrac1", status READY, has 1 handler(s) for this service...
    Handler(s):
      "DEDICATED" established:0 refused:0 state:ready
         LOCAL SERVER
The command completed successfully

=> On node 1 service svctest.pub.racdblab.oraclevcn.com has been registered in the local listener.

Cause the service to fail over. After identifying which instance the service is being offered on, kill that instance by removing the SMON process at the operating system level. Run this on node 1

[opc@lvracdb-s01-2021-11-18-1718421 ~]$ sudo su - oracle
Last login: Fri Nov 19 10:17:29 UTC 2021
[oracle@lvracdb-s01-2021-11-18-1718421 ~]$ ps -ef | grep ora_smon
oracle    8627     1  0 Nov18 ?        00:00:02 ora_smon_lvrac1
oracle   92886 92852  0 10:17 pts/0    00:00:00 grep --color=auto ora_smon
[oracle@lvracdb-s01-2021-11-18-1718421 ~]$

kill  -9 8627

[oracle@lvracdb-s01-2021-11-18-1718421 ~]$ ps -ef | grep ora_smon
oracle   93344 92852  0 10:18 pts/0    00:00:00 grep --color=auto ora_smon

Check the service status:

srvctl status service -d lvrac_fra3md -s svctest
[oracle@lvracdb-s01-2021-11-18-1718421 ~]$ srvctl status service -d lvrac_fra3md -s svctest
Service svctest is running on instance(s) lvrac2

=> Failover to instance 2 !!!

-- Manually relocate the service on instance 1:

srvctl relocate service -d lvrac_fra3md -s svctest -oldinst lvrac2 -newinst lvrac1
[oracle@lvracdb-s01-2021-11-18-1718421 ~]$ srvctl status service -d lvrac_fra3md -s svctest
Service svctest is running on instance(s) lvrac1

Configure services for Application Contimuity 
*********************************************

FAN, connection identifier, TAC, AC, switchover, consumer groups, and many other features and operations are predicated on the use of services. 
Do not use the default database service (the service created automatically with the same name as the database or PDB) 
as this service cannot be disabled, relocated, or restricted and so has no high availability support. 
The services you use are associated with a specific primary or standby role in a Data Guard environment. 
Do not use the initialization parameter service_names for application usage.

Note: If you need to find your database name run the command:

[oracle@lvracdb-s01-2021-11-18-1718421 ~]$ srvctl config database
lvrac_fra3md

Attributes set on the service enable applications to use Application Continuity. 
Create a service, setting the attributes failover_restore, commit_outcome, and failovertype for Application Continuity (AC). 
Replace the values for "-d", "-s", "-preferred" and "-available" with those of your system.

srvctl add service -d lvrac_fra3md -s svc_ac -commit_outcome TRUE -failovertype TRANSACTION -failover_restore LEVEL1 -preferred lvrac1 -available lvrac2 -pdb pdb1 -clbgoal LONG -rlbgoal NONE

Create a service named noac with no AC settings

srvctl add service -d lvrac_fra3md -s noac -commit_outcome FALSE -failovertype NONE -failover_restore NONE -preferred lvrac1 -available lvrac2 -pdb pdb1 -clbgoal LONG -rlbgoal NONE

Start both:

srvctl start service -d lvrac_fra3md -s svc_ac
srvctl start service -d lvrac_fra3md -s noac

[oracle@lvracdb-s01-2021-11-18-1718421 ~]$ srvctl status service -d lvrac_fra3md -s svc_ac
Service svc_ac is running on instance(s) lvrac1
[oracle@lvracdb-s01-2021-11-18-1718421 ~]$ srvctl status service -d lvrac_fra3md -s noac
Service noac is running on instance(s) lvrac1
[oracle@lvracdb-s01-2021-11-18-1718421 ~]$

