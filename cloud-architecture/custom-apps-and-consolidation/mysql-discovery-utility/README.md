# MySQL Database Discovery Utility

MySQL Database Discovery and Analysis Utility is a discovery utility to fetch the database information and the host details. In order to capture complete details of the source MySQL instance, the discovery script will help us fetch the necessary information. It is a shell script with HTML tags embedded to help connect to source instances and fetch the details. This script runs in any flavor of Linux version and any MySQL version 5.6 and above.

## When to use this asset?

This script is to be executed in the discovery phase if it is identified the MySQL on-premises database is to be migrated to OCI.

## How to use this asset?

- Copy ` MySQLdiscovery.sh `  file to the Linux server. 
     
- To execute the script: ``` sh MySQLdiscovery.sh ``` .
The script will generate a DB_REPORT.html file at ` /tmp` location of the server.

## License
Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.
