# Introduction

Cyber security has become an increasingly critical topic as malware and ransomware attacks continue to occur around the world. For mission-critical databases, such attacks leading to lost data and system downtime can have far-ranging impacts throughout the business in terms of revenue, operations, reputation, and even penalties.

The purpose of Oracle Cloud Database Backup Service is to provide a secure, reliable, and cost-effective way to backup and recover Oracle Database workloads that are running in the cloud or on-premises. With this service, you can create backups of your databases and store them in Oracle Cloud Infrastructure Object Storage, which provides highly durable and scalable object storage.
The service offers several benefits, including automated backups, point-in-time recovery, and backup retention policies. It enables you to quickly recover your data in case of data loss or corruption, and can also be used to migrate your databases to the cloud. Additionally, the service helps you meet your regulatory and compliance requirements by providing data encryption and secure backups.

Owner: Bhaskar Ivaturi

## Deployment:

Download and install the Oracle Cloud Backup Module on the database server(s) where your Oracle Database resides. The installation process typically involves running the provided installation scripts and configuring the necessary parameters.

-	Download the Oracle Database Cloud Backup Module for OCI from Oracle Technology Network (OTN).
- Accept the license agreement, click All Supported Platforms, and provide your OTN username and password when prompted. Then download the ZIP file that contains the installer (opc_installer.zip) to your system.
-	Extract the contents of the zip file.
-	The file contains two directories, oci_installer (for Oracle Cloud Infrastructure) and opc_installer (for Oracle Cloud Infrastructure Classic), and a README file.
-	To use Oracle Database Backup Cloud Service for Oracle database backups, you'll need to install the appropriate backup module needed for cloud backups.
-	Run the installer, oci_install.jar, from the oci_installer directory. Provide the required parameters in one line, with each parameter preceded by a hyphen and followed by its value.

The following is an example run of the installer. This example shows how the installer automatically downloads the Oracle Database Cloud Backup Module for OCI for your operating system, creates a wallet that contains Oracle Database Backup Cloud Service identifiers and credentials, creates the backup module configuration file, and downloads the library necessary for backups and restores to Oracle Cloud Infrastructure.

    %java -jar oci_install.jar -host https://objectstorage.<region>.oraclecloud.com
    -pvtKeyFile /oracle/dbs/oci_wallet/oci_pvt
    -pubFingerPrint xx:10:06:b1:fb:24:xx:xx:46:21:16:20:00:xx:xx:00
    -uOCID ocid1.user.oc1..aaaaaaaasd11111111111111111111117z7aibxxxxxxxxxxxxxxxxxxx
    -tOCID ocid1.tenancy.oc1..aaaaaaaav11111111111111111111rft58i6ts3xxxxxxxxxxxxxxxxxx
    -walletDir /oracle/dbs/oci_wallet
    -libDir /oracle/lib
    -bucket db_backups


After installing the backup module, you'll configure the settings that will be used for backup and recovery operations. When using Recovery Manager (RMAN) for backup and recovery operations with Oracle Database Backup Cloud Service, you must configure your RMAN environment.

    RMAN> CONFIGURE DEFAULT DEVICE TYPE TO 'SBT_TAPE';
    RMAN> CONFIGURE CHANNEL DEVICE TYPE sbt PARMS='SBT_LIBRARY=location-of-the-SBT-library-for-the-backup-module, SBT_PARMS=(OPC_PFILE=location-of-the-configuration file)’;
    RMAN> CONFIGURE COMPRESSION ALGORITHM 'MEDIUM’;
    RMAN> CONFIGURE DEVICE TYPE 'SBT_TAPE' PARALLELISM 4 BACKUP TYPE TO COMPRESSED BACKUPSET;
    RMAN> CONFIGURE ENCRYPTION FOR DATABASE ON;


### Backup Destination:

Create an Oracle Cloud Infrastructure Object Storage bucket to serve as the backup destination. This bucket will store the backup files securely in the Oracle Cloud.

##### Backup Schedule and Policies:

Define backup schedules and retention policies based on your requirements. You can specify the frequency and timing of backups, as well as how long to retain them. Oracle Cloud Backup Module(OCBM) supports full and incremental backups to optimize storage consumption and backup duration.

##### Backup and Recovery Operations:

Initiate backups using OCBM commands or integrated RMAN (Recovery Manager) commands. OCBM seamlessly integrates with RMAN, providing familiar commands and workflows.
Monitor the progress and status of backup operations to ensure successful completion.

Perform restore and recovery operations as needed. OCBM allows you to restore the database to a specific point in time using backups stored in OCI Object Storage. Use the RMAN shell scripts for the seamless restore operations.

