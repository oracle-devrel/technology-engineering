# Enable Observability & Management for Multiple External Database Systems with Terraform
 
This Terraform asset enables Database Management, Operations Insights, and/or Stack Monitoring for multiple external container and pluggable databases based on input from two JSON-files in **root_module**:
- **db_systems.json**
- **db_credentials.json**
 
Reviewed: 21.02.2024
 
## How does it work?

OCI's [External Database Service](https://docs.oracle.com/en-us/iaas/external-database/index.html) handles management agent connections to on-prem database systems. Using these connections, certain services in Observability & Management can then be enabled for the external databases: [Database Management](https://docs.oracle.com/en-us/iaas/database-management/home.htm), [Operations Insights](https://docs.oracle.com/en-us/iaas/operations-insights/home.htm), and [Stack Monitoring](https://docs.oracle.com/en-us/iaas/stack-monitoring/index.html). After [installing management agents](https://docs.oracle.com/en-us/iaas/management-agents/doc/install-management-agent-chapter.html), the Terraform configuration files in this asset can perform the database connection setup for agents and enable Observability & Management services for all external databases

## When to use this asset?
 
This asset is for anyone managing multiple on-prem database systems who needs to enable services in Observability & Management. Instead of spending valuable time doing this manually for each container and pluggable database in the OCI Console, just use these Terraform configuration files to complete the setup for you
 
## How to use this asset?

### Prerequisites

