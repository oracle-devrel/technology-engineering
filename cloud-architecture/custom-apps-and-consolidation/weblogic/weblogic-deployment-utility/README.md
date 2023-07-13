# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
# @author: Vasudeva Manikandan

# Weblogic Deployment Utility

This utility allows you to provision a WLS MPI and configure a WebLogic Server domain in Oracle Cloud Infrastructure (OCI) in minutes. It will create and/or configure multiple OCI services such as Compute, Network, OCI Database, Autonomous Database, Identity Cloud Service. The script can be extended to enable Logging, File System, Application Performance Monitoring just by updating the template with right terraform variables and format as outlined in the excel.

## When to use this asset?

This can be used with an OCI Resource Manager stack for WebLogic Server in an existing devops pipeline to quickly provision WebLogic Servers in OCI.
Automate creation of multiple WebLogic Servers for OCI stacks for multiple environments.

## How to use this asset?

1) Install OCI CLI.
2) Install Dependent Python Libraries.
3) Install jq command-line JSON processor if not already installed.
3) Fill in Weblogic MPI Provision template file wl_mpi_template_v2.xlsx`.
4) Run Python Script to read the WLS provision template and generate required JSON.
5) Run OCI CLI Command to create Stack, Update Stack with above JSON and input, Plan and Apply.

### Step 1: Install OCI CLI

1) To install and configure OCICLI, refer https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm for detailed instruction.


### Step 2: Install required python library

1) Install pip using  `sudo yum install python-pip`.
2) Install openpyxl library using `sudo pip3 install openpyxl`.

### Step 3: Create OCI Secret Vault for Weblogic password and DB Password (If JRF)

### Step 4: Update WLS Provisioning Template

Fill in the template file `wl_mpi_template_v2.xlsx`. The template has multiple sheets (Weblogic, Network, LB ,DB and MPI Image specifics (SE_BYOL,EE_BYOL,EE_UCM,SUITE_BYOL,suite_UCM). Update Column 'G' in each of the sheets as per the requirement . Leave the fields blank if it is not applicable or optional. Copy the filled in template file under files directory.

### Step 5: Download Terraform configuration file

You must also download the latest Terraform configuration file as outlined here and rename it as TF_BaseTemplate.zip (https://docs.oracle.com/en/cloud/paas/weblogic-cloud/scripts/download-terraform-configuration-file.html).

### Step 6: Run ./provisionWLS_MPI.sh

Script reads the template excel and converts it to JSON, creates a stack, updates the stack with generated JSON, prepares and applies the plan using the Terraform configuration file TF_BaseTemplate.tf. Check the job status in Console and ensure it succeeds.

### Step 7: Run Apply through OCI Console

Navigate to **Resource Manager - Stack** -> **Job** -> **Apply**

## Useful Links

- https://docs.oracle.com/en/cloud/paas/weblogic-cloud/scripts/terraform-scripts.html.
- https://docs.oracle.com/en/cloud/paas/weblogic-cloud/scripts/download-terraform-configuration-file.html.

## License 

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.