##### Use Case 1: Implement a cyber recovery solution on Oracle Cloud Infrastructure
###### RMAN Scripts for backup and restore
###### Sample Backup script:

    #!/bin/bash
    #
    W_SID=$1
    VDATE=`date +%d'-'%m'-'%Y`
    . /home/oracle/${W_SID}.env
    $ORACLE_HOME/bin/rman target / <<EOF
    SET ENCRYPTION ON;
    RUN {
    ALLOCATE CHANNEL SBT_1 DEVICE TYPE SBT parms='SBT_LIBRARY=/xxx/xxxxx/xxxx/libopc.so, ENV=(OPC_PFILE=/xxx/xxxxx/xxxx//opcCRS.ora)' ;
    ALLOCATE CHANNEL SBT_2 DEVICE TYPE SBT parms='SBT_LIBRARY=/xxx/xxxxx/xxxx/libopc.so, ENV=(OPC_PFILE=/xxx/xxxxx/xxxx//opcCRS.ora)' ;
    ALLOCATE CHANNEL SBT_3 DEVICE TYPE SBT parms='SBT_LIBRARY=/xxx/xxxxx/xxxx/libopc.so, ENV=(OPC_PFILE=/xxx/xxxxx/xxxx//opcCRS.ora)' ;
    ALLOCATE CHANNEL SBT_4 DEVICE TYPE SBT parms='SBT_LIBRARY=/xxx/xxxxx/xxxx/libopc.so, ENV=(OPC_PFILE=/xxx/xxxxx/xxxx//opcCRS.ora)' ;
    BACKUP SECTION SIZE 64G AS COMPRESSED BACKUPSET INCREMENTAL LEVEL 0  DATABASE FORCE TAG '${W_SID}_LEV0_BACKUP_${VDATE}' FORMAT '%U-%d-OSS-DB-19-%I-%T';
    BACKUP AS COMPRESSED BACKUPSET ARCHIVELOG FROM TIME 'SYSDATE-1' FORCE FORMAT '%U-%d-OSS-DB-19-%I-%T';
    }
    EOF


