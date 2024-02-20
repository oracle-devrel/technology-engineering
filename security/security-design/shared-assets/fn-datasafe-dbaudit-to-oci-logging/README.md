# Data Safe Audit Database to OCI Logging

Owner: Fabrizio Zarri

Oracle Data Safe is a fully integrated, regional Cloud service focused on data security. It provides a complete and integrated set of features of the Oracle Cloud Infrastructure (OCI) for protecting sensitive and regulated data in Oracle databases.

Oracle Data Safe delivers essential security services for Oracle Autonomous Database, Exadata Database on Dedicated Infrastructure, Oracle Base Database, and Oracle Databases running in OCI. Data Safe also supports on-premises Oracle Databases, Exadata Database on Cloud@Customer, and multicloud deployments. All Oracle Database customers can reduce the risk of a data breach and simplify compliance by using Data Safe to assess configuration and user risk, monitor and audit user activity, and discover, classify, and mask sensitive data.

Oracle Functions is a serverless, highly scalable, fully managed Functions-as-a-Service platform built on Oracle Cloud Infrastructure and powered by the open-source Fn Project engine. Developers can use Oracle Functions to write and deploy code that delivers business value without worrying about provisioning or managing the underlying infrastructure. Oracle Functions is container-native, with functions packaged as Docker container images.

This Reference Architecture describes OCI Logging solution for collecting Oracle Datasafe Oracle DB Audit Logs for continuous monitoring and troubleshooting. An OCI Function pulls audit logs from Data Safe REST API Endpoints regularly and ingests them in OCI Logging. 
From OCI Logging Data Safe DB Audit Logs, can be sent to OCI Logging Analytics, external SIEM, and OCI Object Storage. See [Design Guidance for SIEM Integration](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/siem-integration.htm)

Reviewed: 01.02.2024

# Prerequisites

- Configure Data Safe to get Database Audit Events from Oracle DataBase.

- Configure the OCI Registry username (your OCI username) and OCI Registry user password (your OCI user auth token), See [Generating an Auth Token to Enable Login to Oracle Cloud Infrastructure Registry](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsgenerateauthtokens.htm)

- Create and/or Check IAM Policies to permit Oracle Cloud Infrastructure Registry username to push function image in OCI Registry. See [Policies to Control Repository Access](https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registrypolicyrepoaccess.htm)

- Permission to `manage` the following types of resources in your Oracle Cloud Infrastructure tenancy: `IAM policies`, `Dynamic Group`, `vcns`, `services-gateways`, `route-tables`, `security-lists`, `subnets`, `functions`, `Monitor Alarms`, and `Notifications`.

- Quota to create the following resources: 1 VCN, 1 subnet, 1 Service Gateway, 1 route rule, 1 function, 1 dynamic group, 1 policy in root compartment, 1 Monitor Alarm, and 1 Notification Subscription.

If you don't have the required permissions and quota, contact your tenancy administrator. See [Policy Reference](https://docs.cloud.oracle.com/en-us/iaas/Content/Identity/Reference/policyreference.htm), [Service Limits](https://docs.cloud.oracle.com/en-us/iaas/Content/General/Concepts/servicelimits.htm), [Compartment Quotas](https://docs.cloud.oracle.com/iaas/Content/General/Concepts/resourcequotas.htm).

# Deploy Using Oracle Resource Manager

