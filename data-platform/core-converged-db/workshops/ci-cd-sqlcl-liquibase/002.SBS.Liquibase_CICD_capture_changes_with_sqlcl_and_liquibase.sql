a. Download the latest version of SqlCL:

https://download.oracle.com/otn_software/java/sqldeveloper/sqlcl-latest.zip

ssh -i /Users/stef/Documents/TSE/Workshops/010.Liquibase_CICD/SSH/id_rsa_lab opc@132.226.192.249

sudo su - oracle

cd /home/oracle

wget https://download.oracle.com/otn_software/java/sqldeveloper/sqlcl-latest.zip

--2023-04-21 07:33:35--  https://download.oracle.com/otn_software/java/sqldeveloper/sqlcl-latest.zip
Resolving download.oracle.com (download.oracle.com)... 104.111.216.80
Connecting to download.oracle.com (download.oracle.com)|104.111.216.80|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: 39744160 (38M) [application/zip]
Saving to: ‘sqlcl-latest.zip’

sqlcl-latest.zip                   100%[==============================================================>]  37.90M   116MB/s    in 0.3s

2023-04-21 07:33:36 (116 MB/s) - ‘sqlcl-latest.zip’ saved [39744160/39744160]

[oracle@myoracledb1 ~]$ ls -ltr
total 57432
drwxr-xr-x. 2 oracle oinstall        6 Sep 13  2021 Templates
drwxr-xr-x. 2 oracle oinstall        6 Sep 13  2021 Public
drwxr-xr-x. 2 oracle oinstall        6 Sep 13  2021 Pictures
drwxr-xr-x. 2 oracle oinstall        6 Sep 13  2021 Music
drwxr-xr-x. 2 oracle oinstall        6 Sep 13  2021 Videos
drwxr-xr-t. 2 oracle oinstall        6 Sep 24  2021 thinclient_drives
drwxr-xr-x. 4 oracle oinstall       59 Nov 26  2021 Documents
-rw-r--r--. 1 oracle oinstall  6871854 Dec  7  2021 liquibase-4.3.2.tar.gz
drwxr-xr-x. 4 oracle oinstall     4096 Dec 20  2021 Downloads
-rwxr-xr-x. 1 oracle oinstall      936 Feb 22  2022 InitialDBConfig.sh
drwxr-xr-x. 2 oracle oinstall       27 Jan 31 14:25 DATAPUMP
-rw-r--r--. 1 oracle oinstall      175 Jan 31 14:40 OH.env
-rw-r--r--. 1 oracle oinstall 39744160 Apr  4 16:01 sqlcl-latest.zip
drwxr-xr-x. 3 oracle oinstall       21 Apr 20 09:12 Desktop
-rw-r--r--. 1 oracle oinstall 12172994 Apr 20 09:51 v23.1.zip
drwxr-xr-x. 2 oracle oinstall        6 Apr 20 10:02 logs
drwxr-xr-x. 7 oracle oinstall      209 Apr 20 10:13 db-sample-schemas-23.1
-rw-r--r--. 1 oracle oinstall     3396 Apr 20 12:08 hr_install.log
drwxr-xr-x. 5 oracle oinstall      231 Apr 20 14:54 liquibase4.3.2
drwxr-xr-x. 3 oracle oinstall       63 Apr 20 15:51 cicd-ws-rep00
[oracle@myoracledb1 ~]$

unzip /home/oracle/sqlcl-latest.zip -d /opt/oracle/
ln -s /opt/oracle/sqlcl/bin/sql /home/oracle/.local/bin/sql

-- Install java 11:

sudo yum install java

Last metadata expiration check: 0:36:23 ago on Fri 21 Apr 2023 07:00:35 AM GMT.
Package java-1.8.0-openjdk-1:1.8.0.302.b08-0.el8_4.x86_64 is already installed.
Dependencies resolved.
==========================================================================================================================================
 Package                        Architecture              Version                               Repository                           Size
==========================================================================================================================================
Installing dependencies:
 jdk-11.0.10                    x86_64                    2000:11.0.10-ga                       ol8_oci_included                    156 M

Transaction Summary
==========================================================================================================================================
Install  1 Package

Total download size: 156 M
Installed size: 292 M
Is this ok [y/N]: y
Downloading Packages:
jdk-11.0.10+8_linux-x64_bin.rpm                                                                            43 MB/s | 156 MB     00:03
------------------------------------------------------------------------------------------------------------------------------------------
Total                                                                                                      43 MB/s | 156 MB     00:03
Running transaction check
Transaction check succeeded.
Running transaction test
Transaction test succeeded.
Running transaction
  Preparing        :                                                                                                                  1/1
  Installing       : jdk-11.0.10-2000:11.0.10-ga.x86_64                                                                               1/1
  Running scriptlet: jdk-11.0.10-2000:11.0.10-ga.x86_64                                                                               1/1
  Verifying        : jdk-11.0.10-2000:11.0.10-ga.x86_64                                                                               1/1

Installed:
  jdk-11.0.10-2000:11.0.10-ga.x86_64

Complete!

-- Test sqlcl:



SQLcl: Release 23.1 Production on Fri Apr 21 07:38:18 2023

Copyright (c) 1982, 2023, Oracle.  All rights reserved.

SQL>

-- Connect to HR schema:

SQL> connect hr/Oracle_4U@localhost:1521/freepdb1
Connected.

-- Verify HR's tables:

SQL> tables

TABLES
______________
REGIONS
COUNTRIES
LOCATIONS
DEPARTMENTS
JOBS
EMPLOYEES
JOB_HISTORY

7 rows selected.

-- Verify liquibase version:

