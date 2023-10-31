# Oracle Data Pump
 
Oracle Data Pump technology enables very high-speed movement of data and metadata from one database to another. Oracle Data Pump is available only on Oracle Database 10g release 1 (10.1) and later. Data Pump consists of two command-line clients and two PL/SQL packages. The command-line clients, expdp and impdp, provide an easy-to-use interface to the Data Pump export and import utilities. You can use expdp and impdp to export and import entire schemas or databases.

The Data Pump export utility writes the schema objects, including the tables and metadata that constitute mining models, to a dump file set. The Data Pump import utility retrieves the schema objects, including the model tables and metadata, from the dump file set and restores them in the target database.

A set of best practices and other useful assets/links can be found in this page.
 
# Table of Contents
 
1. [Team Publications](#team-publications)
2. [Useful Links](#useful-links)
 
# Team Publications
 
- [Data Pump: Export Best Practices](https://macsdata.netlify.app/oradb/migration/datapump/expdp/bestpractices/)
    - Detailed best practices guide around Oracle Data Pump export (expdp), available on Marcus Doeringer's public platform
- [Data Pump: Import Best Practices](https://macsdata.netlify.app/oradb/migration/datapump/impdp/bestpractices/)
    - Detailed best practices guide around Oracle Data Pump import (impdp), available on Marcus Doeringer's public platform
- [Upload Large Data Pump Files to OCI - using OCI CLI Multipart Uploads](https://www.youtube.com/watch?v=9100uKXquic)
    - YouTube Video by Austine Ouma explaining how to use multipart uploads for large data pump files that need to be uploaded to Oracle Cloud Infrastructure
 
# Useful Links
- [Data Pump in Database 21c LiveLabs Workshop](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=742&clear=RR,180&session=1384894897131)
- [Data Pump Best Practices Whitepaper](https://www.oracle.com/a/ocom/docs/oracle-data-pump-best-practices.pdf)
- [Data Pump Basics - YouTube Video](https://www.youtube.com/watch?v=5uLDxPDErsw)
- [Data Pump Best Practices & Real World Scenarios - YouTube Video](https://www.youtube.com/watch?v=960ToLE-ZE8)
- [Data Pump & SQL Developer Web for Oracle Autonomous Database](https://www.thatjeffsmith.com/archive/2023/02/data-pump-sql-developer-web-for-oracle-autonomous-database/)

# License
 
Copyright (c) 2023 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.