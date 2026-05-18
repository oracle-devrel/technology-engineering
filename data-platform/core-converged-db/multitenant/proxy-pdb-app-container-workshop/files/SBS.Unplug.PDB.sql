[oracle@awrrepos AWRREPOS_STEF]$ sqlplus / as sysdba

SQL*Plus: Release 21.0.0.0.0 - Production on Tue Aug 17 12:34:36 2021
Version 21.1.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.


Connected to:
Oracle Database 21c EE Extreme Perf Release 21.0.0.0.0 - Production
Version 21.1.0.0.0

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 PDBAWR			  READ WRITE NO

--- Before unplugging, need to export the PDB encryption keys !!!

SQL> alter session set container=PDBAWR;

Session altered.

SQL> ADMINISTER KEY MANAGEMENT EXPORT KEYS WITH SECRET "YOURSECRET" TO '/tmp/pdbawr.p12' FORCE KEYSTORE IDENTIFIED BY "YOURPASSWORD" ;

keystore altered.

SQL>
SQL>
SQL> exit
Disconnected from Oracle Database 21c EE Extreme Perf Release 21.0.0.0.0 - Production
Version 21.1.0.0.0
[oracle@awrrepos AWRREPOS_STEF]$ sqlplus / as sysdba

SQL*Plus: Release 21.0.0.0.0 - Production on Tue Aug 17 12:35:08 2021
Version 21.1.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.


Connected to:
Oracle Database 21c EE Extreme Perf Release 21.0.0.0.0 - Production
Version 21.1.0.0.0

SQL> alter pluggable database PDBAWR close immediate;

Pluggable database altered.

SQL> alter pluggable database PDBAWR unplug into '/tmp/PDBAWR.xml';

Pluggable database altered.

--- => In that case, PDBAWR.xml contains the METADATA, specially the path to the original datafiles !!!

-- Now I can recreate the PDB, through a plug command !!!

SQL> drop pluggable database PDBAWR keep datafiles;

Pluggable database dropped.

SQL>

--- After re-creating the PDB from the XML file, I unplug it again with data !!!
--- First I need to export the encryption keys !!!

alter session set container = PDBAWR;
ADMINISTER KEY MANAGEMENT EXPORT KEYS WITH SECRET "YOURSECRET" TO '/tmp/pdbawr2.p12' FORCE KEYSTORE IDENTIFIED BY "YOURPASSWORD" ;

keystore altered.



SQL> alter pluggable database PDBAWR unplug into '/tmp/PDBAWR2.pdb';

Pluggable database altered.


-rw-r--r-- 1 oracle asmadmin     10393 Aug 17 12:36 PDBAWR.xml     <========== with metadata only !!!
drwxr-xr-x 2 root   root          4096 Aug 17 12:45 hsperfdata_root
drwxr-xr-x 2 oracle oinstall      4096 Aug 17 12:50 hsperfdata_oracle
-rw-r--r-- 1 oracle asmadmin      2676 Aug 17 12:59 pdbawr2.p12
-rw-r--r-- 1 oracle asmadmin 701947082 Aug 17 13:03 PDBAWR2.pdb    <========== with metadata+data, could be a huge file !!!


--- Now I can create a new PDB from the file !!!

SQL> create pluggable database PDBAWR2 as clone using '/tmp/PDBAWR2.pdb';

Pluggable database created.

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 PDBAWR2			  MOUNTED
SQL> alter pluggable database PDBAWR2 open;

Warning: PDB altered with errors.

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 PDBAWR2			  READ WRITE YES
SQL> alter session set container=PDBAWR2;

Session altered.


SQL> ADMINISTER KEY MANAGEMENT import keys WITH SECRET "YOURSECRET" from '/tmp/pdbawr2.p12' FORCE KEYSTORE IDENTIFIED BY "YOURPASSWORD" with backup;

keystore altered.

SQL>

SQL> exit
Disconnected from Oracle Database 21c EE Extreme Perf Release 21.0.0.0.0 - Production
Version 21.1.0.0.0
[oracle@awrrepos tmp]$ sqlplus / as sysdba

SQL*Plus: Release 21.0.0.0.0 - Production on Tue Aug 17 13:16:19 2021
Version 21.1.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.


Connected to:
Oracle Database 21c EE Extreme Perf Release 21.0.0.0.0 - Production
Version 21.1.0.0.0

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 PDBAWR2			  READ WRITE YES
SQL> alter pluggable database PDBAWR2 close immediate;

Pluggable database altered.

SQL> alter pluggable database PDBAWR2 open;

Pluggable database altered.

SQL> show pdbs

    CON_ID CON_NAME			  OPEN MODE  RESTRICTED
---------- ------------------------------ ---------- ----------
	 2 PDB$SEED			  READ ONLY  NO
	 3 PDBAWR2			  READ WRITE NO
SQL>


-- Check the user data is there !!!

[oracle@awrrepos tmp]$ sqlplus user1/passwd#@awrrepos.skynet.oraclevcn.com:1521/pdbawr2.skynet.oraclevcn.com

SQL*Plus: Release 21.0.0.0.0 - Production on Tue Aug 17 13:17:28 2021
Version 21.1.0.0.0

Copyright (c) 1982, 2020, Oracle.  All rights reserved.

Last Successful login time: Tue Aug 17 2021 12:09:20 +00:00

Connected to:
Oracle Database 21c EE Extreme Perf Release 21.0.0.0.0 - Production
Version 21.1.0.0.0

SQL> select * from test;

	C1
----------
	 0

SQL>