1. Prepare required policies for Management Agent Service, Database Management, Operations Insights, and/or Stack Monitoring:
  - Click [here](https://docs.oracle.com/en-us/iaas/management-agents/doc/perform-prerequisites-deploying-management-agents.html) for more about Management Agent policies
  - Click [here](https://docs.oracle.com/en-us/iaas/database-management/doc/permissions-required-enable-database-management-external-databases.html#DBMGM-GUID-3DDC9D5F-99B8-4DD5-A0C4-194D29FC883F) for more about Database Management policies
  - Click [here](https://docs.oracle.com/en-us/iaas/operations-insights/doc/set-groups-users-and-policies.html) for more about Operations Insights policies
  - Click [here](https://docs.oracle.com/en-us/iaas/stack-monitoring/doc/service-requirements.html) for more about Stack Monitoring policies
2. [Install management agent(s)](https://docs.oracle.com/en-us/iaas/management-agents/doc/install-management-agent-chapter.html) connecting to database systems

    **NOTE**: The management agent can either be installed locally on a database instance host or connect to databases remotely on a separate machine. The agent can connect to and monitor one or more databases

4. [Install Terraform and create RSA keys for API signing](https://docs.oracle.com/en-us/iaas/developer-tutorials/tutorials/tf-provider/01-summary.htm)

    **NOTE**: Remember to save the values in the **configuration file preview** when adding the public API key to an OCI user

### Prepare and apply Terraform configurations

1. Download **root_module** and its configuration files to the machine with the private RSA key and Terraform installation
2. Set configuration options for the OCI provider in **root_module/provider.tf**
   
   **NOTE**: Most options can be set with the configuration file preview values shown when adding a public API key to an OCI user
3. Set **compartment_ocid** variable in **root_module/variables.tf**
   
   **NOTE**: This is the compartment where everything will be managed in the External Database Service: database connections and enablement of services in Observability & Management. This will also be the compartment where all monitoring data will be located across the enabled services
4. Define your database systems in **root_module/db_systems.json**. See **root_module/db_systems_example.json** for an example:
    - Create a database system object for every database system. You can copy-paste the **system1** object as a template in **root_module/db_systems.json**
    
      **NOTE**: You can name the keys for the system objects however you want as long as they are unique e.g. system1, system2, systemA, systemB, Alpha, Beta, etc.
    - For each database system object, copy-paste the template within the **pdbs** array to match the number of pluggable databases per system
    - Now fill out the details for each container and pluggable database in the database system objects as described below:

        | ***Key*** | ***Description*** | ***Mandatory*** |
        |--------------|-----------|------------|
        | **host** | Host name used by management agent for connections with container and pluggable databases in system<br>**NOTE**: It is recommended to use the SCAN hostname for RAC systems | Yes |
        | **port** | Port used by management agent for connections with container and pluggable databases in system | Yes |
        | **protocol** | Protocol used by management agent for connections with container and pluggable databases in system<br>**NOTE**: Must be **TCP** or **TCPS** | Yes |
        | **managementAgentId** | OCID of the management agent connecting to container and pluggable databases in system | Yes |
        | **databaseCredentials** | Key for credential object in **root_module/db_credentials.json** used by management agent for database connections<br>**NOTE**: If **protocol** is set to **TCPS**, the credential object must include **sslSecretId** | Yes |
        | **containerName** | Desired name for container database | Yes |
        | **containerServiceName** | Service name used by management agent for container database connection | Yes |
        | **containerDBManagement** | Add **enable** or **disable** to manage Database Management enablement for container database | Yes |
        | **dbManagementLicense** | Add **BRING_YOUR_OWN_LICENSE** or **LICENSE_INCLUDED** to select the license type used for Database Management. Click [here](https://docs.oracle.com/en-us/iaas/database-management/doc/enable-database-management-external-databases.html) for more | Yes, if **containerDBManagement** is set to **enable** |
        | **containerStackMonitoring** | Add **enable** or **disable** to manage Stack Monitoring enablement for container database | Yes |
        | **asmStackMonitoring** | Add **enable** or **disable** to manage Stack Monitoring enablement for ASM<br>**NOTE**: Enablement requires **containerStackMonitoring** to be **enable** as well | Yes |
        | **asmHost** | Host name used by management agent for ASM connection | Yes, if **asmStackMonitoring** is set to **enable** |
        | **asmPort** | Port used by management agent for ASM connection | Yes, if **asmStackMonitoring** is set to **enable** |
        | **asmServiceName** | Service name used by management agent for ASM connection | Yes, if **asmStackMonitoring** is set to **enable** |
        | **asmCredentials** | Key for credential object in **root_module/db_credentials.json** used by management agent for ASM connection<br>**NOTE**: Credential object must include **userPasswordSecretId** for the ASM password | Yes, if **asmStackMonitoring** is set to **enable** |
        | **pdbName** | Desired name for pluggable database | Yes |
        | **databaseCredentials** | Key for credential object in **root_module/db_credentials.json** used by management agent for database connections<br>**NOTE**: If **protocol** is set to **TCPS**, the credential object must include **sslSecretId** | Yes |
        | **pdbServiceName** | Service name used by management agent for pluggable database connection | Yes |
        | **pdbDBManagement** | Add **enable** or **disable** to manage Database Management enablement for pluggable database<br>**NOTE**: Enablement requires **containerDBManagement** to be **enable** as well | Yes |
        | **pdbStackMonitoring** | Add **enable** or **disable** to manage Database Management enablement for pluggable database<br>**NOTE**: Enablement DOES NOT REQUIRE **containerStackMonitoring** to be **enable** as well | Yes |
        | **pdbOPSI** | Add **enable** or **disable** to manage Operations Insights enablement for pluggable database | Yes |

5. Define your database credentials in **root_module/db_credentials.json**. See **root_module/db_credentials_example.json** for an example:
    - Create a credential object for every credential set used for management agent connections in **root_module/db_systems.json**. You can copy-paste the **cred1** and/or **cred2** objects as templates in **root_module/db_credentials.json**
    - Now fill out the details for each credential object as described below:
        | ***Key*** | ***Description*** | ***Mandatory*** |
        |--------------|-----------|------------|
        | **userName** | Database user name for management agent connections e.g. DBSNMP | Yes |
        | **userPassword** | Database user password in plain text for management agent connections | No, if using **userPasswordSecretId** instead |
        | **userPasswordSecretId** | OCID for encrypted Secret with database user password in OCI Vault. Click [here](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Tasks/managingsecrets.htm) for more<br>**NOTE**: Required to enable Stack Monitoring for ASM | No, if using **userPassword** instead |
        | **userRole** | Database user role for management agent connections<br>**NOTE**: For database connections, **userRole** can be **NORMAL** or **SYSDBA**. For ASM connections, **userRole** can be **SYSASM**, **SYSDBA**, or **SYSOPER** | Yes |
        | **sslSecretId** | OCID for encrypted Secret with JSON containing SSL-settings for database connections via TCPS. Click [here](https://docs.oracle.com/en-us/iaas/external-database/doc/create-connection-external-database.html#EXTUG-GUID-59ECD72C-EAC2-426D-B865-D8DDB1297F0E) for more | Yes, if **protocol** is set to **TCPS** for database system object in **root_module/db_systems.json**|

6. Run the following commands from **root_module** to initialize the Terraform configuration, see its execution plan, and finally apply that plan:
   
    **terraform init**<br>
    **terraform plan**<br>
    **terraform apply**<br>

### Update applied Terraform configurations

To apply new configurations, update **root_module/db_systems.json** and/or **root_module/db_credentials.json** and run **terraform apply** from **root_module** again

### Destroy applied Terraform configurations
To remove everything previously applied by Terraform configurations, run **terraform destroy** from **root_module**
 
## Useful Links
 
- [Oracle](https://www.oracle.com)
    - Oracle's Main Website
- [Terraform Provider](https://registry.terraform.io/providers/oracle/oci/latest/docs)
    - General documentaion for Terraform's Oracle Cloud Infrastructure Provider
- [Management Agent Service](https://docs.oracle.com/en-us/iaas/management-agents/index.html)
    - General documentation for Management Agent Service
- [External Database Service](https://docs.oracle.com/en-us/iaas/external-database/index.html)
    - General documentation for External Database Service
- [Database Management](https://docs.oracle.com/en-us/iaas/database-management/home.htm)
    - General documentation for Database Management
- [Operations Insights](https://docs.oracle.com/en-us/iaas/operations-insights/home.htm)
    - General documentation for Operations Insights
- [Stack Monitoring](https://docs.oracle.com/en-us/iaas/stack-monitoring/index.html)
    - General documentation for Stack Monitoring
 
## License
 
Copyright (c) 2024 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.