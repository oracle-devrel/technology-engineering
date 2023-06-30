# Introduction

The best practices in this document provides recommendations for successfully migrating a 12c database running on a compute VM to a VM DB system (DBCS) in Oracle Cloud Infrastructure (OCI) while simultaneously upgrading the database to the 19c version using the dbcli utility. This document covers planning, preparation, provisioning, data migration, and the upgrade process. It offers insights into optimizing the migration and upgrade journey, ensuring compatibility, minimizing downtime and achieving a seamless transition to the new environment.

Owner: Bhaskar Ivaturi

## Assessment and Planning:

To ensure a smooth migration from Oracle 12c to 19c, it is important to plan the migration timeline while considering any downtime limitations and potential impact on users or applications. The following alternative approaches can be considered based on the size of the source database:

For a source database of approximately 1-2 TB, an export/import method can be employed to migrate and upgrade the database to Oracle 19c. This approach eliminates the need for converting Non-CDB to CDB database and later upgrading the database using DBCLI. To execute this method, it is recommended to refer MOS note 2554156.1, which provides a step-by-step guide for migrating the database to 19c in OCI.

However, if the source database is larger than 2 TB, a different migration approach of hybrid DR along with dbcli tool to upgrade database should be taken to minimize downtime.

The following high-level steps outline this approach:

-	Provision a target 12c VM DB system (DBCS) in OCI.
-	Drop the pluggable database and shut down the CDB database.
-	Configure a standby database for the source database on the newly provisioned 12c VM DB system, utilizing the same ORACLE_HOME binaries and ASM filesystem for the datafiles.
- Install the 19c Oracle Binaries on the 12c VM DB system using dbcli.
-	Start Managed Recovery Process (MRP) till cutover.
-	 During the cutover
      - Activate the physical standby database as the primary database.
      - Convert the Non-CDB 12c database to CDB/PDB.
      - Upgrade the 12c VM DB system database to 19c using dbcli.
      - Execute the necessary post-PDB steps on the DB Node.
      - Configure the application to connect with the 19c database using adcfgclone.pl located under $ADMIN_SCRIPTS_HOME.

The remaining part of the document outlines best practices for the above high level steps.

### Pre-upgrade Tasks:
By thoroughly reviewing the Oracle Database 19c documentation and release notes, verifying hardware and software requirements and evaluating the impact on existing applications, the organization can save approximately half a day in preparation time.

#### Planning and Testing:
-	Develop a comprehensive upgrade plan with specific milestones and timelines.
-	Create a test environment to simulate the upgrade process and validate its impact on applications.
-	Perform thorough testing of all critical application process and functionality in the test environment.
-	Define rollback and backup procedures in case any issues arise during the upgrade.


#### Preparation

Before proceeding with the migration process, it is crucial to ensure that you have completed all the necessary preparations and gone through the required documentation. Take into account the guidelines outlined in the below documents, which are specific to your current versions

- Oracle E-Business Suite Installation and Upgrade Notes Release 12 (12.2) for Linux x86-64 (Doc ID 1330701.1)
-	Interoperability Notes: Oracle E-Business Suite Release 12.2 with Oracle Database 19c (Doc ID 2552181.1)
-	Getting Started with Oracle E-Business Suite on Oracle Cloud Infrastructure (Doc ID 2517025.1)
-	Cloning Oracle E-Business Suite Release 12.2 with Rapid Clone (Doc ID 1383621.1)

By carefully reviewing and adhering to the information presented in these documents, you will be well-prepared for your Oracle E-Business Suite migration and upgrade. Remember to address any necessary patches and updates based on your current versions before initiating the process.


###### Database:
1.	Analyze the existing database and its components, such as tablespaces, data files and schemas.
2.	Resolve any outstanding database issues, such as inconsistencies or corruption.
3.	Implement necessary performance tuning and optimizations before the upgrade.
4.	Ensure that the database is adequately backed up and the backups are accessible during the upgrade process.

By analyzing the existing database, resolving outstanding issues and implementing performance tuning and optimizations beforehand, the organization can save significant downtime.

### Provisioning
-	Create a Database 12c VM DB system in OCI.
-	Make sure the service name matches the desired database name. For example, if you want to keep the same database name as your on-premises instance, use that name.
    - Specify the database name, which should begin with an alphabetic character and can have a maximum of eight alphanumeric characters. Special characters are not allowed.
-	Provide the name for the default pluggable database (PDB).
    - In an Oracle Database 12c deployment, a PDB name is required, but the actual pluggable database created at this stage will not be used by Oracle E-Business Suite. You can enter a dummy value such as "DUMMYPDB." This dummy PDB will be removed later.

Once you have completed the creation of the 12.1.0.2 database and entered the dummy value for the PDB name, you can proceed to drop it by following these steps.
Connect to the database using SQL*Plus as the sysdba user:

    $ sqlplus / as sysdba
    SQL> alter pluggable database DUMMYPDB close immediate;
    SQL> drop pluggable database DUMMYPDB including datafiles;

### Data migration

Configure standby database for source EBS database on the OCI VM DB system. We are using the OCI VM DB system $ORACLE_HOME and ASM (+DATA, +RECO) locations for the physical standby database creation. Creating standby database will save the overall downtime which is required during the cutover by avoiding a database backup and restore, especially if the database size is greater than 2TB.


#### Set up a standby database for your source database

