# SQLcl and Liquibase

[Oracle SQLcl (SQL Developer Command Line)](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/index.html) is a Java-based command line interface for Oracle Database. Using SQLcl, you can execute SQL and PL/SQL statements in interactive or batch mode

[Liquibase](https://www.liquibase.org/) is an open-source database-independent library for tracking, managing and applying database schema changes. This feature is included in the standalone SQLcl offering, which is different from the SQL Developer installation.

You may use the open-source or Pro version of Liquibase to track and manage your database changes. It has support for additional technologies through the use of JDBC driver connections but is limited to standard database metadata. i.e. Data Dictionary. Liquibase also reads and writes all changesets to a single changelog. 

The Liquibase feature is SQLcl extends the base utility with additional metadata changesets, such as APEX and ORDS, and adds and automates the file splitting capabilities, generating changelog and changesets written using the DBMS_METADATA SXML data format.

You can add the functionality to read these specialized changelogs to the Liquibase client by following the instructions in the [Requirements for Using Liquibase](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/23.4/sqcug/using-liquibase.html#GUID-673321E9-1C06-4B9A-A373-52C2CB5AB7B0) section of the documentation.

Reviewed: 27.03.2024
 
## The Liquibase Feature in SQLcl
SQLcl Liquibase with Oracle Database provides extended functionality to the Liquibase experience compared to the open-source Liquibase client. The Liquibase feature in SQLcl enables you to execute commands to generate a changelog for a single object or for a full schema in specialized changelogs and changesets.


# Table of Contents
 
1. [Team Publications](#team-publications)
2. [Useful Links](#useful-links)
3. [Tutorials / How-To's](#tutorials-how-tos)

 
# Team Publications

- [Start your DevOps adventure with Liquibase on ADB](https://medium.com/@devpiotrekk/start-your-apex-devops-adventure-with-liquibase-f8e45c3d1e6a)

# Useful Links

- [Oracle Documentation - Oracle SQLcl Release 23.3](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/23.3/sqcug/using-liquibase.html#GUID-4CA25386-E442-4D9D-B119-C1ACE6B79539 "Using Liquibase")
- [SQLcl 23.3 Downloads](https://www.oracle.com/database/sqldeveloper/technologies/sqlcl/download/)
- [Liquibase Community](https://www.liquibase.org/)
- [Liquibase Documentation](https://docs.liquibase.com/home.html "What is Liquibase?")
- [Liquibase Documentation](https://docs.liquibase.com/start/release-notes/home.html "Release Notes")
- [Best Practices Recommended by Liquibase](https://docs.liquibase.com/concepts/bestpractices.html "Maximize the effectiveness and efficiency of the Liquibase workflow")

## Scripts

- [APEX Lifecycle Management Technical Paper Scripts](https://apex.oracle.com/go/lifecycle-technical-paper-files "Zip download")

# Tutorials / How-To's

- [Oracle LiveLabs - Capture Oracle Database Changes for CI/CD](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3000)
- [Oracle LiveLabs - Oracle Database Operator for Kubernetes + DevOps](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3393)

## Using SQLcl to Capture and Apply Database Changes

### Setting the format of the DDL generated
Using the SET command to set DDL variables, will modify the behavior of the DDL transform option on DBMS_METADATA. 

```
SET DDL [[ PRETTY | SQLTERMINATOR | CONSTRAINTS | REF_CONSTRAINTS | CONSTRAINTS_AS_ALTER|OID | SIZE_BYTE_KEYWORD | PARTITIONING | SEGMENT_ATTRIBUTES | STORAGE | TABLESPACE | SPECIFICATION | BODY | FORCE | INSERT | |INHERIT | RESET] {on|off} ] | OFF ]
```

For example to exclude table properties such as partitions, compression or tablespace details:

```
set ddl partitioning off
set ddl segment_attributes off
set ddl tablespace off
```

### Generating Change Log - Database Definitions
Connect to the source database with sqlcl and use the Liquibase feature to generate object, schema, APEX and ORDS change logs. The sqlcl generates change logs in the current directory only. Liquibase writes to a single file and the location can be specified.

The examples below will be shown using both full syntax and then again with short commands.

```
-- After connection was made to the source system and changing to the output directory.
-- Generate Liquibase Changelog
liquibase generate-changelog -changelog-file lb-changelog.xml

lb gec -chf lb-changelog.xml

-- Generate Schema (change log file will be controller.xml)
liquibase generate-schema

lb ges

-- Generate Schema split the output with SQL format
liquibase generate-db-object -sql

lb geo -sp -sq

-- Generate Schema Object
liquibase generate-schema

lb ges
```

### Apply Change Log - Database Definitions
Connect to the target database with sqlcl to apply object, schema, APEX and ORDS change logs.

```
-- After connection was made to the target system and changing to the output directory.
liquibase update -changelog-file lb-changelog.xml

lb up -chf lb-changelog.xml

-- Using the controller.xml
liquibase update

lb -up
```

Use the directory structure to manage schema versions by following the [Best Practices recommended by Liquibase](https://docs.liquibase.com/concepts/bestpractices.html)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
