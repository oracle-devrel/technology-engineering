# Oracle Data Pump
 
Oracle Data Pump technology enables very high-speed movement of data and metadata from one database to another. Oracle Data Pump is available only on Oracle Database 10g release 1 (10.1) and later. Data Pump consists of two command-line clients and two PL/SQL packages. The command-line clients, expdp and impdp, provide an easy-to-use interface to the Data Pump export and import utilities. You can use expdp and impdp to export and import entire schemas or databases.

The Data Pump export utility writes the schema objects, including the tables and metadata that constitute mining models, to a dump file set. The Data Pump import utility retrieves the schema objects, including the model tables and metadata, from the dump file set and restores them in the target database.

A set of best practices and other useful assets/links can be found in this page.

Reviewed: 05.02.2025

 
# Table of Contents
 
1. [Team Publications](#team-publications)
2. [Useful Links](#useful-links)
 
# Team Publications
 
- [Data Pump: Export Best Practices](https://macsdata.com/oracle/data-pump-best-practices-export)
    - Detailed best practices guide around Oracle Data Pump export (expdp), available on Marcus Doeringer's public platform
- [Data Pump: Import Best Practices](https://macsdata.com/oracle/data-pump-best-practices-import)
    - Detailed best practices guide around Oracle Data Pump import (impdp), available on Marcus Doeringer's public platform
- [Upload Large Data Pump Files to OCI - using OCI CLI Multipart Uploads](https://techrochet.com/use-cli-to-upload-large-data-pump-files-to-oci)
    - Blog post by Austine Ouma explaining how to use multipart uploads for large data pump files that need to be uploaded to Oracle Cloud Infrastructure
- [OCI Cloud Shell Data Pump Import into an Autonomous Database](https://techrochet.com/cloud-shell-import-dumps-into-adb)
    - Blog post by Austine Ouma explaining how to perform a Data Pump Import from OCI Cloud Shell to migrate data into an Autonomous Database on OCI
- [Schema-based Oracle SQL Developer Data Pump Jobs](https://youtu.be/amdl4G_HWYc)
    - YouTube Video by Austine Ouma explaining how to run schema-based data pump jobs via SQL Developer
- [SQL Developer Data Pump import into Autonomous Database](https://techrochet.com/sql-developer-data-pump-import)
    - Blog post by Austine Ouma explaining how to run data pump jobs into Autonomous Database from SQL Developer
- [Interactive Command Mode with Oracle Data Pump](https://youtu.be/Xm0Dx-P_RCs)
    - YouTube Video by Austine Ouma explaining how to manage running jobs in Oracle Data Pump
- [Importing large Data Pump dump files into Oracle Base Database on OCI via OCI Object Storage buckets mounted on the database file system](https://youtu.be/dWlzUMcbbo8)
    - YouTube Video by Austine Ouma explaining how to import large data pump dump files into Oracle Base Database on OCI via OCI Object Storage buckets mounted on the database file system
- [OCI Console Data Pump Import Wizard](https://www.youtube.com/watch?v=FZAJezCQjhE)
    - YouTube Video by Austine Ouma explaining how to use the OCI DB Console Import Wizard to import data into Autonomous Database
- [A Complete Guide to Migrate your Data to Autonomous Database and Best Practices](https://medium.com/@snoozrocks/a-complete-guide-to-migrate-your-data-to-autonomous-database-and-best-practices-8e5fbdaa26eb)
    - This blog post provides a high-level overview of the steps to migrate data from a source Oracle Database to the Autonomous Database Cloud using Data Pump and OCI Object Storage
- [Migrate to Oracle Autonomous DB@Azure using Azure blob storage - Video](https://www.youtube.com/watch?v=CtTgweuLG9s)
    - YouTube video by Mihai Costeanu showing how to import data into Oracle Autonomous DB@Azure using Data Pump and Azure blob storage to store the dump files
- [Migrate to Oracle Autonomous DB@Azure using Azure blob storage](https://macsdata.com/oracle/data-pump-import-adb-azure-blob-storage)
    - Migration Guide showing how to import data into Oracle Autonomous DB@Azure using Data Pump and Azure blob storage to store the dump files, available on Marcus Doeringer's public platform
- [Data Pump Log Analyzer](https://github.com/macsdata/data-pump-log-analyzer)
    - The Data Pump Log Analyzer is a powerful Python script designed to parse and analyze Oracle Data Pump log files. The tool provides valuable insights into Data Pump operations key metrics and performance data
- [Data Pump Log Analyzer: Comprehensive Guide](https://macsdata.com/oracle/data-pump-log-analyzer-guide)
    - The ultimate resource for mastering every option in detail and to unlock the full potential of the Python script, available on Marcus Doeringer's public platform
- [How to Perform DataPump Import to Oracle 19c Database using Export dumps on OCI Object Storage ?](https://amalrajputhenchira.wordpress.com/2025/01/17/how-to-perform-datapump-import-to-oracle-19c-database-using-export-dumps-on-oci-object-storage/)
    - Detailed, step-by-step instructions for Performing DataPump Import to Oracle Database 19c with Export dumps on OCI Object Storage , available on Amalraj Puthenchira's public platform
- [Data Pump Bundle Patch](https://macsdata.com/oracle/data-pump-bundle-patch)
    - Overview and complete installation walkthrough with examples for 19c and 23ai databases, available on Marcus Doeringer's public platform
- [Installing DBMS_CLOUD packages in Oracle 23ai (I) and how to use with Data Pump](https://carlosal.wordpress.com/2025/04/01/installing-dbms_cloud-in-oracle-23ai/)
    - Blog article by Carlos Álvarez showing how easy it is to install DBMS_CLOUD packages in Oracle 23ai and how to export and import with Data Pump to and from Object Storage.

# Useful Links
- [Loading Data from Google Cloud Storage to Oracle Database](https://database-heartbeat.com/2024/10/01/google-storage-to-oracle-database/)
- [Data Pump Features LiveLabs Workshop](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=742&clear=RR,180&session=1384894897131)
- [Data Pump Best Practices Whitepaper](https://www.oracle.com/a/ocom/docs/oracle-data-pump-best-practices.pdf)
- [Data Pump Basics - YouTube Video](https://www.youtube.com/watch?v=5uLDxPDErsw)
- [Data Pump Best Practices & Real World Scenarios - YouTube Video](https://www.youtube.com/watch?v=960ToLE-ZE8)
- [Data Pump & SQL Developer Web for Oracle Autonomous Database](https://www.thatjeffsmith.com/archive/2023/02/data-pump-sql-developer-web-for-oracle-autonomous-database/)

# License
 
Copyright (c) 2025 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
