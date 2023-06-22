# Package Name
oradb_discovery_v3_6_11_19.sql

## Description
The Database discovery & analysis tool is a SQL utility that captures necessary details of an oracle database in order to analyse on-Prem or cloud Oracle Databases for the suitability of migration/upgrades. This utility runs on Non Container or Container databases and helps in generating HTML report with detailed description

## Usage
sqlplus "/ as sysdba"  @oradb_discovery_v3_6_11_19.sql

### Step 1
This is a discovery utility for Oracle database compatible for 11g onwards with a below features:
1.	Current version of the script is v3.6 and it supports Oracle 11g or above database
2.	Single version script for both Oracle Multitenant and  Non-Multitenant database
3.	This is a platform independent script as we need sqlplus "/ as sysdba"  to execute only

This script needs to execute on Oracle database server with a user who has “/as sysdba” access
•	Copy the oradb_discovery_v3_6_11_19.sql file to the server
•	To execute the script 	:  sqlplus "/ as sysdba"  @oradb_discovery_v3_6_11_19.sql

### Step 2
The above script will generate .LST as output files on the same location.  
Please deliver the above .LST to Oracle Migration Factory contact which in return we will generate .HTML file at our end and sent it back to you.


## License
Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.

ORACLE AND ITS AFFILIATES DO NOT PROVIDE ANY WARRANTY WHATSOEVER, EXPRESS OR IMPLIED, FOR ANY SOFTWARE, MATERIAL OR CONTENT OF ANY KIND CONTAINED OR PRODUCED WITHIN THIS REPOSITORY, AND IN PARTICULAR SPECIFICALLY DISCLAIM ANY AND ALL IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR PURPOSE.  FURTHERMORE, ORACLE AND ITS AFFILIATES DO NOT REPRESENT THAT ANY CUSTOMARY SECURITY REVIEW HAS BEEN PERFORMED WITH RESPECT TO ANY SOFTWARE, MATERIAL OR CONTENT CONTAINED OR PRODUCED WITHIN THIS REPOSITORY. IN ADDITION, AND WITHOUT LIMITING THE FOREGOING, THIRD PARTIES MAY HAVE POSTED SOFTWARE, MATERIAL OR CONTENT TO THIS REPOSITORY WITHOUT ANY REVIEW. USE AT YOUR OWN RISK.
