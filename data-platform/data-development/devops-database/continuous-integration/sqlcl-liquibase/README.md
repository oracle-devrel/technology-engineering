# SQLcl and Liquibase

[Oracle SQLcl (SQL Developer Command Line)](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/index.html) is a Java-based command line interface for Oracle Database. Using SQLcl, you can execute SQL and PL/SQL statements in interactive or batch mode. The Project command was introduced in release 24.3, allowing users to manage the creation and administration of a database application. It is targeted towards enterprise-level applications that require structured release processes.

[Liquibase](https://www.liquibase.org/) is an open-source database-independent library for tracking, managing and applying database schema changes. This feature is included in the standalone SQLcl offering, which is different from the SQL Developer installation.

You may use the open-source or Pro version of Liquibase to track and manage your database changes. It has support for additional technologies through the use of JDBC driver connections but is limited to standard database metadata. i.e. Data Dictionary. Liquibase also reads and writes all changesets to a single changelog. 

The Liquibase feature is SQLcl extends the base utility with additional metadata changesets, such as APEX and ORDS, and adds and automates the file splitting capabilities, generating changelog and changesets written using the DBMS_METADATA SXML data format.

You can add the functionality to read these specialized changelogs to the Liquibase client by following the instructions in the [Requirements for Using Liquibase](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/23.4/sqcug/using-liquibase.html#GUID-673321E9-1C06-4B9A-A373-52C2CB5AB7B0) section of the documentation.

# The Liquibase Feature in SQLcl
SQLcl Liquibase with Oracle Database provides extended functionality to the Liquibase experience compared to the open-source Liquibase client. The Liquibase feature in SQLcl enables you to execute commands to generate a changelog for a single object or for a full schema in specialized changelogs and changesets.

Reviewed: 01.12.2025

# Table of Contents
 
1. [Team Publications](#team-publications)
2. [Useful Links](#useful-links)

# Team Publications

- [Start your DevOps adventure with Liquibase on ADB](https://medium.com/@devpiotrekk/start-your-apex-devops-adventure-with-liquibase-f8e45c3d1e6a)

# Useful Links

- [Oracle Documentation - Oracle SQLcl Release](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/)
- [SQLcl Downloads](https://www.oracle.com/database/sqldeveloper/technologies/sqlcl/download/)
- [Oracle Documentation - Introduction to Database Application CI/CD](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/25.3/sqcug/introduction.html)
- [Liquibase Community](https://www.liquibase.org/)
- [Liquibase Documentation](https://docs.liquibase.com/home.html "What is Liquibase?")
- [Liquibase Documentation](https://docs.liquibase.com/start/release-notes/home.html "Release Notes")
- [Best Practices Recommended by Liquibase](https://docs.liquibase.com/concepts/bestpractices.html "Maximize the effectiveness and efficiency of the Liquibase workflow")

## Blogs
- [ThatJeffSmith - Getting started with Oracle Database CI/CD & SQLcl Projects](https://www.thatjeffsmith.com/archive/2025/05/getting-started-with-sqlcl-projects/)

## Videos & Demos 
- [YouTube - Automating Your SQL and PL/SQL Deployments](https://www.youtube.com/watch?app=desktop&v=oyU11sk51ao)
- [YouTube - Using SQLcl and Liquibase to version your Oracle Database](https://www.youtube.com/watch?v=7A-anQoi6tI)
- [DevOps with Oracle Application Express](https://gotsysdba.com/demo-oci-adb-apex-devops-part1)
- [Autonomous DevOps with Liquibase](https://github.com/mikarinneoracle/atp-ords-liquibase-demo)

## Scripts

- [APEX Lifecycle Management Technical Paper Scripts](https://apex.oracle.com/go/lifecycle-technical-paper-files "Zip download")

## Tutorials / How-To's

- [Database CI/CD Project Automation for a React JS Application](https://livelabs.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=4139)
- [Oracle LiveLabs - Capture Oracle Database Changes for CI/CD](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3000)
- [Take Control of Your Database With Automated Schema Changes](https://livelabs.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3692)
- [Oracle LiveLabs - Oracle Database Operator for Kubernetes + DevOps](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3393)


# License

Copyright (c) 2025 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
