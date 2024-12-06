# Database Resource Manager scripts

Use these Database Resource Manager scripts to set up a simple resource plan and consumer groups in a database (PDB) to limit CPU for certain tasks such as redefinition tasks. All scripts must be run as sysdba. Please change the scripts according to your needs. For a detailed description please read the documentation.

Reviewed: 16.04.2024

# When to use this asset?

To learn about database resource manager. 

# How to use this asset?

Run the scripts.

The following scripts help to monitor the setup:
- monitorplan.sql: to monitor the resource plan
- monitorgroup.sql: to monitor the resource group for a user (e.g. after a switch)
- cpu_sess.sql: to monitor resource manager statistics per session
- cpu_user.sql: to display CPU related data for currently active resource consumer groups
- cpu_dop_sess.sql: to display CPU and DOP related data for currently active resource consumer groups
- activeplan.sql: to display active plan and the history of active plans
- throttlingperconsumer.sql: to display information about resources consumed and wait times per consumer group.
Interesting fact: When STATISTICS_LEVEL is set to TYPICAL or ALL, this view contains information about CPU utilization and wait times even when no Resource Manager plan is set or when the Resource Manager plan does not monitor CPU or session resources. Metrics are collected and stored every minute when CPU utilization is not being monitored.

The following scripts helps to setup an environment:
- consumer.sql: to set up the consumer groups
- plan.sql: to set up the resource plan
- planon.sql: switch plan on
- planoff.sql: switch plan off
- removeplan.sql: to remove a resource plan

The foloowing scripts switch a plan or a group to another plan or group:
- switch_sess.sql: to switch a current session to raise or lower resources
- switch_user.sql: to switch a user
- switchplan.sql: to switch a plan

Scripts to test a plan:
- burn.sql: to create REDEF_USER and a program to burn CPU
- burns.sql: to run the script to burn CPU

# Useful Links

## Documentation

- [Database Administrator’s Guide](https://docs.oracle.com/en/database/oracle/oracle-database/19/admin/managing-resources-with-oracle-database-resource-manager.html#GUID-2BEF5482-CF97-4A85-BD90-9195E41E74EF)
- [PL/SQL Packages and Types Reference: DBMS_RESOURCE_MANAGER](https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_RESOURCE_MANAGER.html#GUID-F3B685CB-5F15-4DFB-90FD-6FBBA9B6F6DB)
- [PL/SQL Packages and Types Reference: DBMS_RESOURCE_MANAGER_PRIVS](https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_RESOURCE_MANAGER_PRIVS.html#GUID-B8B082C6-DF53-466B-9B11-1CAFCC3F0509)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
