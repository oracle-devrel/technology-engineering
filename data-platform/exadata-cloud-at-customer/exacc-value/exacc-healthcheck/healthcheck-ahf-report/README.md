# AHF Reports - Customer Guide

**NOTE**: Before generating the AHF reports it is important to install the latest version of the AHF suite.

## Update AHF

The main MOS note for the AHF maintenance is: 

*Autonomous Health Framework (AHF) - Including Trace File Analyzer and Orachk/Exachk (Doc ID 2550798.1)*

**How-To update the AHF software**

* Download the up-to-date AHF software from the MOS Note (*2550798.1*)

* Stage the latest Autonomous Health Framework source file to a temporary directory and unzip it.

        cd /stage/directory
        unzip AHF-LINUX_<version>.zip 

* Execute the following setup command, from the location in which Autonomous Health Framework is staged: 
  
        ./ahf_setup -ahf_loc /opt -data_dir /u02 -local

### Get Latest CVU

It can be required to install the latest Cluster Verification Utility (CVU) utility to allow the exachk to complete the cluvfy checks.

Usualy, running the *_exachk_*, if the CVU update is required, this is the prompt the appears before starting the checks:


    Either Cluster Verification Utility pack (cvupack) does not exist at /opt/oracle.ahf/common/cvu or it is an old or invalid cvupack

    Checking Cluster Verification Utility (CVU) version at CRS Home - /u01/app/19.0.0.0/grid

    This version of Cluster Verification Utility (CVU) was released on 26-Dec-2023 and it is older than 180 days. It is highly recommended that you download the latest version of CVU from MOS patch 30839369 to ensure the highest level of accuracy of the data contained within the report

    Do you want to download latest version of Cluster Verification Utility (CVU) from my oracle support? [y/n] [y]


You can download the zip when prompted, if the VM has internet access and you have MOS account. 
Otherwise you should download the lates CVU version from MOS, sarching patch 30839369. When you have downloaded the zip version of the latest CVU, unzip it into /opt/oracle.ahf/common/cvu and run the *_exachk_*

## Execute AHF Compliance Report

To generate the AHF Compliance Report, please, follow the below instructions.