SQL> lb version
--Starting Liquibase at 07:40:34 (version 4.17.0 #0 built at 2022-11-02 21:48+0000)

Liquibase version:    4.17.0 #0 built at 2022-11-02 21:48+0000
Extension Version:   23.1.0.0/23.1.37-090300


Operation completed successfully.

-- To display a list of all available commands, execute liquibase or lb with no arguments. 

lb

  Usage:
  Liquibase|lb COMMAND {OPTIONS}
  Liquibase|lb  help|he [-example|-ex]
  Liquibase|lb  help|he COMMAND [-syntax|-sy] [-example|-ex]
[...]

exit

Task 2: Capture initial schema and code
***************************************

cd /home/oracle/cicd-ws-rep00
mkdir v1.0
cd v1.0

[oracle@myoracledb1 v1.0]$ pwd
/home/oracle/cicd-ws-rep00/v1.0

-- Capture the HR schema:

sql /nolog
connect hr/Oracle_4U@localhost:1521/freepdb1

SQL> lb genschema

The entered command used deprecated syntax, support for this will be removed in the future.
Old Syntax: lb genschema
New Syntax: lb generate-schema

--Starting Liquibase at 07:44:22 (version 4.17.0 #0 built at 2022-11-02 21:48+0000)


Export Flags Used:

Export Grants		false
Export Synonyms		false

[Method loadCaptureTable]:
	[Type - TYPE_SPEC]:                        509 ms
	[Type - TYPE_BODY]:                        197 ms
	[Type - SEQUENCE]:                         231 ms
	[Type - DIRECTORY]:                         74 ms
	[Type - CLUSTER]:                         4995 ms
	[Type - TABLE]:                          45293 ms
	[Type - MATERIALIZED_VIEW_LOG]:            188 ms
	[Type - MATERIALIZED_VIEW]:                 42 ms
	[Type - VIEW]:                            2669 ms
	[Type - DIMENSION]:                         69 ms
	[Type - FUNCTION]:                         144 ms
	[Type - PROCEDURE]:                        186 ms
	[Type - PACKAGE_SPEC]:                     141 ms
	[Type - DB_LINK]:                           72 ms
	[Type - SYNONYM]:                           77 ms
	[Type - INDEX]:                           3021 ms
	[Type - TRIGGER]:                          197 ms
	[Type - PACKAGE_BODY]:                     148 ms
	[Type - JOB]:                               79 ms

[Method loadCaptureTable]:                       58332 ms
[Method processCaptureTable]:                     6112 ms
[Method cleanupCaptureTable]:                     3375 ms
[Method sortCaptureTable]:                          46 ms
[Method writeChangeLogs]:                           89 ms



Operation completed successfully.

-- From another terminal:

[opc@myoracledb1 ~]$ sudo su - oracle
Last login: Fri Apr 21 07:33:13 GMT 2023 on pts/0
[oracle@myoracledb1 ~]$ cd /home/oracle/cicd-ws-rep00
[oracle@myoracledb1 cicd-ws-rep00]$

-- Review initial changelog generated by Liquibase

vi v1.0/controller.xml

-- Run the following bash commands to set the relative path in initial changelog file.

sed -i -e 's/file="/file=".\//g' v1.0/controller.xml
sed -i -e 's/\/>/ relativeToChangelogFile="true"\/>/g' v1.0/controller.xml

-- In cicd-ws-rep00 folder, create a Liquibase master changelog to reference other changelogs in your project. 
-- The master changelog is used to break up your entire changelog into more manageable pieces, by creating multiple changelogs 
-- to separate your changesets in a way that makes sense for your project.

cat << EOF > hr-master.xml
<?xml version="1.1" encoding="UTF-8"?>
<databaseChangeLog
  xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
                      http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-4.1.xsd">
  <include file="./v1.0/controller.xml" relativeToChangelogFile="true"/>
  <changeSet  author="Developer1"  id="tagDatabase-v1">  
    <tagDatabase  tag="version_1.0"/>  
  </changeSet>
</databaseChangeLog>
EOF

-- From SQLcl, validate your master changelog. Remember you are now in sub-folder v1.0.

SQL> !pwd
/home/oracle/cicd-ws-rep00/v1.0

SQL> lb validate -changelog ./../hr-master.xml

The entered command used deprecated syntax, support for this will be removed in the future.
Old Syntax: lb validate -changelog ./../hr-master.xml
New Syntax: lb validate -changelog-file ./../hr-master.xml

--Starting Liquibase at 07:53:14 (version 4.17.0 #0 built at 2022-11-02 21:48+0000)

-- Loaded 37 change(s)
No validation errors found.

Operation completed successfully.

-- Mark all these initial changes as deployed in the local development database, as they belong to the initial HR schema we used for our project.

SQL> lb changelog-sync-sql -changelog-file ./../hr-master.xml
--Starting Liquibase at 08:06:32 (version 4.17.0 #0 built at 2022-11-02 21:48+0000)

-- Loaded 37 change(s)
-- *********************************************************************
-- SQL to add all changesets to database history table
-- *********************************************************************
-- Change Log: ./../hr-master.xml
-- Ran at: 4/21/23, 8:06 AM
-- Against: HR@jdbc:oracle:thin:@localhost:1521/freepdb1
-- Liquibase version: 4.17.0
-- *********************************************************************

-- Lock Database
UPDATE HR.DATABASECHANGELOGLOCK SET LOCKED = 1, LOCKEDBY = '172.17.0.1 (172.17.0.1)', LOCKGRANTED = SYSTIMESTAMP WHERE ID = 1 AND LOCKED = 0;

-- Release Database Lock
UPDATE HR.DATABASECHANGELOGLOCK SET LOCKED = 0, LOCKEDBY = NULL, LOCKGRANTED = NULL WHERE ID = 1;

Operation completed successfully.

-- Run the previous commands, and commit changes.

SQL> UPDATE HR.DATABASECHANGELOGLOCK SET LOCKED = 1, LOCKEDBY = '172.17.0.1 (172.17.0.1)', LOCKGRANTED = SYSTIMESTAMP WHERE ID = 1 AND LOCKED = 0;

1 row updated.

SQL> UPDATE HR.DATABASECHANGELOGLOCK SET LOCKED = 0, LOCKEDBY = NULL, LOCKGRANTED = NULL WHERE ID = 1;

1 row updated.

SQL> commit;

Commit complete.

-- see changes currently recorded by Liquibase. DATABASECHANGELOG table tracks which changesets have been run in your database schema.

SQL> select ID, AUTHOR, FILENAME, orderexecuted ORD, DESCRIPTION, TAG, EXECTYPE
from DATABASECHANGELOG order by 4 desc;

ID                                          AUTHOR            FILENAME                                      ORD DESCRIPTION                                                          TAG            EXECTYPE
___________________________________________ _________________ __________________________________________ ______ ____________________________________________________________________ ______________ ___________
tagDatabase-v1                              Developer1        ../hr-master.xml                               37 tagDatabase                                                          version_1.0    EXECUTED
5c3de07805546665ea5f89a9da6248912e422dd8    (HR)-Generated    ../v1.0/departments_ref_constraints.xml        36 createOracleRefConstraint objectName=DEPT_LOC_FK, ownerName=HR                      EXECUTED
7bcd599b071b53f135b9774904ed72ded351fc87    (HR)-Generated    ../v1.0/employees_ref_constraints.xml          35 createOracleRefConstraint objectName=EMP_DEPT_FK, ownerName=HR                      EXECUTED
0021967c3f65cc4ae98db87a67c3c6d4d5f6d927    (HR)-Generated    ../v1.0/departments_comments.xml               34 createOracleComment objectName=DEPARTMENTS_COMMENTS, ownerName=HR                   EXECUTED
c1d5af882c57ec1843cd76d62e0c98bd241ecfee    (HR)-Generated    ../v1.0/regions_comments.xml                   33 createOracleComment objectName=REGIONS_COMMENTS, ownerName=HR                       EXECUTED
3e1cbd6678c4ccd8ce8e58bbe93972a650c36f97    (HR)-Generated    ../v1.0/jobs_comments.xml                      32 createOracleComment objectName=JOBS_COMMENTS, ownerName=HR                          EXECUTED
10401b775a504e30632f69c526f6c2e0f9407481    (HR)-Generated    ../v1.0/job_history_comments.xml               31 createOracleComment objectName=JOB_HISTORY_COMMENTS, ownerName=HR                   EXECUTED
456d4fb4a910bca941e8657a9a31e33f1ab4cd3c    (HR)-Generated    ../v1.0/employees_comments.xml                 30 createOracleComment objectName=EMPLOYEES_COMMENTS, ownerName=HR                     EXECUTED
abee54702a80b0ef3de339057f8888f784d6c795    (HR)-Generated    ../v1.0/locations_comments.xml                 29 createOracleComment objectName=LOCATIONS_COMMENTS, ownerName=HR                     EXECUTED
6969594a15c66b1c78e3645988e841f7097ba242    (HR)-Generated    ../v1.0/countries_comments.xml                 28 createOracleComment objectName=COUNTRIES_COMMENTS, ownerName=HR                     EXECUTED
70aedb1927b7de9129c6614a3b0b65371ccd8dbc    (HR)-Generated    ../v1.0/update_job_history_trigger.xml         27 createOracleTrigger objectName=UPDATE_JOB_HISTORY, ownerName=HR                     EXECUTED
f6acef9bdfcf96da9691d863ddcd83ee3358034a    (HR)-Generated    ../v1.0/secure_employees_trigger.xml           26 createOracleTrigger objectName=SECURE_EMPLOYEES, ownerName=HR                       EXECUTED
c127f9e94d93f5acda2af24f693bba606d76a244    (HR)-Generated    ../v1.0/dept_location_ix_index.xml             25 createSxmlObject objectName=DEPT_LOCATION_IX, ownerName=HR                          EXECUTED
70b9d8f74b7262e911d32c43e2daac2bacbba29a    (HR)-Generated    ../v1.0/emp_name_ix_index.xml                  24 createSxmlObject objectName=EMP_NAME_IX, ownerName=HR                               EXECUTED
8354362383fb7c8489aaa426489a5fe96d7eb134    (HR)-Generated    ../v1.0/emp_manager_ix_index.xml               23 createSxmlObject objectName=EMP_MANAGER_IX, ownerName=HR                            EXECUTED
7a8e2352305d3ce3d5a3505d0656bb24ec1e0f96    (HR)-Generated    ../v1.0/emp_email_uk_index.xml                 22 createSxmlObject objectName=EMP_EMAIL_UK, ownerName=HR                              EXECUTED
d73832cfccb9d32aa975a224f2b58cf3efeb5f3f    (HR)-Generated    ../v1.0/emp_job_ix_index.xml                   21 createSxmlObject objectName=EMP_JOB_IX, ownerName=HR                                EXECUTED
4f3fd64504441fdee039736861b8dcd752a6fea1    (HR)-Generated    ../v1.0/jhist_department_ix_index.xml          20 createSxmlObject objectName=JHIST_DEPARTMENT_IX, ownerName=HR                       EXECUTED
b5ce40efc7680b82b1baf63f1100d896967d8665    (HR)-Generated    ../v1.0/loc_city_ix_index.xml                  19 createSxmlObject objectName=LOC_CITY_IX, ownerName=HR                               EXECUTED
7d9a155cc4de6e35746bebaace41d8ed973ddd93    (HR)-Generated    ../v1.0/jhist_employee_ix_index.xml            18 createSxmlObject objectName=JHIST_EMPLOYEE_IX, ownerName=HR                         EXECUTED
9687423a8444cbd4d826963e26f32f030c9933f7    (HR)-Generated    ../v1.0/emp_department_ix_index.xml            17 createSxmlObject objectName=EMP_DEPARTMENT_IX, ownerName=HR                         EXECUTED
b0783ced5928aa9b6811ffe0d2b4dd765840716c    (HR)-Generated    ../v1.0/loc_state_province_ix_index.xml        16 createSxmlObject objectName=LOC_STATE_PROVINCE_IX, ownerName=HR                     EXECUTED
32f76f8ab196f65c5b8ae0c921831c6a7ebc640c    (HR)-Generated    ../v1.0/jhist_job_ix_index.xml                 15 createSxmlObject objectName=JHIST_JOB_IX, ownerName=HR                              EXECUTED
3718348046bdc485651c8286206b48e9af519461    (HR)-Generated    ../v1.0/loc_country_ix_index.xml               14 createSxmlObject objectName=LOC_COUNTRY_IX, ownerName=HR                            EXECUTED
d92d897ec98ec5c2679d8cd01f0485fddd55451a    (HR)-Generated    ../v1.0/add_job_history_procedure.xml          13 createOracleProcedure objectName=ADD_JOB_HISTORY, ownerName=HR                      EXECUTED
76a219c8b2af11bf7c23e55e52573a4f1c99299b    (HR)-Generated    ../v1.0/emp_details_view_view.xml              12 createSxmlObject objectName=EMP_DETAILS_VIEW, ownerName=HR                          EXECUTED
dc533e0b14fa41e54d49cb28c42ff31a3186009e    (HR)-Generated    ../v1.0/job_history_table.xml                  11 createSxmlObject objectName=JOB_HISTORY, ownerName=HR                               EXECUTED
ad2c536c5636ec056d11ce44b28f4e55807cbd12    (HR)-Generated    ../v1.0/locations_table.xml                    10 createSxmlObject objectName=LOCATIONS, ownerName=HR                                 EXECUTED
1dacbd3ff0b3ae34e48d5df9ab3ca052f3995c33    (HR)-Generated    ../v1.0/countries_table.xml                     9 createSxmlObject objectName=COUNTRIES, ownerName=HR                                 EXECUTED
5b8196cf470dfee2036694421aaddff307008907    (HR)-Generated    ../v1.0/secure_dml_procedure.xml                8 createOracleProcedure objectName=SECURE_DML, ownerName=HR                           EXECUTED
52334f421d935229140b0468d06157dd45c20f96    (HR)-Generated    ../v1.0/regions_table.xml                       7 createSxmlObject objectName=REGIONS, ownerName=HR                                   EXECUTED
84d6c14a5af0d22812c689a42e58e6c0cf300c1e    (HR)-Generated    ../v1.0/jobs_table.xml                          6 createSxmlObject objectName=JOBS, ownerName=HR                                      EXECUTED
3679094045b7965245949695613df9351c236f3e    (HR)-Generated    ../v1.0/employees_table.xml                     5 createSxmlObject objectName=EMPLOYEES, ownerName=HR                                 EXECUTED

ID                                          AUTHOR            FILENAME                                   ORD DESCRIPTION                                                  TAG    EXECTYPE
___________________________________________ _________________ _______________________________________ ______ ____________________________________________________________ ______ ___________
18f3f88289eddcfc2b16fdae44a17169f8fe0d3f    (HR)-Generated    ../v1.0/departments_table.xml                4 createSxmlObject objectName=DEPARTMENTS, ownerName=HR               EXECUTED
42e3db1348e500dade36829bab3b7f5343ad6f09    (HR)-Generated    ../v1.0/employees_seq_sequence.xml           3 createSxmlObject objectName=EMPLOYEES_SEQ, ownerName=HR             EXECUTED
93020a4f5c3fc570029b0695d52763142b6e44e1    (HR)-Generated    ../v1.0/departments_seq_sequence.xml         2 createSxmlObject objectName=DEPARTMENTS_SEQ, ownerName=HR           EXECUTED
7ec49fad51eb8c0b53fa0128bf6ef2d3fee25d35    (HR)-Generated    ../v1.0/locations_seq_sequence.xml           1 createSxmlObject objectName=LOCATIONS_SEQ, ownerName=HR             EXECUTED

37 rows selected.

-- Add initial schema changes to the Git repository. Use the second Terminal window tab to run these bash commands in cicd-ws-rep00 folder.

export PATH=$PATH:/usr/local/git/bin
git add v1.0/*

*/

git add hr-master.xml
git commit -a -m "Version 1: Add initial HR schema changelog including code"

[main 3ee6f21] Version 1: Add initial HR schema changelog including code
 38 files changed, 2022 insertions(+)
 create mode 100644 hr-master.xml
 create mode 100644 v1.0/add_job_history_procedure.xml
 create mode 100644 v1.0/controller.xml
 create mode 100644 v1.0/countries_comments.xml
 create mode 100644 v1.0/countries_table.xml
 create mode 100644 v1.0/departments_comments.xml
 create mode 100644 v1.0/departments_ref_constraints.xml
 create mode 100644 v1.0/departments_seq_sequence.xml
 create mode 100644 v1.0/departments_table.xml
 create mode 100644 v1.0/dept_location_ix_index.xml
 create mode 100644 v1.0/emp_department_ix_index.xml
 create mode 100644 v1.0/emp_details_view_view.xml
 create mode 100644 v1.0/emp_email_uk_index.xml
 create mode 100644 v1.0/emp_job_ix_index.xml
 create mode 100644 v1.0/emp_manager_ix_index.xml
 create mode 100644 v1.0/emp_name_ix_index.xml
 create mode 100644 v1.0/employees_comments.xml
 create mode 100644 v1.0/employees_ref_constraints.xml
 create mode 100644 v1.0/employees_seq_sequence.xml
 create mode 100644 v1.0/employees_table.xml
 create mode 100644 v1.0/jhist_department_ix_index.xml
 create mode 100644 v1.0/jhist_employee_ix_index.xml
 create mode 100644 v1.0/jhist_job_ix_index.xml
 create mode 100644 v1.0/job_history_comments.xml
 create mode 100644 v1.0/job_history_table.xml
 create mode 100644 v1.0/jobs_comments.xml
 create mode 100644 v1.0/jobs_table.xml
 create mode 100644 v1.0/loc_city_ix_index.xml
 create mode 100644 v1.0/loc_country_ix_index.xml
 create mode 100644 v1.0/loc_state_province_ix_index.xml
 create mode 100644 v1.0/locations_comments.xml
 create mode 100644 v1.0/locations_seq_sequence.xml
 create mode 100644 v1.0/locations_table.xml
 create mode 100644 v1.0/regions_comments.xml
 create mode 100644 v1.0/regions_table.xml
 create mode 100644 v1.0/secure_dml_procedure.xml
 create mode 100644 v1.0/secure_employees_trigger.xml
 create mode 100644 v1.0/update_job_history_trigger.xml


git push

Username for 'https://github.com': stephane-duprat
Password for 'https://stephane-duprat@github.com': 
Enumerating objects: 42, done.
Counting objects: 100% (42/42), done.
Delta compression using up to 4 threads
Compressing objects: 100% (41/41), done.
Writing objects: 100% (41/41), 14.37 KiB | 2.88 MiB/s, done.
Total 41 (delta 28), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (28/28), done.
To https://github.com/stephane-duprat/cicd-ws-rep00.git
   3839863..3ee6f21  main -> main
[oracle@myoracledb1 cicd-ws-rep00]$


Task 3: Create new database objects and stored code
***************************************************

-- Connect to HR schema and change the data model: from terminal 2

sql hr/Oracle_4U@localhost:1521/freepdb1

create table PROSPECTS as
(select EMPLOYEE_ID as PERSON_ID, FIRST_NAME, LAST_NAME, lower(EMAIL) || '@example.com' as EMAIL,
        PHONE_NUMBER, add_months(HIRE_DATE,-120) as BIRTH_DATE, SALARY * 10 as SAVINGS from HR.EMPLOYEES);

CREATE OR REPLACE PACKAGE investment_check AS
    TYPE check_record IS RECORD(
       id PROSPECTS.PERSON_ID%TYPE,
       first_name PROSPECTS.FIRST_NAME%TYPE,
       last_name PROSPECTS.LAST_NAME%TYPE,
       investment_limit NUMBER);
    TYPE check_table IS TABLE OF check_record;
    FUNCTION get_limits(check_limit NUMBER)
        RETURN check_table
        PIPELINED;
END;
/
CREATE OR REPLACE PACKAGE BODY investment_check AS
    FUNCTION get_limits(check_limit number)
        RETURN check_table
        PIPELINED IS
        l_rec check_record;
    BEGIN
        FOR l_rec IN (
          select PERSON_ID, FIRST_NAME, LAST_NAME, 3*SAVINGS as INVESTMENT_LIMIT
          from PROSPECTS
          where 3*SAVINGS >= check_limit)
        LOOP
          PIPE ROW (l_rec);
        END LOOP;
        RETURN;
    END get_limits;
END;
/

SQL> SELECT * FROM table(investment_check.get_limits(350000));

    ID FIRST_NAME    LAST_NAME       INVESTMENT_LIMIT
______ _____________ ____________ ___________________
   100 Steven        King                      720000
   101 Neena         Yang                      510000
   102 Lex           Garcia                    510000
   108 Nancy         Gruenberg                 360240
   145 John          Singh                     420000
   146 Karen         Partners                  405000
   147 Alberto       Errazuriz                 360000
   201 Michael       Martinez                  390000
   205 Shelley       Higgins                   360240

9 rows selected.

exit

cd /home/oracle/cicd-ws-rep00
[oracle@myoracledb1 cicd-ws-rep00]$ mkdir v2.0
[oracle@myoracledb1 cicd-ws-rep00]$ cd v2.0
[oracle@myoracledb1 v2.0]$ pwd
/home/oracle/cicd-ws-rep00/v2.0

sql /nolog
connect hr/Oracle_4U@localhost:1521/freepdb1

-- Use SQLcl connection in the Terminal window first tab to generate changelogs for each one of the new objects individually (run these commands one by one).

SQL> lb genobject -type table -name PROSPECTS

The entered command used deprecated syntax, support for this will be removed in the future.
Old Syntax: lb genobject -type table -name PROSPECTS
New Syntax: lb generate-object -object-type table -object-name PROSPECTS

--Starting Liquibase at 08:26:26 (version 4.17.0 #0 built at 2022-11-02 21:48+0000)

Changelog created and written out to file prospects_table.xml

Operation completed successfully.

SQL> lb genobject -type PACKAGE_SPEC -name investment_check

The entered command used deprecated syntax, support for this will be removed in the future.
Old Syntax: lb genobject -type PACKAGE_SPEC -name investment_check
New Syntax: lb generate-object -object-type PACKAGE_SPEC -object-name investment_check

--Starting Liquibase at 08:27:15 (version 4.17.0 #0 built at 2022-11-02 21:48+0000)

Changelog created and written out to file investment_check_package_spec.xml

Operation completed successfully.

SQL> lb genobject -type PACKAGE_BODY -name investment_check

The entered command used deprecated syntax, support for this will be removed in the future.
Old Syntax: lb genobject -type PACKAGE_BODY -name investment_check
New Syntax: lb generate-object -object-type PACKAGE_BODY -object-name investment_check

--Starting Liquibase at 08:27:39 (version 4.17.0 #0 built at 2022-11-02 21:48+0000)

Changelog created and written out to file investment_check_package_body.xml

Operation completed successfully.

exit

-- Update master changelog hr-master.xml to include the latest objects and code, specifying this is the second version of the project.

cat << EOF > /home/oracle/cicd-ws-rep00/hr-master.xml
<?xml version="1.1" encoding="UTF-8"?>
<databaseChangeLog
  xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
                      http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-4.1.xsd">
  <include file="./v1.0/controller.xml" relativeToChangelogFile="true"/>
  <changeSet  author="Developer1"  id="tagDatabase-v1">  
    <tagDatabase  tag="version_1.0"/>  
  </changeSet>
  <include file="./v2.0/prospects_table.xml" relativeToChangelogFile="true"/>
  <include file="./v2.0/investment_check_package_spec.xml" relativeToChangelogFile="true"/>
  <include file="./v2.0/investment_check_package_body.xml" relativeToChangelogFile="true"/>
  <changeSet  author="Developer2"  id="tagDatabase-v2">  
    <tagDatabase  tag="version_2.0"/>  
  </changeSet>
</databaseChangeLog>
EOF

--- Validate your hr-master.xml file:

sql /nolog
connect hr/Oracle_4U@localhost:1521/freepdb1

SQL> !pwd
/home/oracle/cicd-ws-rep00/v2.0

SQL> lb validate -changelog-file ./../hr-master.xml
--Starting Liquibase at 08:34:44 (version 4.17.0 #0 built at 2022-11-02 21:48+0000)

-- Loaded 41 change(s)
No validation errors found.

Operation completed successfully.

SQL>

-- Mark all these initial changes as deployed in the local development database.

lb changelog-sync-sql -changelog-file ./../hr-master.xml

--Starting Liquibase at 08:36:16 (version 4.17.0 #0 built at 2022-11-02 21:48+0000)

-- Loaded 41 change(s)
-- *********************************************************************
-- SQL to add all changesets to database history table
-- *********************************************************************
-- Change Log: ./../hr-master.xml
-- Ran at: 4/21/23, 8:36 AM
-- Against: HR@jdbc:oracle:thin:@localhost:1521/freepdb1
-- Liquibase version: 4.17.0
-- *********************************************************************

-- Lock Database
UPDATE HR.DATABASECHANGELOGLOCK SET LOCKED = 1, LOCKEDBY = '172.17.0.1 (172.17.0.1)', LOCKGRANTED = SYSTIMESTAMP WHERE ID = 1 AND LOCKED = 0;

INSERT INTO HR.DATABASECHANGELOG (ID, AUTHOR, FILENAME, DATEEXECUTED, ORDEREXECUTED, MD5SUM, DESCRIPTION, COMMENTS, EXECTYPE, CONTEXTS, LABELS, LIQUIBASE, DEPLOYMENT_ID) VALUES ('542996f24b29997df8b2a831d71597285b4f998a', '(HR)-Generated', '../v2.0/prospects_table.xml', SYSTIMESTAMP, 38, '8:e7492a0170a4661e525b651a006f4ab0', 'createSxmlObject objectName=PROSPECTS, ownerName=HR', '', 'EXECUTED', NULL, NULL, '4.17.0', '2066177577');

-- Logging Oracle Liquibase extension actions to
 DECLARE
 id varchar2(2000) := '542996f24b29997df8b2a831d71597285b4f998a';
 status varchar2(2000) := 'PREPARING';
 rawAction clob;
 rawSxml clob;
 myrow varchar2(2000);
 action clob := '';
 sxml clob := '';
 dep varchar2(2000) := '2066177577';
 author varchar2(2000) := '(HR)-Generated';
 filename varchar2(2000) := '../v2.0/prospects_table.xml';
 insertlog varchar2(2000) := 'insert into HR.DATABASECHANGELOG_ACTIONS (id,author,filename,sql,sxml,deployment_id,status) values (:id,:author,:filename,:action,:sxml,:dep,:status) returning rowid into :out';
 updateaction varchar2(2000) := 'update HR.DATABASECHANGELOG_ACTIONS set sql = sql ||:action where rowid = :myrow ';
 updatesxml varchar2(2000) := 'update HR.DATABASECHANGELOG_ACTIONS set sxml = sxml ||:sxml where rowid = :myrow ';
 begin
action := utl_raw.cast_to_varchar2(utl_encode.base64_decode(utl_raw.cast_to_raw(q'{LS0gb2JqZWN0IGlzIHRoZSBzYW1lIG5vdGhpbmcgdG8gZG8=}')));
sxml := utl_raw.cast_to_varchar2(utl_encode.base64_decode(utl_raw.cast_to_raw(q'{CiAgPFRBQkxFIHhtbG5zPSJodHRwOi8veG1sbnMub3JhY2xlLmNvbS9rdSIgdmVyc2lvbj0iMS4wIj4KICAgPFNDSEVNQT5IUjwvU0NIRU1BPgogICA8TkFNRT5QUk9TUEVDVFM8L05BTUU+CiAgIDxSRUxBVElPTkFMX1RBQkxFPgogICAgICA8Q09MX0xJU1Q+CiAgICAgICAgIDxDT0xfTElTVF9JVEVNPgogICAgICAgICAgICA8TkFNRT5QRVJTT05fSUQ8L05BTUU+CiAgICAgICAgICAgIDxEQVRBVFlQRT5OVU1CRVI8L0RBVEFUWVBFPgogICAgICAgICAgICA8UFJFQ0lTSU9OPjY8L1BSRUNJU0lPTj4KICAgICAgICAgICAgPFNDQUxFPjA8L1NDQUxFPgogICAgICAgICA8L0NPTF9MSVNUX0lURU0+CiAgICAgICAgIDxDT0xfTElTVF9JVEVNPgogICAgICAgICAgICA8TkFNRT5GSVJTVF9OQU1FPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+VkFSQ0hBUjI8L0RBVEFUWVBFPgogICAgICAgICAgICA8TEVOR1RIPjIwPC9MRU5HVEg+CiAgICAgICAgICAgIDxDT0xMQVRFX05BTUU+VVNJTkdfTkxTX0NPTVA8L0NPTExBVEVfTkFNRT4KICAgICAgICAgPC9DT0xfTElTVF9JVEVNPgogICAgICAgICA8Q09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgPE5BTUU+TEFTVF9OQU1FPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+VkFSQ0hBUjI8L0RBVEFUWVBFPgogICAgICAgICAgICA8TEVOR1RIPjI1PC9MRU5HVEg+CiAgICAgICAgICAgIDxDT0xMQVRFX05BTUU+VVNJTkdfTkxTX0NPTVA8L0NPTExBVEVfTkFNRT4KICAgICAgICAgICAgPE5PVF9OVUxMPjwvTk9UX05VTEw+CiAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgICAgPENPTF9MSVNUX0lURU0+CiAgICAgICAgICAgIDxOQU1FPkVNQUlMPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+VkFSQ0hBUjI8L0RBVEFUWVBFPgogICAgICAgICAgICA8TEVOR1RIPjM3PC9MRU5HVEg+CiAgICAgICAgICAgIDxDT0xMQVRFX05BTUU+VVNJTkdfTkxTX0NPTVA8L0NPTExBVEVfTkFNRT4KICAgICAgICAgPC9DT0xfTElTVF9JVEVNPgogICAgICAgICA8Q09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgPE5BTUU+UEhPTkVfTlVNQkVSPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+VkFSQ0hBUjI8L0RBVEFUWVBFPgogICAgICAgICAgICA8TEVOR1RIPjIwPC9MRU5HVEg+CiAgICAgICAgICAgIDxDT0xMQVRFX05BTUU+VVNJTkdfTkxTX0NPTVA8L0NPTExBVEVfTkFNRT4KICAgICAgICAgPC9DT0xfTElTVF9JVEVNPgogICAgICAgICA8Q09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgPE5BTUU+QklSVEhfREFURTwvTkFNRT4KICAgICAgICAgICAgPERBVEFUWVBFPkRBVEU8L0RBVEFUWVBFPgogICAgICAgICA8L0NPTF9MSVNUX0lURU0+CiAgICAgICAgIDxDT0xfTElTVF9JVEVNPgogICAgICAgICAgICA8TkFNRT5TQVZJTkdTPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+TlVNQkVSPC9EQVRBVFlQRT4KICAgICAgICAgPC9DT0xfTElTVF9JVEVNPgogICAgICA8L0NPTF9MSVNUPgogICAgICA8REVGQVVMVF9DT0xMQVRJT04+VVNJTkdfTkxTX0NPTVA8L0RFRkFVTFRfQ09MTEFUSU9OPgogICAgICA8UEhZU0lDQUxfUFJPUEVSVElFUz4KICAgICAgICAgPEhFQVBfVEFCTEU+CiAgICAgICAgICAgIDxTRUdNRU5UX0FUVFJJQlVURVM+CiAgICAgICAgICAgICAgIDxTRUdNRU5UX0NSRUFUSU9OX0lNTUVESUFURT48L1NFR01FTlRfQ1JFQVRJT05fSU1NRURJQVRFPgogICAgICAgICAgICAgICA8UENURlJFRT4xMDwvUENURlJFRT4KICAgICAgICAgICAgICAgPFBDVFVTRUQ+NDA8L1BDVFVTRUQ+CiAgICAgICAgICAgICAgIDxJTklUUkFOUz4xPC9JTklUUkFOUz4KICAgICAgICAgICAgICAgPE1BWFRSQU5TPjI1NTwvTUFYVFJBTlM+CiAgICAgICAgICAgICAgIDxTVE9SQUdFPgogICAgICAgICAgICAgICAgICA8SU5JVElBTD42NTUzNjwvSU5JVElBTD4KICAgICAgICAgICAgICAgICAgPE5FWFQ+MTA0ODU3NjwvTkVYVD4KICAgICAgICAgICAgICAgICAgPE1JTkVYVEVOVFM+MTwvTUlORVhURU5UUz4KICAgICAgICAgICAgICAgICAgPE1BWEVYVEVOVFM+MjE0NzQ4MzY0NTwvTUFYRVhURU5UUz4KICAgICAgICAgICAgICAgICAgPFBDVElOQ1JFQVNFPjA8L1BDVElOQ1JFQVNFPgogICAgICAgICAgICAgICAgICA8RlJFRUxJU1RTPjE8L0ZSRUVMSVNUUz4KICAgICAgICAgICAgICAgICAgPEZSRUVMSVNUX0dST1VQUz4xPC9GUkVFTElTVF9HUk9VUFM+CiAgICAgICAgICAgICAgICAgIDxCVUZGRVJfUE9PTD5ERUZBVUxUPC9CVUZGRVJfUE9PTD4KICAgICAgICAgICAgICAgICAgPEZMQVNIX0NBQ0hFPkRFRkFVTFQ8L0ZMQVNIX0NBQ0hFPgogICAgICAgICAgICAgICAgICA8Q0VMTF9GTEFTSF9DQUNIRT5ERUZBVUxUPC9DRUxMX0ZMQVNIX0NBQ0hFPgogICAgICAgICAgICAgICA8L1NUT1JBR0U+CiAgICAgICAgICAgICAgIDxUQUJMRVNQQUNFPlVTRVJTPC9UQUJMRVNQQUNFPgogICAgICAgICAgICAgICA8TE9HR0lORz5ZPC9MT0dHSU5HPgogICAgICAgICAgICA8L1NFR01FTlRfQVRUUklCVVRFUz4KICAgICAgICAgICAgPENPTVBSRVNTPk48L0NPTVBSRVNTPgogICAgICAgICA8L0hFQVBfVEFCTEU+CiAgICAgIDwvUEhZU0lDQUxfUFJPUEVSVElFUz4KICAgPC9SRUxBVElPTkFMX1RBQkxFPgo8L1RBQkxFPg==}')));
 execute immediate insertlog using id,author,filename,action,sxml,dep,status returning into myrow;
end;
/

update HR.DATABASECHANGELOG_ACTIONS set status = 'RAN' where id = '542996f24b29997df8b2a831d71597285b4f998a' and sequence = (select max(sequence) from HR.DATABASECHANGELOG_ACTIONS where id = '542996f24b29997df8b2a831d71597285b4f998a');

INSERT INTO HR.DATABASECHANGELOG (ID, AUTHOR, FILENAME, DATEEXECUTED, ORDEREXECUTED, MD5SUM, DESCRIPTION, COMMENTS, EXECTYPE, CONTEXTS, LABELS, LIQUIBASE, DEPLOYMENT_ID) VALUES ('62b4ab1d4ee925059a3bc305ed14d87808ea74ab', '(HR)-Generated', '../v2.0/investment_check_package_spec.xml', SYSTIMESTAMP, 39, '8:5bff9926f8413793d96d7431e6787316', 'createOraclePackageSpec objectName=INVESTMENT_CHECK, ownerName=HR', '', 'EXECUTED', NULL, NULL, '4.17.0', '2066177577');

-- Logging Oracle Liquibase extension actions to
 DECLARE
 id varchar2(2000) := '62b4ab1d4ee925059a3bc305ed14d87808ea74ab';
 status varchar2(2000) := 'PREPARING';
 rawAction clob;
 rawSxml clob;
 myrow varchar2(2000);
 action clob := '';
 sxml clob := '';
 dep varchar2(2000) := '2066177577';
 author varchar2(2000) := '(HR)-Generated';
 filename varchar2(2000) := '../v2.0/investment_check_package_spec.xml';
 insertlog varchar2(2000) := 'insert into HR.DATABASECHANGELOG_ACTIONS (id,author,filename,sql,sxml,deployment_id,status) values (:id,:author,:filename,:action,:sxml,:dep,:status) returning rowid into :out';
 updateaction varchar2(2000) := 'update HR.DATABASECHANGELOG_ACTIONS set sql = sql ||:action where rowid = :myrow ';
 updatesxml varchar2(2000) := 'update HR.DATABASECHANGELOG_ACTIONS set sxml = sxml ||:sxml where rowid = :myrow ';
 begin
action := utl_raw.cast_to_varchar2(utl_encode.base64_decode(utl_raw.cast_to_raw(q'{Q1JFQVRFIE9SIFJFUExBQ0UgRURJVElPTkFCTEUgUEFDS0FHRSAiSU5WRVNUTUVOVF9DSEVDSyIgQVMKICAgIFRZUEUgY2hlY2tfcmVjb3JkIElTIFJFQ09SRCgKICAgICAgIGlkIFBST1NQRUNUUy5QRVJTT05fSUQlVFlQRSwKICAgICAgIGZpcnN0X25hbWUgUFJPU1BFQ1RTLkZJUlNUX05BTUUlVFlQRSwKICAgICAgIGxhc3RfbmFtZSBQUk9TUEVDVFMuTEFTVF9OQU1FJVRZUEUsCiAgICAgICBpbnZlc3RtZW50X2xpbWl0IE5VTUJFUik7CiAgICBUWVBFIGNoZWNrX3RhYmxlIElTIFRBQkxFIE9GIGNoZWNrX3JlY29yZDsKICAgIEZVTkNUSU9OIGdldF9saW1pdHMoY2hlY2tfbGltaXQgTlVNQkVSKQogICAgICAgIFJFVFVSTiBjaGVja190YWJsZQogICAgICAgIFBJUEVMSU5FRDsKRU5EOwov}')));
sxml := utl_raw.cast_to_varchar2(utl_encode.base64_decode(utl_raw.cast_to_raw(q'{Q1JFQVRFIE9SIFJFUExBQ0UgRURJVElPTkFCTEUgUEFDS0FHRSAiSFIiLiJJTlZFU1RNRU5UX0NIRUNLIiBBUwogICAgVFlQRSBjaGVja19yZWNvcmQgSVMgUkVDT1JEKAogICAgICAgaWQgUFJPU1BFQ1RTLlBFUlNPTl9JRCVUWVBFLAogICAgICAgZmlyc3RfbmFtZSBQUk9TUEVDVFMuRklSU1RfTkFNRSVUWVBFLAogICAgICAgbGFzdF9uYW1lIFBST1NQRUNUUy5MQVNUX05BTUUlVFlQRSwKICAgICAgIGludmVzdG1lbnRfbGltaXQgTlVNQkVSKTsKICAgIFRZUEUgY2hlY2tfdGFibGUgSVMgVEFCTEUgT0YgY2hlY2tfcmVjb3JkOwogICAgRlVOQ1RJT04gZ2V0X2xpbWl0cyhjaGVja19saW1pdCBOVU1CRVIpCiAgICAgICAgUkVUVVJOIGNoZWNrX3RhYmxlCiAgICAgICAgUElQRUxJTkVEOwpFTkQ7Cg==}')));
 execute immediate insertlog using id,author,filename,action,sxml,dep,status returning into myrow;
end;
/

update HR.DATABASECHANGELOG_ACTIONS set status = 'RAN' where id = '62b4ab1d4ee925059a3bc305ed14d87808ea74ab' and sequence = (select max(sequence) from HR.DATABASECHANGELOG_ACTIONS where id = '62b4ab1d4ee925059a3bc305ed14d87808ea74ab');

INSERT INTO HR.DATABASECHANGELOG (ID, AUTHOR, FILENAME, DATEEXECUTED, ORDEREXECUTED, MD5SUM, DESCRIPTION, COMMENTS, EXECTYPE, CONTEXTS, LABELS, LIQUIBASE, DEPLOYMENT_ID) VALUES ('7a97ef6d7f5c88c013939789036541967b1592ef', '(HR)-Generated', '../v2.0/investment_check_package_body.xml', SYSTIMESTAMP, 40, '8:1d13d6a39f27a1e4eb649750034f5ef4', 'createOraclePackageBody objectName=INVESTMENT_CHECK, ownerName=HR', '', 'EXECUTED', NULL, NULL, '4.17.0', '2066177577');

-- Logging Oracle Liquibase extension actions to
 DECLARE
 id varchar2(2000) := '7a97ef6d7f5c88c013939789036541967b1592ef';
 status varchar2(2000) := 'PREPARING';
 rawAction clob;
 rawSxml clob;
 myrow varchar2(2000);
 action clob := '';
 sxml clob := '';
 dep varchar2(2000) := '2066177577';
 author varchar2(2000) := '(HR)-Generated';
 filename varchar2(2000) := '../v2.0/investment_check_package_body.xml';
 insertlog varchar2(2000) := 'insert into HR.DATABASECHANGELOG_ACTIONS (id,author,filename,sql,sxml,deployment_id,status) values (:id,:author,:filename,:action,:sxml,:dep,:status) returning rowid into :out';
 updateaction varchar2(2000) := 'update HR.DATABASECHANGELOG_ACTIONS set sql = sql ||:action where rowid = :myrow ';
 updatesxml varchar2(2000) := 'update HR.DATABASECHANGELOG_ACTIONS set sxml = sxml ||:sxml where rowid = :myrow ';
 begin
action := utl_raw.cast_to_varchar2(utl_encode.base64_decode(utl_raw.cast_to_raw(q'{Q1JFQVRFIE9SIFJFUExBQ0UgRURJVElPTkFCTEUgUEFDS0FHRSBCT0RZICJJTlZFU1RNRU5UX0NIRUNLIiBBUwogICAgRlVOQ1RJT04gZ2V0X2xpbWl0cyhjaGVja19saW1pdCBudW1iZXIpCiAgICAgICAgUkVUVVJOIGNoZWNrX3RhYmxlCiAgICAgICAgUElQRUxJTkVEIElTCiAgICAgICAgbF9yZWMgY2hlY2tfcmVjb3JkOwogICAgQkVHSU4KICAgICAgICBGT1IgbF9yZWMgSU4gKAogICAgICAgICAgc2VsZWN0IFBFUlNPTl9JRCwgRklSU1RfTkFNRSwgTEFTVF9OQU1FLCAzKlNBVklOR1MgYXMgSU5WRVNUTUVOVF9MSU1JVAogICAgICAgICAgZnJvbSBQUk9TUEVDVFMKICAgICAgICAgIHdoZXJlIDMqU0FWSU5HUyA+PSBjaGVja19saW1pdCkKICAgICAgICBMT09QCiAgICAgICAgICBQSVBFIFJPVyAobF9yZWMpOwogICAgICAgIEVORCBMT09QOwogICAgICAgIFJFVFVSTjsKICAgIEVORCBnZXRfbGltaXRzOwpFTkQ7Ci8=}')));
sxml := utl_raw.cast_to_varchar2(utl_encode.base64_decode(utl_raw.cast_to_raw(q'{Q1JFQVRFIE9SIFJFUExBQ0UgRURJVElPTkFCTEUgUEFDS0FHRSBCT0RZICJIUiIuIklOVkVTVE1FTlRfQ0hFQ0siIEFTCiAgICBGVU5DVElPTiBnZXRfbGltaXRzKGNoZWNrX2xpbWl0IG51bWJlcikKICAgICAgICBSRVRVUk4gY2hlY2tfdGFibGUKICAgICAgICBQSVBFTElORUQgSVMKICAgICAgICBsX3JlYyBjaGVja19yZWNvcmQ7CiAgICBCRUdJTgogICAgICAgIEZPUiBsX3JlYyBJTiAoCiAgICAgICAgICBzZWxlY3QgUEVSU09OX0lELCBGSVJTVF9OQU1FLCBMQVNUX05BTUUsIDMqU0FWSU5HUyBhcyBJTlZFU1RNRU5UX0xJTUlUCiAgICAgICAgICBmcm9tIFBST1NQRUNUUwogICAgICAgICAgd2hlcmUgMypTQVZJTkdTID49IGNoZWNrX2xpbWl0KQogICAgICAgIExPT1AKICAgICAgICAgIFBJUEUgUk9XIChsX3JlYyk7CiAgICAgICAgRU5EIExPT1A7CiAgICAgICAgUkVUVVJOOwogICAgRU5EIGdldF9saW1pdHM7CkVORDsK}')));
 execute immediate insertlog using id,author,filename,action,sxml,dep,status returning into myrow;
end;
/

update HR.DATABASECHANGELOG_ACTIONS set status = 'RAN' where id = '7a97ef6d7f5c88c013939789036541967b1592ef' and sequence = (select max(sequence) from HR.DATABASECHANGELOG_ACTIONS where id = '7a97ef6d7f5c88c013939789036541967b1592ef');

INSERT INTO HR.DATABASECHANGELOG (ID, AUTHOR, FILENAME, DATEEXECUTED, ORDEREXECUTED, MD5SUM, DESCRIPTION, COMMENTS, EXECTYPE, CONTEXTS, LABELS, LIQUIBASE, DEPLOYMENT_ID, TAG) VALUES ('tagDatabase-v2', 'Developer2', '../hr-master.xml', SYSTIMESTAMP, 41, '8:5d1d26bc76302012b3ab880dcf251a1e', 'tagDatabase', '', 'EXECUTED', NULL, NULL, '4.17.0', '2066177577', 'version_2.0');

-- Release Database Lock
UPDATE HR.DATABASECHANGELOGLOCK SET LOCKED = 0, LOCKEDBY = NULL, LOCKGRANTED = NULL WHERE ID = 1;



Operation completed successfully.


--- Run the generated commands and commit:

--- Then check:

SQL> select ID, AUTHOR, FILENAME, orderexecuted ORD, DESCRIPTION, TAG, EXECTYPE
from DATABASECHANGELOG order by 4 desc;

ID                                          AUTHOR            FILENAME                                        ORD DESCRIPTION                                                          TAG            EXECTYPE
___________________________________________ _________________ ____________________________________________ ______ ____________________________________________________________________ ______________ ___________
tagDatabase-v2                              Developer2        ../hr-master.xml                                 41 tagDatabase                                                          version_2.0    EXECUTED
7a97ef6d7f5c88c013939789036541967b1592ef    (HR)-Generated    ../v2.0/investment_check_package_body.xml        40 createOraclePackageBody objectName=INVESTMENT_CHECK, ownerName=HR                   EXECUTED
62b4ab1d4ee925059a3bc305ed14d87808ea74ab    (HR)-Generated    ../v2.0/investment_check_package_spec.xml        39 createOraclePackageSpec objectName=INVESTMENT_CHECK, ownerName=HR                   EXECUTED
542996f24b29997df8b2a831d71597285b4f998a    (HR)-Generated    ../v2.0/prospects_table.xml                      38 createSxmlObject objectName=PROSPECTS, ownerName=HR                                 EXECUTED
tagDatabase-v1                              Developer1        ../hr-master.xml                                 37 tagDatabase                                                          version_1.0    EXECUTED
5c3de07805546665ea5f89a9da6248912e422dd8    (HR)-Generated    ../v1.0/departments_ref_constraints.xml          36 createOracleRefConstraint objectName=DEPT_LOC_FK, ownerName=HR                      EXECUTED
7bcd599b071b53f135b9774904ed72ded351fc87    (HR)-Generated    ../v1.0/employees_ref_constraints.xml            35 createOracleRefConstraint objectName=EMP_DEPT_FK, ownerName=HR                      EXECUTED
0021967c3f65cc4ae98db87a67c3c6d4d5f6d927    (HR)-Generated    ../v1.0/departments_comments.xml                 34 createOracleComment objectName=DEPARTMENTS_COMMENTS, ownerName=HR                   EXECUTED
c1d5af882c57ec1843cd76d62e0c98bd241ecfee    (HR)-Generated    ../v1.0/regions_comments.xml                     33 createOracleComment objectName=REGIONS_COMMENTS, ownerName=HR                       EXECUTED
3e1cbd6678c4ccd8ce8e58bbe93972a650c36f97    (HR)-Generated    ../v1.0/jobs_comments.xml                        32 createOracleComment objectName=JOBS_COMMENTS, ownerName=HR                          EXECUTED
10401b775a504e30632f69c526f6c2e0f9407481    (HR)-Generated    ../v1.0/job_history_comments.xml                 31 createOracleComment objectName=JOB_HISTORY_COMMENTS, ownerName=HR                   EXECUTED
456d4fb4a910bca941e8657a9a31e33f1ab4cd3c    (HR)-Generated    ../v1.0/employees_comments.xml                   30 createOracleComment objectName=EMPLOYEES_COMMENTS, ownerName=HR                     EXECUTED
abee54702a80b0ef3de339057f8888f784d6c795    (HR)-Generated    ../v1.0/locations_comments.xml                   29 createOracleComment objectName=LOCATIONS_COMMENTS, ownerName=HR                     EXECUTED
6969594a15c66b1c78e3645988e841f7097ba242    (HR)-Generated    ../v1.0/countries_comments.xml                   28 createOracleComment objectName=COUNTRIES_COMMENTS, ownerName=HR                     EXECUTED
70aedb1927b7de9129c6614a3b0b65371ccd8dbc    (HR)-Generated    ../v1.0/update_job_history_trigger.xml           27 createOracleTrigger objectName=UPDATE_JOB_HISTORY, ownerName=HR                     EXECUTED
f6acef9bdfcf96da9691d863ddcd83ee3358034a    (HR)-Generated    ../v1.0/secure_employees_trigger.xml             26 createOracleTrigger objectName=SECURE_EMPLOYEES, ownerName=HR                       EXECUTED
c127f9e94d93f5acda2af24f693bba606d76a244    (HR)-Generated    ../v1.0/dept_location_ix_index.xml               25 createSxmlObject objectName=DEPT_LOCATION_IX, ownerName=HR                          EXECUTED
70b9d8f74b7262e911d32c43e2daac2bacbba29a    (HR)-Generated    ../v1.0/emp_name_ix_index.xml                    24 createSxmlObject objectName=EMP_NAME_IX, ownerName=HR                               EXECUTED
8354362383fb7c8489aaa426489a5fe96d7eb134    (HR)-Generated    ../v1.0/emp_manager_ix_index.xml                 23 createSxmlObject objectName=EMP_MANAGER_IX, ownerName=HR                            EXECUTED
7a8e2352305d3ce3d5a3505d0656bb24ec1e0f96    (HR)-Generated    ../v1.0/emp_email_uk_index.xml                   22 createSxmlObject objectName=EMP_EMAIL_UK, ownerName=HR                              EXECUTED
d73832cfccb9d32aa975a224f2b58cf3efeb5f3f    (HR)-Generated    ../v1.0/emp_job_ix_index.xml                     21 createSxmlObject objectName=EMP_JOB_IX, ownerName=HR                                EXECUTED
4f3fd64504441fdee039736861b8dcd752a6fea1    (HR)-Generated    ../v1.0/jhist_department_ix_index.xml            20 createSxmlObject objectName=JHIST_DEPARTMENT_IX, ownerName=HR                       EXECUTED
b5ce40efc7680b82b1baf63f1100d896967d8665    (HR)-Generated    ../v1.0/loc_city_ix_index.xml                    19 createSxmlObject objectName=LOC_CITY_IX, ownerName=HR                               EXECUTED
7d9a155cc4de6e35746bebaace41d8ed973ddd93    (HR)-Generated    ../v1.0/jhist_employee_ix_index.xml              18 createSxmlObject objectName=JHIST_EMPLOYEE_IX, ownerName=HR                         EXECUTED
9687423a8444cbd4d826963e26f32f030c9933f7    (HR)-Generated    ../v1.0/emp_department_ix_index.xml              17 createSxmlObject objectName=EMP_DEPARTMENT_IX, ownerName=HR                         EXECUTED
b0783ced5928aa9b6811ffe0d2b4dd765840716c    (HR)-Generated    ../v1.0/loc_state_province_ix_index.xml          16 createSxmlObject objectName=LOC_STATE_PROVINCE_IX, ownerName=HR                     EXECUTED
32f76f8ab196f65c5b8ae0c921831c6a7ebc640c    (HR)-Generated    ../v1.0/jhist_job_ix_index.xml                   15 createSxmlObject objectName=JHIST_JOB_IX, ownerName=HR                              EXECUTED
3718348046bdc485651c8286206b48e9af519461    (HR)-Generated    ../v1.0/loc_country_ix_index.xml                 14 createSxmlObject objectName=LOC_COUNTRY_IX, ownerName=HR                            EXECUTED
d92d897ec98ec5c2679d8cd01f0485fddd55451a    (HR)-Generated    ../v1.0/add_job_history_procedure.xml            13 createOracleProcedure objectName=ADD_JOB_HISTORY, ownerName=HR                      EXECUTED
76a219c8b2af11bf7c23e55e52573a4f1c99299b    (HR)-Generated    ../v1.0/emp_details_view_view.xml                12 createSxmlObject objectName=EMP_DETAILS_VIEW, ownerName=HR                          EXECUTED
dc533e0b14fa41e54d49cb28c42ff31a3186009e    (HR)-Generated    ../v1.0/job_history_table.xml                    11 createSxmlObject objectName=JOB_HISTORY, ownerName=HR                               EXECUTED
ad2c536c5636ec056d11ce44b28f4e55807cbd12    (HR)-Generated    ../v1.0/locations_table.xml                      10 createSxmlObject objectName=LOCATIONS, ownerName=HR                                 EXECUTED
1dacbd3ff0b3ae34e48d5df9ab3ca052f3995c33    (HR)-Generated    ../v1.0/countries_table.xml                       9 createSxmlObject objectName=COUNTRIES, ownerName=HR                                 EXECUTED

ID                                          AUTHOR            FILENAME                                   ORD DESCRIPTION                                                  TAG    EXECTYPE
___________________________________________ _________________ _______________________________________ ______ ____________________________________________________________ ______ ___________
5b8196cf470dfee2036694421aaddff307008907    (HR)-Generated    ../v1.0/secure_dml_procedure.xml             8 createOracleProcedure objectName=SECURE_DML, ownerName=HR           EXECUTED
52334f421d935229140b0468d06157dd45c20f96    (HR)-Generated    ../v1.0/regions_table.xml                    7 createSxmlObject objectName=REGIONS, ownerName=HR                   EXECUTED
84d6c14a5af0d22812c689a42e58e6c0cf300c1e    (HR)-Generated    ../v1.0/jobs_table.xml                       6 createSxmlObject objectName=JOBS, ownerName=HR                      EXECUTED
3679094045b7965245949695613df9351c236f3e    (HR)-Generated    ../v1.0/employees_table.xml                  5 createSxmlObject objectName=EMPLOYEES, ownerName=HR                 EXECUTED
18f3f88289eddcfc2b16fdae44a17169f8fe0d3f    (HR)-Generated    ../v1.0/departments_table.xml                4 createSxmlObject objectName=DEPARTMENTS, ownerName=HR               EXECUTED
42e3db1348e500dade36829bab3b7f5343ad6f09    (HR)-Generated    ../v1.0/employees_seq_sequence.xml           3 createSxmlObject objectName=EMPLOYEES_SEQ, ownerName=HR             EXECUTED
93020a4f5c3fc570029b0695d52763142b6e44e1    (HR)-Generated    ../v1.0/departments_seq_sequence.xml         2 createSxmlObject objectName=DEPARTMENTS_SEQ, ownerName=HR           EXECUTED
7ec49fad51eb8c0b53fa0128bf6ef2d3fee25d35    (HR)-Generated    ../v1.0/locations_seq_sequence.xml           1 createSxmlObject objectName=LOCATIONS_SEQ, ownerName=HR             EXECUTED

41 rows selected.

exit

-- Add initial schema changes to the Git repository. 

cd /home/oracle/cicd-ws-rep00
git add v2.0/*

*/

[oracle@myoracledb1 cicd-ws-rep00]$ git commit -a -m "Version 2: Prospects table and Investment package"
[main 7fd6ada] Version 2: Prospects table and Investment package
 4 files changed, 146 insertions(+)
 create mode 100644 v2.0/investment_check_package_body.xml
 create mode 100644 v2.0/investment_check_package_spec.xml
 create mode 100644 v2.0/prospects_table.xml
[oracle@myoracledb1 cicd-ws-rep00]$ git push
Enumerating objects: 9, done.
Counting objects: 100% (9/9), done.
Delta compression using up to 4 threads
Compressing objects: 100% (7/7), done.
Writing objects: 100% (7/7), 2.50 KiB | 2.50 MiB/s, done.
Total 7 (delta 2), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (2/2), completed with 1 local object.
To https://github.com/stephane-duprat/cicd-ws-rep00.git
   3ee6f21..7fd6ada  main -> main


Task 4: Modify objects, add code, and re-capture changes
********************************************************

sql hr/Oracle_4U@localhost:1521/freepdb1

CREATE SEQUENCE "HR_EVENTS_SEQ" MINVALUE 1 MAXVALUE 9999999999999999999999999999 INCREMENT BY 1 START WITH 1 CACHE 20 NOORDER NOCYCLE  NOKEEP NOSCALE GLOBAL;

CREATE TABLE  "HR_EVENTS"
   (    "ID" NUMBER,
        "EVENT_ID" NUMBER,
    "REGION" VARCHAR2(10),
    "COUNTRY" VARCHAR2(255),
    "EVENT_DATE" DATE,
    "EVENT_NAME" VARCHAR2(255),
     CONSTRAINT "HR_EVENTS_PK" PRIMARY KEY ("ID")
  USING INDEX ENABLE
   );

CREATE OR REPLACE EDITIONABLE TRIGGER  "BI_HR_EVENTS"
  before insert on "HR_EVENTS"              
  for each row
begin  
  if :new."ID" is null then
    select "HR_EVENTS_SEQ".nextval into :new."ID" from sys.dual;
  end if;
end;
/

ALTER TRIGGER  "BI_HR_EVENTS" ENABLE;

ALTER TABLE prospects ADD experience NUMBER;

ALTER TABLE employees ADD comments CLOB;

exit

cd /home/oracle/cicd-ws-rep00

mkdir v3.0

cd v3.0


sql hr/Oracle_4U@localhost:1521/freepdb1

lb generate-object -object-type SEQUENCE -object-name HR_EVENTS_SEQ
lb generate-object -object-type table -object-name HR_EVENTS
lb generate-object -object-type TRIGGER -object-name BI_HR_EVENTS
lb generate-object -object-type table -object-name prospects
lb generate-object -object-type table -object-name employees
exit

--- Add these lines to hr-master.xml: Add these lines after the last </changeSet> line, leaving the last line unchanged.

<include file="./v3.0/hr_events_seq_sequence.xml" relativeToChangelogFile="true"/>
  <include file="./v3.0/hr_events_table.xml" relativeToChangelogFile="true"/>
  <include file="./v3.0/bi_hr_events_trigger.xml" relativeToChangelogFile="true"/>
  <include file="./v3.0/prospects_table.xml" relativeToChangelogFile="true"/>
  <include file="./v3.0/employees_table.xml" relativeToChangelogFile="true"/>
  <changeSet  author="Developer3"  id="tagDatabase-v3">  
    <tagDatabase  tag="version_3.0"/>  
  </changeSet>

--- After the change, the file looks like this:

[oracle@myoracledb1 v3.0]$ cat ../hr-master.xml
<?xml version="1.1" encoding="UTF-8"?>
<databaseChangeLog
  xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
                      http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-4.1.xsd">
  <include file="./v1.0/controller.xml" relativeToChangelogFile="true"/>
  <changeSet  author="Developer1"  id="tagDatabase-v1">
    <tagDatabase  tag="version_1.0"/>
  </changeSet>
  <include file="./v2.0/prospects_table.xml" relativeToChangelogFile="true"/>
  <include file="./v2.0/investment_check_package_spec.xml" relativeToChangelogFile="true"/>
  <include file="./v2.0/investment_check_package_body.xml" relativeToChangelogFile="true"/>
  <changeSet  author="Developer2"  id="tagDatabase-v2">
    <tagDatabase  tag="version_2.0"/>
  </changeSet>
  <include file="./v3.0/hr_events_seq_sequence.xml" relativeToChangelogFile="true"/>
  <include file="./v3.0/hr_events_table.xml" relativeToChangelogFile="true"/>
  <include file="./v3.0/bi_hr_events_trigger.xml" relativeToChangelogFile="true"/>
  <include file="./v3.0/prospects_table.xml" relativeToChangelogFile="true"/>
  <include file="./v3.0/employees_table.xml" relativeToChangelogFile="true"/>
  <changeSet  author="Developer3"  id="tagDatabase-v3">
    <tagDatabase  tag="version_3.0"/>
  </changeSet>
</databaseChangeLog>
[oracle@myoracledb1 v3.0]$

-- Validate the master changelog:
[oracle@myoracledb1 v3.0]$ pwd
/home/oracle/cicd-ws-rep00/v3.0

sql hr/Oracle_4U@localhost:1521/freepdb1

SQL> lb validate -changelog-file ./../hr-master.xml
--Starting Liquibase at 09:20:12 (version 4.17.0 #0 built at 2022-11-02 21:48+0000)

-- Loaded 47 change(s)
No validation errors found.

Operation completed successfully.

lb changelog-sync-sql -changelog-file ./../hr-master.xml

--Starting Liquibase at 09:20:58 (version 4.17.0 #0 built at 2022-11-02 21:48+0000)

-- Loaded 47 change(s)
-- *********************************************************************
-- SQL to add all changesets to database history table
-- *********************************************************************
-- Change Log: ./../hr-master.xml
-- Ran at: 4/21/23, 9:20 AM
-- Against: HR@jdbc:oracle:thin:@localhost:1521/freepdb1
-- Liquibase version: 4.17.0
-- *********************************************************************

-- Lock Database
UPDATE HR.DATABASECHANGELOGLOCK SET LOCKED = 1, LOCKEDBY = '172.17.0.1 (172.17.0.1)', LOCKGRANTED = SYSTIMESTAMP WHERE ID = 1 AND LOCKED = 0;

INSERT INTO HR.DATABASECHANGELOG (ID, AUTHOR, FILENAME, DATEEXECUTED, ORDEREXECUTED, MD5SUM, DESCRIPTION, COMMENTS, EXECTYPE, CONTEXTS, LABELS, LIQUIBASE, DEPLOYMENT_ID) VALUES ('c2debe824fc7b76fecfeb8c544f592b82f8b1d51', '(HR)-Generated', '../v3.0/hr_events_seq_sequence.xml', SYSTIMESTAMP, 42, '8:4c394499d77bbaccebced0f81cd0fd64', 'createSxmlObject objectName=HR_EVENTS_SEQ, ownerName=HR', '', 'EXECUTED', NULL, NULL, '4.17.0', '2068865675');

-- Logging Oracle Liquibase extension actions to
 DECLARE
 id varchar2(2000) := 'c2debe824fc7b76fecfeb8c544f592b82f8b1d51';
 status varchar2(2000) := 'PREPARING';
 rawAction clob;
 rawSxml clob;
 myrow varchar2(2000);
 action clob := '';
 sxml clob := '';
 dep varchar2(2000) := '2068865675';
 author varchar2(2000) := '(HR)-Generated';
 filename varchar2(2000) := '../v3.0/hr_events_seq_sequence.xml';
 insertlog varchar2(2000) := 'insert into HR.DATABASECHANGELOG_ACTIONS (id,author,filename,sql,sxml,deployment_id,status) values (:id,:author,:filename,:action,:sxml,:dep,:status) returning rowid into :out';
 updateaction varchar2(2000) := 'update HR.DATABASECHANGELOG_ACTIONS set sql = sql ||:action where rowid = :myrow ';
 updatesxml varchar2(2000) := 'update HR.DATABASECHANGELOG_ACTIONS set sxml = sxml ||:sxml where rowid = :myrow ';
 begin
action := utl_raw.cast_to_varchar2(utl_encode.base64_decode(utl_raw.cast_to_raw(q'{LS0gb2JqZWN0IGlzIHRoZSBzYW1lIG5vdGhpbmcgdG8gZG8=}')));
sxml := utl_raw.cast_to_varchar2(utl_encode.base64_decode(utl_raw.cast_to_raw(q'{CiAgPFNFUVVFTkNFIHhtbG5zPSJodHRwOi8veG1sbnMub3JhY2xlLmNvbS9rdSIgdmVyc2lvbj0iMS4wIj4KICAgPFNDSEVNQT5IUjwvU0NIRU1BPgogICA8TkFNRT5IUl9FVkVOVFNfU0VRPC9OQU1FPgogICA8U1RBUlRfV0lUSD4xPC9TVEFSVF9XSVRIPgogICA8SU5DUkVNRU5UPjE8L0lOQ1JFTUVOVD4KICAgPE1JTlZBTFVFPjE8L01JTlZBTFVFPgogICA8TUFYVkFMVUU+OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTwvTUFYVkFMVUU+CiAgIDxDQUNIRT4yMDwvQ0FDSEU+CiAgIDxTQ0FMRT5OT1NDQUxFPC9TQ0FMRT4KPC9TRVFVRU5DRT4=}')));
 execute immediate insertlog using id,author,filename,action,sxml,dep,status returning into myrow;
end;
/

update HR.DATABASECHANGELOG_ACTIONS set status = 'RAN' where id = 'c2debe824fc7b76fecfeb8c544f592b82f8b1d51' and sequence = (select max(sequence) from HR.DATABASECHANGELOG_ACTIONS where id = 'c2debe824fc7b76fecfeb8c544f592b82f8b1d51');

INSERT INTO HR.DATABASECHANGELOG (ID, AUTHOR, FILENAME, DATEEXECUTED, ORDEREXECUTED, MD5SUM, DESCRIPTION, COMMENTS, EXECTYPE, CONTEXTS, LABELS, LIQUIBASE, DEPLOYMENT_ID) VALUES ('5e80225ad636d416d9660bf944c66e1a26c6af42', '(HR)-Generated', '../v3.0/hr_events_table.xml', SYSTIMESTAMP, 43, '8:75602bf89909811294f088ccec6081bf', 'createSxmlObject objectName=HR_EVENTS, ownerName=HR', '', 'EXECUTED', NULL, NULL, '4.17.0', '2068865675');

-- Logging Oracle Liquibase extension actions to
 DECLARE
 id varchar2(2000) := '5e80225ad636d416d9660bf944c66e1a26c6af42';
 status varchar2(2000) := 'PREPARING';
 rawAction clob;
 rawSxml clob;
 myrow varchar2(2000);
 action clob := '';
 sxml clob := '';
 dep varchar2(2000) := '2068865675';
 author varchar2(2000) := '(HR)-Generated';
 filename varchar2(2000) := '../v3.0/hr_events_table.xml';
 insertlog varchar2(2000) := 'insert into HR.DATABASECHANGELOG_ACTIONS (id,author,filename,sql,sxml,deployment_id,status) values (:id,:author,:filename,:action,:sxml,:dep,:status) returning rowid into :out';
 updateaction varchar2(2000) := 'update HR.DATABASECHANGELOG_ACTIONS set sql = sql ||:action where rowid = :myrow ';
 updatesxml varchar2(2000) := 'update HR.DATABASECHANGELOG_ACTIONS set sxml = sxml ||:sxml where rowid = :myrow ';
 begin
action := utl_raw.cast_to_varchar2(utl_encode.base64_decode(utl_raw.cast_to_raw(q'{LS0gb2JqZWN0IGlzIHRoZSBzYW1lIG5vdGhpbmcgdG8gZG8=}')));
sxml := utl_raw.cast_to_varchar2(utl_encode.base64_decode(utl_raw.cast_to_raw(q'{CiAgPFRBQkxFIHhtbG5zPSJodHRwOi8veG1sbnMub3JhY2xlLmNvbS9rdSIgdmVyc2lvbj0iMS4wIj4KICAgPFNDSEVNQT5IUjwvU0NIRU1BPgogICA8TkFNRT5IUl9FVkVOVFM8L05BTUU+CiAgIDxSRUxBVElPTkFMX1RBQkxFPgogICAgICA8Q09MX0xJU1Q+CiAgICAgICAgIDxDT0xfTElTVF9JVEVNPgogICAgICAgICAgICA8TkFNRT5JRDwvTkFNRT4KICAgICAgICAgICAgPERBVEFUWVBFPk5VTUJFUjwvREFUQVRZUEU+CiAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgICAgPENPTF9MSVNUX0lURU0+CiAgICAgICAgICAgIDxOQU1FPkVWRU5UX0lEPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+TlVNQkVSPC9EQVRBVFlQRT4KICAgICAgICAgPC9DT0xfTElTVF9JVEVNPgogICAgICAgICA8Q09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgPE5BTUU+UkVHSU9OPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+VkFSQ0hBUjI8L0RBVEFUWVBFPgogICAgICAgICAgICA8TEVOR1RIPjEwPC9MRU5HVEg+CiAgICAgICAgICAgIDxDT0xMQVRFX05BTUU+VVNJTkdfTkxTX0NPTVA8L0NPTExBVEVfTkFNRT4KICAgICAgICAgPC9DT0xfTElTVF9JVEVNPgogICAgICAgICA8Q09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgPE5BTUU+Q09VTlRSWTwvTkFNRT4KICAgICAgICAgICAgPERBVEFUWVBFPlZBUkNIQVIyPC9EQVRBVFlQRT4KICAgICAgICAgICAgPExFTkdUSD4yNTU8L0xFTkdUSD4KICAgICAgICAgICAgPENPTExBVEVfTkFNRT5VU0lOR19OTFNfQ09NUDwvQ09MTEFURV9OQU1FPgogICAgICAgICA8L0NPTF9MSVNUX0lURU0+CiAgICAgICAgIDxDT0xfTElTVF9JVEVNPgogICAgICAgICAgICA8TkFNRT5FVkVOVF9EQVRFPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+REFURTwvREFUQVRZUEU+CiAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgICAgPENPTF9MSVNUX0lURU0+CiAgICAgICAgICAgIDxOQU1FPkVWRU5UX05BTUU8L05BTUU+CiAgICAgICAgICAgIDxEQVRBVFlQRT5WQVJDSEFSMjwvREFUQVRZUEU+CiAgICAgICAgICAgIDxMRU5HVEg+MjU1PC9MRU5HVEg+CiAgICAgICAgICAgIDxDT0xMQVRFX05BTUU+VVNJTkdfTkxTX0NPTVA8L0NPTExBVEVfTkFNRT4KICAgICAgICAgPC9DT0xfTElTVF9JVEVNPgogICAgICA8L0NPTF9MSVNUPgogICAgICA8UFJJTUFSWV9LRVlfQ09OU1RSQUlOVF9MSVNUPgogICAgICAgICA8UFJJTUFSWV9LRVlfQ09OU1RSQUlOVF9MSVNUX0lURU0+CiAgICAgICAgICAgIDxOQU1FPkhSX0VWRU5UU19QSzwvTkFNRT4KICAgICAgICAgICAgPENPTF9MSVNUPgogICAgICAgICAgICAgICA8Q09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgICAgICAgPE5BTUU+SUQ8L05BTUU+CiAgICAgICAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgPC9DT0xfTElTVD4KICAgICAgICAgICAgPFVTSU5HX0lOREVYPgogICAgICAgICAgICAgICA8SU5ERVhfQVRUUklCVVRFUz4KICAgICAgICAgICAgICAgICAgPFBDVEZSRUU+MTA8L1BDVEZSRUU+CiAgICAgICAgICAgICAgICAgIDxJTklUUkFOUz4yPC9JTklUUkFOUz4KICAgICAgICAgICAgICAgICAgPE1BWFRSQU5TPjI1NTwvTUFYVFJBTlM+CiAgICAgICAgICAgICAgICAgIDxUQUJMRVNQQUNFPlVTRVJTPC9UQUJMRVNQQUNFPgogICAgICAgICAgICAgICAgICA8TE9HR0lORz5ZPC9MT0dHSU5HPgogICAgICAgICAgICAgICA8L0lOREVYX0FUVFJJQlVURVM+CiAgICAgICAgICAgIDwvVVNJTkdfSU5ERVg+CiAgICAgICAgIDwvUFJJTUFSWV9LRVlfQ09OU1RSQUlOVF9MSVNUX0lURU0+CiAgICAgIDwvUFJJTUFSWV9LRVlfQ09OU1RSQUlOVF9MSVNUPgogICAgICA8REVGQVVMVF9DT0xMQVRJT04+VVNJTkdfTkxTX0NPTVA8L0RFRkFVTFRfQ09MTEFUSU9OPgogICAgICA8UEhZU0lDQUxfUFJPUEVSVElFUz4KICAgICAgICAgPEhFQVBfVEFCTEU+CiAgICAgICAgICAgIDxTRUdNRU5UX0FUVFJJQlVURVM+CiAgICAgICAgICAgICAgIDxTRUdNRU5UX0NSRUFUSU9OX0RFRkVSUkVEPjwvU0VHTUVOVF9DUkVBVElPTl9ERUZFUlJFRD4KICAgICAgICAgICAgICAgPFBDVEZSRUU+MTA8L1BDVEZSRUU+CiAgICAgICAgICAgICAgIDxQQ1RVU0VEPjQwPC9QQ1RVU0VEPgogICAgICAgICAgICAgICA8SU5JVFJBTlM+MTwvSU5JVFJBTlM+CiAgICAgICAgICAgICAgIDxNQVhUUkFOUz4yNTU8L01BWFRSQU5TPgogICAgICAgICAgICAgICA8VEFCTEVTUEFDRT5VU0VSUzwvVEFCTEVTUEFDRT4KICAgICAgICAgICAgICAgPExPR0dJTkc+WTwvTE9HR0lORz4KICAgICAgICAgICAgPC9TRUdNRU5UX0FUVFJJQlVURVM+CiAgICAgICAgICAgIDxDT01QUkVTUz5OPC9DT01QUkVTUz4KICAgICAgICAgPC9IRUFQX1RBQkxFPgogICAgICA8L1BIWVNJQ0FMX1BST1BFUlRJRVM+CiAgIDwvUkVMQVRJT05BTF9UQUJMRT4KPC9UQUJMRT4=}')));
 execute immediate insertlog using id,author,filename,action,sxml,dep,status returning into myrow;
end;
/

update HR.DATABASECHANGELOG_ACTIONS set status = 'RAN' where id = '5e80225ad636d416d9660bf944c66e1a26c6af42' and sequence = (select max(sequence) from HR.DATABASECHANGELOG_ACTIONS where id = '5e80225ad636d416d9660bf944c66e1a26c6af42');

INSERT INTO HR.DATABASECHANGELOG (ID, AUTHOR, FILENAME, DATEEXECUTED, ORDEREXECUTED, MD5SUM, DESCRIPTION, COMMENTS, EXECTYPE, CONTEXTS, LABELS, LIQUIBASE, DEPLOYMENT_ID) VALUES ('16c9f75c45ea4089b26d212d79a3dfe451a2c227', '(HR)-Generated', '../v3.0/bi_hr_events_trigger.xml', SYSTIMESTAMP, 44, '8:a6819043015ff46574c9f6f964f42e78', 'createOracleTrigger objectName=BI_HR_EVENTS, ownerName=HR', '', 'EXECUTED', NULL, NULL, '4.17.0', '2068865675');

-- Logging Oracle Liquibase extension actions to
 DECLARE
 id varchar2(2000) := '16c9f75c45ea4089b26d212d79a3dfe451a2c227';
 status varchar2(2000) := 'PREPARING';
 rawAction clob;
 rawSxml clob;
 myrow varchar2(2000);
 action clob := '';
 sxml clob := '';
 dep varchar2(2000) := '2068865675';
 author varchar2(2000) := '(HR)-Generated';
 filename varchar2(2000) := '../v3.0/bi_hr_events_trigger.xml';
 insertlog varchar2(2000) := 'insert into HR.DATABASECHANGELOG_ACTIONS (id,author,filename,sql,sxml,deployment_id,status) values (:id,:author,:filename,:action,:sxml,:dep,:status) returning rowid into :out';
 updateaction varchar2(2000) := 'update HR.DATABASECHANGELOG_ACTIONS set sql = sql ||:action where rowid = :myrow ';
 updatesxml varchar2(2000) := 'update HR.DATABASECHANGELOG_ACTIONS set sxml = sxml ||:sxml where rowid = :myrow ';
 begin
action := utl_raw.cast_to_varchar2(utl_encode.base64_decode(utl_raw.cast_to_raw(q'{Q1JFQVRFIE9SIFJFUExBQ0UgRURJVElPTkFCTEUgVFJJR0dFUiAiQklfSFJfRVZFTlRTIiAKICBiZWZvcmUgaW5zZXJ0IG9uICJIUl9FVkVOVFMiICAgICAgICAgICAgICAKICBmb3IgZWFjaCByb3cKYmVnaW4gIAogIGlmIDpuZXcuIklEIiBpcyBudWxsIHRoZW4KICAgIHNlbGVjdCAiSFJfRVZFTlRTX1NFUSIubmV4dHZhbCBpbnRvIDpuZXcuIklEIiBmcm9tIHN5cy5kdWFsOwogIGVuZCBpZjsKZW5kOwovCi8gCkFMVEVSIFRSSUdHRVIgIkJJX0hSX0VWRU5UUyIgRU5BQkxFOw==}')));
sxml := utl_raw.cast_to_varchar2(utl_encode.base64_decode(utl_raw.cast_to_raw(q'{Q1JFQVRFIE9SIFJFUExBQ0UgRURJVElPTkFCTEUgVFJJR0dFUiAiSFIiLiJCSV9IUl9FVkVOVFMiIAogIGJlZm9yZSBpbnNlcnQgb24gIkhSX0VWRU5UUyIgICAgICAgICAgICAgIAogIGZvciBlYWNoIHJvdwpiZWdpbiAgCiAgaWYgOm5ldy4iSUQiIGlzIG51bGwgdGhlbgogICAgc2VsZWN0ICJIUl9FVkVOVFNfU0VRIi5uZXh0dmFsIGludG8gOm5ldy4iSUQiIGZyb20gc3lzLmR1YWw7CiAgZW5kIGlmOwplbmQ7CgpBTFRFUiBUUklHR0VSICJIUiIuIkJJX0hSX0VWRU5UUyIgRU5BQkxF}')));
 execute immediate insertlog using id,author,filename,action,sxml,dep,status returning into myrow;
end;
/

update HR.DATABASECHANGELOG_ACTIONS set status = 'RAN' where id = '16c9f75c45ea4089b26d212d79a3dfe451a2c227' and sequence = (select max(sequence) from HR.DATABASECHANGELOG_ACTIONS where id = '16c9f75c45ea4089b26d212d79a3dfe451a2c227');

INSERT INTO HR.DATABASECHANGELOG (ID, AUTHOR, FILENAME, DATEEXECUTED, ORDEREXECUTED, MD5SUM, DESCRIPTION, COMMENTS, EXECTYPE, CONTEXTS, LABELS, LIQUIBASE, DEPLOYMENT_ID) VALUES ('dd2e22475b7a54fc9ebd9b1e1135fcce86bc48a8', '(HR)-Generated', '../v3.0/prospects_table.xml', SYSTIMESTAMP, 45, '8:9fa818662d8b636c6e0e92f1b390cb8e', 'createSxmlObject objectName=PROSPECTS, ownerName=HR', '', 'EXECUTED', NULL, NULL, '4.17.0', '2068865675');

-- Logging Oracle Liquibase extension actions to
 DECLARE
 id varchar2(2000) := 'dd2e22475b7a54fc9ebd9b1e1135fcce86bc48a8';
 status varchar2(2000) := 'PREPARING';
 rawAction clob;
 rawSxml clob;
 myrow varchar2(2000);
 action clob := '';
 sxml clob := '';
 dep varchar2(2000) := '2068865675';
 author varchar2(2000) := '(HR)-Generated';
 filename varchar2(2000) := '../v3.0/prospects_table.xml';
 insertlog varchar2(2000) := 'insert into HR.DATABASECHANGELOG_ACTIONS (id,author,filename,sql,sxml,deployment_id,status) values (:id,:author,:filename,:action,:sxml,:dep,:status) returning rowid into :out';
 updateaction varchar2(2000) := 'update HR.DATABASECHANGELOG_ACTIONS set sql = sql ||:action where rowid = :myrow ';
 updatesxml varchar2(2000) := 'update HR.DATABASECHANGELOG_ACTIONS set sxml = sxml ||:sxml where rowid = :myrow ';
 begin
action := utl_raw.cast_to_varchar2(utl_encode.base64_decode(utl_raw.cast_to_raw(q'{LS0gb2JqZWN0IGlzIHRoZSBzYW1lIG5vdGhpbmcgdG8gZG8=}')));
sxml := utl_raw.cast_to_varchar2(utl_encode.base64_decode(utl_raw.cast_to_raw(q'{CiAgPFRBQkxFIHhtbG5zPSJodHRwOi8veG1sbnMub3JhY2xlLmNvbS9rdSIgdmVyc2lvbj0iMS4wIj4KICAgPFNDSEVNQT5IUjwvU0NIRU1BPgogICA8TkFNRT5QUk9TUEVDVFM8L05BTUU+CiAgIDxSRUxBVElPTkFMX1RBQkxFPgogICAgICA8Q09MX0xJU1Q+CiAgICAgICAgIDxDT0xfTElTVF9JVEVNPgogICAgICAgICAgICA8TkFNRT5QRVJTT05fSUQ8L05BTUU+CiAgICAgICAgICAgIDxEQVRBVFlQRT5OVU1CRVI8L0RBVEFUWVBFPgogICAgICAgICAgICA8UFJFQ0lTSU9OPjY8L1BSRUNJU0lPTj4KICAgICAgICAgICAgPFNDQUxFPjA8L1NDQUxFPgogICAgICAgICA8L0NPTF9MSVNUX0lURU0+CiAgICAgICAgIDxDT0xfTElTVF9JVEVNPgogICAgICAgICAgICA8TkFNRT5GSVJTVF9OQU1FPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+VkFSQ0hBUjI8L0RBVEFUWVBFPgogICAgICAgICAgICA8TEVOR1RIPjIwPC9MRU5HVEg+CiAgICAgICAgICAgIDxDT0xMQVRFX05BTUU+VVNJTkdfTkxTX0NPTVA8L0NPTExBVEVfTkFNRT4KICAgICAgICAgPC9DT0xfTElTVF9JVEVNPgogICAgICAgICA8Q09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgPE5BTUU+TEFTVF9OQU1FPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+VkFSQ0hBUjI8L0RBVEFUWVBFPgogICAgICAgICAgICA8TEVOR1RIPjI1PC9MRU5HVEg+CiAgICAgICAgICAgIDxDT0xMQVRFX05BTUU+VVNJTkdfTkxTX0NPTVA8L0NPTExBVEVfTkFNRT4KICAgICAgICAgICAgPE5PVF9OVUxMPjwvTk9UX05VTEw+CiAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgICAgPENPTF9MSVNUX0lURU0+CiAgICAgICAgICAgIDxOQU1FPkVNQUlMPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+VkFSQ0hBUjI8L0RBVEFUWVBFPgogICAgICAgICAgICA8TEVOR1RIPjM3PC9MRU5HVEg+CiAgICAgICAgICAgIDxDT0xMQVRFX05BTUU+VVNJTkdfTkxTX0NPTVA8L0NPTExBVEVfTkFNRT4KICAgICAgICAgPC9DT0xfTElTVF9JVEVNPgogICAgICAgICA8Q09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgPE5BTUU+UEhPTkVfTlVNQkVSPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+VkFSQ0hBUjI8L0RBVEFUWVBFPgogICAgICAgICAgICA8TEVOR1RIPjIwPC9MRU5HVEg+CiAgICAgICAgICAgIDxDT0xMQVRFX05BTUU+VVNJTkdfTkxTX0NPTVA8L0NPTExBVEVfTkFNRT4KICAgICAgICAgPC9DT0xfTElTVF9JVEVNPgogICAgICAgICA8Q09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgPE5BTUU+QklSVEhfREFURTwvTkFNRT4KICAgICAgICAgICAgPERBVEFUWVBFPkRBVEU8L0RBVEFUWVBFPgogICAgICAgICA8L0NPTF9MSVNUX0lURU0+CiAgICAgICAgIDxDT0xfTElTVF9JVEVNPgogICAgICAgICAgICA8TkFNRT5TQVZJTkdTPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+TlVNQkVSPC9EQVRBVFlQRT4KICAgICAgICAgPC9DT0xfTElTVF9JVEVNPgogICAgICAgICA8Q09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgPE5BTUU+RVhQRVJJRU5DRTwvTkFNRT4KICAgICAgICAgICAgPERBVEFUWVBFPk5VTUJFUjwvREFUQVRZUEU+CiAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgPC9DT0xfTElTVD4KICAgICAgPERFRkFVTFRfQ09MTEFUSU9OPlVTSU5HX05MU19DT01QPC9ERUZBVUxUX0NPTExBVElPTj4KICAgICAgPFBIWVNJQ0FMX1BST1BFUlRJRVM+CiAgICAgICAgIDxIRUFQX1RBQkxFPgogICAgICAgICAgICA8U0VHTUVOVF9BVFRSSUJVVEVTPgogICAgICAgICAgICAgICA8U0VHTUVOVF9DUkVBVElPTl9JTU1FRElBVEU+PC9TRUdNRU5UX0NSRUFUSU9OX0lNTUVESUFURT4KICAgICAgICAgICAgICAgPFBDVEZSRUU+MTA8L1BDVEZSRUU+CiAgICAgICAgICAgICAgIDxQQ1RVU0VEPjQwPC9QQ1RVU0VEPgogICAgICAgICAgICAgICA8SU5JVFJBTlM+MTwvSU5JVFJBTlM+CiAgICAgICAgICAgICAgIDxNQVhUUkFOUz4yNTU8L01BWFRSQU5TPgogICAgICAgICAgICAgICA8U1RPUkFHRT4KICAgICAgICAgICAgICAgICAgPElOSVRJQUw+NjU1MzY8L0lOSVRJQUw+CiAgICAgICAgICAgICAgICAgIDxORVhUPjEwNDg1NzY8L05FWFQ+CiAgICAgICAgICAgICAgICAgIDxNSU5FWFRFTlRTPjE8L01JTkVYVEVOVFM+CiAgICAgICAgICAgICAgICAgIDxNQVhFWFRFTlRTPjIxNDc0ODM2NDU8L01BWEVYVEVOVFM+CiAgICAgICAgICAgICAgICAgIDxQQ1RJTkNSRUFTRT4wPC9QQ1RJTkNSRUFTRT4KICAgICAgICAgICAgICAgICAgPEZSRUVMSVNUUz4xPC9GUkVFTElTVFM+CiAgICAgICAgICAgICAgICAgIDxGUkVFTElTVF9HUk9VUFM+MTwvRlJFRUxJU1RfR1JPVVBTPgogICAgICAgICAgICAgICAgICA8QlVGRkVSX1BPT0w+REVGQVVMVDwvQlVGRkVSX1BPT0w+CiAgICAgICAgICAgICAgICAgIDxGTEFTSF9DQUNIRT5ERUZBVUxUPC9GTEFTSF9DQUNIRT4KICAgICAgICAgICAgICAgICAgPENFTExfRkxBU0hfQ0FDSEU+REVGQVVMVDwvQ0VMTF9GTEFTSF9DQUNIRT4KICAgICAgICAgICAgICAgPC9TVE9SQUdFPgogICAgICAgICAgICAgICA8VEFCTEVTUEFDRT5VU0VSUzwvVEFCTEVTUEFDRT4KICAgICAgICAgICAgICAgPExPR0dJTkc+WTwvTE9HR0lORz4KICAgICAgICAgICAgPC9TRUdNRU5UX0FUVFJJQlVURVM+CiAgICAgICAgICAgIDxDT01QUkVTUz5OPC9DT01QUkVTUz4KICAgICAgICAgPC9IRUFQX1RBQkxFPgogICAgICA8L1BIWVNJQ0FMX1BST1BFUlRJRVM+CiAgIDwvUkVMQVRJT05BTF9UQUJMRT4KPC9UQUJMRT4=}')));
 execute immediate insertlog using id,author,filename,action,sxml,dep,status returning into myrow;
end;
/

update HR.DATABASECHANGELOG_ACTIONS set status = 'RAN' where id = 'dd2e22475b7a54fc9ebd9b1e1135fcce86bc48a8' and sequence = (select max(sequence) from HR.DATABASECHANGELOG_ACTIONS where id = 'dd2e22475b7a54fc9ebd9b1e1135fcce86bc48a8');

INSERT INTO HR.DATABASECHANGELOG (ID, AUTHOR, FILENAME, DATEEXECUTED, ORDEREXECUTED, MD5SUM, DESCRIPTION, COMMENTS, EXECTYPE, CONTEXTS, LABELS, LIQUIBASE, DEPLOYMENT_ID) VALUES ('f6a472e23495ea356abcd7d53d575683f0665ad3', '(HR)-Generated', '../v3.0/employees_table.xml', SYSTIMESTAMP, 46, '8:d95618ce24eff1f567e1605e751ce2af', 'createSxmlObject objectName=EMPLOYEES, ownerName=HR', '', 'EXECUTED', NULL, NULL, '4.17.0', '2068865675');

-- Logging Oracle Liquibase extension actions to
 DECLARE
 id varchar2(2000) := 'f6a472e23495ea356abcd7d53d575683f0665ad3';
 status varchar2(2000) := 'PREPARING';
 rawAction clob;
 rawSxml clob;
 myrow varchar2(2000);
 action clob := '';
 sxml clob := '';
 dep varchar2(2000) := '2068865675';
 author varchar2(2000) := '(HR)-Generated';
 filename varchar2(2000) := '../v3.0/employees_table.xml';
 insertlog varchar2(2000) := 'insert into HR.DATABASECHANGELOG_ACTIONS (id,author,filename,sql,sxml,deployment_id,status) values (:id,:author,:filename,:action,:sxml,:dep,:status) returning rowid into :out';
 updateaction varchar2(2000) := 'update HR.DATABASECHANGELOG_ACTIONS set sql = sql ||:action where rowid = :myrow ';
 updatesxml varchar2(2000) := 'update HR.DATABASECHANGELOG_ACTIONS set sxml = sxml ||:sxml where rowid = :myrow ';
 begin
action := utl_raw.cast_to_varchar2(utl_encode.base64_decode(utl_raw.cast_to_raw(q'{LS0gb2JqZWN0IGlzIHRoZSBzYW1lIG5vdGhpbmcgdG8gZG8=}')));
sxml := utl_raw.cast_to_varchar2(utl_encode.base64_decode(utl_raw.cast_to_raw(q'{CiAgPFRBQkxFIHhtbG5zPSJodHRwOi8veG1sbnMub3JhY2xlLmNvbS9rdSIgdmVyc2lvbj0iMS4wIj4KICAgPFNDSEVNQT5IUjwvU0NIRU1BPgogICA8TkFNRT5FTVBMT1lFRVM8L05BTUU+CiAgIDxSRUxBVElPTkFMX1RBQkxFPgogICAgICA8Q09MX0xJU1Q+CiAgICAgICAgIDxDT0xfTElTVF9JVEVNPgogICAgICAgICAgICA8TkFNRT5FTVBMT1lFRV9JRDwvTkFNRT4KICAgICAgICAgICAgPERBVEFUWVBFPk5VTUJFUjwvREFUQVRZUEU+CiAgICAgICAgICAgIDxQUkVDSVNJT04+NjwvUFJFQ0lTSU9OPgogICAgICAgICAgICA8U0NBTEU+MDwvU0NBTEU+CiAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgICAgPENPTF9MSVNUX0lURU0+CiAgICAgICAgICAgIDxOQU1FPkZJUlNUX05BTUU8L05BTUU+CiAgICAgICAgICAgIDxEQVRBVFlQRT5WQVJDSEFSMjwvREFUQVRZUEU+CiAgICAgICAgICAgIDxMRU5HVEg+MjA8L0xFTkdUSD4KICAgICAgICAgICAgPENPTExBVEVfTkFNRT5VU0lOR19OTFNfQ09NUDwvQ09MTEFURV9OQU1FPgogICAgICAgICA8L0NPTF9MSVNUX0lURU0+CiAgICAgICAgIDxDT0xfTElTVF9JVEVNPgogICAgICAgICAgICA8TkFNRT5MQVNUX05BTUU8L05BTUU+CiAgICAgICAgICAgIDxEQVRBVFlQRT5WQVJDSEFSMjwvREFUQVRZUEU+CiAgICAgICAgICAgIDxMRU5HVEg+MjU8L0xFTkdUSD4KICAgICAgICAgICAgPENPTExBVEVfTkFNRT5VU0lOR19OTFNfQ09NUDwvQ09MTEFURV9OQU1FPgogICAgICAgICAgICA8Tk9UX05VTEw+CiAgICAgICAgICAgICAgIDxOQU1FPkVNUF9MQVNUX05BTUVfTk48L05BTUU+CiAgICAgICAgICAgIDwvTk9UX05VTEw+CiAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgICAgPENPTF9MSVNUX0lURU0+CiAgICAgICAgICAgIDxOQU1FPkVNQUlMPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+VkFSQ0hBUjI8L0RBVEFUWVBFPgogICAgICAgICAgICA8TEVOR1RIPjI1PC9MRU5HVEg+CiAgICAgICAgICAgIDxDT0xMQVRFX05BTUU+VVNJTkdfTkxTX0NPTVA8L0NPTExBVEVfTkFNRT4KICAgICAgICAgICAgPE5PVF9OVUxMPgogICAgICAgICAgICAgICA8TkFNRT5FTVBfRU1BSUxfTk48L05BTUU+CiAgICAgICAgICAgIDwvTk9UX05VTEw+CiAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgICAgPENPTF9MSVNUX0lURU0+CiAgICAgICAgICAgIDxOQU1FPlBIT05FX05VTUJFUjwvTkFNRT4KICAgICAgICAgICAgPERBVEFUWVBFPlZBUkNIQVIyPC9EQVRBVFlQRT4KICAgICAgICAgICAgPExFTkdUSD4yMDwvTEVOR1RIPgogICAgICAgICAgICA8Q09MTEFURV9OQU1FPlVTSU5HX05MU19DT01QPC9DT0xMQVRFX05BTUU+CiAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgICAgPENPTF9MSVNUX0lURU0+CiAgICAgICAgICAgIDxOQU1FPkhJUkVfREFURTwvTkFNRT4KICAgICAgICAgICAgPERBVEFUWVBFPkRBVEU8L0RBVEFUWVBFPgogICAgICAgICAgICA8Tk9UX05VTEw+CiAgICAgICAgICAgICAgIDxOQU1FPkVNUF9ISVJFX0RBVEVfTk48L05BTUU+CiAgICAgICAgICAgIDwvTk9UX05VTEw+CiAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgICAgPENPTF9MSVNUX0lURU0+CiAgICAgICAgICAgIDxOQU1FPkpPQl9JRDwvTkFNRT4KICAgICAgICAgICAgPERBVEFUWVBFPlZBUkNIQVIyPC9EQVRBVFlQRT4KICAgICAgICAgICAgPExFTkdUSD4xMDwvTEVOR1RIPgogICAgICAgICAgICA8Q09MTEFURV9OQU1FPlVTSU5HX05MU19DT01QPC9DT0xMQVRFX05BTUU+CiAgICAgICAgICAgIDxOT1RfTlVMTD4KICAgICAgICAgICAgICAgPE5BTUU+RU1QX0pPQl9OTjwvTkFNRT4KICAgICAgICAgICAgPC9OT1RfTlVMTD4KICAgICAgICAgPC9DT0xfTElTVF9JVEVNPgogICAgICAgICA8Q09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgPE5BTUU+U0FMQVJZPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+TlVNQkVSPC9EQVRBVFlQRT4KICAgICAgICAgICAgPFBSRUNJU0lPTj44PC9QUkVDSVNJT04+CiAgICAgICAgICAgIDxTQ0FMRT4yPC9TQ0FMRT4KICAgICAgICAgPC9DT0xfTElTVF9JVEVNPgogICAgICAgICA8Q09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgPE5BTUU+Q09NTUlTU0lPTl9QQ1Q8L05BTUU+CiAgICAgICAgICAgIDxEQVRBVFlQRT5OVU1CRVI8L0RBVEFUWVBFPgogICAgICAgICAgICA8UFJFQ0lTSU9OPjI8L1BSRUNJU0lPTj4KICAgICAgICAgICAgPFNDQUxFPjI8L1NDQUxFPgogICAgICAgICA8L0NPTF9MSVNUX0lURU0+CiAgICAgICAgIDxDT0xfTElTVF9JVEVNPgogICAgICAgICAgICA8TkFNRT5NQU5BR0VSX0lEPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+TlVNQkVSPC9EQVRBVFlQRT4KICAgICAgICAgICAgPFBSRUNJU0lPTj42PC9QUkVDSVNJT04+CiAgICAgICAgICAgIDxTQ0FMRT4wPC9TQ0FMRT4KICAgICAgICAgPC9DT0xfTElTVF9JVEVNPgogICAgICAgICA8Q09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgPE5BTUU+REVQQVJUTUVOVF9JRDwvTkFNRT4KICAgICAgICAgICAgPERBVEFUWVBFPk5VTUJFUjwvREFUQVRZUEU+CiAgICAgICAgICAgIDxQUkVDSVNJT04+NDwvUFJFQ0lTSU9OPgogICAgICAgICAgICA8U0NBTEU+MDwvU0NBTEU+CiAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgICAgPENPTF9MSVNUX0lURU0+CiAgICAgICAgICAgIDxOQU1FPkNPTU1FTlRTPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+Q0xPQjwvREFUQVRZUEU+CiAgICAgICAgICAgIDxDT0xMQVRFX05BTUU+VVNJTkdfTkxTX0NPTVA8L0NPTExBVEVfTkFNRT4KICAgICAgICAgPC9DT0xfTElTVF9JVEVNPgogICAgICA8L0NPTF9MSVNUPgogICAgICA8Q0hFQ0tfQ09OU1RSQUlOVF9MSVNUPgogICAgICAgICA8Q0hFQ0tfQ09OU1RSQUlOVF9MSVNUX0lURU0+CiAgICAgICAgICAgIDxOQU1FPkVNUF9TQUxBUllfTUlOPC9OQU1FPgogICAgICAgICAgICA8Q09ORElUSU9OPnNhbGFyeSA+IDA8L0NPTkRJVElPTj4KICAgICAgICAgPC9DSEVDS19DT05TVFJBSU5UX0xJU1RfSVRFTT4KICAgICAgPC9DSEVDS19DT05TVFJBSU5UX0xJU1Q+CiAgICAgIDxQUklNQVJZX0tFWV9DT05TVFJBSU5UX0xJU1Q+CiAgICAgICAgIDxQUklNQVJZX0tFWV9DT05TVFJBSU5UX0xJU1RfSVRFTT4KICAgICAgICAgICAgPE5BTUU+RU1QX0VNUF9JRF9QSzwvTkFNRT4KICAgICAgICAgICAgPENPTF9MSVNUPgogICAgICAgICAgICAgICA8Q09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgICAgICAgPE5BTUU+RU1QTE9ZRUVfSUQ8L05BTUU+CiAgICAgICAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgPC9DT0xfTElTVD4KICAgICAgICAgICAgPFVTSU5HX0lOREVYPgogICAgICAgICAgICAgICA8SU5ERVhfQVRUUklCVVRFUz4KICAgICAgICAgICAgICAgICAgPFBDVEZSRUU+MTA8L1BDVEZSRUU+CiAgICAgICAgICAgICAgICAgIDxJTklUUkFOUz4yPC9JTklUUkFOUz4KICAgICAgICAgICAgICAgICAgPE1BWFRSQU5TPjI1NTwvTUFYVFJBTlM+CiAgICAgICAgICAgICAgICAgIDxTVE9SQUdFPgogICAgICAgICAgICAgICAgICAgICA8SU5JVElBTD42NTUzNjwvSU5JVElBTD4KICAgICAgICAgICAgICAgICAgICAgPE5FWFQ+MTA0ODU3NjwvTkVYVD4KICAgICAgICAgICAgICAgICAgICAgPE1JTkVYVEVOVFM+MTwvTUlORVhURU5UUz4KICAgICAgICAgICAgICAgICAgICAgPE1BWEVYVEVOVFM+MjE0NzQ4MzY0NTwvTUFYRVhURU5UUz4KICAgICAgICAgICAgICAgICAgICAgPFBDVElOQ1JFQVNFPjA8L1BDVElOQ1JFQVNFPgogICAgICAgICAgICAgICAgICAgICA8RlJFRUxJU1RTPjE8L0ZSRUVMSVNUUz4KICAgICAgICAgICAgICAgICAgICAgPEZSRUVMSVNUX0dST1VQUz4xPC9GUkVFTElTVF9HUk9VUFM+CiAgICAgICAgICAgICAgICAgICAgIDxCVUZGRVJfUE9PTD5ERUZBVUxUPC9CVUZGRVJfUE9PTD4KICAgICAgICAgICAgICAgICAgICAgPEZMQVNIX0NBQ0hFPkRFRkFVTFQ8L0ZMQVNIX0NBQ0hFPgogICAgICAgICAgICAgICAgICAgICA8Q0VMTF9GTEFTSF9DQUNIRT5ERUZBVUxUPC9DRUxMX0ZMQVNIX0NBQ0hFPgogICAgICAgICAgICAgICAgICA8L1NUT1JBR0U+CiAgICAgICAgICAgICAgICAgIDxUQUJMRVNQQUNFPlVTRVJTPC9UQUJMRVNQQUNFPgogICAgICAgICAgICAgICAgICA8TE9HR0lORz5ZPC9MT0dHSU5HPgogICAgICAgICAgICAgICA8L0lOREVYX0FUVFJJQlVURVM+CiAgICAgICAgICAgIDwvVVNJTkdfSU5ERVg+CiAgICAgICAgIDwvUFJJTUFSWV9LRVlfQ09OU1RSQUlOVF9MSVNUX0lURU0+CiAgICAgIDwvUFJJTUFSWV9LRVlfQ09OU1RSQUlOVF9MSVNUPgogICAgICA8VU5JUVVFX0tFWV9DT05TVFJBSU5UX0xJU1Q+CiAgICAgICAgIDxVTklRVUVfS0VZX0NPTlNUUkFJTlRfTElTVF9JVEVNPgogICAgICAgICAgICA8TkFNRT5FTVBfRU1BSUxfVUs8L05BTUU+CiAgICAgICAgICAgIDxDT0xfTElTVD4KICAgICAgICAgICAgICAgPENPTF9MSVNUX0lURU0+CiAgICAgICAgICAgICAgICAgIDxOQU1FPkVNQUlMPC9OQU1FPgogICAgICAgICAgICAgICA8L0NPTF9MSVNUX0lURU0+CiAgICAgICAgICAgIDwvQ09MX0xJU1Q+CiAgICAgICAgICAgIDxVU0lOR19JTkRFWD4KICAgICAgICAgICAgICAgPElOREVYX0FUVFJJQlVURVM+CiAgICAgICAgICAgICAgICAgIDxQQ1RGUkVFPjEwPC9QQ1RGUkVFPgogICAgICAgICAgICAgICAgICA8SU5JVFJBTlM+MjwvSU5JVFJBTlM+CiAgICAgICAgICAgICAgICAgIDxNQVhUUkFOUz4yNTU8L01BWFRSQU5TPgogICAgICAgICAgICAgICAgICA8U1RPUkFHRT4KICAgICAgICAgICAgICAgICAgICAgPElOSVRJQUw+NjU1MzY8L0lOSVRJQUw+CiAgICAgICAgICAgICAgICAgICAgIDxORVhUPjEwNDg1NzY8L05FWFQ+CiAgICAgICAgICAgICAgICAgICAgIDxNSU5FWFRFTlRTPjE8L01JTkVYVEVOVFM+CiAgICAgICAgICAgICAgICAgICAgIDxNQVhFWFRFTlRTPjIxNDc0ODM2NDU8L01BWEVYVEVOVFM+CiAgICAgICAgICAgICAgICAgICAgIDxQQ1RJTkNSRUFTRT4wPC9QQ1RJTkNSRUFTRT4KICAgICAgICAgICAgICAgICAgICAgPEZSRUVMSVNUUz4xPC9GUkVFTElTVFM+CiAgICAgICAgICAgICAgICAgICAgIDxGUkVFTElTVF9HUk9VUFM+MTwvRlJFRUxJU1RfR1JPVVBTPgogICAgICAgICAgICAgICAgICAgICA8QlVGRkVSX1BPT0w+REVGQVVMVDwvQlVGRkVSX1BPT0w+CiAgICAgICAgICAgICAgICAgICAgIDxGTEFTSF9DQUNIRT5ERUZBVUxUPC9GTEFTSF9DQUNIRT4KICAgICAgICAgICAgICAgICAgICAgPENFTExfRkxBU0hfQ0FDSEU+REVGQVVMVDwvQ0VMTF9GTEFTSF9DQUNIRT4KICAgICAgICAgICAgICAgICAgPC9TVE9SQUdFPgogICAgICAgICAgICAgICAgICA8VEFCTEVTUEFDRT5VU0VSUzwvVEFCTEVTUEFDRT4KICAgICAgICAgICAgICAgICAgPExPR0dJTkc+WTwvTE9HR0lORz4KICAgICAgICAgICAgICAgPC9JTkRFWF9BVFRSSUJVVEVTPgogICAgICAgICAgICA8L1VTSU5HX0lOREVYPgogICAgICAgICA8L1VOSVFVRV9LRVlfQ09OU1RSQUlOVF9MSVNUX0lURU0+CiAgICAgIDwvVU5JUVVFX0tFWV9DT05TVFJBSU5UX0xJU1Q+CiAgICAgIDxGT1JFSUdOX0tFWV9DT05TVFJBSU5UX0xJU1Q+CiAgICAgICAgIDxGT1JFSUdOX0tFWV9DT05TVFJBSU5UX0xJU1RfSVRFTT4KICAgICAgICAgICAgPE5BTUU+RU1QX0RFUFRfRks8L05BTUU+CiAgICAgICAgICAgIDxDT0xfTElTVD4KICAgICAgICAgICAgICAgPENPTF9MSVNUX0lURU0+CiAgICAgICAgICAgICAgICAgIDxOQU1FPkRFUEFSVE1FTlRfSUQ8L05BTUU+CiAgICAgICAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgPC9DT0xfTElTVD4KICAgICAgICAgICAgPFJFRkVSRU5DRVM+CiAgICAgICAgICAgICAgIDxTQ0hFTUE+SFI8L1NDSEVNQT4KICAgICAgICAgICAgICAgPE5BTUU+REVQQVJUTUVOVFM8L05BTUU+CiAgICAgICAgICAgICAgIDxDT0xfTElTVD4KICAgICAgICAgICAgICAgICAgPENPTF9MSVNUX0lURU0+CiAgICAgICAgICAgICAgICAgICAgIDxOQU1FPkRFUEFSVE1FTlRfSUQ8L05BTUU+CiAgICAgICAgICAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgICAgPC9DT0xfTElTVD4KICAgICAgICAgICAgPC9SRUZFUkVOQ0VTPgogICAgICAgICA8L0ZPUkVJR05fS0VZX0NPTlNUUkFJTlRfTElTVF9JVEVNPgogICAgICAgICA8Rk9SRUlHTl9LRVlfQ09OU1RSQUlOVF9MSVNUX0lURU0+CiAgICAgICAgICAgIDxOQU1FPkVNUF9KT0JfRks8L05BTUU+CiAgICAgICAgICAgIDxDT0xfTElTVD4KICAgICAgICAgICAgICAgPENPTF9MSVNUX0lURU0+CiAgICAgICAgICAgICAgICAgIDxOQU1FPkpPQl9JRDwvTkFNRT4KICAgICAgICAgICAgICAgPC9DT0xfTElTVF9JVEVNPgogICAgICAgICAgICA8L0NPTF9MSVNUPgogICAgICAgICAgICA8UkVGRVJFTkNFUz4KICAgICAgICAgICAgICAgPFNDSEVNQT5IUjwvU0NIRU1BPgogICAgICAgICAgICAgICA8TkFNRT5KT0JTPC9OQU1FPgogICAgICAgICAgICAgICA8Q09MX0xJU1Q+CiAgICAgICAgICAgICAgICAgIDxDT0xfTElTVF9JVEVNPgogICAgICAgICAgICAgICAgICAgICA8TkFNRT5KT0JfSUQ8L05BTUU+CiAgICAgICAgICAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgICAgPC9DT0xfTElTVD4KICAgICAgICAgICAgPC9SRUZFUkVOQ0VTPgogICAgICAgICA8L0ZPUkVJR05fS0VZX0NPTlNUUkFJTlRfTElTVF9JVEVNPgogICAgICAgICA8Rk9SRUlHTl9LRVlfQ09OU1RSQUlOVF9MSVNUX0lURU0+CiAgICAgICAgICAgIDxOQU1FPkVNUF9NQU5BR0VSX0ZLPC9OQU1FPgogICAgICAgICAgICA8Q09MX0xJU1Q+CiAgICAgICAgICAgICAgIDxDT0xfTElTVF9JVEVNPgogICAgICAgICAgICAgICAgICA8TkFNRT5NQU5BR0VSX0lEPC9OQU1FPgogICAgICAgICAgICAgICA8L0NPTF9MSVNUX0lURU0+CiAgICAgICAgICAgIDwvQ09MX0xJU1Q+CiAgICAgICAgICAgIDxSRUZFUkVOQ0VTPgogICAgICAgICAgICAgICA8U0NIRU1BPkhSPC9TQ0hFTUE+CiAgICAgICAgICAgICAgIDxOQU1FPkVNUExPWUVFUzwvTkFNRT4KICAgICAgICAgICAgICAgPENPTF9MSVNUPgogICAgICAgICAgICAgICAgICA8Q09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgICAgICAgICAgPE5BTUU+RU1QTE9ZRUVfSUQ8L05BTUU+CiAgICAgICAgICAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgICAgPC9DT0xfTElTVD4KICAgICAgICAgICAgPC9SRUZFUkVOQ0VTPgogICAgICAgICA8L0ZPUkVJR05fS0VZX0NPTlNUUkFJTlRfTElTVF9JVEVNPgogICAgICA8L0ZPUkVJR05fS0VZX0NPTlNUUkFJTlRfTElTVD4KICAgICAgPERFRkFVTFRfQ09MTEFUSU9OPlVTSU5HX05MU19DT01QPC9ERUZBVUxUX0NPTExBVElPTj4KICAgICAgPFBIWVNJQ0FMX1BST1BFUlRJRVM+CiAgICAgICAgIDxIRUFQX1RBQkxFPgogICAgICAgICAgICA8U0VHTUVOVF9BVFRSSUJVVEVTPgogICAgICAgICAgICAgICA8U0VHTUVOVF9DUkVBVElPTl9JTU1FRElBVEU+PC9TRUdNRU5UX0NSRUFUSU9OX0lNTUVESUFURT4KICAgICAgICAgICAgICAgPFBDVEZSRUU+MTA8L1BDVEZSRUU+CiAgICAgICAgICAgICAgIDxQQ1RVU0VEPjQwPC9QQ1RVU0VEPgogICAgICAgICAgICAgICA8SU5JVFJBTlM+MTwvSU5JVFJBTlM+CiAgICAgICAgICAgICAgIDxNQVhUUkFOUz4yNTU8L01BWFRSQU5TPgogICAgICAgICAgICAgICA8U1RPUkFHRT4KICAgICAgICAgICAgICAgICAgPElOSVRJQUw+NjU1MzY8L0lOSVRJQUw+CiAgICAgICAgICAgICAgICAgIDxORVhUPjEwNDg1NzY8L05FWFQ+CiAgICAgICAgICAgICAgICAgIDxNSU5FWFRFTlRTPjE8L01JTkVYVEVOVFM+CiAgICAgICAgICAgICAgICAgIDxNQVhFWFRFTlRTPjIxNDc0ODM2NDU8L01BWEVYVEVOVFM+CiAgICAgICAgICAgICAgICAgIDxQQ1RJTkNSRUFTRT4wPC9QQ1RJTkNSRUFTRT4KICAgICAgICAgICAgICAgICAgPEZSRUVMSVNUUz4xPC9GUkVFTElTVFM+CiAgICAgICAgICAgICAgICAgIDxGUkVFTElTVF9HUk9VUFM+MTwvRlJFRUxJU1RfR1JPVVBTPgogICAgICAgICAgICAgICAgICA8QlVGRkVSX1BPT0w+REVGQVVMVDwvQlVGRkVSX1BPT0w+CiAgICAgICAgICAgICAgICAgIDxGTEFTSF9DQUNIRT5ERUZBVUxUPC9GTEFTSF9DQUNIRT4KICAgICAgICAgICAgICAgICAgPENFTExfRkxBU0hfQ0FDSEU+REVGQVVMVDwvQ0VMTF9GTEFTSF9DQUNIRT4KICAgICAgICAgICAgICAgPC9TVE9SQUdFPgogICAgICAgICAgICAgICA8VEFCTEVTUEFDRT5VU0VSUzwvVEFCTEVTUEFDRT4KICAgICAgICAgICAgICAgPExPR0dJTkc+WTwvTE9HR0lORz4KICAgICAgICAgICAgPC9TRUdNRU5UX0FUVFJJQlVURVM+CiAgICAgICAgICAgIDxDT01QUkVTUz5OPC9DT01QUkVTUz4KICAgICAgICAgPC9IRUFQX1RBQkxFPgogICAgICA8L1BIWVNJQ0FMX1BST1BFUlRJRVM+CiAgICAgIDxUQUJMRV9QUk9QRVJUSUVTPgogICAgICAgICA8Q09MVU1OX1BST1BFUlRJRVM+CiAgICAgICAgICAgIDxDT0xfTElTVD4KICAgICAgICAgICAgICAgPENPTF9MSVNUX0lURU0+CiAgICAgICAgICAgICAgICAgIDxOQU1FPkNPTU1FTlRTPC9OQU1FPgogICAgICAgICAgICAgICAgICA8REFUQVRZUEU+Q0xPQjwvREFUQVRZUEU+CiAgICAgICAgICAgICAgICAgIDxMT0JfUFJPUEVSVElFUz4KICAgICAgICAgICAgICAgICAgICAgPFNUT1JBR0VfVEFCTEU+CiAgICAgICAgICAgICAgICAgICAgICAgIDxUQUJMRVNQQUNFPlVTRVJTPC9UQUJMRVNQQUNFPgogICAgICAgICAgICAgICAgICAgICAgICA8U0VDVVJFRklMRT48L1NFQ1VSRUZJTEU+CiAgICAgICAgICAgICAgICAgICAgICAgIDxTVE9SQUdFX0lOX1JPVz40MDAwPC9TVE9SQUdFX0lOX1JPVz4KICAgICAgICAgICAgICAgICAgICAgICAgPFNUT1JBR0U+CiAgICAgICAgICAgICAgICAgICAgICAgICAgIDxJTklUSUFMPjI2MjE0NDwvSU5JVElBTD4KICAgICAgICAgICAgICAgICAgICAgICAgICAgPE5FWFQ+MTA0ODU3NjwvTkVYVD4KICAgICAgICAgICAgICAgICAgICAgICAgICAgPE1JTkVYVEVOVFM+MTwvTUlORVhURU5UUz4KICAgICAgICAgICAgICAgICAgICAgICAgICAgPE1BWEVYVEVOVFM+MjE0NzQ4MzY0NTwvTUFYRVhURU5UUz4KICAgICAgICAgICAgICAgICAgICAgICAgICAgPFBDVElOQ1JFQVNFPjA8L1BDVElOQ1JFQVNFPgogICAgICAgICAgICAgICAgICAgICAgICAgICA8QlVGRkVSX1BPT0w+REVGQVVMVDwvQlVGRkVSX1BPT0w+CiAgICAgICAgICAgICAgICAgICAgICAgICAgIDxGTEFTSF9DQUNIRT5ERUZBVUxUPC9GTEFTSF9DQUNIRT4KICAgICAgICAgICAgICAgICAgICAgICAgICAgPENFTExfRkxBU0hfQ0FDSEU+REVGQVVMVDwvQ0VMTF9GTEFTSF9DQUNIRT4KICAgICAgICAgICAgICAgICAgICAgICAgPC9TVE9SQUdFPgogICAgICAgICAgICAgICAgICAgICAgICA8Q0hVTks+ODE5MjwvQ0hVTks+CiAgICAgICAgICAgICAgICAgICAgICAgIDxDQUNIRT5OPC9DQUNIRT4KICAgICAgICAgICAgICAgICAgICAgICAgPExPR0dJTkc+WTwvTE9HR0lORz4KICAgICAgICAgICAgICAgICAgICAgICAgPFZBTElEQVRFPk48L1ZBTElEQVRFPgogICAgICAgICAgICAgICAgICAgICA8L1NUT1JBR0VfVEFCTEU+CiAgICAgICAgICAgICAgICAgIDwvTE9CX1BST1BFUlRJRVM+CiAgICAgICAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgPC9DT0xfTElTVD4KICAgICAgICAgPC9DT0xVTU5fUFJPUEVSVElFUz4KICAgICAgPC9UQUJMRV9QUk9QRVJUSUVTPgogICA8L1JFTEFUSU9OQUxfVEFCTEU+CjwvVEFCTEU+}')));
 execute immediate insertlog using id,author,filename,action,sxml,dep,status returning into myrow;
end;
/

update HR.DATABASECHANGELOG_ACTIONS set status = 'RAN' where id = 'f6a472e23495ea356abcd7d53d575683f0665ad3' and sequence = (select max(sequence) from HR.DATABASECHANGELOG_ACTIONS where id = 'f6a472e23495ea356abcd7d53d575683f0665ad3');

INSERT INTO HR.DATABASECHANGELOG (ID, AUTHOR, FILENAME, DATEEXECUTED, ORDEREXECUTED, MD5SUM, DESCRIPTION, COMMENTS, EXECTYPE, CONTEXTS, LABELS, LIQUIBASE, DEPLOYMENT_ID, TAG) VALUES ('tagDatabase-v3', 'Developer3', '../hr-master.xml', SYSTIMESTAMP, 47, '8:72f1de0946663a3b84b239dd766671e9', 'tagDatabase', '', 'EXECUTED', NULL, NULL, '4.17.0', '2068865675', 'version_3.0');

-- Release Database Lock
UPDATE HR.DATABASECHANGELOGLOCK SET LOCKED = 0, LOCKEDBY = NULL, LOCKGRANTED = NULL WHERE ID = 1;



Operation completed successfully.


--- Run the previous commands and commit:

-- And check:

SQL> select ID, AUTHOR, FILENAME, orderexecuted ORD, DESCRIPTION, TAG, EXECTYPE
from DATABASECHANGELOG order by 4 desc;

ID                                          AUTHOR            FILENAME                                        ORD DESCRIPTION                                                          TAG            EXECTYPE
___________________________________________ _________________ ____________________________________________ ______ ____________________________________________________________________ ______________ ___________
tagDatabase-v3                              Developer3        ../hr-master.xml                                 47 tagDatabase                                                          version_3.0    EXECUTED
f6a472e23495ea356abcd7d53d575683f0665ad3    (HR)-Generated    ../v3.0/employees_table.xml                      46 createSxmlObject objectName=EMPLOYEES, ownerName=HR                                 EXECUTED
dd2e22475b7a54fc9ebd9b1e1135fcce86bc48a8    (HR)-Generated    ../v3.0/prospects_table.xml                      45 createSxmlObject objectName=PROSPECTS, ownerName=HR                                 EXECUTED
16c9f75c45ea4089b26d212d79a3dfe451a2c227    (HR)-Generated    ../v3.0/bi_hr_events_trigger.xml                 44 createOracleTrigger objectName=BI_HR_EVENTS, ownerName=HR                           EXECUTED
5e80225ad636d416d9660bf944c66e1a26c6af42    (HR)-Generated    ../v3.0/hr_events_table.xml                      43 createSxmlObject objectName=HR_EVENTS, ownerName=HR                                 EXECUTED
c2debe824fc7b76fecfeb8c544f592b82f8b1d51    (HR)-Generated    ../v3.0/hr_events_seq_sequence.xml               42 createSxmlObject objectName=HR_EVENTS_SEQ, ownerName=HR                             EXECUTED
tagDatabase-v2                              Developer2        ../hr-master.xml                                 41 tagDatabase                                                          version_2.0    EXECUTED
7a97ef6d7f5c88c013939789036541967b1592ef    (HR)-Generated    ../v2.0/investment_check_package_body.xml        40 createOraclePackageBody objectName=INVESTMENT_CHECK, ownerName=HR                   EXECUTED
62b4ab1d4ee925059a3bc305ed14d87808ea74ab    (HR)-Generated    ../v2.0/investment_check_package_spec.xml        39 createOraclePackageSpec objectName=INVESTMENT_CHECK, ownerName=HR                   EXECUTED
542996f24b29997df8b2a831d71597285b4f998a    (HR)-Generated    ../v2.0/prospects_table.xml                      38 createSxmlObject objectName=PROSPECTS, ownerName=HR                                 EXECUTED
tagDatabase-v1                              Developer1        ../hr-master.xml                                 37 tagDatabase                                                          version_1.0    EXECUTED
5c3de07805546665ea5f89a9da6248912e422dd8    (HR)-Generated    ../v1.0/departments_ref_constraints.xml          36 createOracleRefConstraint objectName=DEPT_LOC_FK, ownerName=HR                      EXECUTED
7bcd599b071b53f135b9774904ed72ded351fc87    (HR)-Generated    ../v1.0/employees_ref_constraints.xml            35 createOracleRefConstraint objectName=EMP_DEPT_FK, ownerName=HR                      EXECUTED
0021967c3f65cc4ae98db87a67c3c6d4d5f6d927    (HR)-Generated    ../v1.0/departments_comments.xml                 34 createOracleComment objectName=DEPARTMENTS_COMMENTS, ownerName=HR                   EXECUTED
c1d5af882c57ec1843cd76d62e0c98bd241ecfee    (HR)-Generated    ../v1.0/regions_comments.xml                     33 createOracleComment objectName=REGIONS_COMMENTS, ownerName=HR                       EXECUTED
3e1cbd6678c4ccd8ce8e58bbe93972a650c36f97    (HR)-Generated    ../v1.0/jobs_comments.xml                        32 createOracleComment objectName=JOBS_COMMENTS, ownerName=HR                          EXECUTED
10401b775a504e30632f69c526f6c2e0f9407481    (HR)-Generated    ../v1.0/job_history_comments.xml                 31 createOracleComment objectName=JOB_HISTORY_COMMENTS, ownerName=HR                   EXECUTED
456d4fb4a910bca941e8657a9a31e33f1ab4cd3c    (HR)-Generated    ../v1.0/employees_comments.xml                   30 createOracleComment objectName=EMPLOYEES_COMMENTS, ownerName=HR                     EXECUTED
abee54702a80b0ef3de339057f8888f784d6c795    (HR)-Generated    ../v1.0/locations_comments.xml                   29 createOracleComment objectName=LOCATIONS_COMMENTS, ownerName=HR                     EXECUTED
6969594a15c66b1c78e3645988e841f7097ba242    (HR)-Generated    ../v1.0/countries_comments.xml                   28 createOracleComment objectName=COUNTRIES_COMMENTS, ownerName=HR                     EXECUTED
70aedb1927b7de9129c6614a3b0b65371ccd8dbc    (HR)-Generated    ../v1.0/update_job_history_trigger.xml           27 createOracleTrigger objectName=UPDATE_JOB_HISTORY, ownerName=HR                     EXECUTED
f6acef9bdfcf96da9691d863ddcd83ee3358034a    (HR)-Generated    ../v1.0/secure_employees_trigger.xml             26 createOracleTrigger objectName=SECURE_EMPLOYEES, ownerName=HR                       EXECUTED
c127f9e94d93f5acda2af24f693bba606d76a244    (HR)-Generated    ../v1.0/dept_location_ix_index.xml               25 createSxmlObject objectName=DEPT_LOCATION_IX, ownerName=HR                          EXECUTED
70b9d8f74b7262e911d32c43e2daac2bacbba29a    (HR)-Generated    ../v1.0/emp_name_ix_index.xml                    24 createSxmlObject objectName=EMP_NAME_IX, ownerName=HR                               EXECUTED
8354362383fb7c8489aaa426489a5fe96d7eb134    (HR)-Generated    ../v1.0/emp_manager_ix_index.xml                 23 createSxmlObject objectName=EMP_MANAGER_IX, ownerName=HR                            EXECUTED
7a8e2352305d3ce3d5a3505d0656bb24ec1e0f96    (HR)-Generated    ../v1.0/emp_email_uk_index.xml                   22 createSxmlObject objectName=EMP_EMAIL_UK, ownerName=HR                              EXECUTED
d73832cfccb9d32aa975a224f2b58cf3efeb5f3f    (HR)-Generated    ../v1.0/emp_job_ix_index.xml                     21 createSxmlObject objectName=EMP_JOB_IX, ownerName=HR                                EXECUTED
4f3fd64504441fdee039736861b8dcd752a6fea1    (HR)-Generated    ../v1.0/jhist_department_ix_index.xml            20 createSxmlObject objectName=JHIST_DEPARTMENT_IX, ownerName=HR                       EXECUTED
b5ce40efc7680b82b1baf63f1100d896967d8665    (HR)-Generated    ../v1.0/loc_city_ix_index.xml                    19 createSxmlObject objectName=LOC_CITY_IX, ownerName=HR                               EXECUTED
7d9a155cc4de6e35746bebaace41d8ed973ddd93    (HR)-Generated    ../v1.0/jhist_employee_ix_index.xml              18 createSxmlObject objectName=JHIST_EMPLOYEE_IX, ownerName=HR                         EXECUTED
9687423a8444cbd4d826963e26f32f030c9933f7    (HR)-Generated    ../v1.0/emp_department_ix_index.xml              17 createSxmlObject objectName=EMP_DEPARTMENT_IX, ownerName=HR                         EXECUTED
b0783ced5928aa9b6811ffe0d2b4dd765840716c    (HR)-Generated    ../v1.0/loc_state_province_ix_index.xml          16 createSxmlObject objectName=LOC_STATE_PROVINCE_IX, ownerName=HR                     EXECUTED
32f76f8ab196f65c5b8ae0c921831c6a7ebc640c    (HR)-Generated    ../v1.0/jhist_job_ix_index.xml                   15 createSxmlObject objectName=JHIST_JOB_IX, ownerName=HR                              EXECUTED

ID                                          AUTHOR            FILENAME                                    ORD DESCRIPTION                                                       TAG    EXECTYPE
___________________________________________ _________________ ________________________________________ ______ _________________________________________________________________ ______ ___________
3718348046bdc485651c8286206b48e9af519461    (HR)-Generated    ../v1.0/loc_country_ix_index.xml             14 createSxmlObject objectName=LOC_COUNTRY_IX, ownerName=HR                 EXECUTED
d92d897ec98ec5c2679d8cd01f0485fddd55451a    (HR)-Generated    ../v1.0/add_job_history_procedure.xml        13 createOracleProcedure objectName=ADD_JOB_HISTORY, ownerName=HR           EXECUTED
76a219c8b2af11bf7c23e55e52573a4f1c99299b    (HR)-Generated    ../v1.0/emp_details_view_view.xml            12 createSxmlObject objectName=EMP_DETAILS_VIEW, ownerName=HR               EXECUTED
dc533e0b14fa41e54d49cb28c42ff31a3186009e    (HR)-Generated    ../v1.0/job_history_table.xml                11 createSxmlObject objectName=JOB_HISTORY, ownerName=HR                    EXECUTED
ad2c536c5636ec056d11ce44b28f4e55807cbd12    (HR)-Generated    ../v1.0/locations_table.xml                  10 createSxmlObject objectName=LOCATIONS, ownerName=HR                      EXECUTED
1dacbd3ff0b3ae34e48d5df9ab3ca052f3995c33    (HR)-Generated    ../v1.0/countries_table.xml                   9 createSxmlObject objectName=COUNTRIES, ownerName=HR                      EXECUTED
5b8196cf470dfee2036694421aaddff307008907    (HR)-Generated    ../v1.0/secure_dml_procedure.xml              8 createOracleProcedure objectName=SECURE_DML, ownerName=HR                EXECUTED
52334f421d935229140b0468d06157dd45c20f96    (HR)-Generated    ../v1.0/regions_table.xml                     7 createSxmlObject objectName=REGIONS, ownerName=HR                        EXECUTED
84d6c14a5af0d22812c689a42e58e6c0cf300c1e    (HR)-Generated    ../v1.0/jobs_table.xml                        6 createSxmlObject objectName=JOBS, ownerName=HR                           EXECUTED
3679094045b7965245949695613df9351c236f3e    (HR)-Generated    ../v1.0/employees_table.xml                   5 createSxmlObject objectName=EMPLOYEES, ownerName=HR                      EXECUTED
18f3f88289eddcfc2b16fdae44a17169f8fe0d3f    (HR)-Generated    ../v1.0/departments_table.xml                 4 createSxmlObject objectName=DEPARTMENTS, ownerName=HR                    EXECUTED
42e3db1348e500dade36829bab3b7f5343ad6f09    (HR)-Generated    ../v1.0/employees_seq_sequence.xml            3 createSxmlObject objectName=EMPLOYEES_SEQ, ownerName=HR                  EXECUTED
93020a4f5c3fc570029b0695d52763142b6e44e1    (HR)-Generated    ../v1.0/departments_seq_sequence.xml          2 createSxmlObject objectName=DEPARTMENTS_SEQ, ownerName=HR                EXECUTED
7ec49fad51eb8c0b53fa0128bf6ef2d3fee25d35    (HR)-Generated    ../v1.0/locations_seq_sequence.xml            1 createSxmlObject objectName=LOCATIONS_SEQ, ownerName=HR                  EXECUTED

47 rows selected.

exit

cd /home/oracle/cicd-ws-rep00
git add v3.0/*

*/

[oracle@myoracledb1 cicd-ws-rep00]$ git commit -a -m "Version 3: HR Events table and trigger"
[main e86189b] Version 3: HR Events table and trigger
 6 files changed, 510 insertions(+)
 create mode 100644 v3.0/bi_hr_events_trigger.xml
 create mode 100644 v3.0/employees_table.xml
 create mode 100644 v3.0/hr_events_seq_sequence.xml
 create mode 100644 v3.0/hr_events_table.xml
 create mode 100644 v3.0/prospects_table.xml
[oracle@myoracledb1 cicd-ws-rep00]$ git push
Enumerating objects: 11, done.
Counting objects: 100% (11/11), done.
Delta compression using up to 4 threads
Compressing objects: 100% (9/9), done.
Writing objects: 100% (9/9), 4.33 KiB | 2.17 MiB/s, done.
Total 9 (delta 4), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (4/4), completed with 2 local objects.
To https://github.com/stephane-duprat/cicd-ws-rep00.git
   7fd6ada..e86189b  main -> main

-- On GitHub, click on cicd-ws-rep00 link in the breadcrumbs at the top of the page. 
-- On the right side, under Releases, click Create a new release. 
-- Create a Release called 'Version 3 production', use Tag version 'V3'. Click Publish release.

Task 5: Working on patch that changes columns in table
******************************************************

-- In this section of the lab Developer #1 is working on a ticket that has been raised for an issue. 
-- This patch can be developed on a separate Git branch. Run these bash commands in the second Terminal window tab to create a new branch called ticket001.

[oracle@myoracledb1 cicd-ws-rep00]$ git checkout -b ticket001
Switched to a new branch 'ticket001'

[oracle@myoracledb1 cicd-ws-rep00]$ git status
On branch ticket001
Untracked files:
  (use "git add <file>..." to include in what will be committed)
	liquibase.properties

nothing added to commit but untracked files present (use "git add" to track)

mkdir v3.1
cd v3.1

sql hr/Oracle_4U@localhost:1521/freepdb1

alter table PROSPECTS set unused (BIRTH_DATE);

alter table PROSPECTS drop column PHONE_NUMBER;

ALTER TABLE prospects ADD credit_limit NUMBER;

SQL> lb generate-object -object-type TABLE -object-name prospects
--Starting Liquibase at 08:29:23 (version 4.17.0 #0 built at 2022-11-02 21:48+0000)

Changelog created and written out to file prospects_table.xml

Operation completed successfully.

-- Update master changelog hr-master.xml to include the patched PROSPECTS table, specifying this is the version 3.1 of the project. 
-- Add these lines after the last </changeSet> line, leaving the last line unchanged.

<include file="./v3.1/prospects_table.xml" relativeToChangelogFile="true"/>
  <changeSet  author="Developer1"  id="tagDatabase-tk001">  
    <tagDatabase  tag="version_3.1"/>  
  </changeSet>
</databaseChangeLog>

-- The file should look like this:

SQL> !cat ../hr-master.xml
<?xml version="1.1" encoding="UTF-8"?>
<databaseChangeLog
  xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
                      http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-4.1.xsd">
  <include file="./v1.0/controller.xml" relativeToChangelogFile="true"/>
  <changeSet  author="Developer1"  id="tagDatabase-v1">
    <tagDatabase  tag="version_1.0"/>
  </changeSet>
  <include file="./v2.0/prospects_table.xml" relativeToChangelogFile="true"/>
  <include file="./v2.0/investment_check_package_spec.xml" relativeToChangelogFile="true"/>
  <include file="./v2.0/investment_check_package_body.xml" relativeToChangelogFile="true"/>
  <changeSet  author="Developer2"  id="tagDatabase-v2">
    <tagDatabase  tag="version_2.0"/>
  </changeSet>
  <include file="./v3.0/hr_events_seq_sequence.xml" relativeToChangelogFile="true"/>
  <include file="./v3.0/hr_events_table.xml" relativeToChangelogFile="true"/>
  <include file="./v3.0/bi_hr_events_trigger.xml" relativeToChangelogFile="true"/>
  <include file="./v3.0/prospects_table.xml" relativeToChangelogFile="true"/>
  <include file="./v3.0/employees_table.xml" relativeToChangelogFile="true"/>
  <changeSet  author="Developer3"  id="tagDatabase-v3">
    <tagDatabase  tag="version_3.0"/>
  </changeSet>
<include file="./v3.1/prospects_table.xml" relativeToChangelogFile="true"/>
  <changeSet  author="Developer1"  id="tagDatabase-tk001">
    <tagDatabase  tag="version_3.1"/>
  </changeSet>
</databaseChangeLog>

-- Validate the file:

SQL> lb validate -changelog-file ./../hr-master.xml
--Starting Liquibase at 09:31:54 (version 4.17.0 #0 built at 2022-11-02 21:48+0000)

-- Loaded 49 change(s)
No validation errors found.

Operation completed successfully.

lb changelog-sync-sql -changelog-file ./../hr-master.xml

--Starting Liquibase at 09:32:40 (version 4.17.0 #0 built at 2022-11-02 21:48+0000)

-- Loaded 49 change(s)
-- *********************************************************************
-- SQL to add all changesets to database history table
-- *********************************************************************
-- Change Log: ./../hr-master.xml
-- Ran at: 4/24/23, 9:32 AM
-- Against: HR@jdbc:oracle:thin:@localhost:1521/freepdb1
-- Liquibase version: 4.17.0
-- *********************************************************************

-- Lock Database
UPDATE HR.DATABASECHANGELOGLOCK SET LOCKED = 1, LOCKEDBY = '172.17.0.1 (172.17.0.1)', LOCKGRANTED = SYSTIMESTAMP WHERE ID = 1 AND LOCKED = 0;

INSERT INTO HR.DATABASECHANGELOG (ID, AUTHOR, FILENAME, DATEEXECUTED, ORDEREXECUTED, MD5SUM, DESCRIPTION, COMMENTS, EXECTYPE, CONTEXTS, LABELS, LIQUIBASE, DEPLOYMENT_ID) VALUES ('eed32d35b0d4944bd0f130bfa41329b004e49d52', '(HR)-Generated', '../v3.1/prospects_table.xml', SYSTIMESTAMP, 48, '8:940b396a09bd03b7702aca63f2530bb5', 'createSxmlObject objectName=PROSPECTS, ownerName=HR', '', 'EXECUTED', NULL, NULL, '4.17.0', '2328767609');

-- Logging Oracle Liquibase extension actions to
 DECLARE
 id varchar2(2000) := 'eed32d35b0d4944bd0f130bfa41329b004e49d52';
 status varchar2(2000) := 'PREPARING';
 rawAction clob;
 rawSxml clob;
 myrow varchar2(2000);
 action clob := '';
 sxml clob := '';
 dep varchar2(2000) := '2328767609';
 author varchar2(2000) := '(HR)-Generated';
 filename varchar2(2000) := '../v3.1/prospects_table.xml';
 insertlog varchar2(2000) := 'insert into HR.DATABASECHANGELOG_ACTIONS (id,author,filename,sql,sxml,deployment_id,status) values (:id,:author,:filename,:action,:sxml,:dep,:status) returning rowid into :out';
 updateaction varchar2(2000) := 'update HR.DATABASECHANGELOG_ACTIONS set sql = sql ||:action where rowid = :myrow ';
 updatesxml varchar2(2000) := 'update HR.DATABASECHANGELOG_ACTIONS set sxml = sxml ||:sxml where rowid = :myrow ';
 begin
action := utl_raw.cast_to_varchar2(utl_encode.base64_decode(utl_raw.cast_to_raw(q'{LS0gb2JqZWN0IGlzIHRoZSBzYW1lIG5vdGhpbmcgdG8gZG8=}')));
sxml := utl_raw.cast_to_varchar2(utl_encode.base64_decode(utl_raw.cast_to_raw(q'{CiAgPFRBQkxFIHhtbG5zPSJodHRwOi8veG1sbnMub3JhY2xlLmNvbS9rdSIgdmVyc2lvbj0iMS4wIj4KICAgPFNDSEVNQT5IUjwvU0NIRU1BPgogICA8TkFNRT5QUk9TUEVDVFM8L05BTUU+CiAgIDxSRUxBVElPTkFMX1RBQkxFPgogICAgICA8Q09MX0xJU1Q+CiAgICAgICAgIDxDT0xfTElTVF9JVEVNPgogICAgICAgICAgICA8TkFNRT5QRVJTT05fSUQ8L05BTUU+CiAgICAgICAgICAgIDxEQVRBVFlQRT5OVU1CRVI8L0RBVEFUWVBFPgogICAgICAgICAgICA8UFJFQ0lTSU9OPjY8L1BSRUNJU0lPTj4KICAgICAgICAgICAgPFNDQUxFPjA8L1NDQUxFPgogICAgICAgICA8L0NPTF9MSVNUX0lURU0+CiAgICAgICAgIDxDT0xfTElTVF9JVEVNPgogICAgICAgICAgICA8TkFNRT5GSVJTVF9OQU1FPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+VkFSQ0hBUjI8L0RBVEFUWVBFPgogICAgICAgICAgICA8TEVOR1RIPjIwPC9MRU5HVEg+CiAgICAgICAgICAgIDxDT0xMQVRFX05BTUU+VVNJTkdfTkxTX0NPTVA8L0NPTExBVEVfTkFNRT4KICAgICAgICAgPC9DT0xfTElTVF9JVEVNPgogICAgICAgICA8Q09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgPE5BTUU+TEFTVF9OQU1FPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+VkFSQ0hBUjI8L0RBVEFUWVBFPgogICAgICAgICAgICA8TEVOR1RIPjI1PC9MRU5HVEg+CiAgICAgICAgICAgIDxDT0xMQVRFX05BTUU+VVNJTkdfTkxTX0NPTVA8L0NPTExBVEVfTkFNRT4KICAgICAgICAgICAgPE5PVF9OVUxMPjwvTk9UX05VTEw+CiAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgICAgPENPTF9MSVNUX0lURU0+CiAgICAgICAgICAgIDxOQU1FPkVNQUlMPC9OQU1FPgogICAgICAgICAgICA8REFUQVRZUEU+VkFSQ0hBUjI8L0RBVEFUWVBFPgogICAgICAgICAgICA8TEVOR1RIPjM3PC9MRU5HVEg+CiAgICAgICAgICAgIDxDT0xMQVRFX05BTUU+VVNJTkdfTkxTX0NPTVA8L0NPTExBVEVfTkFNRT4KICAgICAgICAgPC9DT0xfTElTVF9JVEVNPgogICAgICAgICA8Q09MX0xJU1RfSVRFTT4KICAgICAgICAgICAgPE5BTUU+U0FWSU5HUzwvTkFNRT4KICAgICAgICAgICAgPERBVEFUWVBFPk5VTUJFUjwvREFUQVRZUEU+CiAgICAgICAgIDwvQ09MX0xJU1RfSVRFTT4KICAgICAgICAgPENPTF9MSVNUX0lURU0+CiAgICAgICAgICAgIDxOQU1FPkVYUEVSSUVOQ0U8L05BTUU+CiAgICAgICAgICAgIDxEQVRBVFlQRT5OVU1CRVI8L0RBVEFUWVBFPgogICAgICAgICA8L0NPTF9MSVNUX0lURU0+CiAgICAgICAgIDxDT0xfTElTVF9JVEVNPgogICAgICAgICAgICA8TkFNRT5DUkVESVRfTElNSVQ8L05BTUU+CiAgICAgICAgICAgIDxEQVRBVFlQRT5OVU1CRVI8L0RBVEFUWVBFPgogICAgICAgICA8L0NPTF9MSVNUX0lURU0+CiAgICAgIDwvQ09MX0xJU1Q+CiAgICAgIDxERUZBVUxUX0NPTExBVElPTj5VU0lOR19OTFNfQ09NUDwvREVGQVVMVF9DT0xMQVRJT04+CiAgICAgIDxQSFlTSUNBTF9QUk9QRVJUSUVTPgogICAgICAgICA8SEVBUF9UQUJMRT4KICAgICAgICAgICAgPFNFR01FTlRfQVRUUklCVVRFUz4KICAgICAgICAgICAgICAgPFNFR01FTlRfQ1JFQVRJT05fSU1NRURJQVRFPjwvU0VHTUVOVF9DUkVBVElPTl9JTU1FRElBVEU+CiAgICAgICAgICAgICAgIDxQQ1RGUkVFPjEwPC9QQ1RGUkVFPgogICAgICAgICAgICAgICA8UENUVVNFRD40MDwvUENUVVNFRD4KICAgICAgICAgICAgICAgPElOSVRSQU5TPjE8L0lOSVRSQU5TPgogICAgICAgICAgICAgICA8TUFYVFJBTlM+MjU1PC9NQVhUUkFOUz4KICAgICAgICAgICAgICAgPFNUT1JBR0U+CiAgICAgICAgICAgICAgICAgIDxJTklUSUFMPjY1NTM2PC9JTklUSUFMPgogICAgICAgICAgICAgICAgICA8TkVYVD4xMDQ4NTc2PC9ORVhUPgogICAgICAgICAgICAgICAgICA8TUlORVhURU5UUz4xPC9NSU5FWFRFTlRTPgogICAgICAgICAgICAgICAgICA8TUFYRVhURU5UUz4yMTQ3NDgzNjQ1PC9NQVhFWFRFTlRTPgogICAgICAgICAgICAgICAgICA8UENUSU5DUkVBU0U+MDwvUENUSU5DUkVBU0U+CiAgICAgICAgICAgICAgICAgIDxGUkVFTElTVFM+MTwvRlJFRUxJU1RTPgogICAgICAgICAgICAgICAgICA8RlJFRUxJU1RfR1JPVVBTPjE8L0ZSRUVMSVNUX0dST1VQUz4KICAgICAgICAgICAgICAgICAgPEJVRkZFUl9QT09MPkRFRkFVTFQ8L0JVRkZFUl9QT09MPgogICAgICAgICAgICAgICAgICA8RkxBU0hfQ0FDSEU+REVGQVVMVDwvRkxBU0hfQ0FDSEU+CiAgICAgICAgICAgICAgICAgIDxDRUxMX0ZMQVNIX0NBQ0hFPkRFRkFVTFQ8L0NFTExfRkxBU0hfQ0FDSEU+CiAgICAgICAgICAgICAgIDwvU1RPUkFHRT4KICAgICAgICAgICAgICAgPFRBQkxFU1BBQ0U+VVNFUlM8L1RBQkxFU1BBQ0U+CiAgICAgICAgICAgICAgIDxMT0dHSU5HPlk8L0xPR0dJTkc+CiAgICAgICAgICAgIDwvU0VHTUVOVF9BVFRSSUJVVEVTPgogICAgICAgICAgICA8Q09NUFJFU1M+TjwvQ09NUFJFU1M+CiAgICAgICAgIDwvSEVBUF9UQUJMRT4KICAgICAgPC9QSFlTSUNBTF9QUk9QRVJUSUVTPgogICA8L1JFTEFUSU9OQUxfVEFCTEU+CjwvVEFCTEU+}')));
 execute immediate insertlog using id,author,filename,action,sxml,dep,status returning into myrow;
end;
/

update HR.DATABASECHANGELOG_ACTIONS set status = 'RAN' where id = 'eed32d35b0d4944bd0f130bfa41329b004e49d52' and sequence = (select max(sequence) from HR.DATABASECHANGELOG_ACTIONS where id = 'eed32d35b0d4944bd0f130bfa41329b004e49d52');

INSERT INTO HR.DATABASECHANGELOG (ID, AUTHOR, FILENAME, DATEEXECUTED, ORDEREXECUTED, MD5SUM, DESCRIPTION, COMMENTS, EXECTYPE, CONTEXTS, LABELS, LIQUIBASE, DEPLOYMENT_ID, TAG) VALUES ('tagDatabase-tk001', 'Developer1', '../hr-master.xml', SYSTIMESTAMP, 49, '8:e8ba23b627cd16a7daa848e704ea6e8c', 'tagDatabase', '', 'EXECUTED', NULL, NULL, '4.17.0', '2328767609', 'version_3.1');

-- Release Database Lock
UPDATE HR.DATABASECHANGELOGLOCK SET LOCKED = 0, LOCKEDBY = NULL, LOCKGRANTED = NULL WHERE ID = 1;



Operation completed successfully.

--- Run the previous commands and commit.


SQL> select ID, AUTHOR, FILENAME, orderexecuted ORD, DESCRIPTION, TAG, EXECTYPE
  2*   from DATABASECHANGELOG order by 4 desc;

ID                                          AUTHOR            FILENAME                                        ORD DESCRIPTION                                                          TAG            EXECTYPE
___________________________________________ _________________ ____________________________________________ ______ ____________________________________________________________________ ______________ ___________
tagDatabase-tk001                           Developer1        ../hr-master.xml                                 49 tagDatabase                                                          version_3.1    EXECUTED
eed32d35b0d4944bd0f130bfa41329b004e49d52    (HR)-Generated    ../v3.1/prospects_table.xml                      48 createSxmlObject objectName=PROSPECTS, ownerName=HR                                 EXECUTED
tagDatabase-v3                              Developer3        ../hr-master.xml                                 47 tagDatabase                                                          version_3.0    EXECUTED
f6a472e23495ea356abcd7d53d575683f0665ad3    (HR)-Generated    ../v3.0/employees_table.xml                      46 createSxmlObject objectName=EMPLOYEES, ownerName=HR                                 EXECUTED
dd2e22475b7a54fc9ebd9b1e1135fcce86bc48a8    (HR)-Generated    ../v3.0/prospects_table.xml                      45 createSxmlObject objectName=PROSPECTS, ownerName=HR                                 EXECUTED
16c9f75c45ea4089b26d212d79a3dfe451a2c227    (HR)-Generated    ../v3.0/bi_hr_events_trigger.xml                 44 createOracleTrigger objectName=BI_HR_EVENTS, ownerName=HR                           EXECUTED
5e80225ad636d416d9660bf944c66e1a26c6af42    (HR)-Generated    ../v3.0/hr_events_table.xml                      43 createSxmlObject objectName=HR_EVENTS, ownerName=HR                                 EXECUTED
c2debe824fc7b76fecfeb8c544f592b82f8b1d51    (HR)-Generated    ../v3.0/hr_events_seq_sequence.xml               42 createSxmlObject objectName=HR_EVENTS_SEQ, ownerName=HR                             EXECUTED
tagDatabase-v2                              Developer2        ../hr-master.xml                                 41 tagDatabase                                                          version_2.0    EXECUTED
7a97ef6d7f5c88c013939789036541967b1592ef    (HR)-Generated    ../v2.0/investment_check_package_body.xml        40 createOraclePackageBody objectName=INVESTMENT_CHECK, ownerName=HR                   EXECUTED
62b4ab1d4ee925059a3bc305ed14d87808ea74ab    (HR)-Generated    ../v2.0/investment_check_package_spec.xml        39 createOraclePackageSpec objectName=INVESTMENT_CHECK, ownerName=HR                   EXECUTED
542996f24b29997df8b2a831d71597285b4f998a    (HR)-Generated    ../v2.0/prospects_table.xml                      38 createSxmlObject objectName=PROSPECTS, ownerName=HR                                 EXECUTED
tagDatabase-v1                              Developer1        ../hr-master.xml                                 37 tagDatabase                                                          version_1.0    EXECUTED
5c3de07805546665ea5f89a9da6248912e422dd8    (HR)-Generated    ../v1.0/departments_ref_constraints.xml          36 createOracleRefConstraint objectName=DEPT_LOC_FK, ownerName=HR                      EXECUTED
7bcd599b071b53f135b9774904ed72ded351fc87    (HR)-Generated    ../v1.0/employees_ref_constraints.xml            35 createOracleRefConstraint objectName=EMP_DEPT_FK, ownerName=HR                      EXECUTED
0021967c3f65cc4ae98db87a67c3c6d4d5f6d927    (HR)-Generated    ../v1.0/departments_comments.xml                 34 createOracleComment objectName=DEPARTMENTS_COMMENTS, ownerName=HR                   EXECUTED
c1d5af882c57ec1843cd76d62e0c98bd241ecfee    (HR)-Generated    ../v1.0/regions_comments.xml                     33 createOracleComment objectName=REGIONS_COMMENTS, ownerName=HR                       EXECUTED
3e1cbd6678c4ccd8ce8e58bbe93972a650c36f97    (HR)-Generated    ../v1.0/jobs_comments.xml                        32 createOracleComment objectName=JOBS_COMMENTS, ownerName=HR                          EXECUTED
10401b775a504e30632f69c526f6c2e0f9407481    (HR)-Generated    ../v1.0/job_history_comments.xml                 31 createOracleComment objectName=JOB_HISTORY_COMMENTS, ownerName=HR                   EXECUTED
456d4fb4a910bca941e8657a9a31e33f1ab4cd3c    (HR)-Generated    ../v1.0/employees_comments.xml                   30 createOracleComment objectName=EMPLOYEES_COMMENTS, ownerName=HR                     EXECUTED
abee54702a80b0ef3de339057f8888f784d6c795    (HR)-Generated    ../v1.0/locations_comments.xml                   29 createOracleComment objectName=LOCATIONS_COMMENTS, ownerName=HR                     EXECUTED
6969594a15c66b1c78e3645988e841f7097ba242    (HR)-Generated    ../v1.0/countries_comments.xml                   28 createOracleComment objectName=COUNTRIES_COMMENTS, ownerName=HR                     EXECUTED
70aedb1927b7de9129c6614a3b0b65371ccd8dbc    (HR)-Generated    ../v1.0/update_job_history_trigger.xml           27 createOracleTrigger objectName=UPDATE_JOB_HISTORY, ownerName=HR                     EXECUTED
f6acef9bdfcf96da9691d863ddcd83ee3358034a    (HR)-Generated    ../v1.0/secure_employees_trigger.xml             26 createOracleTrigger objectName=SECURE_EMPLOYEES, ownerName=HR                       EXECUTED
c127f9e94d93f5acda2af24f693bba606d76a244    (HR)-Generated    ../v1.0/dept_location_ix_index.xml               25 createSxmlObject objectName=DEPT_LOCATION_IX, ownerName=HR                          EXECUTED
70b9d8f74b7262e911d32c43e2daac2bacbba29a    (HR)-Generated    ../v1.0/emp_name_ix_index.xml                    24 createSxmlObject objectName=EMP_NAME_IX, ownerName=HR                               EXECUTED
8354362383fb7c8489aaa426489a5fe96d7eb134    (HR)-Generated    ../v1.0/emp_manager_ix_index.xml                 23 createSxmlObject objectName=EMP_MANAGER_IX, ownerName=HR                            EXECUTED
7a8e2352305d3ce3d5a3505d0656bb24ec1e0f96    (HR)-Generated    ../v1.0/emp_email_uk_index.xml                   22 createSxmlObject objectName=EMP_EMAIL_UK, ownerName=HR                              EXECUTED
d73832cfccb9d32aa975a224f2b58cf3efeb5f3f    (HR)-Generated    ../v1.0/emp_job_ix_index.xml                     21 createSxmlObject objectName=EMP_JOB_IX, ownerName=HR                                EXECUTED
4f3fd64504441fdee039736861b8dcd752a6fea1    (HR)-Generated    ../v1.0/jhist_department_ix_index.xml            20 createSxmlObject objectName=JHIST_DEPARTMENT_IX, ownerName=HR                       EXECUTED
b5ce40efc7680b82b1baf63f1100d896967d8665    (HR)-Generated    ../v1.0/loc_city_ix_index.xml                    19 createSxmlObject objectName=LOC_CITY_IX, ownerName=HR                               EXECUTED
7d9a155cc4de6e35746bebaace41d8ed973ddd93    (HR)-Generated    ../v1.0/jhist_employee_ix_index.xml              18 createSxmlObject objectName=JHIST_EMPLOYEE_IX, ownerName=HR                         EXECUTED
9687423a8444cbd4d826963e26f32f030c9933f7    (HR)-Generated    ../v1.0/emp_department_ix_index.xml              17 createSxmlObject objectName=EMP_DEPARTMENT_IX, ownerName=HR                         EXECUTED

ID                                          AUTHOR            FILENAME                                      ORD DESCRIPTION                                                        TAG    EXECTYPE
___________________________________________ _________________ __________________________________________ ______ __________________________________________________________________ ______ ___________
b0783ced5928aa9b6811ffe0d2b4dd765840716c    (HR)-Generated    ../v1.0/loc_state_province_ix_index.xml        16 createSxmlObject objectName=LOC_STATE_PROVINCE_IX, ownerName=HR           EXECUTED
32f76f8ab196f65c5b8ae0c921831c6a7ebc640c    (HR)-Generated    ../v1.0/jhist_job_ix_index.xml                 15 createSxmlObject objectName=JHIST_JOB_IX, ownerName=HR                    EXECUTED
3718348046bdc485651c8286206b48e9af519461    (HR)-Generated    ../v1.0/loc_country_ix_index.xml               14 createSxmlObject objectName=LOC_COUNTRY_IX, ownerName=HR                  EXECUTED
d92d897ec98ec5c2679d8cd01f0485fddd55451a    (HR)-Generated    ../v1.0/add_job_history_procedure.xml          13 createOracleProcedure objectName=ADD_JOB_HISTORY, ownerName=HR            EXECUTED
76a219c8b2af11bf7c23e55e52573a4f1c99299b    (HR)-Generated    ../v1.0/emp_details_view_view.xml              12 createSxmlObject objectName=EMP_DETAILS_VIEW, ownerName=HR                EXECUTED
dc533e0b14fa41e54d49cb28c42ff31a3186009e    (HR)-Generated    ../v1.0/job_history_table.xml                  11 createSxmlObject objectName=JOB_HISTORY, ownerName=HR                     EXECUTED
ad2c536c5636ec056d11ce44b28f4e55807cbd12    (HR)-Generated    ../v1.0/locations_table.xml                    10 createSxmlObject objectName=LOCATIONS, ownerName=HR                       EXECUTED
1dacbd3ff0b3ae34e48d5df9ab3ca052f3995c33    (HR)-Generated    ../v1.0/countries_table.xml                     9 createSxmlObject objectName=COUNTRIES, ownerName=HR                       EXECUTED
5b8196cf470dfee2036694421aaddff307008907    (HR)-Generated    ../v1.0/secure_dml_procedure.xml                8 createOracleProcedure objectName=SECURE_DML, ownerName=HR                 EXECUTED
52334f421d935229140b0468d06157dd45c20f96    (HR)-Generated    ../v1.0/regions_table.xml                       7 createSxmlObject objectName=REGIONS, ownerName=HR                         EXECUTED
84d6c14a5af0d22812c689a42e58e6c0cf300c1e    (HR)-Generated    ../v1.0/jobs_table.xml                          6 createSxmlObject objectName=JOBS, ownerName=HR                            EXECUTED
3679094045b7965245949695613df9351c236f3e    (HR)-Generated    ../v1.0/employees_table.xml                     5 createSxmlObject objectName=EMPLOYEES, ownerName=HR                       EXECUTED
18f3f88289eddcfc2b16fdae44a17169f8fe0d3f    (HR)-Generated    ../v1.0/departments_table.xml                   4 createSxmlObject objectName=DEPARTMENTS, ownerName=HR                     EXECUTED
42e3db1348e500dade36829bab3b7f5343ad6f09    (HR)-Generated    ../v1.0/employees_seq_sequence.xml              3 createSxmlObject objectName=EMPLOYEES_SEQ, ownerName=HR                   EXECUTED
93020a4f5c3fc570029b0695d52763142b6e44e1    (HR)-Generated    ../v1.0/departments_seq_sequence.xml            2 createSxmlObject objectName=DEPARTMENTS_SEQ, ownerName=HR                 EXECUTED
7ec49fad51eb8c0b53fa0128bf6ef2d3fee25d35    (HR)-Generated    ../v1.0/locations_seq_sequence.xml              1 createSxmlObject objectName=LOCATIONS_SEQ, ownerName=HR                   EXECUTED

49 rows selected.

exit

cd /home/oracle/cicd-ws-rep00
git add v3.1/*
*/
git commit -a -m "Version 3 ticket 001: Prospects drop 2 columns, add 1"

[oracle@myoracledb1 cicd-ws-rep00]$ git commit -a -m "Version 3 ticket 001: Prospects drop 2 columns, add 1"
[ticket001 ec7dc2d] Version 3 ticket 001: Prospects drop 2 columns, add 1
 2 files changed, 89 insertions(+)
 create mode 100644 v3.1/prospects_table.xml

[oracle@myoracledb1 cicd-ws-rep00]$ git push --set-upstream origin ticket001
Username for 'https://github.com': stephane-duprat
Password for 'https://stephane-duprat@github.com':
Enumerating objects: 7, done.
Counting objects: 100% (7/7), done.
Delta compression using up to 4 threads
Compressing objects: 100% (4/4), done.
Writing objects: 100% (5/5), 1.42 KiB | 1.42 MiB/s, done.
Total 5 (delta 2), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (2/2), completed with 2 local objects.
remote:
remote: Create a pull request for 'ticket001' on GitHub by visiting:
remote:      https://github.com/stephane-duprat/cicd-ws-rep00/pull/new/ticket001
remote:
To https://github.com/stephane-duprat/cicd-ws-rep00.git
 * [new branch]      ticket001 -> ticket001
Branch 'ticket001' set up to track remote branch 'ticket001' from 'origin'.

-- On GitHub, click on cicd-ws-rep00 link in the breadcrumbs at the top of the page to refresh it. 
-- You will see this message: ticket001 had recent pushes less than a minute ago.

-- Click Compare & pull request > Create pull request. Merge pull request > Confirm merge.

-- When finished, you will receive this message: Pull request successfully merged and closed. Click Delete branch.