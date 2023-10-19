Install Sample Program and configure services

-- Connect to node1 as "oracle", and install a sample application:

cd /home/oracle
wget https://objectstorage.us-ashburn-1.oraclecloud.com/p/O8AOujhwl1dSTqhfH69f3nkV6TNZWU3KaIF4TZ-XuCaZ5w-xHEQ14ViOVhUXQjPB/n/oradbclouducm/b/LiveLabTemp/o/ACDemo_19c.zip

[oracle@lvracdb-s01-2021-11-18-1718421 ~]$ wget https://objectstorage.us-ashburn-1.oraclecloud.com/p/O8AOujhwl1dSTqhfH69f3nkV6TNZWU3KaIF4TZ-XuCaZ5w-xHEQ14ViOVhUXQjPB/n/oradbclouducm/b/LiveLabTemp/o/ACDemo_19c.zip
--2021-11-19 10:32:10--  https://objectstorage.us-ashburn-1.oraclecloud.com/p/O8AOujhwl1dSTqhfH69f3nkV6TNZWU3KaIF4TZ-XuCaZ5w-xHEQ14ViOVhUXQjPB/n/oradbclouducm/b/LiveLabTemp/o/ACDemo_19c.zip
Resolving objectstorage.us-ashburn-1.oraclecloud.com (objectstorage.us-ashburn-1.oraclecloud.com)... 134.70.32.1, 134.70.24.1, 134.70.28.1
Connecting to objectstorage.us-ashburn-1.oraclecloud.com (objectstorage.us-ashburn-1.oraclecloud.com)|134.70.32.1|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: 8573765 (8.2M) [application/x-zip-compressed]
Saving to: 'ACDemo_19c.zip'

100%[==================================================================================================>] 8,573,765   12.2MB/s   in 0.7s

2021-11-19 10:32:11 (12.2 MB/s) - 'ACDemo_19c.zip' saved [8573765/8573765]


Unzip the ACDemo_19c.zip file

cd /home/oracle
unzip ACDemo_19c.zip

[oracle@lvracdb-s01-2021-11-18-1718421 ~]$ ls -ltr
total 8392
-rw-r--r-- 1 oracle oinstall    2717 Mar 16  2021 README.txt
drwxr-xr-x 6 oracle oinstall    4096 Sep  8 13:42 acdemo
-rw-r--r-- 1 oracle oinstall    7990 Sep  9 13:46 SETUP_AC_TEST.sh
-rw-r--r-- 1 oracle oinstall 8573765 Sep 10 04:21 ACDemo_19c.zip
[oracle@lvracdb-s01-2021-11-18-1718421 ~]$

Set the execute bit +x on the SETUP_AC_TEST.sh script

chmod +x SETUP_AC_TEST.sh

Run the script SETUP_AC_TEST.sh. You will be prompted for INPUTS. If a default value is shown, press ENTER to accept

./SETUP_AC_TEST.sh

Make the run scripts executable

cd /home/oracle/acdemo
chmod +x run*
chmod +x kill_session.sh

Examine Service Attributes and Program Settings

Identify your service names:

srvctl status service -d `srvctl config database`

[oracle@lvracdb-s01-2021-11-18-1718421 acdemo]$ srvctl status service -d `srvctl config database`
Service ac_service is running on instance(s) lvrac1
Service noac is running on instance(s) lvrac1
Service svc_ac is running on instance(s) lvrac1
Service svctest is running on instance(s) lvrac1
Service tac_service is running on instance(s) lvrac1
Service unisrv is running on instance(s) lvrac1,lvrac2

srvctl config service -d  `srvctl config database` -s noac

