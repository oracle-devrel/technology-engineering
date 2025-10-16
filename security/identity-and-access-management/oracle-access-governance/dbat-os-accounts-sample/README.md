# DBAT OS Accounts Sample

This asset contains the code and deployment steps required to integrate an Oracle Access Governance system with an Oracle Database for the purposes of trusted/target recon which simulates the granting of OS level access to POSIX hosts.

At the time of writing, this capability is not offered natively in OAG.

The described integration and data can be used for all supported user/account lifecycle operations in OAG, including use in access certification. Note that this simulates a connected system, therefore changes to OS level user access will be reflected in the targeted database tables.

Review Date: 04.08.2025

# When to use this asset?

Whenever a system that needs to be integrated with OAG does not have a natively supported connector, but can be easily modeled as data stored inside of database tables.

# How to use this asset?

## Pre-requisites and dependencies

The following components are required and assumed to already be available in this guide:
- A Premium license Oracle Access Governance instance.
- An Oracle Database installation or Oracle Autonomous Database instance (for supported database types and versions, please consult [the OAG integration documentation](https://docs.oracle.com/en/cloud/paas/access-governance/tatoi/index.html#GUID-8C827C87-8D8F-4FCB-9895-F370F25FEB00)).
- A podman/docker installation for the OAG DBAT agent deployment. This installation can be performed on the same host as the Oracle Database, if preferred. Note that otherwise this system must have network access to the above Oracle Database deployment, for a direct DB connection.

## Deployment steps

Please ensure the requirements listed above have been satisfied.

**Once a database installation/instance is available** follow the below steps to deploy the provided sample SQL schema:

1. Connect to the database as dba (with sysdba role) and create a schema user for the purposes of the integration, by running:

**Note:** Please adjust the provided sample sizes and naming as needed.

```
CREATE TABLESPACE oagts
  DATAFILE 'oagts.dat'
    SIZE 100M
    REUSE
    AUTOEXTEND ON NEXT 100M MAXSIZE 500M;

CREATE USER OAG IDENTIFIED BY <your_secure_password>
  DEFAULT TABLESPACE oagts
  TEMPORARY TABLESPACE temp QUOTA UNLIMITED ON oagts;

GRANT CREATE SESSION TO OAG;
GRANT SELECT on dba_role_privs TO OAG;
GRANT SELECT on dba_sys_privs TO OAG;
GRANT SELECT on dba_ts_quotas TO OAG;
GRANT SELECT on dba_tablespaces TO OAG;
GRANT SELECT on dba_users TO OAG;
GRANT CREATE USER TO OAG;
GRANT ALTER ANY TABLE TO OAG;
GRANT GRANT ANY PRIVILEGE TO OAG;
GRANT GRANT ANY ROLE TO OAG;
GRANT DROP USER TO OAG;
GRANT SELECT on dba_roles TO OAG;
GRANT SELECT ON dba_profiles TO OAG;
GRANT ALTER USER TO OAG;
GRANT CREATE ANY TABLE TO OAG;
GRANT DROP ANY TABLE TO OAG;
GRANT CREATE ANY PROCEDURE TO OAG;
GRANT DROP ANY PROCEDURE TO OAG;
```

2. Connect to the database as the newly create OAG user (using the password you've set with the above command), and execute the `OS_Account.sql` file. This will create all the quired table schema and populate it with sample data.

**In order to achieve the DBAT integration in Oracle Access Governance**, follow the below steps to create a new orchestrated system:

**Note:** The Connect URL format provided below is meant for pluggable databases using DB service names. Please adjust it as needed. All types of jdbc URL formats are supported, including basic SID-based URLs such as: `jdbc:oracle:thin:@hostname:port:SID`.

1. Go to **Service Administration -> Manage orchestrated systems**.
2. Click on **+ Add an Orchestrated system**.
3. In the **Select System** step, pick `Database Application Table (Oracle DB)`, and click on Next.
4. In the **Enter Details** step, enter the details provided below. Ensure the `I want to manage permissions for this system.`option **is ticked**. Optionally, ensure the `This is the authoritative source for my identities.` option remains unticked should you want to create the identities through other means, **otherwise please tick it** to ensure that for the purposes of this example the identities will be imported using data from the **OS_ACCOUNT** table. Click on Next.

```
What do you want to call this system?: OS Account
How do you want to describe this system: OS level user account
```

5. Click on Confirm if you are using both authoritative and manager permission integration modes.
6. In the **Add Owners** step, use the default values and click on Next.
7. In the **Account Settings** step, use the default values and click on Next.
8. In the **Integration** step, enter the following details, adjusted to your particular deployment settings. Leave the rest of the fields on their default values, and click on Add.

```
Easy Connect URL for Oracle Database: jdbc:oracle:thin:@//hostname:port/dbservicename
User Name: OAG
Password: <your_secure_password>
Confirm password: <your_secure_password>
User account table name: OS_ACCOUNT
Permissions tables: OS_HOST
Account permission tables: OS_ACCOUNT_HOST
Key column mappings: OS_ACCOUNT:USERID,OS_HOST:HOSTID
Name column mappings: OS_ACCOUNT:USERNAME,OS_HOST:HOSTNAME
User account table password column mapping: OS_ACCOUNT:PASSWORD
User account table status column mapping: OS_ACCOUNT:STATUS
```

9. On the **Finish up** step, first click on the `Download` link and save the agent package, then select `Activate and prepare the data load with the provided defaults` and click on I'm done.
10. Use the downloaded `OS_Account.zip` archive to deploy the OAG agent as per the steps covered in [this guide](https://docs.oracle.com/en/cloud/paas/access-governance/lllho/index.html#GUID-67A8B48F-9358-4B95-A36C-5871E3726FAB). Once the agent is deployed and started, it will automatically validate the configurations and import the data into OAG, and you can start using the integration.

Please also see the useful link below for more detailed deployment steps.

# Useful Links

[Identity Orchestration: Unifying Diverse Systems for Seamless Identity Governance and Management](https://docs.oracle.com/en/cloud/paas/access-governance/seihs/#articletitle)
[Integrate with Database Application Tables (Oracle)](https://docs.oracle.com/en/cloud/paas/access-governance/bdato/#articletitle)

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