###### Sample Restore script:

    #!/bin/bash
    ###############################################################################
    # $Header: db_restore.sh v0.1 - DB Restore $
    # NAME
    #   db_restore.sh
    # FUNCTION
    #   This script will restore the control file, and restore & recover the database using standby DB backup which is taken to object storage.
    #   This script is executed as an Oracle user and needs to be updated as per your environment.
    # UPDATE The Script as per your environment.
    #   1) Update the environment file name and path which needs to be sourced.
    #   2) Make sure we have the required pfile in place to start the DB in nomount.
    #   3) Update the DBSID.
    #   4) Disk Group name at set newname for database line.
    # NOTES
    # MODIFIED
    ##############################################################################
    # User specific aliases and functions
    . /home/oracle/DB.env
    sqlplus -s "/ as sysdba" << EOF
    startup nomount pfile='/u01/OCI-Cyber-scripts/DB-Restore/db/pfile.ora';
    create spfile='+DATA' from pfile='/u01/OCI-Cyber-scripts/DB-Restore/db/pfile.ora';
    startup nomount force;
    EOF
    rman target / << EOF
    run
    {
    set DBID <Update the DB ID Value>;
    ALLOCATE CHANNEL SBT1 DEVICE TYPE SBT parms='SBT_LIBRARY=/u01/OCI-Cyber-scripts/DB-Restore/opc/lib/libopc.so, ENV=(OPC_PFILE=/u01/OCI-Cyber-scripts/DB-Restore/opc/opcCRS.ora)' ;
    restore PRIMARY controlfile from AUTOBACKUP maxdays 20;
    alter database mount;
    }
    EOF
    sqlplus -s "/ as sysdba" << EOF
    alter database disable block change tracking;
    alter database set standby to maximize performance;
    EOF
    srvctl status database -d $ORACLE_UNQNAME
    sqlplus -S "/ as sysdba" << EOF > /u01/OCI-Cyber-scripts/DB-Restore/db/current_seq.log
    set head off
    set echo off
    set feedback off
    select 'set until sequence ' || seq# || ' thread ' || thread# || '; ' "Recover Command"
    from (
    select * from (
    select thread#, sequence# seq#, next_change# from (
    select * from v\$backup_archivelog_details
    where thread# || '_' || sequence# in
    (select thread# || '_' || max(sequence#) from v\$backup_archivelog_details group by thread#)
    ) order by next_change#
    ) where rownum = 1 ) ;
    EOF
    echo "run" > /u01/OCI-Cyber-scripts/DB-Restore/db/rman_restore.sh
    echo "{" >> /u01/OCI-Cyber-scripts/DB-Restore/db/rman_restore.sh
    echo "ALLOCATE CHANNEL CH1 DEVICE TYPE SBT parms='SBT_LIBRARY=/u01/OCI-Cyber-scripts/DB-Restore/opc/lib/libopc.so, ENV=(OPC_PFILE=/u01/OCI-Cyber-scripts/DB-Restore/opc/opcCRS.ora)';" >> /u01/OCI-Cyber-scripts/DB-Restore/db/rman_restore.sh
    echo "ALLOCATE CHANNEL CH2 DEVICE TYPE SBT parms='SBT_LIBRARY=/u01/OCI-Cyber-scripts/DB-Restore/opc/lib/libopc.so, ENV=(OPC_PFILE=/u01/OCI-Cyber-scripts/DB-Restore/opc/opcCRS.ora)';" >> /u01/OCI-Cyber-scripts/DB-Restore/db/rman_restore.sh
    echo "ALLOCATE CHANNEL CH3 DEVICE TYPE SBT parms='SBT_LIBRARY=/u01/OCI-Cyber-scripts/DB-Restore/opc/lib/libopc.so, ENV=(OPC_PFILE=/u01/OCI-Cyber-scripts/DB-Restore/opc/opcCRS.ora)';" >> /u01/OCI-Cyber-scripts/DB-Restore/db/rman_restore.sh
    echo "ALLOCATE CHANNEL CH4 DEVICE TYPE SBT parms='SBT_LIBRARY=/u01/OCI-Cyber-scripts/DB-Restore/opc/lib/libopc.so, ENV=(OPC_PFILE=/u01/OCI-Cyber-scripts/DB-Restore/opc/opcCRS.ora)';" >> /u01/OCI-Cyber-scripts/DB-Restore/db/rman_restore.sh
    echo "set newname for database to '+DATA'; " >> /u01/OCI-Cyber-scripts/DB-Restore/db/rman_restore.sh
    cat /u01/OCI-Cyber-scripts/DB-Restore/db/current_seq.log >> /u01/OCI-Cyber-scripts/DB-Restore/db/rman_restore.sh
    echo "restore database;" >> /u01/OCI-Cyber-scripts/DB-Restore/db/rman_restore.sh
    echo "switch datafile all;" >> /u01/OCI-Cyber-scripts/DB-Restore/db/rman_restore.sh
    echo "recover database;" >> /u01/OCI-Cyber-scripts/DB-Restore/db/rman_restore.sh
    echo "}" >> /u01/OCI-Cyber-scripts/DB-Restore/db/rman_restore.sh
    chmod +x /u01/OCI-Cyber-scripts/DB-Restore/db/rman_restore.sh
    rman target / cmdfile=/u01/OCI-Cyber-scripts/DB-Restore/db/rman_restore.sh log=/u01/OCI-Cyber-scripts/DB-Restore/db/logs/rman_restore_`date +%Y%m%d%H%M%S`.log
    sqlplus -s "/ as sysdba" << EOF
    alter database set standby to maximize performance;
    alter database open resetlogs;
    EOF
    srvctl stop database -d $ORACLE_UNQNAME
    srvctl start database -d $ORACLE_UNQNAME -o "read only"
    srvctl status database -d $ORACLE_UNQNAME -v


##### Use Case 2: Create DR Using backup from Object Storage
To perform targetless duplication in RMAN without connecting to the source database or catalog, the BACKUP LOCATION clause is used. However, this method is only applicable when the source database backups are stored in a DISK location. If the source database utilizes Oracle Database Backup Cloud Service (e.g., ZDM or EBS Cloud Manager) for cloud backups, the following steps need to be followed:
1)	Apply one-off patch 26082402:
-	For Oracle RDBMS versions 12c and later, it is necessary to apply the patch 26082402.
-	Please note that this bug is fixed starting from Oracle RDBMS version 19.1 onwards.
2)	Create an XML file with backup information:
-	On the destination database server, execute the odbsrmt.py script (bundled along with the libopc.so library file).
-	This script generates an XML file containing the necessary backup information. The XML file will be utilized by the DUPLICATE command in RMAN.
By following these steps, the targetless duplication process can be performed successfully, even when using cloud backups from Oracle Database Backup Cloud Service. The patch application ensures that any relevant issues are resolved, and the odbsrmt.py script facilitates the creation of the XML file containing the required backup information for the DUPLICATE command in RMAN.