[oracle@lvracdb-s01-2021-11-18-1718421 acdemo]$ srvctl config service -d  `srvctl config database` -s noac
Service name: noac
Server pool:
Cardinality: 1
Service role: PRIMARY
Management policy: AUTOMATIC
DTP transaction: false
AQ HA notifications: false
Global: false
Commit Outcome: false
Failover type: NONE
Failover method:
Failover retries:
Failover delay:
Failover restore: NONE
Connection Load Balancing Goal: LONG
Runtime Load Balancing Goal: NONE
TAF policy specification: NONE
Edition:
Pluggable database name: pdb1
Hub service:
Maximum lag time: ANY
SQL Translation Profile:
Retention: 86400 seconds
Replay Initiation Time: 300 seconds
Drain timeout:
Stop option:
Session State Consistency: DYNAMIC
GSM Flags: 0
Service is enabled
Preferred instances: lvrac1
Available instances: lvrac2
CSS critical: no
Service uses Java: false

srvctl config service -d $(srvctl config database) -s tac_service

[oracle@lvracdb-s01-2021-11-18-1718421 acdemo]$ srvctl config service -d $(srvctl config database) -s tac_service
Service name: tac_service
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
Failover delay: 10
Failover restore: AUTO
Connection Load Balancing Goal: LONG
Runtime Load Balancing Goal: NONE
TAF policy specification: NONE
Edition:
Pluggable database name: pdb1
Hub service:
Maximum lag time: ANY
SQL Translation Profile:
Retention: 86400 seconds
Replay Initiation Time: 300 seconds
Drain timeout:
Stop option:
Session State Consistency: AUTO
GSM Flags: 0
Service is enabled
Preferred instances: lvrac1
Available instances: lvrac2
CSS critical: no
Service uses Java: false

To enable TAC commit_outcome is TRUE, failovertype is set to AUTO, and failover_restore is AUTO
Note: The attributes failoverretry and failoverdelay are not required when RETRY_COUNT and RETRY_DELAY are set in the connect string\/URL as recommended

STEP3: run the app in NOREPLAY mode
***********************************

[oracle@lvracdb-s01-2021-11-18-1718421 acdemo]$ cat ac_noreplay.properties
#Stub file to build ac_noreplay.properties
# Use vanilla datasource
datasource=oracle.jdbc.pool.OracleDataSource

# Set verbose mode
VERBOSE=FALSE

# database JDBC URL
url=jdbc:oracle:thin:@(DESCRIPTION=(CONNECT_TIMEOUT=90)(RETRY_COUNT=50)(RETRY_DELAY=3)(TRANSPORT_CONNECT_TIMEOUT=3)(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(HOST=lvracdb-s01-2021-11-18-171842-scan.pub.racdblab.oraclevcn.com)(PORT=1521)))(CONNECT_DATA=(SERVICE_NAME=noac.pub.racdblab.oraclevcn.com)))

# database username and password
username=hr
password=<passwd>

# Disable FAN
fastConnectionFailover=FALSE

#Disable connection tests
validateConnectionOnBorrow=FALSE

# number of connections in the UCP''s pool
ucp_pool_size=20

#Connection Wait Timeout for busy pool
connectionWaitTimeout=5

# number of active threads (this simulates concurrent load)
number_of_threads=10

# think time is how much time the threads will sleep before looping
thread_think_time=50
~

STEP 4: run the app with no Replay
**********************************


cd /home/oracle/acdemo

[oracle@lvracdb-s01-2021-11-18-1718421 acdemo]$ ./runnoreplay
######################################################
Connecting to jdbc:oracle:thin:@(DESCRIPTION=(CONNECT_TIMEOUT=90)(RETRY_COUNT=50)(RETRY_DELAY=3)(TRANSPORT_CONNECT_TIMEOUT=3)(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(HOST=lvracdb-s01-2021-11-18-171842-scan.pub.racdblab.oraclevcn.com)(PORT=1521)))(CONNECT_DATA=(SERVICE_NAME=noac.pub.racdblab.oraclevcn.com)))
 # of Threads             : 10
 UCP pool size            : 20
FCF Enabled:  false
VCoB Enabled: false
ONS Configuration:  null
Enable Intensive Wload:  false
Thread think time        : 50 ms
######################################################

Starting the pool now... (please wait)
Pool is started in 7438ms
2 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 682, avg response time from db 12ms
0 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 1518, avg response time from db 7ms
2 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 2340, avg response time from db 8ms


