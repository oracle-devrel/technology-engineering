# Oracle Database Continuous Integration Supporting Features
Reviewed: "15.01.2024"

To support LifeCycle changes the Oracle Database & APEX provide serveral PL/SQL Packages to support Metadata management. Maintianing a log or history of changes provides the abaility to track changes over time, associate updates with modification requests or bugs and support analysis of code.

Databases, like files on the desktop, only a single version is saved by the storage engine in a consistent manner, ensuring the data's (metadata) integrity.

The primary PL/SQL package are: 
[DBMS_METADATA](https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_METADATA.html#GUID-F72B5833-C14E-4713-A588-6BDF4D4CBA2A) 
- The DBMS_METADATA package provides a way for you to retrieve metadata from the database dictionary as XML or creation DDL and to submit the XML to re-create the object.

## [APEX_EXPORT](https://docs.oracle.com/en/database/oracle/apex/23.2/aeapi/APEX_EXPORT.html#GUID-6A4628A6-9F86-4394-9938-87A7FFFC7BC8) 
- The APEX_EXPORT package provides APIs to export the definitions of applications, files, feedback, and workspaces to text files.

## [DBMS_CLOUD_REPO](https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/dbms-cloud-repo-package.html#GUID-F8F0037B-6451-4742-9144-9FCE44459F64) 
- The DBMS_CLOUD_REPO package provides for use of and management of cloud hosted code repositories from Oracle Database. Supported cloud code repositories include GitHub, AWS CodeCommit , and Azure Repos.
## ORDS_MODULE 
- ORDS_MODULE provides PL/SQL APIs to manage ORDS objects, oauth clients, priviledges, roles and modules. Currently ORDS_MODULE is only documented in the code of the various packages, functions and views.


# Table of Contents
1. [Team Publications](#team-publications)
2. [Useful Links](#useful-links)
3. [Tutorials / How To's](#tutorials-how-tos)

 
# Team Publications
- ## DevOps with ADB using DBMS_CLOUD
   - [Part 1](https://medium.com/oracledevs/apex-service-can-devops-too-dbms-cloud-on-autonomous-72be9842d2f8)
   - [Part 2](https://medium.com/oracledevs/apex-service-devops-part-2-ed737a4fc583)

# Useful Links
## Documentation
- [DBMS_METADATA](https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_METADATA.html#GUID-F72B5833-C14E-4713-A588-6BDF4D4CBA2A "Oracle Database 19c PL/SQL Packages and Types Reference") 
- [DBMS_METADATA](https://docs.oracle.com/en/database/oracle/oracle-database/19/sutil/using-oracle-dbms_metadata-api.html#GUID-D9B1300F-B21D-416E-8B9B-C542195EF249 "Oracle Database 19c Using the Metadata APIs")
- [APEX_EXPORT](https://docs.oracle.com/en/database/oracle/apex/23.2/aeapi/APEX_EXPORT.html#GUID-6A4628A6-9F86-4394-9938-87A7FFFC7BC8 "APEX 23.2 API Reference")
- [DBMS_CLOUD_REPO](https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/dbms-cloud-repo-package.html#GUID-F8F0037B-6451-4742-9144-9FCE44459F64 "Autonomous Database Supplied Package Reference") 


## [ThatJeffSmith](https://www.thatjeffsmith.com/archive/tag/liquibase/ "That Jeff Smith and Liquibase")
- [BLOG: How to Export Your RESTful Services](https://www.thatjeffsmith.com/archive/2018/12/how-to-export-your-restful-services/)


# Tutorials / How To's
- TBD


# License
 
Copyright (c) 2023 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE]( https://github.com/oracle-devrel/technology-engineering/blob/folder-structure/LICENSE) for more details.
