Write a callout
***************

1. Connect to both compute nodes as grid
****************************************

Node1: ssh -i /Users/stef/Documents/Preventa/TMP/sshkeybundle/privateKey opc@<node1_public_ip>
Node2: ssh -i /Users/stef/Documents/Preventa/TMP/sshkeybundle/privateKey opc@<node2_public_ip>

sudo su - grid

--- On both nodes, create a shell script FAN callout !!!

cd /u01/app/19.0.0.0/grid/racg/usrco/
[grid@lvracdb-s01-2021-11-18-1718421 usrco]$ ls -ltr
total 0

-- Copy the following lines in a file: callout-log.sh

#!/usr/bin/bash
umask 022
FAN_LOGFILE=/tmp/`hostname -s`_events.log
echo $* " reported = "`date` >> ${FAN_LOGFILE} &


cat callout-log.sh

#!/usr/bin/bash
umask 022
FAN_LOGFILE=/tmp/lvracdb-s01-2021-11-18-1718422_events.log
echo  " reported = "Mon Nov 22 13:40:30 UTC 2021 >>  &

[grid@lvracdb-s01-2021-11-18-1718421 usrco]$ chmod +x /u01/app/19.0.0.0/grid/racg/usrco/callout-log.sh
[grid@lvracdb-s01-2021-11-18-1718421 usrco]$ ls -ltr
total 4
-rwxr-xr-x 1 grid oinstall 403 Nov 22 13:29 callout-log.sh
[grid@lvracdb-s01-2021-11-18-1718421 usrco]$

2. Generate an event
*********************

-- From any node, list the cluster resources !!!
/u01/app/19.0.0.0/grid/bin/crsctl stat res -t

[grid@lvracdb-s01-2021-11-18-1718422 usrco]$ /u01/app/19.0.0.0/grid/bin/crsctl stat res -t
--------------------------------------------------------------------------------
Name           Target  State        Server                   State details
--------------------------------------------------------------------------------
Local Resources
--------------------------------------------------------------------------------
ora.DATA.COMMONSTORE.advm
               ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
               ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
ora.LISTENER.lsnr
               ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
               ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
ora.chad
               ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
               ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
ora.data.commonstore.acfs
               ONLINE  ONLINE       lvracdb-s01-2021-11-18-17mounted on /opt/orac
                                    18421                    le/dcs/commonstore,S
                                                             TABLE
               ONLINE  ONLINE       lvracdb-s01-2021-11-18-17mounted on /opt/orac
                                    18422                    le/dcs/commonstore,S
                                                             TABLE
ora.net1.network
               ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
               ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
ora.ons
               ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
               ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
ora.proxy_advm
               ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
               ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
--------------------------------------------------------------------------------
Cluster Resources
--------------------------------------------------------------------------------
ora.DATA.dg(ora.asmgroup)
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
      2        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
ora.LISTENER_ASM.lsnr(ora.asmgroup)
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
      2        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
ora.LISTENER_SCAN1.lsnr
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
ora.LISTENER_SCAN2.lsnr
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
ora.LISTENER_SCAN3.lsnr
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
ora.RECO.dg(ora.asmgroup)
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
      2        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
ora.asm(ora.asmgroup)
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17Started,STABLE
                                    18421
      2        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17Started,STABLE
                                    18422
ora.asmnet1.asmnetwork(ora.asmgroup)
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
      2        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
ora.cdp1.cdp
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
ora.cdp2.cdp
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
ora.cdp3.cdp
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
ora.cvu
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
ora.lvrac_fra3md.ac_service.svc
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
ora.lvrac_fra3md.db
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17Open,HOME=/u01/app/o
                                    18421                    racle/product/19.0.0
                                                             .0/dbhome_1,STABLE
      2        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17Open,HOME=/u01/app/o
                                    18422                    racle/product/19.0.0
                                                             .0/dbhome_1,STABLE
ora.lvrac_fra3md.noac.svc
      2        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
ora.lvrac_fra3md.svc_ac.svc
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
ora.lvrac_fra3md.svctest.svc
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
ora.lvrac_fra3md.tac_service.svc
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
ora.lvrac_fra3md.unisrv.svc
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
      2        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