--- Kill SMON of the instance where noac service is currently running:
stef@stef-mac sshkeybundle % ssh -i /Users/stef/Documents/Preventa/TMP/sshkeybundle/privateKey opc@152.70.180.236
Last login: Fri Nov 19 10:00:57 2021 from 92.56.97.244
[opc@lvracdb-s01-2021-11-18-1718421 ~]$
[opc@lvracdb-s01-2021-11-18-1718421 ~]$
[opc@lvracdb-s01-2021-11-18-1718421 ~]$ sudo su - oracle
Last login: Fri Nov 19 10:57:30 UTC 2021
[oracle@lvracdb-s01-2021-11-18-1718421 ~]$
[oracle@lvracdb-s01-2021-11-18-1718421 ~]$
[oracle@lvracdb-s01-2021-11-18-1718421 ~]$ ps -ef | grep smon
root     35442     1  1 Nov18 ?        00:17:40 /u01/app/19.0.0.0/grid/bin/osysmond.bin
grid     36088     1  0 Nov18 ?        00:00:01 asm_smon_+ASM1
oracle   39453 39393  0 10:58 pts/1    00:00:00 grep --color=auto smon
oracle   94293     1  0 10:18 ?        00:00:00 ora_smon_lvrac1
[oracle@lvracdb-s01-2021-11-18-1718421 ~]$ kill -9 94293
[oracle@lvracdb-s01-2021-11-18-1718421 ~]$

java.sql.SQLRecoverableException: No more data to read from socket
	at oracle.jdbc.driver.T4CMAREngineNIO.prepareForUnmarshall(T4CMAREngineNIO.java:811)
	at oracle.jdbc.driver.T4CMAREngineNIO.unmarshalUB1(T4CMAREngineNIO.java:449)
	at oracle.jdbc.driver.T4CTTIfun.receive(T4CTTIfun.java:410)
	at oracle.jdbc.driver.T4CTTIfun.doRPC(T4CTTIfun.java:269)
	at oracle.jdbc.driver.T4C8Oall.doOALL(T4C8Oall.java:655)
	at oracle.jdbc.driver.T4CPreparedStatement.doOall8(T4CPreparedStatement.java:270)
	at oracle.jdbc.driver.T4CPreparedStatement.doOall8(T4CPreparedStatement.java:91)
	at oracle.jdbc.driver.T4CPreparedStatement.executeForDescribe(T4CPreparedStatement.java:807)
	at oracle.jdbc.driver.OracleStatement.executeMaybeDescribe(OracleStatement.java:983)
	at oracle.jdbc.driver.OracleStatement.doExecuteWithTimeout(OracleStatement.java:1168)
	at oracle.jdbc.driver.OraclePreparedStatement.executeInternal(OraclePreparedStatement.java:3666)
	at oracle.jdbc.driver.T4CPreparedStatement.executeInternal(T4CPreparedStatement.java:1426)
	at oracle.jdbc.driver.OraclePreparedStatement.executeQuery(OraclePreparedStatement.java:3713)
	at oracle.jdbc.driver.OraclePreparedStatementWrapper.executeQuery(OraclePreparedStatementWrapper.java:1167)
	at oracle.ucp.jdbc.proxy.oracle$1ucp$1jdbc$1proxy$1oracle$1StatementProxy$2oracle$1jdbc$1internal$1OraclePreparedStatement$$$Proxy.executeQuery(Unknown Source)
	at acdemo.Worker.databaseWorkload(Worker.java:56)
	at acdemo.Worker.run(Worker.java:137)
	at java.lang.Thread.run(Thread.java:748)
Application error handling: attempting to get a new connection No more data to read from socket.
FCF information:
0 borrowed, 10 pending, 0ms getConnection wait, TotalBorrowed 5211, avg response time from db 14ms
 Application driven connection retry succeeded
 Application driven connection retry succeeded
 Application driven connection retry succeeded
 Application driven connection retry succeeded
 Application driven connection retry succeeded
 Application driven connection retry succeeded
 Application driven connection retry succeeded
 Application driven connection retry succeeded
 Application driven connection retry succeeded
 Application driven connection retry succeeded