**NOTE**: run _ahfctl_ root user.

    $ sudo su - root
    $ # ahfctl compliance
    
    Searching for running databases . . . . .
    
    .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
    List of running databases registered in OCR
    
    1. MY1DB
    2. MY2DB
    3. MY3DB
    4. MY4DB
    5. MY5DB
    6. MY6DB
    7. All of above
    8. None of above
    
    Select databases from list for checking best practices. For multiple databases, select 7 for All or comma separated number like 1,2 etc [1-8][7].
    
    Searching out ORACLE_HOME for selected databases.
    
    .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
    .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
    
    Checking Status of Oracle Software Stack - Clusterware, ASM, RDBMS
    
    .  .  . . . .  .  . . . .  .  . . . .  .  . . . .  .  . . . .  .  . . . .
    .  .  .  . . . .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
    
    Starting to run exachk in background on custexcclu1-ux3wk2 using socket
    
    
    .
    .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
    .  .  .  .  .  .  .  .  .  .
    
    Checking Status of Oracle Software Stack - Clusterware, ASM, RDBMS on custexcclu1-ux3wk1
    
    .  .  . . . .  .  . . . .  .  . . . .  .  . . . .  .  . . . .  .  . . . .
    .  .  .  . . . .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
    -------------------------------------------------------------------------------------------------------
                                                     Oracle Stack Status
    -------------------------------------------------------------------------------------------------------
      Host Name       CRS Installed  RDBMS Installed    CRS UP    ASM UP  RDBMS UP    DB Instance Name
    -------------------------------------------------------------------------------------------------------
    custexcclu1-ux3wk1          Yes          Yes          Yes      Yes      Yes          MY3DB1 MY5DB1 MY6DB1 MY2DB1 MY1DB1 MY4DB
    -------------------------------------------------------------------------------------------------------
    .  .  .  .  .  .  .  .  .
    
    *** Checking Best Practice Recommendations ( Pass / Warning / Fail ) ***
    
    .  .  .  .  .  .
    
    ============================================================
          Node name - custexcclu1-ux3wk1
    ============================================================
    . . . . . . . . . .
     Collecting - ASM Diskgroup Attributes
     Collecting - ASM High Redundancy Grid Disks
     Collecting - ASM diskgroup usable free space
     Collecting - ASM initialization parameters
     Collecting - Database Parameters for MY1DB database
     Collecting - Database Parameters for MY2DB database
     Collecting - Database Parameters for MY3DB database
     Collecting - Database Parameters for MY4DB database
     Collecting - Database Parameters for MY5DB database
     Collecting - Database Parameters for MY6DB database
     Collecting - Database Undocumented Parameters for MY1DB database
     Collecting - Database Undocumented Parameters for MY2DB database
     Collecting - Database Undocumented Parameters for MY3DB database
     Collecting - Database Undocumented Parameters for MY4DB database
     Collecting - Database Undocumented Parameters for MY5DB database
     Collecting - Database Undocumented Parameters for MY6DB database
     Collecting - ASM Disk Group for Infrastructure Software and Configuration
     Collecting - CELL ID Info
     Collecting - CPU Information
     Collecting - Clusterware and RDBMS software version
     Collecting - Compute node PCI bus slot speed for RDMA Network Fabric HCAs
     Collecting - Exadata Critical Issue EX88
     Collecting - Gather Dbaas Platform Information
     Collecting - KFOD and CRS Patches/Patchlevel info
     Collecting - Kernel parameters
     Collecting - Maximum number of semaphore sets on system
     Collecting - Maximum number of semaphores on system
     Collecting - Monthly recommended patches for Grid Infrastructure
     Collecting - Monthly recommended pathes for Database Home
     Collecting - OS Packages
     Collecting - Patches for Grid Infrastructure
     Collecting - Patches for RDBMS Home
     Collecting - Patches xml for Grid Infrastructure
     Collecting - Patches xml for RDBMS Home
     Collecting - RDBMS and GRID software owner UID across cluster
     Collecting - RDBMS patch inventory
     Collecting - Verify CPU configuration across all VMs in the cluster
     Collecting - number of semaphore operations per semop system call
     Collecting - CRS user limits configuration
     Collecting - CRS user time zone check
     Collecting - Clusterware patch inventory
     Collecting - Collect Data Guard TFA Data
     Collecting - Collect ksplice fixes [Database Server]
     Collecting - Collection for dbcs service and port status
     Collecting - Data collection for /etc/crontab
     Collecting - Data collection for opc user
     Collecting - Data collection for shell customization
     Collecting - Exadata Critical Issue DB09
     Collecting - Exadata Critical Issue EX33
     Collecting - Exadata Critical Issue EX55
     Collecting - Exadata Critical Issue EX56
     Collecting - Exadata Critical Issue EX57
     Collecting - Exadata Critical Issue EX58
     Collecting - Exadata Critical Issue EX64
     Collecting - Exadata Critical Issue EX67
     Collecting - Exadata software version on database server
     Collecting - Exadata version on database server
     Collecting - HCA firmware version on database server
     Collecting - HCA transfer rate on database server
     Collecting - Infrastructure Software and Configuration for compute
     Collecting - Linux system service and RAC process configuration
     Collecting - MaxStartups setting in sshd_config
     Collecting - OFED Software version on database server
     Collecting - Obtain hardware information
     Collecting - Operating system and Kernel version on database server
     Collecting - Oracle monitoring agent and/or OS settings on ADR diagnostic directories
     Collecting - SELinux status
     Collecting - Sudoers data collection for opc user
     Collecting - System Event Log
     Collecting - Validate key sysctl.conf parameters on database servers
     Collecting - Verify DBaaS RPM tools and rpm database integrity
     Collecting - Verify DSA authentication is not supported for SSH equivalency
     Collecting - Verify Data Network is Separate from Management Network
     Collecting - Verify IP routing configuration on database servers
     Collecting - Verify Oracle High Availability Services Automatic Startup Configuration
     Collecting - Verify Quorum disks configuration
     Collecting - Verify RDMA Network Fabric kernel parameters on database servers
     Collecting - Verify RoCE Interfaces Status [Database Server]
     Collecting - Verify TCP Selective Acknowledgement is enabled
     Collecting - Verify active kernel version matches expected version for installed Exadata Image
     Collecting - Verify available ksplice fixes are installed [Database Server]
     Collecting - Verify database server file systems have Maximum mount count = -1
     Collecting - Verify imageinfo on database server
     Collecting - Verify imageinfo on database server to compare systemwide
     Collecting - Verify installed rpm(s) kernel type match the active kernel version
     Collecting - Verify no database server kernel out of memory errors
     Collecting - Verify proper ACFS drivers are installed for Spectre v2 mitigation
     Collecting - Verify sysctl.conf parameter vm.nr_hugepages value is same or less in initramfs [Database Server]
     Collecting - Verify the Name Service Cache Daemon (NSCD) configuration
     Collecting - Verify the vm.min_free_kbytes configuration
     Collecting - Verify umask value is 0022 for opc and oracle user
     Collecting - collect time server data [Database Server]
     Collecting - root time zone check
    
    Data collections completed. Checking best practices on custexcclu1-ux3wk1.
    ------------------------------------------------------------
    
     WARNING =>  SYSTEM tablespace is being used by audit objects for MY2DB
     WARNING =>  SYSTEM tablespace is being used by audit objects for MY5DB
     WARNING =>  Database dictionary consistency check for multitenant database reported one or more failure for MY2DB
     WARNING =>  Database dictionary consistency check for multitenant database reported one or more failure for MY5DB
     CRITICAL => System is exposed to Exadata Critical Issue DB52
     WARNING =>  Verify Database Memory Allocation
     UNDETERMINED =>     Data Guard is not Ready for Switchover for MY3DB
     UNDETERMINED =>     Data Guard is not Ready for Switchover for MY4DB
     UNDETERMINED =>     Data Guard is not Ready for Failover for MY3DB
     UNDETERMINED =>     Data Guard is not Ready for Failover for MY4DB
     UNDETERMINED =>     Transport Lag is greater than 30 seconds for MY3DB
     UNDETERMINED =>     Transport Lag is greater than 30 seconds for MY4DB
     UNDETERMINED =>     Apply Lag is greater than 30 seconds for MY3DB
     UNDETERMINED =>     Apply Lag is greater than 30 seconds for MY4DB
     INFO =>     Oracle GoldenGate failure prevention best practices
     INFO =>     One or more non-default AWR baselines should be created for MY2DB
     INFO =>     One or more non-default AWR baselines should be created for MY5DB
     WARNING =>  One or more open PDBs have failed service verification checks for MY2DB
     WARNING =>  One or more open PDBs have failed service verification checks for MY5DB
     INFO =>     Database parameter AUDIT_TRAIL should be set to the recommended value for MY1DB
     INFO =>     Please refer to data and guidance provided for database parameter processes for MY2DB
     INFO =>     Please refer to data and guidance provided for database parameter processes for MY5DB
     INFO =>     SELinux configuration is not as expected
     FAIL =>     One or more log archive destination and alternate log archive destination settings are not as recommended for MY5DB
     FAIL =>     Table AUD$[FGA_LOG$] should use Automatic Segment Space Management for MY2DB
     FAIL =>     Table AUD$[FGA_LOG$] should use Automatic Segment Space Management for MY5DB
     FAIL =>     Database parameter COMPATIBLE should be set to recommended value for MY5DB
     FAIL =>     Database parameter DB_BLOCK_CHECKING on primary is not set to the recommended value. for MY2DB
     WARNING =>  Standby is not opened read only with managed recovery in real time apply mode for MY3DB
     WARNING =>  Standby is not opened read only with managed recovery in real time apply mode for MY4DB
     WARNING =>  Standby is not opened read only with managed recovery in real time apply mode for MY6DB
     WARNING =>  Standby is not in READ ONLY WITH APPLY mode for MY3DB
     WARNING =>  Standby is not in READ ONLY WITH APPLY mode for MY4DB
     WARNING =>  Standby is not in READ ONLY WITH APPLY mode for MY6DB
     INFO =>     Operational Best Practices
     INFO =>     Database Consolidation Best Practices
     INFO =>     Computer failure prevention best practices
     INFO =>     Data corruption prevention best practices
     INFO =>     Logical corruption prevention best practices
     INFO =>     Database/Cluster/Site failure prevention best practices
     INFO =>     Client failover operational best practices
     WARNING =>  Local undo is not enabled for MY5DB
     FAIL =>     Database parameter target_pdbs is not set within best practice thresholds for MY1DB
     FAIL =>     Database parameter target_pdbs is not set within best practice thresholds for MY2DB
     FAIL =>     Database parameter target_pdbs is not set within best practice thresholds for MY5DB
     INFO =>     While initialization parameter LOG_ARCHIVE_CONFIG is set it should be verified for your environment on Standby Database for MY1DB
     INFO =>     Database failure prevention best practices
     INFO =>     While initialization parameter LOG_ARCHIVE_CONFIG is set it should be verified for your environment on Primary Database for MY5DB
     FAIL =>     Primary database is not protected with Data Guard (standby database) for real-time data protection and availability for MY2DB
     INFO =>     Storage failures prevention best practices
     INFO =>     The Optimizer fixes for 19c database version is disabled by default for bugs with status value 0 for MY2DB
     INFO =>     The Optimizer fixes for 19c database version is disabled by default for bugs with status value 0 for MY5DB
     INFO =>     Software maintenance best practices
     WARNING =>  Some Auto Extensible datafiles are not expanding by at least one stripe width for MY5DB
     INFO =>     CPU Capacity sizing data activity monitoring information
     WARNING =>  TNS aliases are not defined properly for database backups using dbaastools
     FAIL =>     The integrity check of key GI startup files did not succeed
     FAIL =>     FRA space management problem file types are present without an RMAN backup completion within the last 7 days for MY2DB
     INFO =>     Oracle recovery manager(rman) best practices
     WARNING =>  RMAN controlfile autobackup should be set to ON for MY2DB
     WARNING =>  RMAN controlfile autobackup should be set to ON for MY5DB
     WARNING =>  RMAN controlfile autobackup should be set to ON for MY5DB
     INFO =>     Exadata Critical Issues (Doc ID 1270094.1):- DB1-DB4,DB6,DB9-DB50,DB52-DB53 EX1-EX65,EX67,EX69-EX78,EX80-EX85,EX88 and IB1-IB3,IB5-IB9
     WARNING =>  TNS_ADMIN variable in Oracle Cluster Registry is not configured as expected for MY5DB
     WARNING =>  Multiple Oracle database instances discovered, observe database consolidation best practices
     WARNING =>  Database metadata in environment file is not consistent with Oracle Cluster Registry for MY5DB
     INFO =>     Database feature usage statistics for MY1DB
     INFO =>     Database feature usage statistics for MY2DB
     INFO =>     Database feature usage statistics for MY5DB
     INFO =>     Database feature usage statistics for MY5DB
     WARNING =>  There exists one or more underscore parameters without a comment for MY2DB
     CRITICAL => System is exposed to Exadata Critical Issue DB50
     FAIL =>     KMS configuration validation for database encryption is not successful for MY2DB
     FAIL =>     KMS configuration validation for database encryption is not successful for MY5DB
     FAIL =>     Recommended bug fixes are not applied for RDBMS home for /u02/app/oracle/product/19.0.0.0/dbhome_14
     FAIL =>     Recommended bug fixes are not applied for RDBMS home for /u02/app/oracle/product/19.0.0.0/dbhome_15
     FAIL =>     Recommended bug fixes are not applied for RDBMS home for /u02/app/oracle/product/19.0.0.0/dbhome_16
     FAIL =>     Recommended bug fixes are not applied for CRS home
     WARNING =>  Number of inactive patches for database home exceeds the default recommendation for /u02/app/oracle/product/19.0.0.0/dbhome_14
     WARNING =>  Number of inactive patches for database home exceeds the default recommendation for /u02/app/oracle/product/19.0.0.0/dbhome_15
     WARNING =>  Number of inactive patches for database home exceeds the default recommendation for /u02/app/oracle/product/19.0.0.0/dbhome_16
    
    
    
    
    
    
    Copying results from custexcclu1-ux3wk2 and generating report. This might take a while. Be patient.
    
    
    ============================================================
          Node name - custexcclu1-ux3wk2
    ============================================================
    . . . . . . . . . .
     Collecting - ASM Diskgroup Attributes
     Collecting - ASM High Redundancy Grid Disks
     Collecting - ASM diskgroup usable free space
     Collecting - ASM initialization parameters
     Collecting - Database Parameters for MY1DB database
     Collecting - Database Parameters for MY2DB database
     Collecting - Database Parameters for MY3DB database
     Collecting - Database Parameters for MY4DB database
     Collecting - Database Parameters for MY5DB database
     Collecting - Database Parameters for MY6DB database
     Collecting - Database Undocumented Parameters for MY1DB database
     Collecting - Database Undocumented Parameters for MY2DB database
     Collecting - Database Undocumented Parameters for MY3DB database
     Collecting - Database Undocumented Parameters for MY4DB database
     Collecting - Database Undocumented Parameters for MY5DB database
     Collecting - Database Undocumented Parameters for MY6DB database
     Collecting - ASM Disk Group for Infrastructure Software and Configuration
     Collecting - CELL ID Info
     Collecting - CPU Information
     Collecting - Clusterware and RDBMS software version
     Collecting - Compute node PCI bus slot speed for RDMA Network Fabric HCAs
     Collecting - Exadata Critical Issue EX88
     Collecting - Gather Dbaas Platform Information
     Collecting - KFOD and CRS Patches/Patchlevel info
     Collecting - Kernel parameters
     Collecting - Maximum number of semaphore sets on system
     Collecting - Maximum number of semaphores on system
     Collecting - Monthly recommended patches for Grid Infrastructure
     Collecting - Monthly recommended pathes for Database Home
     Collecting - OS Packages
     Collecting - Patches for Grid Infrastructure
     Collecting - Patches for RDBMS Home
     Collecting - Patches xml for Grid Infrastructure
     Collecting - Patches xml for RDBMS Home
     Collecting - RDBMS and GRID software owner UID across cluster
     Collecting - RDBMS patch inventory
     Collecting - Verify CPU configuration across all VMs in the cluster
     Collecting - number of semaphore operations per semop system call
    
    Data collections completed. Checking best practices on custexcclu1-ux3wk2.
    ------------------------------------------------------------
    
     WARNING =>  SYSTEM tablespace is being used by audit objects for MY2DB
     WARNING =>  SYSTEM tablespace is being used by audit objects for MY5DB
     CRITICAL => System is exposed to Exadata Critical Issue DB52
     WARNING =>  Verify Database Memory Allocation
     UNDETERMINED =>     Data Guard is not Ready for Switchover for MY3DB
     UNDETERMINED =>     Data Guard is not Ready for Switchover for MY4DB
     UNDETERMINED =>     Data Guard is not Ready for Failover for MY3DB
     UNDETERMINED =>     Data Guard is not Ready for Failover for MY4DB
     UNDETERMINED =>     Transport Lag is greater than 30 seconds for MY3DB
     UNDETERMINED =>     Transport Lag is greater than 30 seconds for MY4DB
     UNDETERMINED =>     Apply Lag is greater than 30 seconds for MY3DB
     UNDETERMINED =>     Apply Lag is greater than 30 seconds for MY4DB
     INFO =>     Oracle GoldenGate failure prevention best practices
     WARNING =>  One or more open PDBs have failed service verification checks for MY2DB
     WARNING =>  One or more open PDBs have failed service verification checks for MY5DB
     INFO =>     Database parameter AUDIT_TRAIL should be set to the recommended value for MY1DB
     INFO =>     Please refer to data and guidance provided for database parameter processes for MY2DB
     INFO =>     Please refer to data and guidance provided for database parameter processes for MY5DB
     INFO =>     SELinux configuration is not as expected
     FAIL =>     Database parameter COMPATIBLE should be set to recommended value for MY5DB
     FAIL =>     Database parameter DB_BLOCK_CHECKING on primary is not set to the recommended value. for MY2DB
     FAIL =>     Database parameter target_pdbs is not set within best practice thresholds for MY1DB
     FAIL =>     Database parameter target_pdbs is not set within best practice thresholds for MY2DB
     FAIL =>     Database parameter target_pdbs is not set within best practice thresholds for MY5DB
     INFO =>     While initialization parameter LOG_ARCHIVE_CONFIG is set it should be verified for your environment on Standby Database for MY1DB
     INFO =>     The Optimizer fixes for 19c database version is disabled by default for bugs with status value 0 for MY2DB
     INFO =>     The Optimizer fixes for 19c database version is disabled by default for bugs with status value 0 for MY5DB
     WARNING =>  Some Auto Extensible datafiles are not expanding by at least one stripe width for MY5DB
     WARNING =>  TNS aliases are not defined properly for database backups using dbaastools
     FAIL =>     The integrity check of key GI startup files did not succeed
     WARNING =>  TNS_ADMIN variable in Oracle Cluster Registry is not configured as expected for MY5DB
     WARNING =>  Multiple Oracle database instances discovered, observe database consolidation best practices
     WARNING =>  Database metadata in environment file is not consistent with Oracle Cluster Registry for MY5DB
     WARNING =>  There exists one or more underscore parameters without a comment for MY2DB
     CRITICAL => System is exposed to Exadata Critical Issue DB50
     FAIL =>     Recommended bug fixes are not applied for RDBMS home for /u02/app/oracle/product/19.0.0.0/dbhome_14
     FAIL =>     Recommended bug fixes are not applied for RDBMS home for /u02/app/oracle/product/19.0.0.0/dbhome_15
     FAIL =>     Recommended bug fixes are not applied for RDBMS home for /u02/app/oracle/product/19.0.0.0/dbhome_16
     FAIL =>     Recommended bug fixes are not applied for CRS home
     WARNING =>  Number of inactive patches for database home exceeds the default recommendation for /u02/app/oracle/product/19.0.0.0/dbhome_14
     WARNING =>  Number of inactive patches for database home exceeds the default recommendation for /u02/app/oracle/product/19.0.0.0/dbhome_15
     WARNING =>  Number of inactive patches for database home exceeds the default recommendation for /u02/app/oracle/product/19.0.0.0/dbhome_16
    
    ------------------------------------------------------------
                          CLUSTERWIDE CHECKS
    ------------------------------------------------------------
    
     UNDETERMINED =>     CPU contention may be impacting database performance.
     FAIL =>     All $ORACLE_HOMEs should have same patches across database servers
     UNDETERMINED =>     System is exposed to Exadata Critical Issue EX83
     FAIL =>     Verify no orphaned files exist in ASM
    ------------------------------------------------------------
    
    UPLOAD [if required] - /u02/oracle.ahf/data/custexcclu1-ux3wk1/exachk/user_root/output/exachk_custexcclu1-ux3wk1_MY6DB_101024_13265.zip


At the end of the exachk script execution, a zip file is created. The default path of the ZIP file should be: 

**_/u02/oracle.ahf/data/[NODE-NAME]/exachk/user_root/output/exachk_[node-name]_mmddyyyy_hhmmss_SN.zip_**

## Execute AHF Insight Report

To generate the AHF Insight Report, please, follow the below instructions.

**NOTE**: run _ahf_ as root user.

    $ ahf analysis create --type insights
    Starting analysis and collecting data for insights
    Collecting data for AHF Insights (This may take a few minutes per node)
    AHF Insights report contains information of 2:00:00 hrs
    From Date : 10/24/2024 12:55:39 - To Date : 10/24/2024 14:55:39
    Report is generated at :  /u02/oracle.ahf/data/repository/collection_Thu_Oct_24_14_55_45_UTC_2024_node_all/custexcclu2-l9lkn1_insights_2024_10_24_14_56_36.zip

Reviewed: 01/22/26

## License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details. 
