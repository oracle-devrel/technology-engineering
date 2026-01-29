# AWR dumps collection - Customer Guide

## Introduction
Below the instructions to generate the AWR Dump, required to proceed with the DB Performance Health Check.

Specifically for the Performance Health Check an AWR dump collected for at least a 24 hour period is needed.

NOTE: The scripts ask for Begin/End Snap which should be midnight to the next midnight to cover the 24 hour period.


## Generate AWR Dump

- Connect on the Database Server where the DB that you want to analyse reside

- Open a __sqlplus__ session

- From the SQL prompt, enter:



        -- This returns a list of the databases in the AWR schema.
        @?/rdbms/admin/awrextr.sql



- Enter the database from which the AWR data will be extracted


        -- For example, to select the database with the database    identifier of 123456789 enter the value 123456789
        Enter value for db_id: [YOUR DB ID]

    ```

- Specify the number of days for the list of Snapshot IDs


        -- A list of existing snapshots for the specified time range    will be displayed. For example, snapshots captured in the last 2   days are displayed when an value of 2 is entered.
        Enter value for num_days: [DAYS]


- Define the snapshot range for AWR data to be extracted by specifying a beginning and ending Snapshot Id


        -- For example, to select a snapshot with a snapshot Id of 20 as the beginning snapshot, and the snapshot with a snapshot Id of 30 as the ending snapshot, enter 20 for [x] and 30 for [y].
        Enter value for begin_snap: [x] Enter value for end_snap: [y]


- After defining the range a list of directory objects is displayed.

- Enter the name of the directory object pointing to the directory where the export dump file will be stored.


        -- For example, to select the directory object MY_DATA_PUMPsimply enter MY_DATA_PUMPat the prompt.
        Enter value for directory name: [Your DATA PUMP Directory]


- Finally specify the prefix for the export dump file name (a .dmp suffix will be automatically appended to the file name)


        Enter value for file_name:


- The amount of AWR data that needs to be extracted will determine the processing time for the AWR extract operation. After the dump file is created, Data Pump can be used to transport the file to another system.

### Example of Generating AWR Dump


    $ sqp
    
    SQL*Plus: Release 19.0.0.0.0 - Production on Mon Aug 19 15:39:39 2024
    Version 19.18.0.0.0
    
    Copyright (c) 1982, 2022, Oracle.  All rights reserved.
    
    
    Connected to:
    Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
    Version 19.18.0.0.0
    
    SQL> @?/rdbms/admin/awrextr.sql
    ~~~~~~~~~~~~~
    AWR EXTRACT
    ~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ~  This script will extract the AWR data for a range of snapshots  ~
    ~  into a dump file.  The script will prompt users for the         ~
    ~  following information:                                          ~
    ~     (1) database id                                              ~
    ~     (2) snapshot range to extract                                ~
    ~     (3) name of directory object                                 ~
    ~     (4) name of dump file                                        ~
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    
    Databases in this Workload Repository schema
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
       DB Id     DB Name      Host
    ------------ ------------ ------------
    * 979111315  GRDBA        srcnode1
    
    * 979111315  GRDBA        srcnode2
    
    * 979111315  GRDBA        tgtnode1
    
    * 979111315  GRDBA        tgtnode2
    
    
    The default database id is the local one: '979111315'.  To use this
    database id, press <return> to continue, otherwise enter an alternative.
    
    Enter value for dbid: 979111315
    
    Using 979111315 for Database ID
    
    
    Specify the number of days of snapshots to choose from
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Entering the number of days (n) will result in the most recent
    (n) days of snapshots being listed.  Pressing <return> without
    specifying a number lists all completed snapshots.
    
    
    Enter value for num_days: 10
    
    Listing the last 10 days of Completed Snapshots
    
    DB Name        Snap Id    Snap Started
    ------------ --------- ------------------
    GRDBA                1 13 Aug 2024 12:00
                         2 13 Aug 2024 13:00
                         3 13 Aug 2024 14:00
                         4 13 Aug 2024 15:00
                         5 13 Aug 2024 16:00
                         6 13 Aug 2024 17:00
                         7 13 Aug 2024 18:00
                         8 13 Aug 2024 19:00
                         9 14 Aug 2024 09:43
                        10 14 Aug 2024 11:00
                        11 14 Aug 2024 12:00
                        12 14 Aug 2024 13:00
                        13 14 Aug 2024 14:00
                        14 14 Aug 2024 15:00
                        15 14 Aug 2024 16:00
                        16 14 Aug 2024 17:00
                        17 14 Aug 2024 18:00
                        18 19 Aug 2024 11:39
                        19 19 Aug 2024 13:00
                        20 19 Aug 2024 14:00
                        21 19 Aug 2024 15:00
    
    
    Specify the Begin and End Snapshot Ids
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Enter value for begin_snap: 1
    Begin Snapshot Id specified: 1
    
    Enter value for end_snap: 21
    End   Snapshot Id specified: 21
    
    
    Specify the Directory Name
    ~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    Directory Name                 Directory Path
    ------------------------------ -----------------------------------------------------------
    DATA_PUMP_DIR                  /u02/app/oracle/product/19.0.0.0/dbhome_45/rdbms/log
    DBMS_OPTIM_ADMINDIR            /u02/app/oracle/product/19.0.0.0/dbhome_45/rdbms/admin
    DBMS_OPTIM_LOGDIR              /u02/app/oracle/product/19.0.0.0/dbhome_45/cfgtoollogs
    GR_AWRDUMP                     /acfs01/acfs/GR_AWRDUMP
    JAVA$JOX$CUJS$DIRECTORY$       /u02/app/oracle/product/19.0.0.0/dbhome_11/javavm/admin/
    OPATCH_INST_DIR                /u02/app/oracle/product/19.0.0.0/dbhome_11/OPatch
    OPATCH_LOG_DIR                 /u02/app/oracle/product/19.0.0.0/dbhome_11/rdbms/log
    OPATCH_SCRIPT_DIR              /u02/app/oracle/product/19.0.0.0/dbhome_11/QOpatch
    ORACLE_BASE                    /u02/app/oracle
    ORACLE_HOME                    /u02/app/oracle/product/19.0.0.0/dbhome_45
    ORACLE_OCM_CONFIG_DIR          /u02/app/oracle/product/19.0.0.0/dbhome_45/ccr/state
    ORACLE_OCM_CONFIG_DIR2         /u02/app/oracle/product/19.0.0.0/dbhome_45/ccr/state
    SDO_DIR_ADMIN                  /u02/app/oracle/product/19.0.0.0/dbhome_45/md/admin
    SDO_DIR_WORKXMLDIR             /u02/app/oracle/product/19.0.0.0/dbhome_45/rdbms/xml
    XSDDIR                         /u02/app/oracle/product/19.0.0.0/dbhome_45/rdbms/xml/schema
    
    
    Choose a Directory Name from the above list (case-sensitive).
    
    Enter value for directory_name: GR_AWRDUMP
    
    Using the dump directory: GR_AWRDUMP
    
    Specify the Name of the Extract Dump File
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    The prefix for the default dump file name is awrdat_1_21.
    To use this name, press <return> to continue, otherwise enter
    an alternative.
    
    Enter value for file_name:
    
    Using the dump file prefix: awrdat_1_21
    |
    | ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    |  The AWR extract dump file will be located
    |  in the following directory/file:
    |   /acfs01/acfs/GR_AWRDUMP
    |   awrdat_1_21.dmp
    | ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    |
    |  *** AWR Extract Started ...
    |
    |  This operation will take a few moments. The
    |  progress of the AWR extract operation can be
    |  monitored in the following directory/file:
    |   /acfs01/acfs/GR_AWRDUMP
    |   awrdat_1_21.log
    |
    
    End of AWR Extract

Reviewed: 01/22/26

## License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details. 

Reviewed 30/10/2024