1 borrowed, 0 pending, 11ms getConnection wait, TotalBorrowed 5355, avg response time from db 84ms
0 borrowed, 0 pending, 10ms getConnection wait, TotalBorrowed 5806, avg response time from db 57ms


=> After a few seconds, application is reconnected to node 2

Application Continuity
**********************

Examine the ac_replay.properties file to see that we are using a replay datasource oracle.jdbc.replay.OracleDataSourceImpl and we have enabled FAN, 
fastConnectionFailover=TRUE and connection tests validateConnectionOnBorrow=TRUE. 
The URL uses the recommended format and connects to the service you created previously, which has AC attributes set.

cd /home/oracle/acdemo

cat ac_replay.properties

[oracle@lvracdb-s01-2021-11-18-1718421 acdemo]$ cat ac_replay.properties
# Stub file to create ac_replay.properties
# Use replay datasource
datasource=oracle.jdbc.replay.OracleDataSourceImpl

# Set verbose mode
VERBOSE=FALSE

# database JDBC URL
url=jdbc:oracle:thin:@(DESCRIPTION=(CONNECT_TIMEOUT=90)(RETRY_COUNT=50)(RETRY_DELAY=3)(TRANSPORT_CONNECT_TIMEOUT=3)(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(HOST=lvracdb-s01-2021-11-18-171842-scan.pub.racdblab.oraclevcn.com)(PORT=1521)))(CONNECT_DATA=(SERVICE_NAME=ac_service.pub.racdblab.oraclevcn.com)))

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

[oracle@lvracdb-s01-2021-11-18-1718421 acdemo]$ srvctl status service -d $(srvctl config database) -s ac_service
Service ac_service is running on instance(s) lvrac2

[oracle@lvracdb-s01-2021-11-18-1718421 acdemo]$ srvctl relocate service -d $(srvctl config database) -s ac_service -oldinst lvrac2 -newinst lvrac1
[oracle@lvracdb-s01-2021-11-18-1718421 acdemo]$ srvctl status service -d $(srvctl config database) -s ac_service
Service ac_service is running on instance(s) lvrac1
[oracle@lvracdb-s01-2021-11-18-1718421 acdemo]$

-- Start app in replay mode:
cd /home/oracle/acdemo
./runreplay

######################################################
Connecting to jdbc:oracle:thin:@(DESCRIPTION=(CONNECT_TIMEOUT=90)(RETRY_COUNT=50)(RETRY_DELAY=3)(TRANSPORT_CONNECT_TIMEOUT=3)(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(HOST=lvracdb-s01-2021-11-18-171842-scan.pub.racdblab.oraclevcn.com)(PORT=1521)))(CONNECT_DATA=(SERVICE_NAME=ac_service.pub.racdblab.oraclevcn.com)))
 # of Threads             : 10
 UCP pool size            : 20
FCF Enabled:  true
VCoB Enabled: true
ONS Configuration:  null
Enable Intensive Wload:  false
Thread think time        : 50 ms
######################################################

Starting the pool now... (please wait)
Pool is started in 6286ms
4 borrowed, 0 pending, 1ms getConnection wait, TotalBorrowed 507, avg response time from db 26ms
5 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 1186, avg response time from db 19ms

-- Kill smon on instance 1:

[oracle@lvracdb-s01-2021-11-18-1718421 ~]$ ps -ef | grep smon
root     35442     1  1 Nov18 ?        01:29:41 /u01/app/19.0.0.0/grid/bin/osysmond.bin
grid     36088     1  0 Nov18 ?        00:00:06 asm_smon_+ASM1
oracle   64589     1  0 08:57 ?        00:00:00 ora_smon_lvrac1
oracle   73308 62438  0 09:03 pts/1    00:00:00 grep --color=auto smon
[oracle@lvracdb-s01-2021-11-18-1718421 ~]$
[oracle@lvracdb-s01-2021-11-18-1718421 ~]$
[oracle@lvracdb-s01-2021-11-18-1718421 ~]$ kill -9 64589