-	Ensure that you have executed the "adpreclone" utility on both the application and database tiers.
- As part of preparing for standby database creation, you must enable force logging on the source database.

      SQL> ALTER DATABASE FORCE LOGGING;
-	Take an RMAN backup of the source database. This backup will be used to create the standby database. Make sure to include all required data files, control files, and archived redo logs in the backup. Create a parameter file (pfile) for the standby database with the necessary configurations.

In the pfile, set the "DB_FILE_NAME_CONVERT" parameter to specify the conversion of file paths from the primary to the standby database.

######Example:
    ALTER SYSTEM SET DB_FILE_NAME_CONVERT='/u01/prod/data/', '+DATA/<DB_UNIQUE_NAME>/<Source DB Name>/' SCOPE=SPFILE;
    Additionally, set the LOG_FILE_NAME_CONVERT parameter to convert the paths for redo log files. For example:
    ALTER SYSTEM SET LOG_FILE_NAME_CONVERT='/u01/prod/redo/','+RECO/' SCOPE=SPFILE;

-	Use the RMAN "DUPLICATE" command to duplicate the target database (primary) to the standby database. Specify the backup location path where the RMAN backup from the primary database is stored.
######Example:
      DUPLICATE TARGET DATABASE TO <source DB name>  BACKUP LOCATION <'backup location path'>;
-	Start the managed recovery and make sure the archives are getting shipped and applied to the standby database.

During the cutover we will cancel the managed recovery and activate physical standby database.

######Example:
    SQL> ALTER DATABASE RECOVER MANAGED STANDBY DATABASE FINISH;
    SQL> SELECT SWITCHOVER_STATUS FROM V$DATABASE;

    SWITCHOVER_STATUS
    --------------------
    TO PRIMARY

    SQL> ALTER DATABASE ACTIVATE PHYSICAL STANDBY DATABASE;

After activating the standby database, it is important to run the data patch utility to update patches and ensure the database is up to date. This step is crucial before checking for any violations that could affect the conversion to a pluggable database.

Before converting the Non-CDB database into the CDB on the VM DB system, it is of utmost importance to conduct a comprehensive assessment for any plug-in violations. It is crucial to identify and resolve these violations prior to the conversion process as they have the potential to disrupt the plugging process. Even if the conversion process appears to be smooth and error-free, it is still possible to encounter these issues when attempting to open the pluggable database in read/write mode following the conversion. It is therefore necessary to address any violations proactively to ensure a seamless transition and avoid complications during the subsequent usage of the pluggable database.


#### Identify and fix any plug-in violations

Errors reported for components installed on the PDB but not on the CDB need to be resolved before proceeding further. In this case, the missing component will need to be installed on the CDB.
Errors reported for components installed on the CDB but not on the PDB can be ignored. These will be resolved when the EBS database is plugged into the CDB.
SQL patch errors can be ignored at this point.
Review warnings regarding mismatched database parameters and update any that are critical for your environment. For more information, refer to Document 396009.1, Database Initialization Parameters for Oracle E-Business Suite Release 12.

### Upgrade Process
Before we start the upgrade process ensure that you verify the precheck output file generated during the execution prior to initiating the upgrade process. This can be accomplished by performing a validation using both the hcheck.sql script and the dbcli upgrade-database command with the --precheck flag. Also, make sure that we always update the dbcli tool and use the latest version using cliadm update-dbcli command.

*The hcheck.sql file can be downloaded from the MOS Note 136697.1*

To ensure a successful upgrade process, follow these steps:
-	Utilize DBCLI command-line tools for the upgrade process.
-	Execute the command dbcli upgrade --precheck. This will generate an upgrade.xml file.
-	Carefully examine the upgrade.xml file for any reported errors.
-	Fix the reported errors in the upgrade.xml file, addressing each error individually.
-	Once you have made the necessary fixes, rerun the command dbcli upgrade --precheck.
-	Repeat the above steps until all the reported errors in the upgrade.xml file have been resolved.
-	Monitor the upgrade process for any errors or warnings and address them promptly.
-	Verify the post-upgrade status of the database, including the successful completion of all upgrade steps.

By diligently following this approach, you can ensure that the upgrade process proceeds smoothly and all identified errors are properly addressed.

######Example of error:
    -<PreUpgradeChecks>
    	-<PreUpgradeCheck Status="ERROR" ID="purge_recyclebin">
    	-<Rule>
    		-<Message ID="CHECK.PURGE_RECYCLEBIN.RULE">

To upgrade the database make sure we use the correct DB ID and DB Home ID
######Example
    dbcli upgrade-database -i 1xxxx000-x111-1xxx-11x0-11xx00x1x1x0 -dh 00x0xx1x-x1x1-1x1x-x0xx-xxx0x10xxx00 --upgradeOptions "-keepEvents"

where -i is the 12c DB ID and -dh is the 19c DB home ID value. You can get these values using **dbcli list-databases** & **dbcli list-dbhomes**. Please refer MOS Note 2673057.1 for more information.

### Post-upgrade Tasks
-	Conduct thorough testing of the upgraded database to validate its functionality.
-	Update any necessary configurations, parameters or settings in the upgraded database.
-	Revalidate the performance of critical application processes and tune the database if required.
-	Communicate the successful completion of the upgrade to relevant stakeholders.

### Maintenance and Support
-	Establish a plan for ongoing database maintenance and support activities.
-	Schedule regular backups, patching and performance monitoring for the upgraded database.
-	Stay up to date with Oracle's support and patching releases for Oracle Database 19c.