###### Example

    python odbsrmt.py --mode=rman-listfile  --host=https://swiftobjectstorage.<region>.oraclecloud.com/v1/<namespace> --container=<container_name> --forcename=duplicate.xml –dir=/u01/install/APPS/backup/ --credential=Username/"tokenID" --dbid=<database ID>
    odbsrmt.py: ALL outputs will be written to [/u01/install/APPS/backup/duplicate.xml]
    odbsrmt.py: Processing container backup_db...
    cloud_slave_processors: Thread Thread_0 starting to download metadata XML files...
    cloud_slave_processors: Thread Thread_0 successfully done
    odbsrmt.py: ALL outputs have been written to [/u01/install/APPS/backup/duplicate.xml]




###### Script to duplicate standby database.

      connect auxiliary /
      set DECRYPTION identified by  "<password>";
      run {
      ALLOCATE AUXILIARY CHANNEL aux1 DEVICE TYPE SBT parms='SBT_LIBRARY=/u01/install/APPS/backup/lib/libopc.so, ENV=(OPC_PFILE=/u01/install/APPS/backup/opcdbbkp.ora)';
      ALLOCATE AUXILIARY CHANNEL aux2 DEVICE TYPE SBT parms='SBT_LIBRARY=/u01/install/APPS/backup/lib/libopc.so, ENV=(OPC_PFILE=/u01/install/APPS/backup/opcdbbkp.ora)';
      ALLOCATE AUXILIARY CHANNEL aux3 DEVICE TYPE SBT parms='SBT_LIBRARY=/u01/install/APPS/backup/lib/libopc.so, ENV=(OPC_PFILE=/u01/install/APPS/backup/opcdbbkp.ora)';
      ALLOCATE AUXILIARY CHANNEL aux4 DEVICE TYPE SBT parms='SBT_LIBRARY=/u01/install/APPS/backup/lib/libopc.so, ENV=(OPC_PFILE=/u01/install/APPS/backup/opcdbbkp.ora)';
      duplicate target database for standby backup location from file '/u01/install/APPS/backup/duplicate.xml' nofilenamecheck;
      }

*Reference doc: Perform RMAN Targetless Duplication Using Cloud (Oracle Database Backup Cloud Service) Backups (Doc ID 2454290.1)*

#### Validation/Testing

Test Scenario – This script, named validation.sql, runs the validation queries while connected as sysdba. It provides a comprehensive validation report for the target database after the restore process. The script sets various SQL*Plus settings to control output formatting and executes the necessary queries. The results include information such as the PDB name, current date, database name, open mode, database status, logins, and status of distinct datafiles, tablespaces, tempfiles, and datafiles. It also reports the number of invalid objects and the count of recoverable files.

Executing this script ensures a thorough validation of the restored database, enabling confirmation of a successful restore operation and providing critical information for further testing and analysis.

    #!/bin/bash
    ###############################################################################
    # $Header: validation.sql - DB Restore $
    # NAME
    #   validation.sql
    # FUNCTION
    #   This script runs the validation queries connected as sysdba.
    # NOTES
    # MODIFIED
    ###############################################################################
    # User-specific aliases and functions
    #
    # Source the DB envirnomnet
    #
    . /home/oracle/DB.env
    ORACLE_PDB_SID=PDBSID; export ORACLE_PDB_SID
    #
    #echo "Validation Report of Database"
    #echo "================================="
    #
    sqlplus -s "/ as sysdba" << EOF
    set echo off
    set verify off
    set feedback off
    set heading off
    set trimspool on
    #set termout off

    col Distinct_Datafile_Status for a24
    col Distinct_Tablespaces_Status for a27
    col Distinct_Tempfiles_Status for a25
    col Distinct_Datafiles_Status for a25
    SET NUMWIDTH 20

    select 'pdb:'||PDB_NAME from dba_pdbs;
    select 'Sysdate:'||sysdate from dual;
    select 'DB_Name:'||name from v\$database;
    select 'Open_Mode:'||open_mode from v\$database;
    select 'Status:'||status from v\$instance;
    select 'Current_scn:'||current_scn from v\$database;
    select 'Database_Status:'||database_status from v\$instance;
    select 'Logins:'||logins from v\$instance;
    select distinct 'Distinct_Datafile_Status:'||status from v\$datafile;
    select distinct 'Distinct_Tablespaces_Status:'||status from dba_Tablespaces;
    select distinct 'Distinct_Tempfiles_Status:'||status from dba_data_files;
    select distinct 'Distinct_Datafiles_status:'||status from dba_temp_files;
    select 'Invalids:'||count(*) from dba_objects where status='INVALID';
    select 'Recover_Files:'||count(*) from v\$recover_file;

    EOF