8 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 1926, avg response time from db 13ms
1 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 2627, avg response time from db 17ms
2 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 3297, avg response time from db 20ms
1 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 4003, avg response time from db 17ms
0 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 4721, avg response time from db 15ms
4 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 5339, avg response time from db 26ms
4 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 6055, avg response time from db 16ms
10 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 6491, avg response time from db 13ms
10 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 6551, avg response time from db 1072ms   <=    avg response time briefly increases, but no error !!!
1 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 7091, avg response time from db 44ms
2 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 7827, avg response time from db 14ms
4 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 8589, avg response time from db 12ms

No errors occur. Application Continuity traps the error(s), re-establishes connections at a surviving instance, and replays any uncommitted transactions. 
We do not progress in to any of the application''s error handling routines

Transparent Application Continuity
**********************************

Examine the tac_replay.properties file to see that we are using a replay datasource oracle.jdbc.replay.OracleDataSourceImpl 
and we have enabled FAN, fastConnectionFailover=TRUE and connection tests validateConnectionOnBorrow=TRUE. 
The URL uses the recommended format and connects to the service you created previously, which has AC attributes set.

[oracle@lvracdb-s01-2021-11-18-1718421 acdemo]$ cat tac_replay.properties
# Stub file to create tac_replay.properties
# Use replay datasource
datasource=oracle.jdbc.replay.OracleDataSourceImpl

# Set verbose mode
VERBOSE=FALSE

# database JDBC URL
url=jdbc:oracle:thin:@(DESCRIPTION=(CONNECT_TIMEOUT=90)(RETRY_COUNT=50)(RETRY_DELAY=3)(TRANSPORT_CONNECT_TIMEOUT=3)(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(HOST=lvracdb-s01-2021-11-18-171842-scan.pub.racdblab.oraclevcn.com)(PORT=1521)))(CONNECT_DATA=(SERVICE_NAME=tac_service.pub.racdblab.oraclevcn.com)))

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

[oracle@lvracdb-s01-2021-11-18-1718421 acdemo]$ srvctl status service -d $(srvctl config database) -s tac_service
Service tac_service is running on instance(s) lvrac2
[oracle@lvracdb-s01-2021-11-18-1718421 acdemo]$ srvctl relocate service -d $(srvctl config database) -s tac_service -oldinst lvrac2 -newinst lvrac1
[oracle@lvracdb-s01-2021-11-18-1718421 acdemo]$ srvctl status service -d $(srvctl config database) -s tac_service
Service tac_service is running on instance(s) lvrac1
[oracle@lvracdb-s01-2021-11-18-1718421 acdemo]$

cd /home/oracle/acdemo
./runtacreplay

[oracle@lvracdb-s01-2021-11-18-1718421 acdemo]$ ./runtacreplay
######################################################
Connecting to jdbc:oracle:thin:@(DESCRIPTION=(CONNECT_TIMEOUT=90)(RETRY_COUNT=50)(RETRY_DELAY=3)(TRANSPORT_CONNECT_TIMEOUT=3)(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(HOST=lvracdb-s01-2021-11-18-171842-scan.pub.racdblab.oraclevcn.com)(PORT=1521)))(CONNECT_DATA=(SERVICE_NAME=tac_service.pub.racdblab.oraclevcn.com)))
 # of Threads             : 10
 UCP pool size            : 20
FCF Enabled:  true
VCoB Enabled: true
ONS Configuration:  null
Enable Intensive Wload:  false
Thread think time        : 50 ms
######################################################

Starting the pool now... (please wait)
Pool is started in 4744ms
1 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 619, avg response time from db 17ms
2 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 1417, avg response time from db 9ms
1 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 2234, avg response time from db 7ms
5 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 3040, avg response time from db 8ms

