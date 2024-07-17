-- Live Lab: https://apexapps.oracle.com/pls/apex/dbpm/r/livelabs/workshop-attendee-2?p210_workshop_id=835&p210_type=3&session=4182485884819

-- Machines:
-- Shard catalog: <public_ip>	(<private_ip>):  ssh -i /Users/stef/Documents/TSE/Workshops/003.Continuous.Availability/SSH/id_rsa_lab opc@<public_ip>
-- Shard 1: <public_ip> (<private_ip>)      :   ssh -i /Users/stef/Documents/TSE/Workshops/003.Continuous.Availability/SSH/id_rsa_lab opc@<public_ip>
-- Shard 2: <public_ip> (<private_ip>)      :  ssh -i /Users/stef/Documents/TSE/Workshops/003.Continuous.Availability/SSH/id_rsa_lab opc@<public_ip>
-- Shard 3: <public_ip> (<private_ip>)      :   ssh -i /Users/stef/Documents/TSE/Workshops/003.Continuous.Availability/SSH/id_rsa_lab opc@<public_ip>

Objectives

In this workshop, you will

    Deploy a shard database with two shards using system managed sharding.
    Migrate application to the shard database
    Working with the shard database.
    Extent the shard database with the third shard.


A. Check the environment:
*************************

Connect to the 4 machines, and check that the database is up and running on each one of them:

-- Shard catalog:
ssh -i /Users/stef/Documents/TSE/Workshops/003.Continuous.Availability/SSH/id_rsa_lab opc@130.61.44.229

[opc@cata ~]$ sudo -i
[root@cata ~]# su - oracle
Last login: Wed Jun 29 10:34:17 GMT 2022
[oracle@cata ~]$ sqlplus / as sysdba

SQL*Plus: Release 19.0.0.0.0 - Production on Thu Jun 30 07:51:02 2022
Version 19.11.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.


Connected to:
Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
Version 19.11.0.0.0

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 CATAPDB			  READ WRITE NO
SQL>
SQL> exit

lsnrctl status LISTENER

-- Shard 1:

ssh -i /Users/stef/Documents/TSE/Workshops/003.Continuous.Availability/SSH/id_rsa_lab opc@130.61.118.80

[opc@shd1 ~]$ sudo -i
[root@shd1 ~]# su - oracle
Last login: Wed Jun 29 10:37:39 GMT 2022
[oracle@shd1 ~]$ sqlplus / as sysdba

SQL*Plus: Release 19.0.0.0.0 - Production on Thu Jun 30 08:00:34 2022
Version 19.11.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.


Connected to:
Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
Version 19.11.0.0.0

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 SHDPDB1			  READ WRITE NO
SQL>

exit

lsnrctl status LISTENER

ICI
-- Shard 2:
ssh -i /Users/stef/Documents/Preventa/TMP/sshkeybundle/privateKey opc@130.61.102.103

[opc@shd2 ~]$ sudo -i
[root@shd2 ~]# su - oracle
Last login: Mon Nov  8 17:48:29 GMT 2021
[oracle@shd2 ~]$ sqlplus / as sysdba

SQL*Plus: Release 19.0.0.0.0 - Production on Tue Nov 9 11:38:01 2021
Version 19.11.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.


Connected to:
Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
Version 19.11.0.0.0

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 SHDPDB2			  READ WRITE NO

exit

lsnrctl status LISTENER

-- Shard 3:
ssh -i /Users/stef/Documents/Preventa/TMP/sshkeybundle/privateKey opc@130.61.112.37

[opc@shd3 ~]$ sudo -i
[root@shd3 ~]# su - oracle
Last login: Mon Nov  8 17:50:18 GMT 2021
[oracle@shd3 ~]$ sqlplus / as sysdba

SQL*Plus: Release 19.0.0.0.0 - Production on Tue Nov 9 11:38:51 2021
Version 19.11.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.


Connected to:
Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
Version 19.11.0.0.0

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 SHDPDB3			  READ WRITE NO
exit

lsnrctl status LISTENER