ora.lvracdb-s01-2021-11-18-1718421.vip
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
ora.lvracdb-s01-2021-11-18-1718422.vip
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
ora.qosmserver
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
ora.scan1.vip
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18422
ora.scan2.vip
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
ora.scan3.vip
      1        ONLINE  ONLINE       lvracdb-s01-2021-11-18-17STABLE
                                    18421
--------------------------------------------------------------------------------

--- Stop instance 1:

export ORACLE_HOME=/u01/app/19.0.0.0/grid
export PATH=$ORACLE_HOME/bin:$PATH
[grid@lvracdb-s01-2021-11-18-1718421 usrco]$ srvctl stop instance -d $(srvctl config database) -i lvrac1 -o immediate -force
[grid@lvracdb-s01-2021-11-18-1718421 usrco]$ srvctl status database -d $(srvctl config database)
Instance lvrac1 is not running on node lvracdb-s01-2021-11-18-1718421
Instance lvrac2 is running on node lvracdb-s01-2021-11-18-1718422
[grid@lvracdb-s01-2021-11-18-1718421 usrco]$

--- If your callout was written correctly and had the appropriate execute permissions, a file named hostname_events.log should be visible in the /tmp directory

[grid@lvracdb-s01-2021-11-18-1718421 usrco]$ ls -altr /tmp/*.log | grep events
-rw-r--r-- 1 grid   oinstall 1165 Nov 22 13:50 /tmp/lvracdb-s01-2021-11-18-1718421_events.log
[grid@lvracdb-s01-2021-11-18-1718421 usrco]$

cat /tmp/lvracdb-s01-2021-11-18-1718421_events.log
SERVICEMEMBER VERSION=1.0 service=unisrv.pub.racdblab.oraclevcn.com database=lvrac_fra3md instance=lvrac1 host=lvracdb-s01-2021-11-18-1718421 status=down reason=USER timestamp=2021-11-22 13:50:04 timezone=+00:00 db_domain=pub.racdblab.oraclevcn.com  reported = Mon Nov 22 13:50:04 UTC 2021
INSTANCE VERSION=1.0 service=lvrac_fra3md.pub.racdblab.oraclevcn.com database=lvrac_fra3md instance=lvrac1 host=lvracdb-s01-2021-11-18-1718421 status=down reason=USER timestamp=2021-11-22 13:50:44 timezone=+00:00 db_domain=pub.racdblab.oraclevcn.com  reported = Mon Nov 22 13:50:44 UTC 2021

--- Check on node2:

[grid@lvracdb-s01-2021-11-18-1718422 usrco]$ ls -ltr /tmp/*.log | grep events
[grid@lvracdb-s01-2021-11-18-1718422 usrco]$

-- Restart instance 1:

srvctl start instance -d $(srvctl config database) -i lvrac1

-- And check the log again: observe new lines were added to the logfile !!!

INSTANCE VERSION=1.0 service=lvrac_fra3md.pub.racdblab.oraclevcn.com database=lvrac_fra3md instance=lvrac1 host=lvracdb-s01-2021-11-18-1718421 status=up reason=USER timestamp=2021-11-22 13:54:32 timezone=+00:00 db_domain=pub.racdblab.oraclevcn.com  reported = Mon Nov 22 13:54:32 UTC 2021
SERVICEMEMBER VERSION=1.0 service=unisrv.pub.racdblab.oraclevcn.com database=lvrac_fra3md instance=lvrac1 host=lvracdb-s01-2021-11-18-1718421 status=up reason=USER card=2 timestamp=2021-11-22 13:54:34 timezone=+00:00 db_domain=pub.racdblab.oraclevcn.com  reported = Mon Nov 22 13:54:34 UTC 2021

3. Create a more elaborate callout
**********************************

Callouts can be any shell-script or executable. There can be multiple callouts in the racg/usrco directory and all will be executed with the FAN payload as arguments. 
The scripts are executed sequentially, so it is not recommended to have many scripts in this directory, 
as they could place a load on the system that is not desired, and there may be timeliness issues if the scripts wait for scheduling.

Create a second shell script on each node, in directory /u01/app/19.0.0.0/grid/racg/usrco/

cat callout_elaborate.sh

#!/usr/bin/bash
    # Scan and parse HA event payload arguments:
    #
    # define AWK
    AWK=/bin/awk
    # Define a log file to see results
    FAN_LOGFILE=/tmp/`hostname -s`.log
    # Event type is handled differently
    NOTIFY_EVENTTYPE=$1
    for ARGS in $*; do
        PROPERTY=`echo $ARGS | $AWK -F "=" '{print $1}'`
        VALUE=`echo $ARGS | $AWK -F "=" '{print $2}'`
        case $PROPERTY in
          VERSION|version) NOTIFY_VERSION=$VALUE ;;
          SERVICE|service) NOTIFY_SERVICE=$VALUE ;;
          DATABASE|database) NOTIFY_DATABASE=$VALUE ;;
          INSTANCE|instance) NOTIFY_INSTANCE=$VALUE ;;
          HOST|host) NOTIFY_HOST=$VALUE ;;
          STATUS|status) NOTIFY_STATUS=$VALUE ;;
          REASON|reason) NOTIFY_REASON=$VALUE ;;
          CARD|card) NOTIFY_CARDINALITY=$VALUE ;;
          VIP_IPS|vip_ips) NOTIFY_VIPS=$VALUE ;; #VIP_IPS for public_nw_down
          TIMESTAMP|timestamp) NOTIFY_LOGDATE=$VALUE ;; # catch event date
          TIMEZONE|timezone) NOTIFY_TZONE=$VALUE ;;
          ??:??:??) NOTIFY_LOGTIME=$PROPERTY ;; # catch event time (hh24:mi:ss)
        esac
    done

    # FAN events with the following conditions will be inserted# into the critical trouble ticket system:
    # NOTIFY_EVENTTYPE => SERVICE | DATABASE | NODE
    # NOTIFY_STATUS => down | public_nw_down | nodedown
    #
    if (( [ "$NOTIFY_EVENTTYPE" = "SERVICE" ] ||[ "$NOTIFY_EVENTTYPE" = "DATABASE" ] || \
        [ "$NOTIFY_EVENTTYPE" = "NODE" ] \
        ) && \
        ( [ "$NOTIFY_STATUS" = "down" ] || \
        [ "$NOTIFY_STATUS" = "public_nw_down" ] || \
        [ "$NOTIFY_STATUS" = "nodedown " ] ) \
        ) ; then
        # << CALL TROUBLE TICKET LOGGING PROGRAM AND PASS RELEVANT NOTIFY_* ARGUMENTS >>
        echo "Create a service request as " ${NOTIFY_EVENTTYPE} " " ${NOTIFY_STATUS} " occured at " ${NOTIFY_LOGTIME} >> ${FAN_LOGFILE}
    else
        echo "Found no interesting event: " ${NOTIFY_EVENTTYPE} " " ${NOTIFY_STATUS} >> ${FAN_LOGFILE}
    fi

chmod +x callout_elaborate.sh

--
--- Stop the database !!!

export ORACLE_HOME=/u01/app/19.0.0.0/grid
export PATH=$ORACLE_HOME/bin:$PATH
[grid@sduclunode1 usrco]$ srvctl stop database -d $(srvctl config database) -o immediate -force

[grid@sduclunode1 usrco]$ srvctl status database -d $(srvctl config database)
Instance SDURAC1 is not running on node sduclunode1
Instance SDURAC2 is not running on node sduclunode2

-- Review log file on /tmp  on both nodes !!!

[grid@lvracdb-s01-2021-11-18-1718421 ~]$ cat /tmp/lvracdb-s01-2021-11-18-1718421.log
Found no interesting event:  SERVICEMEMBER   down
Found no interesting event:  INSTANCE   down

[grid@lvracdb-s01-2021-11-18-1718422 ~]$ cat /tmp/lvracdb-s01-2021-11-18-1718422.log
Found no interesting event:  SERVICEMEMBER   down
Found no interesting event:  SERVICEMEMBER   down
Found no interesting event:  SERVICEMEMBER   down
Create a service request as  SERVICE   down  occured at  15:29:36
Create a service request as  SERVICE   down  occured at  15:29:36
Create a service request as  SERVICE   down  occured at  15:29:36
Found no interesting event:  SERVICEMEMBER   down
Create a service request as  SERVICE   down  occured at  15:29:36
Found no interesting event:  SERVICEMEMBER   down
Create a service request as  SERVICE   down  occured at  15:29:37
Found no interesting event:  SERVICEMEMBER   down
Create a service request as  SERVICE   down  occured at  15:29:37
Found no interesting event:  INSTANCE   down
Create a service request as  DATABASE   down  occured at  15:30:12

-- Start the database !!!

[grid@lvracdb-s01-2021-11-18-1718421 ~]$ srvctl start database -d $(srvctl config database)


[grid@lvracdb-s01-2021-11-18-1718421 ~]$ cat /tmp/lvracdb-s01-2021-11-18-1718421.log
Found no interesting event:  SERVICEMEMBER   down
Found no interesting event:  INSTANCE   down
Found no interesting event:  INSTANCE   up
Found no interesting event:  DATABASE   up
Found no interesting event:  SERVICE   up
Found no interesting event:  SERVICEMEMBER   up
Found no interesting event:  SERVICE   up
Found no interesting event:  SERVICEMEMBER   up
Found no interesting event:  SERVICE   up
Found no interesting event:  SERVICEMEMBER   up
Found no interesting event:  SERVICE   up
Found no interesting event:  SERVICEMEMBER   up
Found no interesting event:  SERVICEMEMBER   up
Found no interesting event:  SERVICE   up
Found no interesting event:  SERVICEMEMBER   up
[grid@lvracdb-s01-2021-11-18-1718421 ~]$

[grid@lvracdb-s01-2021-11-18-1718422 ~]$ cat /tmp/lvracdb-s01-2021-11-18-1718422.log
Found no interesting event:  SERVICEMEMBER   down
Found no interesting event:  SERVICEMEMBER   down
Found no interesting event:  SERVICEMEMBER   down
Create a service request as  SERVICE   down  occured at  15:29:36
Create a service request as  SERVICE   down  occured at  15:29:36
Create a service request as  SERVICE   down  occured at  15:29:36
Found no interesting event:  SERVICEMEMBER   down
Create a service request as  SERVICE   down  occured at  15:29:36
Found no interesting event:  SERVICEMEMBER   down
Create a service request as  SERVICE   down  occured at  15:29:37
Found no interesting event:  SERVICEMEMBER   down
Create a service request as  SERVICE   down  occured at  15:29:37
Found no interesting event:  INSTANCE   down
Create a service request as  DATABASE   down  occured at  15:30:12
Found no interesting event:  INSTANCE   up
Found no interesting event:  SERVICEMEMBER   up
Found no interesting event:  SERVICE   up

Client-side FAN events
**********************


FAN events are sent to the application mid-tier or client tier using the Oracle Notification Service (ONS). ONS is configured automatically on the cluster when you install Grid Infrastructure. 
CRS manages the stop and start of the ONS daemon.

ONS is configured automatically by FAN-aware Oracle clients, which include Universal Connection Pool (UCP), ODP.Net, Weblogic Server with Active Gridlink, 
CMAN and others, when a particular format connect string is used 
(for more information on this refer to the Application Continuity checklist: https://www.oracle.com//technetwork/database/clustering/checklist-ac-6676160.pdf)

In order to determine if a client has received FAN events may require running your client in a debug fashion. This may be difficult to do and even more difficult to interpret.

To confirm that FAN events are being received at a particular tier, you can install a java utility called FANWatcher, that will subscribe to ONS on a cluster and display events that it receives.

--- We will install FANWatcher on node1 !!!

--- As user oracle:

mkdir -p /home/oracle/fANWatcher
cd /home/oracle/fANWatcher
-- Download FANWatcher with wget !!!

wget https://objectstorage.uk-london-1.oraclecloud.com/p/gKfwKKgzqSfL4A48e6lSKZYqyFdDzvu57md4B1MegMU/n/lrojildid9yx/b/labtest_bucket/o/fanWatcher_19c.zip

--2021-11-22 15:39:19--  https://objectstorage.uk-london-1.oraclecloud.com/p/gKfwKKgzqSfL4A48e6lSKZYqyFdDzvu57md4B1MegMU/n/lrojildid9yx/b/labtest_bucket/o/fanWatcher_19c.zip
Resolving objectstorage.uk-london-1.oraclecloud.com (objectstorage.uk-london-1.oraclecloud.com)... 134.70.64.1, 134.70.56.1, 134.70.60.1
Connecting to objectstorage.uk-london-1.oraclecloud.com (objectstorage.uk-london-1.oraclecloud.com)|134.70.64.1|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: 6116 (6.0K) [application/x-zip-compressed]
Saving to: 'fanWatcher_19c.zip'

100%[================================================================================================>] 6,116       --.-K/s   in 0s

2021-11-22 15:39:19 (82.6 MB/s) - 'fanWatcher_19c.zip' saved [6116/6116]

[oracle@lvracdb-s01-2021-11-18-1718421 fANWatcher]$ ls -ltr
total 8
-rw-r--r-- 1 oracle oinstall 6116 Aug 18  2020 fanWatcher_19c.zip
[oracle@lvracdb-s01-2021-11-18-1718421 fANWatcher]$


-- Unzip fanwatcher !!!

[oracle@lvracdb-s01-2021-11-18-1718421 fANWatcher]$ unzip fanWatcher_19c.zip
Archive:  fanWatcher_19c.zip
  inflating: fanWatcher.bash
  inflating: fanWatcher.class
  inflating: fanWatcher.java

[oracle@lvracdb-s01-2021-11-18-1718421 fANWatcher]$ ls -ltr
total 28
-rw-r--r-- 1 oracle oinstall 6416 Jun 24  2020 fanWatcher.java
-rw-r--r-- 1 oracle oinstall 5733 Jun 24  2020 fanWatcher.class
-rw-r--r-- 1 oracle oinstall 6116 Aug 18  2020 fanWatcher_19c.zip
-rw-r--r-- 1 oracle oinstall  905 Aug 18  2020 fanWatcher.bash
[oracle@lvracdb-s01-2021-11-18-1718421 fANWatcher]$

--- For the database connection, I'll use:

-- User: hr
-- Password: W3lc0m3#W3lc0m3#
-- Database service: noac
-- Connect String: (DESCRIPTION=(CONNECT_TIMEOUT=90)(RETRY_COUNT=50)(RETRY_DELAY=3)(TRANSPORT_CONNECT_TIMEOUT=3)(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(HOST=lvracdb-s01-2021-11-18-171842-scan.pub.racdblab.oraclevcn.com)(PORT=1521)))(CONNECT_DATA=(SERVICE_NAME=noac.pub.racdblab.oraclevcn.com)))

-- Edit fanWatcher.bash and replace the values by your values:

[oracle@lvracdb-s01-2021-11-18-1718421 fANWatcher]$ cat fanWatcher.bash
#!/usr/bin/bash
ORACLE_HOME=/u01/app/oracle/product/19.0.0.0/dbhome_1
JAVA_HOME=${ORACLE_HOME}/jdk
export ORACLE_HOME
export JAVA_HOME
# Set the credentials in the environment. If you don't like doing this,
# hardcode them into the java program
# Edit the values for password, url, user and CLASSPATH
password=W3lc0m3#W3lc0m3#
url='jdbc:oracle:thin:@(DESCRIPTION=(CONNECT_TIMEOUT=90)(RETRY_COUNT=50)(RETRY_DELAY=3)(TRANSPORT_CONNECT_TIMEOUT=3)(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(HOST=lvracdb-s01-2021-11-18-171842-scan.pub.racdblab.oraclevcn.com)(PORT=1521)))(CONNECT_DATA=(SERVICE_NAME=noac.pub.racdblab.oraclevcn.com)))'
user=hr
export password url user
CLASSPATH="/u01/app/oracle/product/19.0.0.0/dbhome_1/jdbc/lib/ojdbc8.jar:/u01/app/oracle/product/19.0.0.0/dbhome_1/opmn/lib/ons.jar:."
export CLASSPATH

# Compile fanWatcher with the exported classpath
#javac fanWatcher.java

# Run fanwatcher with autoons
${JAVA_HOME}/jre/bin/java fanWatcher autoons
# EOF

--- Run the bash script !!!
chmod +x fanWatcher.bash
./fanWatcher.bash

Auto-ONS configuration=maxconnections.0001=0003
nodes.0001=LVRACDB-S01-2021-11-18-171842-SCAN.PUB.RACDBLAB.ORACLEVCN.COM:6200
Opening FAN Subscriber Window ...

--- From another terminal, kill smon process of instance 2 !!!

[oracle@lvracdb-s01-2021-11-18-1718422 ~]$ ps -ef | grep pmon
oracle   11853 11774  0 15:48 pts/0    00:00:00 grep --color=auto pmon
grid     35905     1  0 Nov18 ?        00:00:22 asm_pmon_+ASM2
grid     42411     1  0 Nov18 ?        00:00:22 apx_pmon_+APX2
oracle   97854     1  0 15:34 ?        00:00:00 ora_pmon_lvrac2
[oracle@lvracdb-s01-2021-11-18-1718422 ~]$
[oracle@lvracdb-s01-2021-11-18-1718422 ~]$
[oracle@lvracdb-s01-2021-11-18-1718422 ~]$ kill -9 97854

-- Return to Fan Watcher terminal window and review:

** Event Header **
Notification Type: database/event/service
Delivery Time: Mon Nov 22 15:48:41 UTC 2021
Creation Time: Mon Nov 22 15:48:41 UTC 2021
Generating Node: lvracdb-s01-2021-11-18-1718421
Event payload:
VERSION=1.0 event_type=SERVICEMEMBER service=unisrv.pub.racdblab.oraclevcn.com instance=lvrac2 database=lvrac_fra3md db_domain=pub.racdblab.oraclevcn.com host=lvracdb-s01-2021-11-18-1718422 status=down reason=FAILURE timestamp=2021-11-22 15:48:41 timezone=+00:00

** Event Header **
Notification Type: database/event/service
Delivery Time: Mon Nov 22 15:48:42 UTC 2021
Creation Time: Mon Nov 22 15:48:42 UTC 2021
Generating Node: lvracdb-s01-2021-11-18-1718421
Event payload:
VERSION=1.0 event_type=INSTANCE service=lvrac_fra3md.pub.racdblab.oraclevcn.com instance=lvrac2 database=lvrac_fra3md db_domain=pub.racdblab.oraclevcn.com host=lvracdb-s01-2021-11-18-1718422 status=down reason=FAILURE timestamp=2021-11-22 15:48:42 timezone=+00:00


-- After some seconds CRS restarts instance 2 and its services, and fanWatcher gets notified through ONS:

** Event Header **
Notification Type: database/event/service
Delivery Time: Mon Nov 22 15:49:16 UTC 2021
Creation Time: Mon Nov 22 15:49:16 UTC 2021
Generating Node: lvracdb-s01-2021-11-18-1718421
Event payload:
VERSION=1.0 event_type=INSTANCE service=lvrac_fra3md.pub.racdblab.oraclevcn.com instance=lvrac2 database=lvrac_fra3md db_domain=pub.racdblab.oraclevcn.com host=lvracdb-s01-2021-11-18-1718422 status=up reason=FAILURE timestamp=2021-11-22 15:49:16 timezone=+00:00

** Event Header **
Notification Type: database/event/service
Delivery Time: Mon Nov 22 15:49:18 UTC 2021
Creation Time: Mon Nov 22 15:49:18 UTC 2021
Generating Node: lvracdb-s01-2021-11-18-1718421
Event payload:
VERSION=1.0 event_type=SERVICEMEMBER service=unisrv.pub.racdblab.oraclevcn.com instance=lvrac2 database=lvrac_fra3md db_domain=pub.racdblab.oraclevcn.com host=lvracdb-s01-2021-11-18-1718422 status=up card=2 reason=FAILURE timestamp=2021-11-22 15:49:18 timezone=+00:00