[oracle@lvracdb-s01-2021-11-18-1718421 ~]$ ps -ef | grep smon
oracle    9036  7516  0 09:32 pts/1    00:00:00 grep --color=auto smon
root     35442     1  1 Nov18 ?        01:30:15 /u01/app/19.0.0.0/grid/bin/osysmond.bin
grid     36088     1  0 Nov18 ?        00:00:06 asm_smon_+ASM1
oracle   75842     1  0 09:04 ?        00:00:00 ora_smon_lvrac1
[oracle@lvracdb-s01-2021-11-18-1718421 ~]$ kill -9 75842

1 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 4642, avg response time from db 8ms
5 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 5462, avg response time from db 8ms
1 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 6283, avg response time from db 7ms
3 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 7097, avg response time from db 8ms
1 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 7922, avg response time from db 7ms
1 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 8741, avg response time from db 7ms
10 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 8877, avg response time from db 6ms
2 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 9444, avg response time from db 107ms   <=== Slight RT increment !!!
0 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 10267, avg response time from db 7ms
1 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 11094, avg response time from db 7ms
1 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 11917, avg response time from db 7ms
1 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 12742, avg response time from db 7ms
0 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 13588, avg response time from db 6ms
0 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 14430, avg response time from db 6ms
2 borrowed, 0 pending, 0ms getConnection wait, TotalBorrowed 15268, avg response time from db 6ms

TAC will protect applications that do, or do not use a connection pool

[oracle@lvracdb-s01-2021-11-18-1718421 ~]$ srvctl status service -d $(srvctl config database) -s tac_service
Service tac_service is running on instance(s) lvrac1

Connect to the database with SQL*Plus as the HR user over the TAC-enabled service

sqlplus hr/<passwd>@"(DESCRIPTION=(CONNECT_TIMEOUT=90)(RETRY_COUNT=50)(RETRY_DELAY=3)(TRANSPORT_CONNECT_TIMEOUT=3)(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(HOST=lvracdb-s01-2021-11-18-171842-scan.pub.racdblab.oraclevcn.com)(PORT=1521)))(CONNECT_DATA=(SERVICE_NAME=tac_service.pub.racdblab.oraclevcn.com)))"

Update a row in the table EMP4AC. For example:

select empno, ename  from emp4ac where rownum < 10;

     EMPNO ENAME
---------- ----------
      5814 Bob5814
      2271 Bob2271
      3538 Bob3538
      3033 Bob3033
      7151 Bob7151
      8948 Bob8948
      5642 Bob5642
     -9208 Bob-9208
     -7790 Bob-7790

9 rows selected.

update emp4ac set empno=9999 where empno=5642 and ename='Bob5642' and rownum < 10;

SQL> update emp4ac set empno=9999 where empno=5642 and ename='Bob5642' and rownum < 10;

1 row updated.


From another terminal window run the kill_session.sh script against the TAC-enabled service

cd /home/oracle/acdemo
./kill_session.sh tac_service.pub.racdblab.oraclevcn.com

SQL*Plus: Release 19.0.0.0.0 - Production on Mon Nov 22 11:48:42 2021
Version 19.12.0.0.0

Copyright (c) 1982, 2021, Oracle.  All rights reserved.

Last Successful login time: Fri Nov 19 2021 12:08:57 +00:00

Connected to:
Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.12.0.0.0

SQL> SQL>
'ALTERSYSTEMKILLSESSION'''||SID||','||SERIAL#||'''IMMEDIATE;'
--------------------------------------------------------------------------------
ALTER SYSTEM KILL SESSION '346,24628' IMMEDIATE;

SQL> SQL> Disconnected from Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.12.0.0.0

SQL*Plus: Release 19.0.0.0.0 - Production on Mon Nov 22 11:48:43 2021
Version 19.12.0.0.0

Copyright (c) 1982, 2021, Oracle.  All rights reserved.

Last Successful login time: Mon Nov 22 2021 11:48:43 +00:00

Connected to:
Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.12.0.0.0

SQL>
System altered.

SQL> Disconnected from Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.12.0.0.0
[oracle@lvracdb-s01-2021-11-18-1718421 acdemo]$

Go back to the sql*plus command line and commit your transaction:

SQL> commit;

Commit complete.

SQL>

=> TAC protected your Sql*Plus session !!!