1. Click [![Deploy to Oracle Cloud](https://oci-resourcemanager-plugin.plugins.oci.oraclecloud.com/latest/deploy-to-oracle-cloud.svg)](https://cloud.oracle.com/resourcemanager/stacks/create?region=home&zipUrl=https://github.com/oracle-devrel/technology-engineering/releases/download/fn-datasafe-to-oci-logging/fn-datasafe-dbaudit-to-oci-logging.zip)

2. If you aren't already signed in, when prompted, enter the tenancy and user credentials.

3. Review and accept the terms and conditions.

4. Select the region where you want to deploy the stack.

5. Follow the on-screen prompts and instructions to create the stack.

6. After creating the stack, click **Terraform Actions**, and select **Plan**.

7. Wait for the job to be completed, and review the plan.

8. To make any changes, return to the Stack Details page, click **Edit Stack**, and make the required changes. Then, run the **Plan** action again.

9. If no further changes are necessary, return to the Stack Details page, click **Terraform Actions**, and select **Apply**.

## Deploy Using the Terraform CLI

## Clone the Module
Now, you'll want a local copy of this repo. You can make that with the commands:

    git clone https://github.com/oracle-devrel/technology-engineering.git
    cd security/security-design/shared-assets/fn-datasafe-dbaudit-to-oci-logging
    ls

## Prerequisites
First off, you'll need to do some pre-deploy setup for Docker and Fn Project inside your machine:

```
sudo su -
yum update
yum install yum-utils
yum-config-manager --enable *addons
yum install docker-engine
groupadd docker
service docker restart
usermod -a -G docker opc
chmod 666 /var/run/docker.sock
exit
curl -LSs https://raw.githubusercontent.com/fnproject/cli/master/install | sh
exit
```

OR

you'll use [Oracle Linux Cloud Developer Image](https://docs.oracle.com/en-us/iaas/oracle-linux/developer/index.htm). The Oracle Linux Cloud Developer image provides the latest development tools, languages, and Oracle Cloud Infrastructure Software Development Kits (SDKs) to rapidly deploy, that include Podman instead of Docker.
The Oracle Linux Cloud Developer image doesn't include Fn Project but it is easy to setup:

```
curl -LSs https://raw.githubusercontent.com/fnproject/cli/master/install | sh
```

Also, please follow this [note](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsinstalldocker.htm#Install_Docker_for_Use_with_Oracle_Functions__section_podman_instead_of_docker). By default, Fn Project (and by extension, OCI Functions) assumes the use of Docker to build and deploy function images. However, the Fn Project also supports Podman as an alternative to Docker. When using Fn Project CLI version 0.6.12 and above, you can set a configuration setting to specify that you want to use Podman instead of Docker. 


## Set Up and Configure Terraform

1. Complete the prerequisites described [here](https://github.com/cloud-partners/oci-prerequisites).   

2. Create a `terraform.tfvars` file, and specify the following variables:

```
# Authentication
tenancy_ocid         = "<tenancy_ocid>"
user_ocid            = "<user_ocid>"
fingerprint          = "<finger_print>"
private_key_path     = "<pem_private_key_path>"

# #OCI Region Identifier (see: https://docs.oracle.com/en-us/iaas/Content/General/Concepts/regions.htm)
region = "<oci_region>"

# Compartment
compartment_ocid = "<compartment_ocid>"

# OCIR
ocir_user_name         = "<ocir_user_name>"  <- OCI Registry username (your OCI username)
ocir_user_password     = "<ocir_user_password>" <- OCI Registry user password (your OCI user auth token)

# Deployment name is used in resource names
deployment_name="<deployment name>"

```

Please note that the `terraform.tfvars` file will include sensitive information and needs to be protected from unauthorized usage.

## Create the Resources
Run the following commands:

    terraform init
    terraform plan
    terraform apply

## Test the stack 

You can test the stack by login/logout in the DB already integrated with Data Safe that generates the DB audit log. The function will load the logs in 1 minute and you can see it in Logging Console.
In the Logging Console will be present a new Log Group (ex. loggr-test-eu-milan-1-fn_ds_to_ol-d54e) and relative 2 logs:
- Log with data from Data Safe: Log Type Custom (example log name: log-test-eu-milan-1-fn_ds_to_ol-d54e)
- Log execution function: Log Type Service (example log name: fn-datasafe-dbaudit-test-eu-milan-1-fn_ds_to_ol-d54e)

## Destroy the Deployment
When you no longer need the deployment, you can run this command to destroy the resources:

    terraform destroy

If there is an error in destroying the object storage bucket, manually delete the bucket and run "terraform destroy" again.

## Test Environment
We tested the terraform script in [Oracle Linux Cloud Developer Image](https://docs.oracle.com/en-us/iaas/oracle-linux/developer/index.htm) and Oracle Resource Manager. 

## Architecture Diagram
![](./images/DatasafetoOCILoggingArchitecture.jpg)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
